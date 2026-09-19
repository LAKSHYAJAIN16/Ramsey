"""The WATCHING/CORRECTING state machine that decides what to DO with a
CookingCheck - see docs/vision.md. Routes corrections through the existing
brain.py persona/tool-call loop instead of a parallel text path, so a
correction actually sounds like Ramsey and gets logged via
memory.remember_mistake() (already existed on CookMemory, never called
by anything until now).

vision.py stays pure (photo in, structured result out, no side
effects); this module is where the state lives.
"""
from typing import Any, Dict, List, Optional, Tuple

from backend.chef.brain import handle_message
from backend.chef.memory import CookMemory
from backend.chef.session import KitchenSession, PendingCorrection
from backend.chef.vision import StationCheck, check_cooking


def _is_mistake(station: StationCheck) -> bool:
    if station.matches_expected_step is False:
        return True
    return station.doneness in ("overcooked", "burnt")


def _is_resolved(station: StationCheck) -> bool:
    return station.matches_expected_step is not False and station.doneness not in ("overcooked", "burnt")


def _observation_text(dish: str, vessel: str, station: StationCheck, escalating: bool) -> str:
    contents = ", ".join(station.contents) or "nothing visible"
    prefix = "Still not right after a correction" if escalating else "Doesn't look right for the current step"
    return (
        f"[camera] Looking at the {vessel} while making {dish}. Contents: {contents}. "
        f"{prefix}: {station.note or station.doneness}."
    )


def _single_pending(session: KitchenSession) -> Tuple[Optional[str], Optional[PendingCorrection]]:
    # Only used to focus the vision prompt on one specific open issue when
    # there's exactly one - with several open at once the prompt stays
    # generic and each station is judged independently below regardless.
    if len(session.pending_corrections) == 1:
        vessel, pc = next(iter(session.pending_corrections.items()))
        return vessel, pc
    return None, None


async def monitor_cooking(
    client: Any,
    session: KitchenSession,
    memory: CookMemory,
    image_bytes: bytes,
    filename: str,
) -> Dict[str, Any]:
    """One frame in, one decision out per vessel in frame. See docs/vision.md."""
    state = session.to_state_dict()
    dish = state["title"]
    current_step = state["current_step"]

    _, focus = _single_pending(session)
    check = await check_cooking(
        client, image_bytes, filename, dish, current_step,
        pending_issue=focus.issue if focus else None,
    )

    station_results: List[Dict[str, Any]] = []
    replies: List[Dict[str, Optional[str]]] = []

    for station in check.stations:
        vessel = station.vessel
        existing = session.pending_correction_for(vessel)

        if existing is not None:
            if _is_resolved(station):
                session.resolve_correction(vessel)
                station_results.append({"vessel": vessel, "action": "confirmed"})
                replies.append({"vessel": vessel, "text": "Better - carry on.", "audio_url": None})
            elif existing.cooldown_elapsed:
                session.flag_correction(vessel, station.note or existing.issue)
                observation = _observation_text(dish, vessel, station, escalating=True)
                result = await handle_message(client, session, memory, observation)
                station_results.append({"vessel": vessel, "action": "correction", "note": station.note})
                replies.append({"vessel": vessel, "text": result["text"], "audio_url": result.get("audio_url")})
            else:
                station_results.append({"vessel": vessel, "action": "silent"})
            continue

        if _is_mistake(station):
            issue = station.note or f"doesn't match the current step ({station.doneness})"
            session.flag_correction(vessel, issue)
            memory.remember_mistake(f"{dish}: {vessel} - {issue}")
            observation = _observation_text(dish, vessel, station, escalating=False)
            result = await handle_message(client, session, memory, observation)
            station_results.append({"vessel": vessel, "action": "correction", "note": issue})
            replies.append({"vessel": vessel, "text": result["text"], "audio_url": result.get("audio_url")})
        else:
            station_results.append({"vessel": vessel, "action": "silent"})

    return {
        "objects": check.objects,
        "stations": station_results,
        "replies": replies,
        "state": session.to_state_dict(),
    }
