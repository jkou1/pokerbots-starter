import pytest

from vals_tools.sft_audit import audit_target


def test_real_empty_reasoning_target_is_incompatible_with_single_newline_prefill():
    # Captured from train_3061a33ce578's token_viz payload. The first double
    # newline was one token (271), while official inference prefills token 198.
    tokens = ["\n\n", "</think>", "\n\n", "<tool_call>", "\n", "<", "function"]
    with pytest.raises(ValueError, match="single-newline thinking prefill"):
        audit_target({
            "student_prompt": "<|im_start|>assistant\n<think>",
            "sampled_tokens": tokens,
            "loss_mask": [1] * len(tokens),
        })


def test_protocol_target_closes_reasoning_before_call_with_loss_on_close():
    tokens = [
        "Tool",
        " call",
        " follows",
        ".",
        "\n",
        "</think>",
        "\n\n",
        "<tool_call>",
    ]
    # Captured boundary from train_87b51a9211a1: the newline belongs to the
    # student prompt, and the first target token is "Tool".
    payload = {
        "student_prompt": "<|im_start|>assistant\n<think>\n",
        "sampled_tokens": tokens,
        "loss_mask": [1] * len(tokens),
    }
    assert audit_target(payload)["reasoning_close_supervised"]
    payload["loss_mask"][5] = 0
    with pytest.raises(ValueError, match="explicitly supervised"):
        audit_target(payload)


@pytest.mark.parametrize("mutation,match", [
    ("extra_newline", "protocol marker"),
    ("missing_call", "contain a tool call"),
    ("call_inside_reasoning", "before reasoning closes"),
    ("short_mask", "matching lengths"),
])
def test_reject_malformed_target_even_with_correct_prompt(mutation, match):
    tokens = ["Tool", " call", " follows", ".", "\n", "</think>", "\n\n", "<tool_call>"]
    if mutation == "extra_newline":
        tokens.insert(0, "\n")
    elif mutation == "missing_call":
        tokens.pop()
    elif mutation == "call_inside_reasoning":
        tokens[5], tokens[7] = tokens[7], tokens[5]
    payload = {
        "student_prompt": "<|im_start|>assistant\n<think>\n",
        "sampled_tokens": tokens,
        "loss_mask": [1] * len(tokens),
    }
    if mutation == "short_mask":
        payload["loss_mask"].pop()
    with pytest.raises(ValueError, match=match):
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
