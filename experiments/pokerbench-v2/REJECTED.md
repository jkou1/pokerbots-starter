# Rejected before training

The v2 scaler matched only amounts followed by `chips`. Some preflop source histories use bare amounts such as `HJ raise 2.0`, so v2 doubled blinds/pot but left those action sizes unchanged. No model was trained on v2. All three remote v2 datasets are tagged rejected and described as unsafe to train.

Use corrected v3 instead: one-pass scaling handles both forms without double scaling, fractional states are excluded, and focused monetary legality checks reject unsupported source labels. v3 GPU training remains on hold while GRPO is prioritized.
