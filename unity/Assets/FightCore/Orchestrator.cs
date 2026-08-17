// Port of fight_env/orchestrator/{orchestrator,duel_orchestrator}.py.
using System.Collections.Generic;

namespace FightCore
{
    public sealed class Orchestrator
    {
        private readonly Player _f1;
        private readonly Player _f2;

        public Orchestrator(Player fighter1, Player fighter2)
        {
            _f1 = fighter1;
            _f2 = fighter2;
        }

        // orchestrator.py :: Orchestrator.flow
        public (List<Response> f1Responses, List<Response> f2Responses) Flow()
        {
            var snapshot1 = _f1.MakeSnapshot();
            var snapshot2 = _f2.MakeSnapshot();

            _f1.Tick();
            _f2.Tick();

            // "later distance check here" -> currently always resolved
            var (f1Responses, f2Responses) = ResolveDuel(_f1, _f2);

            bool f1Fallback = _f1.Fallback();
            bool f2Fallback = _f2.Fallback();

            bool f1Intent = _f1.ProcessIntent();
            bool f2Intent = _f2.ProcessIntent();

            bool f1Reactive = _f1.Reactive(snapshot1);
            bool f2Reactive = _f2.Reactive(snapshot2);

            _f1.Cleanup(f1Fallback, f1Intent, f1Reactive);
            _f2.Cleanup(f2Fallback, f2Intent, f2Reactive);

            return (f1Responses, f2Responses);
        }

        // duel_orchestrator.py :: DuelOrchestrator.resolve
        private static (List<Response>, List<Response>) ResolveDuel(Player f1, Player f2)
        {
            var event1 = f1.Event();
            var event2 = f2.Event();

            var (f1Res, f2Res) = Resolution.ResolveDuelists(event1, event2);
            var (f2Res2, f1Res2) = Resolution.ResolveDuelists(event2, event1);

            var f1Responses = new List<Response> { f1Res, f1Res2 };
            var f2Responses = new List<Response> { f2Res, f2Res2 };

            f1.ProcessResponses(f1Responses);
            f2.ProcessResponses(f2Responses);

            return (f1Responses, f2Responses);
        }
    }
}