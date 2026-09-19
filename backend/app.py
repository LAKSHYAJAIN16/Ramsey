from pathlib import Path
import secrets
from typing import Dict, Optional
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import config
from backend.chef.backboard_client import BackboardClient
from backend.chef.brain import handle_message
from backend.chef.fridge import suggest_dishes_from_photo
from backend.chef.memory import MemoryStore
from backend.chef.session import KitchenSession
from backend.models import ChatMessage, ChatReply, FridgeSuggestions, ProgressUpdate, Recipe, SafetyCommand
from backend.profiles import ProfileStore
from backend.recipe_engine.browserbase_client import BrowserbaseClient
from backend.recipe_engine.cache import load_demo_recipe
from backend.recipe_engine.service import get_recipe

app = FastAPI(title="Ramsey")
app.add_middleware(SessionMiddleware, secret_key=config.SESSION_SECRET, same_site="lax", https_only=False)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_sessions: Dict[str, KitchenSession] = {}
_memory_store = MemoryStore()
_browserbase = BrowserbaseClient(config.BROWSERBASE_API_KEY, config.BROWSERBASE_PROJECT_ID)
_backboard = BackboardClient(config.BACKBOARD_API_KEY, config.BACKBOARD_MODEL)
_profiles = ProfileStore()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ramsey"}


def _current_profile(request: Request) -> Optional[dict]:
    subject = request.session.get("google_sub")
    return _profiles.get(subject) if subject else None


@app.get("/api/me")
async def api_me(request: Request):
    profile = _current_profile(request)
    return {
        "authenticated": bool(profile),
        "oauth_ready": bool(config.GOOGLE_CLIENT_ID and config.GOOGLE_CLIENT_SECRET),
        "profile": profile,
    }


@app.post("/api/me/progress")
async def api_complete_meal(request: Request, body: ProgressUpdate):
    subject = request.session.get("google_sub")
    if not subject:
        raise HTTPException(status_code=401, detail="Sign in to save cooking progress.")
    profile = _profiles.add_completed_meal(subject, body.calories)
    if not profile:
        raise HTTPException(status_code=401, detail="Profile no longer exists.")
    return profile


