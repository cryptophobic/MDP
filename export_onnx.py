"""
Export the trained SB3 PPO policy (fight_ppo.zip) to ONNX for Unity Sentis.

The exported graph takes the 7-float observation and returns the action LOGITS
(shape [1, 4]); argmax is done in C#. This mirrors model.predict(deterministic=True)
which, for a Categorical policy, picks argmax of the logits.

Validation: compares argmax(ONNX logits) against model.predict on random
observations, both via the torch wrapper and via onnxruntime on the exported file.

Run:  python export_onnx.py
Out:  fight_ppo.onnx
"""

import numpy as np
import torch as th
from stable_baselines3 import PPO

MODEL = "fight_ppo"
ONNX_OUT = "fight_ppo.onnx"
OPSET = 15  # Unity Sentis supports opset 7-15


class OnnxPolicy(th.nn.Module):
    """Wraps the SB3 policy to output raw action logits for a Discrete space."""

    def __init__(self, policy):
        super().__init__()
        self.policy = policy

    def forward(self, obs):
        dist = self.policy.get_distribution(obs)
        return dist.distribution.logits


def main():
    model = PPO.load(MODEL, device="cpu")
    policy = model.policy
    policy.set_training_mode(False)

    wrapper = OnnxPolicy(policy)

    dummy = th.zeros(1, 7, dtype=th.float32)
    th.onnx.export(
        wrapper,
        dummy,
        ONNX_OUT,
        input_names=["obs"],
        output_names=["logits"],
        opset_version=OPSET,
        dynamo=False,
    )
    print(f"Exported {ONNX_OUT} (opset {OPSET}).")

    # ---- validation ----
    obs_space = model.observation_space
    rng = np.random.default_rng(0)
    N = 3000

    # Deterministic sampling within the observation bounds for coverage.
    lows = obs_space.low.astype(np.float32)
    highs = obs_space.high.astype(np.float32)

    # torch-wrapper vs model.predict
    wmiss = 0
    samples = []
    for _ in range(N):
        o = (lows + rng.random(7).astype(np.float32) * (highs - lows)).astype(np.float32)
        samples.append(o)
        a_pred, _ = model.predict(o, deterministic=True)
        with th.no_grad():
            logits = wrapper(th.tensor(o).unsqueeze(0)).numpy()[0]
        if int(a_pred) != int(np.argmax(logits)):
            wmiss += 1
    print(f"argmax(torch wrapper) vs model.predict : {N - wmiss}/{N} match")

    # onnxruntime on the exported file vs model.predict
    try:
        import onnxruntime as ort

        sess = ort.InferenceSession(ONNX_OUT, providers=["CPUExecutionProvider"])
        in_name = sess.get_inputs()[0].name
        omiss = 0
        for o in samples:
            logits = sess.run(None, {in_name: o.reshape(1, 7)})[0][0]
            a_pred, _ = model.predict(o, deterministic=True)
            if int(a_pred) != int(np.argmax(logits)):
                omiss += 1
        print(f"argmax(ONNX runtime)  vs model.predict : {N - omiss}/{N} match")
        status = "OK" if omiss == 0 else "DIVERGENCE"
        print(f"ONNX export {status}.")
    except Exception as e:  # pragma: no cover
        print(f"onnxruntime validation skipped: {e}")


if __name__ == "__main__":
    main()