// Port of FightEnv._get_obs and its ACTION_TO_IDX map (fight_env/gym_env.py).
// This is the exact vector the trained policy consumes; the ordering and the
// compact task->index mapping MUST match Python or Sentis inference misbehaves.
using System.Collections.Generic;

namespace FightCore
{
    public static class Observation
    {
        public static readonly Dictionary<FighterTask, int> ActionToIdx =
            new Dictionary<FighterTask, int>
            {
                { FighterTask.NONE, 0 },
                { FighterTask.FIGHTING_STANCE, 1 },
                { FighterTask.ATTACK_1, 2 },
                { FighterTask.DEFENSE, 3 },
                { FighterTask.PARRY, 4 },
                { FighterTask.STUNNED, 5 },
                { FighterTask.HURT, 6 },
                { FighterTask.RIPOSTE, 7 },
                { FighterTask.DEAD, 8 },
            };

        private static int Idx(FighterTask task) =>
            ActionToIdx.TryGetValue(task, out var v) ? v : 0;

        // [my_hp, my_stamina, my_action, my_frame, opp_hp, opp_action, opp_frame]
        public static float[] Encode(Player agent, Player opponent)
        {
            var am = agent.Model;
            var om = opponent.Model;
            return new float[]
            {
                am.Hp,
                am.Stamina,
                Idx(am.Task),
                am.Timeline.FrameOffset,
                om.Hp,
                Idx(om.Task),
                om.Timeline.FrameOffset,
            };
        }
    }
}