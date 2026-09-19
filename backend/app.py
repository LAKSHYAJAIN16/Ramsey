import asyncio
import base64
import secrets
import time
from pathlib import Path
from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile, WebSocket, WebSocketDisconnect
from starlette.requests import HTTPConnection
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import config
from backend.chef.backboard_client import BackboardClient
from backend.chef.brain import handle_message
from backend.chef.cooking_monitor import monitor_cooking
from backend.chef.fridge import suggest_dishes_from_photo
from backend.chef.kitchen_spots import KitchenSpotStore
from backend.chef.memory import MemoryStore
from backend.chef.session import KitchenSession
from backend.chef.step_assist import assess_frame
from backend.chef.vision import check_cooking, check_hazard, check_kitchen_setup, identify_spot
from backend.firebase_auth import verify_firebase_id_token
from backend.models import (
    ChatMessage,
    ChatReply,
    CookingCheck,
    FridgeSuggestions,
    HazardCheck,
    KitchenSetup,
    ProgressUpdate,
    Recipe,
    SafetyCommand,
    SpotIdentification,
)
from backend.profiles import ProfileStore
from backend.recipe_engine.browserbase_client import BrowserbaseClient
from backend.recipe_engine.cache import load_demo_recipe
from backend.recipe_engine.service import get_recipe, RecipeNotFound

async def require_cook(connection: HTTPConnection):
    path = connection.url.path
    if path in {"/health", "/api/me", "/api/auth/firebase", "/api/auth/logout", "/api/pair", "/app"}:
        return
    uid = connection.session.get("firebase_uid")
    token = connection.headers.get("authorization", "").removeprefix("Bearer ")
    grant = _quest_tokens.get(token)
    if grant and grant[2] < time.monotonic():
        _quest_tokens.pop(token, None); grant = None
    if not uid and not grant:
        raise HTTPException(401, "Sign in with Google before starting a cooking session.")
    sid = connection.path_params.get("session_id") or connection.query_params.get("session_id")
    if path == '/api/recipe' and not sid: sid = 'default'
    body = {}
    if isinstance(connection, Request) and connection.method in {"POST", "DELETE"}:
        if "application/json" in connection.headers.get("content-type", ""):
            try: body = await connection.json()
            except ValueError: body = {}
        elif "multipart/form-data" in connection.headers.get("content-type", ""):
            body = await connection.form()
        if hasattr(body, "get"):
            sid = sid or body.get("session_id")
    if grant:
        if path not in {f"/api/session/{grant[0]}", f"/api/session/{grant[0]}/action", "/api/chat", "/api/chat/voice", "/api/vision/assist"} or sid != grant[0]:
            raise HTTPException(403, "Quest access is limited to its paired cooking session.")
        uid = grant[1]
    if sid:
        session = _sessions.get(sid)
        if session and session.owner_uid != uid:
            raise HTTPException(403, "This cooking session belongs to another user.")
        if not session and path != "/api/recipe" and not path.endswith("/recipe"):
            raise HTTPException(404, "Select a recipe on the desktop first.")
    if path.startswith('/api/kitchen/spots'):
        kitchen_id = connection.query_params.get('kitchen_id') or (body.get('kitchen_id') if hasattr(body, 'get') else None)
        if kitchen_id != uid:
            raise HTTPException(403, "Kitchen spots belong to your profile.")


app = FastAPI(title="Ramsey", dependencies=[Depends(require_cook)])
app.add_middleware(SessionMiddleware, secret_key=config.SESSION_SECRET, same_site="lax", https_only=False)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_sessions: Dict[str, KitchenSession] = {}
_pair_codes: dict[str, tuple[str, float]] = {}
_quest_tokens: dict[str, tuple[str, str, float]] = {}
_memory_store = MemoryStore()
_browserbase = BrowserbaseClient(config.BROWSERBASE_API_KEY, config.BROWSERBASE_PROJECT_ID)
_backboard = BackboardClient(config.BACKBOARD_API_KEY, config.BACKBOARD_MODEL)
_profiles = ProfileStore()
_kitchen_spots = KitchenSpotStore()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ramsey"}


