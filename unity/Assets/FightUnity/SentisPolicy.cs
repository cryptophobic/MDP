// Inference wrapper: runs the exported PPO policy (fight_ppo.onnx).
// Gated behind FIGHT_INFERENCE (com.unity.ai.inference, Unity 6.1+) or
// FIGHT_SENTIS (legacy com.unity.sentis). The asmdef defines one of these only
// when the corresponding package is installed. Without either, this file is
// empty, so the demo keeps compiling/running on keyboard + bot input.
#if FIGHT_INFERENCE || FIGHT_SENTIS
using System;
#if FIGHT_INFERENCE
using Unity.InferenceEngine;   // Sentis renamed to Unity Inference Engine (6.1+)
#else
using Unity.Sentis;            // legacy package
#endif
using UnityEngine;

namespace FightUnity
{
    public sealed class SentisPolicy : IDisposable
    {
        private readonly Worker _worker;

        private SentisPolicy(Model model)
        {
            _worker = new Worker(model, BackendType.CPU);
        }

        // Loads a ModelAsset from Resources (e.g. "fight_ppo"). Returns null if
        // the asset is missing so the caller can fall back gracefully.
        public static SentisPolicy TryLoad(string resourceName)
        {
            var asset = Resources.Load<ModelAsset>(resourceName);
            if (asset == null)
            {
                Debug.LogWarning($"[FightUnity] ModelAsset '{resourceName}' not found in Resources.");
                return null;
            }
            return new SentisPolicy(ModelLoader.Load(asset));
        }

        // obs -> action logits -> argmax action index. Matches the Python
        // model.predict(deterministic=True) contract (argmax of the logits).
        public int Act(float[] obs)
        {
            using var input = new Tensor<float>(new TensorShape(1, obs.Length), obs);
            _worker.Schedule(input);

            using var output = (_worker.PeekOutput() as Tensor<float>).ReadbackAndClone();
            var logits = output.DownloadToArray();

            int best = 0;
            for (int i = 1; i < logits.Length; i++)
                if (logits[i] > logits[best]) best = i;
            return best;
        }

        public void Dispose() => _worker?.Dispose();
    }
}
#endif