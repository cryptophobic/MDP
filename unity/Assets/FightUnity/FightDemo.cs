// Self-contained render + play demo. Add this one component to an empty
// GameObject (Tools > FightCore > Create Demo Object does it for you) and press
// Play. It builds the camera, ground, two fighters and the HUD bars at runtime,
// then ticks FightCore on a fixed 120 ms accumulator and shows the result.
//
// The HUD bars are drawn with SpriteRenderers (no UGUI/Canvas dependency), so
// this works in a minimal project with no extra packages installed.
//
// This is the view/driver layer only. FightCore stays engine-free; nothing here
// leaks back into it. Controls: Q/W/E = agent attack/block/parry, R = restart.
using FightCore;
using UnityEngine;

namespace FightUnity
{
    public sealed class FightDemo : MonoBehaviour
    {
        [Header("Timing")]
        [Tooltip("Logical tick length in seconds. Matches fight_env FRAME_DURATION (120 ms).")]
        public float TickSeconds = 0.120f;

        [Header("Layout")]
        public float CameraSize = 2.2f;
        public float GroundY = -1.8f;
        public float FighterScale = 2.5f;
        public float FighterSpacing = 0.6f;

        [Header("AI")]
        [Tooltip("Drive the left fighter with the trained PPO policy. Needs the " +
                 "com.unity.sentis package + fight_ppo.onnx in Resources; otherwise " +
                 "the left fighter is keyboard-controlled (Q/W/E).")]
        public bool AgentUsesPolicy = true;

        private Player _agent;
        private Player _opponent;
        private Orchestrator _orchestrator;
        private AggressiveBot _bot;
#if FIGHT_SENTIS || FIGHT_INFERENCE
        private SentisPolicy _policy;
#endif

        private FighterView _agentView;
        private FighterView _opponentView;

        private Bar _agentHp, _agentSt, _opponentHp, _opponentSt;

        private Camera _cam;
        private float _accumulator;

        // ---- lifecycle ----

        private void Start()
        {
            BuildCamera();
            BuildFighters();
            BuildHud();
            NewMatch();
        }

        private void Update()
        {
            HandleInput();

            if (!(_agent.IsDead || _opponent.IsDead))
            {
                _accumulator += Time.deltaTime;
                while (_accumulator >= TickSeconds)
                {
                    _accumulator -= TickSeconds;
                    StepOnce();
                }
            }

            Render();
        }

        // ---- simulation ----

        private void NewMatch()
        {
            _agent = MakePlayer("agent");
            _opponent = MakePlayer("opponent");
            _orchestrator = new Orchestrator(_agent, _opponent);
            _bot = new AggressiveBot(_opponent, _agent);
            _accumulator = 0f;
#if FIGHT_SENTIS || FIGHT_INFERENCE
            if (AgentUsesPolicy && _policy == null)
                _policy = SentisPolicy.TryLoad("fight_ppo");
#endif
            Render();
        }

        private static Player MakePlayer(string name)
        {
            var p = new Player(name);
            p.SetArmour(ArmourTypes.LIGHT_ARMOUR);
            p.SetShield(Shields.BUCKLER);
            p.SetWeapon(Weapons.GLADIUS);
            return p;
        }

        private void StepOnce()
        {
#if FIGHT_SENTIS || FIGHT_INFERENCE
            // Policy drives the agent: obs -> logits -> argmax -> intent.
            // Same order as gym_env.step: agent intent, then bot, then flow.
            if (_policy != null)
            {
                var action = AgentActions.Map(_policy.Act(Observation.Encode(_agent, _opponent)));
                if (action != ActionType.NONE) _agent.RequestIntent(action);
            }
#endif
            _bot.NextMove();          // opponent decides
            _orchestrator.Flow();     // one logical tick
        }

        private void OnDestroy()
        {
#if FIGHT_SENTIS || FIGHT_INFERENCE
            _policy?.Dispose();
#endif
        }

        private void HandleInput()
        {
            if (Input.GetKeyDown(KeyCode.Q)) _agent.RequestIntent(ActionType.ATTACK);
            if (Input.GetKeyDown(KeyCode.W)) _agent.RequestIntent(ActionType.BLOCK);
            if (Input.GetKeyDown(KeyCode.E)) _agent.RequestIntent(ActionType.PARRY);
            if (Input.GetKeyDown(KeyCode.R)) NewMatch();
        }

        // ---- rendering ----

        private void Render()
        {
            _agentView.Apply(_agent.MakeSnapshot());
            _opponentView.Apply(_opponent.MakeSnapshot());

            var am = _agent.Model;
            var om = _opponent.Model;
            _agentHp.SetRatio(Ratio(am.Hp, am.Stats.MaxHp));
            _agentSt.SetRatio(Ratio(am.Stamina, am.Stats.MaxStamina));
            _opponentHp.SetRatio(Ratio(om.Hp, om.Stats.MaxHp));
            _opponentSt.SetRatio(Ratio(om.Stamina, om.Stats.MaxStamina));
        }

