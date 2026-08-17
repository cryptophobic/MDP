// Maps a policy's discrete action index -> ActionType.
// Mirrors AGENT_ACTIONS in fight_env/gym_env.py: [NONE, ATTACK, BLOCK, PARRY].
using FightCore;

namespace FightUnity
{
    public static class AgentActions
    {
        private static readonly ActionType[] Table =
        {
            ActionType.NONE,   // 0
            ActionType.ATTACK, // 1
            ActionType.BLOCK,  // 2
            ActionType.PARRY,  // 3
        };

        public static ActionType Map(int actionIndex) =>
            (actionIndex >= 0 && actionIndex < Table.Length) ? Table[actionIndex] : ActionType.NONE;
    }
}