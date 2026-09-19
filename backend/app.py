import base64
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, File, Form, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import config
from backend.chef.backboard_client import BackboardClient
from backend.chef.brain import handle_message
from backend.chef.memory import MemoryStore
from backend.chef.session import KitchenSession
from backend.models import ChatMessage, ChatReply, Recipe
from backend.recipe_engine.browserbase_client import BrowserbaseClient
from backend.recipe_engine.cache import load_demo_recipe
from backend.recipe_engine.service import get_recipe

app = FastAPI(title="Ramsey")
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


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ramsey"}


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

    result = await handle_message(
        _backboard,
        session,
        memory,
        user_text="",
        audio_input=audio_bytes,
        voice={"stt": "default", "tts": "default"},
    )
    _memory_store.save()

    audio_b64 = base64.b64encode(result["audio"]).decode() if result.get("audio") else None
    return {"reply": result["text"], "tool_calls": result["tool_calls"], "audio_base64": audio_b64, "state": result["state"]}


_frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
