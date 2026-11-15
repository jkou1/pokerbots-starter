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


@pytest.mark.parametrize("newline_in_prompt", [False, True])
def test_equivalent_managed_and_official_boundaries(newline_in_prompt):
    # Live 2026-11-15 managed samples move token198 into the prompt. Requiring
    # another target newline would reject a valid sample or introduce drift.
    tokens = ["Tool", " call", " follows", ".", "\n", "</think>", "\n\n", "<tool_call>"]
    prompt = "<|im_start|>assistant\n<think>"
    if newline_in_prompt:
        prompt += "\n"
    else:
        tokens.insert(0, "\n")
    payload = {"student_prompt": prompt, "sampled_tokens": tokens, "loss_mask": [1] * len(tokens)}
    result = audit_target(payload)
    assert result["combined_boundary_verified"]
    assert result["prefill_newline_location"] == ("prompt" if newline_in_prompt else "target")


def test_double_newline_across_prompt_target_boundary_is_rejected():
    tokens = ["\n", "Tool", " call", " follows", ".", "\n", "</think>", "<tool_call>"]
    payload = {"student_prompt": "<think>\n", "sampled_tokens": tokens, "loss_mask": [1] * len(tokens)}
    with pytest.raises(ValueError, match="one newline"):
        audit_target(payload)


@pytest.mark.parametrize("masked_close", [False, True])
def test_current_managed_target_requires_supervised_reasoning_close(masked_close):
    tokens = ["Tool", " call", " follows", ".", "\n", "</think>", "<tool_call>"]
    mask = [1] * len(tokens)
    if masked_close:
        mask[5] = 0
    else:
        tokens.pop(5)
        mask.pop(5)
    with pytest.raises(ValueError, match="explicitly supervised"):
        audit_target({"student_prompt": "<think>\n", "sampled_tokens": tokens, "loss_mask": mask})