@app.get("/api/auth/google/login")
async def google_login(request: Request):
    if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured on this server.")
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    params = urlencode({
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@app.get("/api/auth/google/callback")
async def google_callback(request: Request, code: str = Query(...), state: str = Query(...)):
    expected_state = request.session.pop("oauth_state", None)
    if not expected_state or not secrets.compare_digest(state, expected_state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state.")
    token_payload = {
        "code": code,
        "client_id": config.GOOGLE_CLIENT_ID,
        "client_secret": config.GOOGLE_CLIENT_SECRET,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        token_response = await client.post("https://oauth2.googleapis.com/token", data=token_payload)
        if token_response.is_error:
            raise HTTPException(status_code=502, detail="Google token exchange failed.")
        access_token = token_response.json().get("access_token")
        user_response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if user_response.is_error:
        raise HTTPException(status_code=502, detail="Google profile lookup failed.")
    user = user_response.json()
    if not user.get("sub") or not user.get("email"):
        raise HTTPException(status_code=502, detail="Google did not return a usable profile.")
    _profiles.upsert_google_user(user["sub"], user["email"], user.get("name") or user["email"], user.get("picture"))
    request.session["google_sub"] = user["sub"]
    return RedirectResponse(url="/app/")


@app.post("/api/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return {"ok": True}


def _safety_response(phrase: str) -> Optional[dict]:
    normalized = phrase.strip().lower()
    if "code red" in normalized:
        return {"command": "code_red", "message": "Potential emergency detected. Confirm before calling emergency services."}
    if "code yellow" in normalized:
        return {"command": "code_yellow", "message": "Kitchen safety tips ready."}
    return None


@app.post("/api/safety/command")
async def api_safety_command(body: SafetyCommand):
    """Voice/STT adapters can send their transcript here before normal chat.

    Code Red intentionally never dials emergency services automatically. The
    client must show a deliberate, accessible confirmation action first.
    """
    response = _safety_response(body.phrase)
    return response or {"command": None, "message": "No safety command detected."}


@app.get("/api/recipe", response_model=Recipe)
async def api_get_recipe(dish: str = Query(...), demo: bool = Query(False), session_id: str = Query("default")):
    recipe = load_demo_recipe() if demo else await get_recipe(_browserbase, dish)
    _sessions[session_id] = KitchenSession(recipe)
    return recipe


@app.get("/api/session/{session_id}")
async def api_get_session(session_id: str):
    session = _sessions.get(session_id)
    if session is None:
        return {"error": "no active session"}
    return session.to_state_dict()


@app.post("/api/chat", response_model=ChatReply)
async def api_chat(message: ChatMessage):
    safety = _safety_response(message.text)
    if safety:
        return ChatReply(reply=safety["message"], tool_calls=[safety])
    session = _sessions.get(message.session_id)
    if session is None:
        session = KitchenSession(load_demo_recipe())
        _sessions[message.session_id] = session

    memory = _memory_store.get(message.session_id)
    result = await handle_message(_backboard, session, memory, message.text)
    _memory_store.save()

    return ChatReply(
        reply=result["text"],
        tool_calls=result["tool_calls"],
        recipe=session.recipe,
    )


class ActionRequest(BaseModel):
    action: str
    index: Optional[int] = None


def _get_or_create_session(session_id: str) -> KitchenSession:
    session = _sessions.get(session_id)
    if session is None:
        session = KitchenSession(load_demo_recipe())
        _sessions[session_id] = session
    return session


@app.post("/api/session/{session_id}/action")
async def api_session_action(session_id: str, body: ActionRequest):
    """Direct pinch/controller actions - Back / Timer / Next / tick ingredient.

    Kept separate from /api/chat so a button press never has to round-trip
    through the model.
    """
    session = _get_or_create_session(session_id)

    if body.action == "next":
        session.next_step()
    elif body.action == "back":
        session.back_step()
    elif body.action == "repeat":
        pass
    elif body.action == "start_timer":
        session.start_timer()
    elif body.action == "toggle_ingredient" and body.index is not None:
        session.toggle_ingredient(body.index)
    else:
        return {"error": f"unknown or incomplete action: {body.action}"}

    return session.to_state_dict()


@app.post("/api/chat/voice")
async def api_chat_voice(session_id: str = Form(...), audio: UploadFile = File(...)):
    """Hold-to-talk: record on the headset, Backboard does STT + model + TTS
    server-side, so nothing depends on browser Web Speech support.
    """
    session = _get_or_create_session(session_id)
    memory = _memory_store.get(session_id)
    audio_bytes = await audio.read()

    # Provider/model choice here is a guess (docs.backboard.io/sdk/voice
    # shows the {"stt": {...}, "tts": {...}} shape but not a default
    # provider) - swap in a real one once a key is live (Tier 0).
    result = await handle_message(
        _backboard,
        session,
        memory,
        user_text="",
        audio_input=audio_bytes,
        voice={"stt": {"provider": "elevenlabs"}, "tts": {"provider": "elevenlabs"}},
    )
    _memory_store.save()

    return {
        "reply": result["text"],
        "tool_calls": result["tool_calls"],
        "audio_url": result["audio_url"],
        "state": result["state"],
    }


@app.post("/api/fridge/analyze", response_model=FridgeSuggestions)
async def api_fridge_analyze(photo: UploadFile = File(...)):
    """Photo of a fridge/pantry -> dish name ideas. Take the recipe race
    from there with the normal /api/recipe?dish=... call once the cook
    picks one - this endpoint only suggests, it doesn't fetch full recipes.
    """
    image_bytes = await photo.read()
    return await suggest_dishes_from_photo(_backboard, image_bytes, photo.filename or "fridge.jpg")


_project_root = Path(__file__).resolve().parent.parent
_frontend_dir = _project_root / "frontend"
_homepage_dir = _project_root / "homepage"

@app.get("/app")
async def app_redirect():
    return RedirectResponse(url="/app/")


# Order matters: more specific mounts must be registered before the
# catch-all "/" mount, or the app would never be reached.
if _frontend_dir.exists():
    app.mount("/app", StaticFiles(directory=str(_frontend_dir), html=True), name="app")
if _homepage_dir.exists():
    app.mount("/", StaticFiles(directory=str(_homepage_dir), html=True), name="homepage")
