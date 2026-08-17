// EditMode parity tests: replay each Python-generated fixture through FightCore
// and assert frame-for-frame equality. Mirrors scratchpad/parity_runner locally.
//
// Requires the Newtonsoft JSON package: add "com.unity.nuget.newtonsoft-json"
// via Package Manager (Add package by name) if it is not already present.
//
// Fixtures are read from the canonical Python location (repo-root/parity/
// trajectories) so there is a single source of truth. This is EditMode-only,
// so reading outside Assets/ is fine.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using FightCore;
using Newtonsoft.Json.Linq;
using NUnit.Framework;
using UnityEngine;

namespace FightCore.Tests
{
    public class ParityTests
    {
        private static string FixtureDir =>
            Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "parity", "trajectories"));

        // One test case per fixture file.
        public static IEnumerable<string> Fixtures()
        {
            var dir = FixtureDir;
            if (!Directory.Exists(dir)) yield break;
            foreach (var f in Directory.GetFiles(dir, "*.json").OrderBy(f => f))
                yield return Path.GetFileName(f);
        }

        private static Player MakePlayer(string name)
        {
            var p = new Player(name);
            p.SetArmour(ArmourTypes.LIGHT_ARMOUR);
            p.SetShield(Shields.BUCKLER);
            p.SetWeapon(Weapons.GLADIUS);
            return p;
        }

        [Test]
        [TestCaseSource(nameof(Fixtures))]
        public void Replays_Fixture_Frame_For_Frame(string fixtureName)
        {
            var path = Path.Combine(FixtureDir, fixtureName);
            Assert.IsTrue(File.Exists(path), $"Fixture not found: {path}");

            var root = JObject.Parse(File.ReadAllText(path));
            var frames = (JArray)root["frames"];

            var agent = MakePlayer("agent");
            var opp = MakePlayer("opponent");
            var orch = new Orchestrator(agent, opp);

            foreach (var f in frames)
            {
                int fIdx = (int)f["frame"];

                if (fIdx >= 0)
                {
                    int a = (int)f["agent_action"];
                    int b = (int)f["opponent_action"];
                    if (a != (int)ActionType.NONE) agent.RequestIntent((ActionType)a);
                    if (b != (int)ActionType.NONE) opp.RequestIntent((ActionType)b);
                    orch.Flow();
                }

                AssertFighter($"f{fIdx}.agent", (JObject)f["agent"], agent);
                AssertFighter($"f{fIdx}.opponent", (JObject)f["opponent"], opp);
                AssertObs($"f{fIdx}.obs", (JArray)f["obs"], agent, opp);
                AssertResponses($"f{fIdx}.agent_responses", (JArray)f["agent_responses"], agent);
                AssertResponses($"f{fIdx}.opponent_responses", (JArray)f["opponent_responses"], opp);

                if (agent.IsDead || opp.IsDead) break;
            }
        }

        private static void AssertFighter(string ctx, JObject exp, Player p)
        {
            Assert.AreEqual((int)exp["hp"], p.Model.Hp, $"{ctx}.hp");
            Assert.AreEqual((int)exp["stamina"], p.Model.Stamina, $"{ctx}.stamina");
            Assert.AreEqual((int)exp["task"], (int)p.Model.Task, $"{ctx}.task");
            Assert.AreEqual((int)exp["frame_offset"], p.Model.Timeline.FrameOffset, $"{ctx}.frame_offset");
            Assert.AreEqual((bool)exp["is_dead"], p.Model.IsDead, $"{ctx}.is_dead");
        }

        private static void AssertObs(string ctx, JArray exp, Player agent, Player opp)
        {
            var got = Observation.Encode(agent, opp);
            Assert.AreEqual(exp.Count, got.Length, $"{ctx}.length");
            for (int i = 0; i < got.Length; i++)
                Assert.AreEqual((double)exp[i], got[i], 1e-6, $"{ctx}[{i}]");
        }

        private static void AssertResponses(string ctx, JArray exp, Player p)
        {
            var got = p.Model.CurrentResponses;
            Assert.AreEqual(exp.Count, got.Count, $"{ctx}.count");
            for (int i = 0; i < got.Count; i++)
            {
                var pair = (JArray)exp[i];
                Assert.AreEqual((int)pair[0], (int)got[i].Type, $"{ctx}[{i}].type");
                Assert.AreEqual((int)pair[1], got[i].Value, $"{ctx}[{i}].value");
            }
        }
    }
}