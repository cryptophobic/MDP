// Port of fight_env/player/player.py.
using System.Collections.Generic;

namespace FightCore
{
    public sealed class Player
    {
        // Exposed for the observation encoder and orchestrator; kept public to
        // mirror the Python code's direct ._model access rather than hide it.
        public readonly PlayerModel Model;

        public Player(string name, int hp = Config.DEFAULT_HP, int stamina = Config.DEFAULT_STAMINA)
        {
            Model = new PlayerModel();
            var stats = new Stats(name, hp, stamina);
            Model.Stats = stats;
            Model.Hp = stats.Hp;
            Model.Stamina = stats.Stamina;
        }

        public bool IsDead => Model.IsDead;

        public void SetShield(Shields shield) => Model.Stats.SetShield(shield);
        public void SetArmour(ArmourTypes armour) => Model.Stats.SetArmour(armour);
        public void SetWeapon(Weapons weapon) => Model.Stats.SetWeapon(weapon);

        public void Tick()
        {
            Processing.ProcessCurrentTask(Model);
            Model.CurrentEvent = Model.Stats.MaterializeEvent(Model.Timeline.CurrentEvent);
            Model.Timeline.Tick();
        }

        public void RequestIntent(ActionType action, int ttl = 1)
        {
            Model.RequestedAction = new Intent(action, ttl);
        }

        public Event Event() => Model.CurrentEvent;

        public bool Fallback() => Processing.TryTransition(Model, FighterTask.FIGHTING_STANCE);

        public bool ProcessIntent()
        {
            var task = Processing.ProcessIntent(Model);
            if (task != FighterTask.NONE)
                return Processing.TryTransition(Model, task);
            return false;
        }

        public void ProcessResponses(List<Response> responses)
        {
            Model.CurrentResponses = responses;
            foreach (var response in responses)
                Processing.ProcessResponse(Model, response);
        }

        public bool Reactive(PlayerSnapshot snapshot)
        {
            var task = Processing.ProcessChanges(Model, snapshot);
            return Processing.TryTransition(Model, task);
        }

        public void Cleanup(bool fallbackResolved, bool intentResolved, bool reactiveResolved)
        {
            if (intentResolved && !reactiveResolved)
                Model.RequestedAction = null;

            if (Model.RequestedAction != null)
            {
                Model.RequestedAction.Ttl -= 1;
                if (Model.RequestedAction.Ttl <= 0)
                    Model.RequestedAction = null;
            }
        }

        public PlayerSnapshot MakeSnapshot() => new PlayerSnapshot(Model);
    }
}