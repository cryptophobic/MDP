// Port of fight_env/player/refs/events.py :: resolution_table + Rule.
using System;
using System.Collections.Generic;

namespace FightCore
{
    public sealed class Rule
    {
        public readonly Func<Event, Event, bool> When;
        public readonly Func<Event, Event, (Response, Response)> Emit;
        public Rule(Func<Event, Event, bool> when, Func<Event, Event, (Response, Response)> emit)
        { When = when; Emit = emit; }
    }

    public static class Resolution
    {
        private static Response R(Responses t, int v = 0) => new Response(t, v);

        // Keyed by ordered event pair. Lookup tries (a,b) then (a, ANY),
        // matching _resolve_duelists in duel_orchestrator.py.
        public static readonly Dictionary<(Events, Events), List<Rule>> Table =
            new Dictionary<(Events, Events), List<Rule>>
            {
                { (Events.STUNNED, Events.ANY), new List<Rule> {
                    new Rule((a, b) => true,
                             (a, b) => (R(Responses.NONE), R(Responses.HAS_RIPOSTE_WINDOW_OPEN)))
                } },
                { (Events.DEAD, Events.ANY), new List<Rule> {
                    new Rule((a, b) => true,
                             (a, b) => (R(Responses.DEAD), R(Responses.WON)))
                } },
                { (Events.ATTACK, Events.ANY), new List<Rule> {
                    new Rule((a, b) => true,
                             (a, b) => (R(Responses.HAS_ATTACKED, a.Value),
                                        R(Responses.HAS_BEEN_ATTACKED, a.Value)))
                } },
                { (Events.ATTACK, Events.PARRY), new List<Rule> {
                    new Rule((a, b) => true,
                             (a, b) => (R(Responses.HAS_BEEN_PARRIED, a.Value),
                                        R(Responses.HAS_PARRIED, a.Value)))
                } },
                { (Events.ATTACK, Events.BLOCK), new List<Rule> {
                    new Rule((a, b) => a.Value <= b.Value,
                             (a, b) => (R(Responses.HAS_BEEN_BLOCKED, a.Value),
                                        R(Responses.HAS_BLOCKED, a.Value))),
                    new Rule((a, b) => a.Value > b.Value,
                             (a, b) => (R(Responses.HAS_DEFENSE_BROKEN, a.Value - b.Value),
                                        R(Responses.HAS_BEEN_DEFENSE_BROKEN, a.Value - b.Value))),
                } },
            };

        // duel_orchestrator.py :: _resolve_duelists
        public static (Response, Response) ResolveDuelists(Event e1, Event e2)
        {
            var keys = new[] { (e1.Type, e2.Type), (e1.Type, Events.ANY) };
            foreach (var key in keys)
            {
                if (Table.TryGetValue(key, out var rules))
                {
                    foreach (var rule in rules)
                        if (rule.When(e1, e2))
                            return rule.Emit(e1, e2);
                }
            }
            return (R(Responses.NONE), R(Responses.NONE));
        }
    }
}