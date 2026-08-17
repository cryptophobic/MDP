// Port of fight_env/player/processing/{task,intent,reactive,response}_processing.py.
using System.Collections.Generic;
using System.Linq;

namespace FightCore
{
    public static class Processing
    {
        // -------- task_processing.py --------

        public static bool TryTransition(PlayerModel model, FighterTask candidate)
        {
            if (model.Timeline.Expired)
            {
                SetTask(model, candidate);
                return true;
            }

            if (model.Task == candidate)
                return false;

            var current = Tasks.Data[model.Task];
            var incoming = Tasks.Data[candidate];

            bool prioritised = incoming.Priority > current.Priority;

            if (!prioritised && current.Priority == incoming.Priority)
            {
                if (model.Timeline.FrameNumber == 0)
                    prioritised = incoming.StartPriority > current.StartPriority;

                if (!prioritised && current.Interruptible)
                    prioritised = true;
            }

            if (prioritised)
            {
                SetTask(model, candidate);
                return true;
            }

            return false;
        }

        public static void SetTask(PlayerModel model, FighterTask task)
        {
            var taskData = Tasks.Data[task];

            model.Task = task;

            model.Timeline = new TaskTimeline(
                duration: taskData.Duration,
                loop: taskData.Loop,
                events: taskData.EventsByFrame);

            // NOTE: the stats-adjusted calc_stamina_cost_* path is commented out in
            // the Python set_task; the live code uses the raw base costs. Mirror that.
            model.StaminaCostEnterTask = taskData.BaseStaminaCost;
            model.StaminaCostFrame = taskData.BaseStaminaCostFrame;
        }

        public static void ProcessCurrentTask(PlayerModel model)
        {
            if (model.Timeline.FrameNumber == 0)
                model.Stamina -= model.StaminaCostEnterTask;

            if (model.Timeline.Expired)
            {
                SetTask(model, FighterTask.NONE);
                return; // early return: no frame cost / clamp this tick
            }

            model.Stamina -= model.StaminaCostFrame;
            if (model.Stamina > model.Stats.MaxStamina)
                model.Stamina = model.Stats.MaxStamina;
        }

        // -------- intent_processing.py --------

        private static FighterTask ResolveAttack(PlayerModel model)
        {
            if (model.CurrentResponses.Any(r => r.Type == Responses.HAS_RIPOSTE_WINDOW_OPEN))
                return FighterTask.RIPOSTE;
            return FighterTask.ATTACK_1;
        }

        public static FighterTask ProcessIntent(PlayerModel model)
        {
            var action = model.RequestedAction != null ? model.RequestedAction.Action : ActionType.NONE;
            var task = IntentMapping.IntentTask[action];
            if (task == FighterTask.ATTACK_1)
                task = ResolveAttack(model);
            return task;
        }

        // -------- reactive_processing.py --------

        public static FighterTask ProcessChanges(PlayerModel current, PlayerSnapshot last)
        {
            if (current.Hp <= 0)
                return FighterTask.DEAD;
            if (current.Hp < last.Hp)
                return FighterTask.HURT;
            if (current.Stamina <= 0)
                return FighterTask.STUNNED;
            if (current.Task == FighterTask.NONE)
                return FighterTask.FIGHTING_STANCE;
            if (last.Task == FighterTask.STUNNED)
                return current.Stamina >= current.Stats.MaxStamina / 2
                    ? FighterTask.FIGHTING_STANCE
                    : FighterTask.STUNNED;

            return FighterTask.NONE;
        }

        // -------- response_processing.py --------

        private const int INSTANT_STUN = 9999;

        public static void ProcessResponse(PlayerModel state, Response response)
        {
            if (response.Type == Responses.DEAD)
            {
                state.IsDead = true;
                return;
            }

            int staminaCost = StaminaCostOnResponse(state.Stats, response);
            if (staminaCost == INSTANT_STUN)
                staminaCost = state.Stamina - Config.STAMINA_BOTTOM_LIMIT;

            state.Stamina -= staminaCost;

            int hpCost = HpCostOnResponse(state.Stats, response);
            state.Hp = System.Math.Max(state.Hp - hpCost, 0);
        }

        private static int StaminaCostOnResponse(Stats stats, Response response)
        {
            switch (response.Type)
            {
                case Responses.HAS_BLOCKED:
                    return stats.Shield.Weight + 2 * response.Value - stats.Shield.Defense;
                case Responses.HAS_BEEN_BLOCKED:
                    return stats.Weapon.Weight + response.Value;
                case Responses.HAS_BEEN_PARRIED:
                    return INSTANT_STUN;
                default:
                    return 0;
            }
        }

        private static int HpCostOnResponse(Stats stats, Response response)
        {
            switch (response.Type)
            {
                case Responses.HAS_BEEN_ATTACKED:
                    return response.Value - stats.Armour.Defense;
                default:
                    return 0;
            }
        }
    }
}