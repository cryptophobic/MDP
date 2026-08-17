// Renders one fighter: picks the sprite for the current task/frame_offset.
// Mirrors fight_env/ui/fighter.py :: Fighter.get_current_frame.
using FightCore;
using UnityEngine;

namespace FightUnity
{
    [RequireComponent(typeof(SpriteRenderer))]
    public sealed class FighterView : MonoBehaviour
    {
        public bool FacingRight = true;

        private SpriteRenderer _sr;

        private void Awake()
        {
            _sr = GetComponent<SpriteRenderer>();
            _sr.flipX = !FacingRight;
        }

        public void Apply(PlayerSnapshot snapshot)
        {
            var frames = AnimationLibrary.Frames(snapshot.Task);
            if (frames == null || frames.Length == 0)
            {
                _sr.sprite = null;
                return;
            }

            // frame = frame_offset % frame_count (same as Animation.get_frame).
            int idx = ((snapshot.FrameOffset % frames.Length) + frames.Length) % frames.Length;
            _sr.sprite = frames[idx];
            _sr.flipX = !FacingRight;
        }
    }
}