        private static float Ratio(int cur, int max) =>
            max <= 0 ? 0f : Mathf.Clamp01((float)cur / max);

        // ---- scene construction ----

        private void BuildCamera()
        {
            _cam = Camera.main;
            if (_cam == null)
            {
                var go = new GameObject("Main Camera");
                go.tag = "MainCamera";
                _cam = go.AddComponent<Camera>();
            }
            _cam.orthographic = true;
            _cam.orthographicSize = CameraSize;
            _cam.clearFlags = CameraClearFlags.SolidColor;
            _cam.backgroundColor = Rgb(40, 44, 52);
            _cam.transform.position = new Vector3(0f, 0f, -10f);
        }

        private void BuildFighters()
        {
            _agentView = MakeFighter("AgentView", -FighterSpacing, facingRight: true);
            _opponentView = MakeFighter("OpponentView", FighterSpacing, facingRight: false);

            var ground = new GameObject("Ground");
            var sr = ground.AddComponent<SpriteRenderer>();
            sr.sprite = SolidSprite();
            sr.color = Rgb(60, 65, 75);
            sr.sortingOrder = -1;
            ground.transform.position = new Vector3(0f, GroundY - 0.25f, 0f);
            ground.transform.localScale = new Vector3(40f, 0.5f, 1f);
        }

        private FighterView MakeFighter(string name, float x, bool facingRight)
        {
            var go = new GameObject(name);
            go.transform.position = new Vector3(x, GroundY, 0f);
            go.transform.localScale = Vector3.one * FighterScale;
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sortingOrder = 0;
            var view = go.AddComponent<FighterView>();
            view.FacingRight = facingRight;
            return view;
        }

        private void BuildHud()
        {
            // Bars live in world space, parented to the camera at the screen corners.
            float halfH = CameraSize;
            float halfW = CameraSize * _cam.aspect;
            const float bw = 1.6f, bh = 0.16f, margin = 0.18f, gap = 0.06f;

            float topY = halfH - margin - bh * 0.5f;
            float rowY = topY - bh - gap;
            float leftX = -halfW + margin + bw * 0.5f;
            float rightX = halfW - margin - bw * 0.5f;

            _agentHp = Bar.Create(_cam.transform, "AgentHP", leftX, topY, bw, bh, Rgb(60, 20, 20), Rgb(200, 40, 40));
            _agentSt = Bar.Create(_cam.transform, "AgentStamina", leftX, rowY, bw, bh, Rgb(20, 60, 20), Rgb(40, 200, 40));
            _opponentHp = Bar.Create(_cam.transform, "OppHP", rightX, topY, bw, bh, Rgb(60, 20, 20), Rgb(200, 40, 40));
            _opponentSt = Bar.Create(_cam.transform, "OppStamina", rightX, rowY, bw, bh, Rgb(20, 60, 20), Rgb(40, 200, 40));
        }

        // ---- helpers ----

        private static Color Rgb(int r, int g, int b) => new Color(r / 255f, g / 255f, b / 255f);

        private static Sprite _solid;
        private static Sprite SolidSprite()
        {
            // Reusable 1x1 white sprite at PPU 1 (1 unit). Tint via SpriteRenderer.color.
            if (_solid == null)
            {
                var tex = new Texture2D(1, 1);
                tex.SetPixel(0, 0, Color.white);
                tex.Apply();
                _solid = Sprite.Create(tex, new Rect(0, 0, 1, 1), new Vector2(0.5f, 0.5f), 1f);
            }
            return _solid;
        }

        // A HUD bar drawn as two sprites: dark background + left-anchored fill.
        private sealed class Bar
        {
            private Transform _fill;
            private float _width;
            private float _height;

            public static Bar Create(Transform camera, string name, float x, float y,
                                     float width, float height, Color bgColor, Color fillColor)
            {
                var root = new GameObject(name);
                root.transform.SetParent(camera, false);
                root.transform.localPosition = new Vector3(x, y, 1f);

                var bg = new GameObject("bg").AddComponent<SpriteRenderer>();
                bg.transform.SetParent(root.transform, false);
                bg.sprite = SolidSprite();
                bg.color = bgColor;
                bg.sortingOrder = 100;
                bg.transform.localScale = new Vector3(width, height, 1f);

                var fill = new GameObject("fill").AddComponent<SpriteRenderer>();
                fill.transform.SetParent(root.transform, false);
                fill.sprite = SolidSprite();
                fill.color = fillColor;
                fill.sortingOrder = 101;

                var bar = new Bar { _fill = fill.transform, _width = width, _height = height };
                bar.SetRatio(1f);
                return bar;
            }

            public void SetRatio(float ratio)
            {
                float r = Mathf.Clamp01(ratio);
                float w = _width * r;
                // Grow from the left edge: keep left edge fixed at -_width/2.
                _fill.localScale = new Vector3(w, _height, 1f);
                _fill.localPosition = new Vector3(-_width * 0.5f + w * 0.5f, 0f, -0.01f);
            }
        }
    }
}