def _current_profile(request: Request) -> Optional[dict]:
    uid = request.session.get("firebase_uid")
    return _profiles.get(uid) if uid else None


@app.get("/api/me")
async def api_me(request: Request):
    profile = _current_profile(request)
    return {
        "authenticated": bool(profile),
        "uid": request.session.get("firebase_uid") if profile else None,
        "oauth_ready": bool(config.FIREBASE_PROJECT_ID),
        "profile": profile,
    }


@app.post("/api/me/progress")
async def api_complete_meal(request: Request, body: ProgressUpdate):
    uid = request.session.get("firebase_uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Sign in to save cooking progress.")
    profile = _profiles.add_completed_meal(uid, body.calories)
    if not profile:
        raise HTTPException(status_code=401, detail="Profile no longer exists.")
    return profile


class FirebaseSignIn(BaseModel):
    idToken: str


@app.post("/api/auth/firebase")
async def firebase_sign_in(request: Request, body: FirebaseSignIn):
    if not config.FIREBASE_PROJECT_ID:
        raise HTTPException(status_code=503, detail="Firebase is not configured on this server.")
    try:
        claims = await verify_firebase_id_token(body.idToken)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Firebase token: {exc}")
    if not claims.get("email"):
        raise HTTPException(status_code=502, detail="Firebase did not return a usable profile.")
    try:
        _profiles.upsert_firebase_user(claims["sub"], claims["email"], claims.get("name") or claims["email"], claims.get("picture"))
    except RuntimeError as exc:
        raise HTTPException(503, "Google verified your account, but profile storage is not configured. Add the Firebase Admin service account to the desktop backend.") from exc
    request.session["firebase_uid"] = claims["sub"]
    return {
        "authenticated": True,
        "uid": claims["sub"],
        "oauth_ready": True,
        "profile": _profiles.get(claims["sub"]),
    }


@app.post("/api/auth/logout")
async def logout(request: Request):
    uid = request.session.get("firebase_uid")
    for token, grant in list(_quest_tokens.items()):
        if grant[1] == uid: del _quest_tokens[token]
    for code, (sid, _) in list(_pair_codes.items()):
        if sid in _sessions and _sessions[sid].owner_uid == uid: del _pair_codes[code]
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
async def api_get_recipe(request: Request, dish: str = Query(...), demo: bool = Query(False), session_id: str = Query("default")):
    try:
        recipe = load_demo_recipe() if demo else await get_recipe(_browserbase, dish)
    except RecipeNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, "Recipe search provider is unavailable. Try again shortly; no demo was substituted.") from exc
    _sessions[session_id] = KitchenSession(recipe)
    _sessions[session_id].owner_uid = request.session.get("firebase_uid")
    return recipe


@app.get("/api/session/{session_id}")
async def api_get_session(session_id: str):
    session = _sessions.get(session_id)
    if session is None:
        return {"error": "no active session"}
    _save_session_completion(session)
    return session.to_state_dict()


