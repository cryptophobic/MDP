// Maps FighterTask -> sliced sprite frames, loaded from Resources/Animations.
// Mirrors fight_env/player/refs/animations.py (same sheet-per-task mapping).
using System.Collections.Generic;
using FightCore;
using UnityEngine;

namespace FightUnity
{
    public static class AnimationLibrary
    {
        // FighterTask -> sheet file base name (matches animations.py).
        private static readonly Dictionary<FighterTask, string> SheetName =
            new Dictionary<FighterTask, string>
            {
                { FighterTask.ATTACK_1, "Attack_1" },
                { FighterTask.ATTACK_2, "Attack_2" },
                { FighterTask.ATTACK_3, "Attack_3" },
                { FighterTask.BLOW_TO_SHIELD, "Blow_to_shield" },
                { FighterTask.DEAD, "Dead" },
                { FighterTask.DEFENSE, "Defense" },
                { FighterTask.FIGHTING_STANCE, "Fighting_Stance" },
                { FighterTask.HURT, "Hurt" },
                { FighterTask.IDLE, "Idle" },
                { FighterTask.JUMP, "Jump" },
                { FighterTask.JUMP_STRIKE, "Jump_Strike" },
                { FighterTask.PARRY, "Parry" },
                { FighterTask.POWER_PUNCH_1, "Power_punch_1" },
                { FighterTask.POWER_PUNCH_2, "Power_punch_2" },
                { FighterTask.RIPOSTE, "Riposte" },
                { FighterTask.ROLLING, "Rolling" },
                { FighterTask.RUN, "Run" },
                { FighterTask.SHIELD_STRIKE, "Shield_Strike" },
                { FighterTask.STUNNED, "Stunned" },
                { FighterTask.WALK, "Walk" },
            };

        private static readonly Dictionary<FighterTask, Sprite[]> _cache =
            new Dictionary<FighterTask, Sprite[]>();

        // Returns the ordered frames for a task, or the FIGHTING_STANCE frames as
        // a fallback for tasks with no sheet (e.g. NONE). Null only if art missing.
        public static Sprite[] Frames(FighterTask task)
        {
            if (_cache.TryGetValue(task, out var cached))
                return cached;

            if (!SheetName.TryGetValue(task, out var baseName))
            {
                var fallback = task == FighterTask.FIGHTING_STANCE
                    ? null
                    : Frames(FighterTask.FIGHTING_STANCE);
                _cache[task] = fallback;
                return fallback;
            }

            var sprites = Resources.LoadAll<Sprite>("Animations/" + baseName);
            if (sprites == null || sprites.Length == 0)
            {
                Debug.LogWarning($"[FightUnity] No sliced sprites for '{baseName}'. " +
                                 "Run Tools > FightCore > Slice Animation Sheets.");
                _cache[task] = null;
                return null;
            }

            // Resources.LoadAll order is not guaranteed; sort by the numeric suffix
            // Unity appends when slicing (e.g. Attack_1_0, Attack_1_1, ...).
            System.Array.Sort(sprites, (a, b) => FrameIndex(a.name).CompareTo(FrameIndex(b.name)));
            _cache[task] = sprites;
            return sprites;
        }

        private static int FrameIndex(string spriteName)
        {
            int us = spriteName.LastIndexOf('_');
            if (us >= 0 && int.TryParse(spriteName.Substring(us + 1), out var idx))
                return idx;
            return 0;
        }
    }
}