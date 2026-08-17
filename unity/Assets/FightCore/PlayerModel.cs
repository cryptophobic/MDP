// Port of fight_env/player/player_model.py and player_snapshot.py.
using System.Collections.Generic;

namespace FightCore
{
    public sealed class PlayerModel
    {
        public FighterTask Task = FighterTask.NONE;
        public TaskTimeline Timeline = new TaskTimeline();
        public Stats Stats;
        public Event CurrentEvent;
        public List<Response> CurrentResponses = new List<Response>();
        public Intent RequestedAction;

        public int StaminaCostFrame;
        public int StaminaCostEnterTask;

        public bool IsDead;

        public int Hp;
        public int Stamina;
    }

    // fight_env/player/player_snapshot.py :: PlayerSnapshot
    public sealed class PlayerSnapshot
    {
        public readonly int Hp;
        public readonly int MaxHp;
        public readonly int Stamina;
        public readonly int MaxStamina;
        public readonly FighterTask Task;
        public readonly int FrameOffset;
        public readonly string Name;

        public PlayerSnapshot(PlayerModel model)
        {
            Hp = model.Hp;
            MaxHp = model.Stats.MaxHp;
            Stamina = model.Stamina;
            MaxStamina = model.Stats.MaxStamina;
            Task = model.Task;
            Name = model.Stats.Name;
            FrameOffset = model.Timeline.FrameOffset;
        }
    }
}