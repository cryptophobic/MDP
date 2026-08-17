// C# port of fight_env/bots/aggressive.py — a scripted opponent for the demo.
// Lives in FightUnity (not FightCore) so randomness stays out of the
// deterministic, parity-tested core.
using FightCore;

namespace FightUnity
{
    public sealed class AggressiveBot
    {
        private readonly Player _player;
        private readonly Player _opponent;
        private readonly System.Random _rng;

        public AggressiveBot(Player player, Player opponent, int seed = 12345)
        {
            _player = player;
            _opponent = opponent;
            _rng = new System.Random(seed);
        }

        public void NextMove()
        {
            var snap = _opponent.MakeSnapshot();

            if (snap.Task == FighterTask.ATTACK_1 && snap.FrameOffset == 1)
            {
                if (_rng.NextDouble() > 0.3) { _player.RequestIntent(ActionType.BLOCK); return; }
            }

            if (snap.Task == FighterTask.RIPOSTE && snap.FrameOffset == 2)
            {
                if (_rng.NextDouble() > 0.3) { _player.RequestIntent(ActionType.BLOCK); return; }
            }

            if (snap.Task == FighterTask.STUNNED)
            {
                if (_rng.NextDouble() > 0.3) _player.RequestIntent(ActionType.ATTACK);
                return;
            }

            if (snap.Stamina >= snap.MaxStamina / 2)
            {
                if (_rng.NextDouble() > 0.8) _player.RequestIntent(ActionType.ATTACK);
            }
        }
    }
}