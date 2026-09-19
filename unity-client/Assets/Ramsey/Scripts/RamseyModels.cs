using System;

namespace Ramsey
{
    [Serializable] public class Recipe { public string title, source_url, method; public int servings; public string[] ingredients, steps; }
    [Serializable] public class KitchenState { public string title, current_step, error; public int step_index, total_steps, points; public bool completed; public string[] ingredients; public int[] checked_ingredients; public TimerState[] timers; }
    [Serializable] public class TimerState { public string label; public int remaining_seconds; }
    [Serializable] public class SessionAction { public string action; public int index; }
    [Serializable] public class ChatRequest { public string session_id, text; }
    [Serializable] public class ChatResponse { public string reply, audio_url, transcript; public KitchenState state; public Recipe recipe; }
    [Serializable] public class Station { public string vessel, doneness, note; public string[] contents; }
    [Serializable] public class CookingResponse { public Station[] stations; public string[] objects; }
    [Serializable] public class ClientConfig { public string backendUrl = ""; }
    [Serializable] public class PairRequest { public string code; }
    [Serializable] public class PairResponse { public string session_id, token; public KitchenState state; }
    [Serializable] public class AssistObservation { public string hazard; public string[] plating_tips; }
    [Serializable] public class EquipmentDetection { public string label; public float confidence, x, y, width, height; }
    [Serializable] public class AssistResponse { public string message, audio_url; public bool advanced; public KitchenState state; public AssistObservation observation; public EquipmentDetection[] equipment; }
}