@app.post("/api/session/{session_id}/pair")
async def create_pair_code(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(404, "Choose a recipe on the desktop first.")
    now = time.monotonic()
    for key, (sid, expiry) in list(_pair_codes.items()):
        if expiry < now or sid == session_id:
            del _pair_codes[key]
    code = secrets.token_hex(4).upper()
    _pair_codes[code] = (session_id, now + 600)
    return {"code": code, "expires_in": 600}


class PairRequest(BaseModel):
    code: str


@app.post("/api/pair")
async def join_pair(body: PairRequest):
    entry = _pair_codes.pop(body.code.strip().upper(), None)
    if not entry or entry[1] < time.monotonic() or entry[0] not in _sessions:
        raise HTTPException(404, "Pairing code invalid or expired. Generate a new one on the desktop.")
    sid = entry[0]
    token = secrets.token_urlsafe(32)
    _quest_tokens[token] = (sid, _sessions[sid].owner_uid, time.monotonic() + 12 * 3600)
    return {"session_id": sid, "token": token, "state": _sessions[sid].to_state_dict()}


@app.post("/api/session/{session_id}/recipe")
async def api_load_session_recipe(request: Request, session_id: str, recipe: Recipe):
    """Start a session from the Quest's bundled or cached recipe."""
    if not recipe.steps or not all(step.strip() for step in recipe.steps) or not recipe.title.strip():
        raise HTTPException(status_code=422, detail="A recipe needs a title and non-empty steps.")
    session = KitchenSession(recipe)
    session.owner_uid = request.session.get("firebase_uid")
    _sessions[session_id] = session
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

    memory = _memory_store.get(session.owner_uid or message.session_id)
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


def _save_session_completion(session: KitchenSession):
    if session.completed and session.owner_uid and not session.profile_saved:
        try:
            profile = _profiles.add_completed_meal(session.owner_uid, 0, session.completion_id)
            session.profile_saved = profile is not None
        except Exception:
            # Completion remains visible locally; retry on the next session read.
            session.profile_saved = False


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
    elif body.action == "complete":
        session.complete()
    elif body.action == "start_timer":
        session.start_timer()
    elif body.action == "toggle_ingredient" and body.index is not None:
        session.toggle_ingredient(body.index)
    else:
        return {"error": f"unknown or incomplete action: {body.action}"}

    _save_session_completion(session)
    return session.to_state_dict()


@app.post("/api/vision/assist")
async def api_vision_assist(session_id: str = Form(...), photo: UploadFile = File(...), plating: bool = Form(True)):
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(404, "Pair with an active desktop recipe first.")
    if session.monitor_busy:
        raise HTTPException(409, "A camera check is already running.")
    session.monitor_busy = True
    try:
        image = await photo.read(4 * 1024 * 1024 + 1)
        if not image or len(image) > 4 * 1024 * 1024:
            raise HTTPException(413, "Send a non-empty image under 4 MB.")
        result = await assess_frame(_backboard, session, image, photo.filename or "kitchen.jpg", plating)
        if _sessions.get(session_id) is not session:
            return {"state": _sessions[session_id].to_state_dict(), "advanced": False, "message": "Recipe changed; checking again shortly."}
        _save_session_completion(session)
        result["state"] = session.to_state_dict()
        return result
    finally:
        session.monitor_busy = False


@app.post("/api/chat/voice")
async def api_chat_voice(session_id: str = Form(...), audio: UploadFile = File(...)):
    """Hold-to-talk: record on the headset, Backboard does STT + model + TTS
    server-side, so nothing depends on browser Web Speech support.
    """
    session = _get_or_create_session(session_id)
    memory = _memory_store.get(session.owner_uid or session_id)
    audio_bytes = await audio.read(4 * 1024 * 1024 + 1)
    if not audio_bytes or len(audio_bytes) > 4 * 1024 * 1024:
        raise HTTPException(413, "Send a non-empty recording under 4 MB.")

    # Explicit provider/model/voice, per Backboard's HTTP voice contract.
    result = await handle_message(
        _backboard,
        session,
        memory,
        user_text="",
        audio_input=audio_bytes,
        voice={
            "stt": {"provider": "elevenlabs", "model": "scribe_v2"},
            "tts": {"provider": "openai", "model": "tts-1", "voice": "alloy", "output_format": "mp3"},
        },
    )
    _memory_store.save()

    return {
        "reply": result["text"],
        "tool_calls": result["tool_calls"],
        "audio_url": result["audio_url"],
        "transcript": result.get("transcript"),
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


@app.post("/api/vision/identify-spot", response_model=SpotIdentification)
async def api_identify_spot(photo: UploadFile = File(...)):
    """Unity headset camera photo of a real-world surface -> a best-guess
    label (Stove/Counter/Sink/...), for the cook to confirm before pinning
    a spatial anchor there.
    """
    image_bytes = await photo.read()
    return await identify_spot(_backboard, image_bytes, photo.filename or "spot.jpg")


@app.post("/api/vision/check-cooking", response_model=CookingCheck)
async def api_check_cooking(session_id: str = Form(...), photo: UploadFile = File(...)):
    """One-shot vision check: every cooking vessel in frame, contents,
    doneness, and whether each matches the current step. No state-machine
    side effects (no correction tracking, no memory writes) - for a manual
    "check now" trigger or the phone-fallback path. WS /ws/vision/{id}
    is the stateful version Unity actually streams to during a cook.
    """
    session = _get_or_create_session(session_id)
    image_bytes = await photo.read()
    state = session.to_state_dict()
    return await check_cooking(_backboard, image_bytes, photo.filename or "dish.jpg", state["title"], state["current_step"])


@app.post("/api/vision/check-hazard", response_model=HazardCheck)
async def api_check_hazard(photo: UploadFile = File(...)):
    """Smoke/fire/boil-over check. Informational only - never triggers an
    automatic emergency call. A "high" severity result should surface the
    same manual-confirmation Code Red dialog the voice-triggered phrase
    already does (see _safety_response below).
    """
    image_bytes = await photo.read()
    return await check_hazard(_backboard, image_bytes, photo.filename or "hazard.jpg")


@app.post("/api/vision/scan-kitchen", response_model=KitchenSetup)
async def api_scan_kitchen(session_id: str = Form(...), photo: UploadFile = File(...)):
    """Wide shot of the kitchen before cooking starts -> what equipment/
    ingredients are visibly ready, and what the recipe needs that isn't.
    Meant to run once at session start, not per-step.
    """
    session = _get_or_create_session(session_id)
    image_bytes = await photo.read()
    return await check_kitchen_setup(_backboard, image_bytes, photo.filename or "kitchen.jpg", session.recipe.title, session.recipe.ingredients)


@app.websocket("/ws/vision/{session_id}")
async def ws_vision_monitor(websocket: WebSocket, session_id: str):
    """The streaming/stateful path: Unity holds this open during an active
    cook and sends a frame whenever it wants a check; results push back as
    they finish. Two concurrent loops, not one sequential one: receiving
    always keeps only the LATEST frame (overwriting anything unprocessed),
    while a separate loop analyzes whatever's freshest whenever it's free -
    so a burst of frames while one analysis is in flight gets collapsed
    down to the newest one, never queued and processed late. See docs/vision.md.
    """
    await websocket.accept()
    session = _get_or_create_session(session_id)
    memory = _memory_store.get(session_id)
    latest: Dict[str, Any] = {}
    frame_available = asyncio.Event()

    async def receive_loop():
        while True:
            latest["payload"] = await websocket.receive_json()
            frame_available.set()

    async def process_loop():
        while True:
            await frame_available.wait()
            frame_available.clear()
            payload = latest.get("payload") or {}
            image_bytes = base64.b64decode(payload.get("image_b64", "")) if payload.get("image_b64") else b""
            if not image_bytes:
                await websocket.send_json({"error": "no image"})
                continue
            result = await monitor_cooking(_backboard, session, memory, image_bytes, payload.get("filename", "frame.jpg"))
            _memory_store.save()
            await websocket.send_json(result)

    receiver = asyncio.ensure_future(receive_loop())
    processor = asyncio.ensure_future(process_loop())
    try:
        await asyncio.wait([receiver, processor], return_when=asyncio.FIRST_COMPLETED)
    except WebSocketDisconnect:
        pass
    finally:
        receiver.cancel()
        processor.cancel()


class KitchenSpotCreate(BaseModel):
    kitchen_id: str
    label: str


@app.post("/api/kitchen/spots")
async def api_create_kitchen_spot(body: KitchenSpotCreate):
    """Unity POSTs a confirmed, labeled spatial anchor here so it's backed
    by the Python backend, not just on-device Unity storage.
    """
    return _kitchen_spots.add(body.kitchen_id, body.label)


@app.get("/api/kitchen/spots")
async def api_list_kitchen_spots(kitchen_id: str = Query(...)):
    return _kitchen_spots.list(kitchen_id)


@app.delete("/api/kitchen/spots/{spot_id}")
async def api_delete_kitchen_spot(spot_id: str, kitchen_id: str = Query(...)):
    _kitchen_spots.remove(kitchen_id, spot_id)
    return {"ok": True}


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
