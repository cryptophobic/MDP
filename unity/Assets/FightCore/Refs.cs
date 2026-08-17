// Port of fight_env/player/refs/{tasks,events,intents}.py enums and value types.
// Enum integer values MUST match the Python IntEnum values verbatim: the parity
// fixtures record task/response ints, and the observation encoder depends on them.
using System.Collections.Generic;

namespace FightCore
{
    // fight_env/player/refs/tasks.py :: FighterTask
    public enum FighterTask
    {
        NONE = 0,
        FIGHTING_STANCE = 1,
        ATTACK_1 = 2,
        ATTACK_2 = 3,
        ATTACK_3 = 4,
        DEAD = 5,
        DEFENSE = 6,
        STUNNED = 7,
        HURT = 8,
        PARRY = 9,
        POWER_PUNCH_1 = 10,
        POWER_PUNCH_2 = 11,
        RIPOSTE = 12,
        ROLLING = 13,
        RUN = 14,
        SHIELD_STRIKE = 15,
        WALK = 16,
        IDLE = 17,
        JUMP = 18,
        JUMP_STRIKE = 19,
        BLOW_TO_SHIELD = 20,
    }

    // fight_env/player/refs/events.py :: Events
    public enum Events
    {
        NONE = 0,
        ATTACK = 1,
        BLOCK = 2,
        PARRY = 3,
        DEAD = 4,
        ANY = 6,
        CRITICAL_ATTACK = 7,
        STUNNED = 8,
        ATTACK_STARTED = 9,
    }

    // fight_env/player/refs/events.py :: Responses
    public enum Responses
    {
        NONE = 0,
        HAS_ATTACKED = 1,
        HAS_BEEN_ATTACKED = 2,
        HAS_BLOCKED = 3,
        HAS_BEEN_BLOCKED = 4,
        HAS_PARRIED = 5,
        HAS_BEEN_PARRIED = 6,
        DEAD = 7,
        WON = 8,
        HAS_RIPOSTED = 9,
        HAS_BEEN_RIPOSTED = 10,
        HAS_DEFENSE_BROKEN = 11,
        HAS_BEEN_DEFENSE_BROKEN = 12,
        HAS_RIPOSTE_WINDOW_OPEN = 13,
    }

    // fight_env/player/refs/intents.py :: ActionType
    public enum ActionType
    {
        NONE = 0,
        ATTACK = 1,
        BLOCK = 2,
        PARRY = 3,
    }

    // fight_env/player/refs/events.py :: Event (frozen dataclass)
    public readonly struct Event
    {
        public readonly Events Type;
        public readonly int Value;
        public Event(Events type, int value = 0) { Type = type; Value = value; }
    }

    // fight_env/player/refs/events.py :: Response (frozen dataclass)
    public readonly struct Response
    {
        public readonly Responses Type;
        public readonly int Value;
        public Response(Responses type, int value = 0) { Type = type; Value = value; }
    }

    // fight_env/player/refs/intents.py :: Intent (mutable: ttl decrements)
    public sealed class Intent
    {
        public ActionType Action;
        public int Ttl;
        public bool Resolved;
        public Intent(ActionType action, int ttl = 0) { Action = action; Ttl = ttl; }
    }

    // fight_env/player/refs/intents.py :: intent_task_mapping
    public static class IntentMapping
    {
        public static readonly Dictionary<ActionType, FighterTask> IntentTask =
            new Dictionary<ActionType, FighterTask>
            {
                { ActionType.NONE, FighterTask.NONE },
                { ActionType.ATTACK, FighterTask.ATTACK_1 },
                { ActionType.BLOCK, FighterTask.DEFENSE },
                { ActionType.PARRY, FighterTask.PARRY },
            };
    }
}