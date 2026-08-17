// Port of fight_env/player/refs/tasks.py :: TaskData, TaskTimeline, tasks_data.
using System.Collections.Generic;

namespace FightCore
{
    public sealed class TaskData
    {
        public FighterTask TaskType;
        public int Priority;
        public int StartPriority;
        public int BaseStaminaCost;
        public int BaseStaminaCostFrame;
        public int Duration;
        public bool Loop;
        public Dictionary<int, Events> EventsByFrame;
        public bool Interruptible;

        public TaskData(
            FighterTask taskType,
            int priority = 0,
            int startPriority = 0,
            int baseStaminaCost = 0,
            int baseStaminaCostFrame = 0,
            int duration = 0,
            bool loop = false,
            Dictionary<int, Events> events = null,
            bool interruptible = false)
        {
            TaskType = taskType;
            Priority = priority;
            StartPriority = startPriority;
            BaseStaminaCost = baseStaminaCost;
            BaseStaminaCostFrame = baseStaminaCostFrame;
            Duration = duration;
            Loop = loop;
            EventsByFrame = events ?? new Dictionary<int, Events>();
            Interruptible = interruptible;
        }
    }

    // fight_env/player/refs/tasks.py :: TaskTimeline
    public sealed class TaskTimeline
    {
        public int FrameNumber;
        public int StartFrameNumber;
        public int Duration;
        public bool Loop;
        public Dictionary<int, Events> EventsByFrame;

        public TaskTimeline(int duration = 0, bool loop = false, Dictionary<int, Events> events = null)
        {
            Duration = duration;
            Loop = loop;
            EventsByFrame = events ?? new Dictionary<int, Events>();
        }

        public int FrameOffset
        {
            get
            {
                int offset = FrameNumber - StartFrameNumber;
                if (Duration != 0)
                    return Loop ? offset % Duration : offset;
                return 0;
            }
        }

        public Events CurrentEvent
        {
            get
            {
                return EventsByFrame.TryGetValue(FrameOffset, out var e) ? e : Events.NONE;
            }
        }

        public void Tick() => FrameNumber += 1;

        public bool Expired => FrameOffset >= Duration;
    }

    public static class Tasks
    {
        private const int RESTORE = Config.BASE_STAMINA_RESTORE_VALUE_PER_TICK;

        public static readonly Dictionary<FighterTask, TaskData> Data =
            new Dictionary<FighterTask, TaskData>
            {
                { FighterTask.DEAD, new TaskData(
                    FighterTask.DEAD, priority: 100, duration: 5,
                    events: new Dictionary<int, Events> { { 3, Events.DEAD } }) },

                { FighterTask.STUNNED, new TaskData(
                    FighterTask.STUNNED, priority: 50, startPriority: 1,
                    baseStaminaCostFrame: -RESTORE, duration: 1, loop: false,
                    events: new Dictionary<int, Events> { { 0, Events.STUNNED } }) },

                { FighterTask.HURT, new TaskData(
                    FighterTask.HURT, priority: 90, baseStaminaCost: 2, duration: 2) },

                { FighterTask.ATTACK_1, new TaskData(
                    FighterTask.ATTACK_1, priority: 50, baseStaminaCost: 2, duration: 4,
                    events: new Dictionary<int, Events>
                        { { 0, Events.ATTACK_STARTED }, { 2, Events.ATTACK } }) },

                { FighterTask.PARRY, new TaskData(
                    FighterTask.PARRY, priority: 50, baseStaminaCost: 2, duration: 4,
                    events: new Dictionary<int, Events> { { 1, Events.PARRY } }) },

                { FighterTask.RIPOSTE, new TaskData(
                    FighterTask.RIPOSTE, priority: 50, baseStaminaCost: 2, duration: 5,
                    events: new Dictionary<int, Events> { { 3, Events.CRITICAL_ATTACK } }) },

                { FighterTask.DEFENSE, new TaskData(
                    FighterTask.DEFENSE, priority: 50, duration: 1,
                    events: new Dictionary<int, Events> { { 0, Events.BLOCK } }) },

                { FighterTask.FIGHTING_STANCE, new TaskData(
                    FighterTask.FIGHTING_STANCE, baseStaminaCostFrame: -RESTORE,
                    interruptible: true, duration: 1, loop: true) },

                { FighterTask.NONE, new TaskData(
                    FighterTask.NONE, interruptible: true, priority: -1) },
            };
    }
}