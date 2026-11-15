import pytest

from vals_tools.sft_audit import audit_target


def test_real_empty_reasoning_target_is_incompatible_with_single_newline_prefill():
    # Captured from train_3061a33ce578's token_viz payload. The first double
    # newline was one token (271), while official inference prefills token 198.
    tokens = ["\n\n", "</think>", "\n\n", "<tool_call>", "\n", "<", "function"]
    with pytest.raises(ValueError, match="one newline"):
        audit_target({"sampled_tokens": tokens, "loss_mask": [1] * len(tokens)})


def test_protocol_target_closes_reasoning_before_call_with_loss_on_close():
    tokens = [
        "\n",
        "Tool",
        " call",
        " follows",
        ".",
        "\n",
        "</think>",
        "\n\n",
        "<tool_call>",
    ]
    payload = {"sampled_tokens": tokens, "loss_mask": [1] * len(tokens)}
    assert audit_target(payload)["reasoning_close_supervised"]
    payload["loss_mask"][6] = 0
    with pytest.raises(ValueError, match="explicitly supervised"):
        audit_target(payload)
