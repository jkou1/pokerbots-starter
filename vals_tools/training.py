"""Shared checkpoint and supervised-dataset utilities."""

from __future__ import annotations

import json
from pathlib import Path

from ac2.runtime import FunctionCall, Message, Reasoning, Task
from ac2.sdk.model import ModelConfig

TOOLS = json.loads(
    (Path(__file__).resolve().parents[1] / "opsd/tools.json").read_text()
)
PROTOCOL_MARKER = "Tool call follows."
SFT_TARGET_FORMAT = "qwen-protocol-boundary-v2"


def model_source(args):
    return ModelConfig(checkpoint=args.checkpoint) if args.checkpoint else args.model


def supervised_task(row: dict) -> Task:
    # Each canonical example contains exactly one trainable reply. Never silently train historical assistant turns.
    if any(item.get("role") not in ("system", "user") for item in row["input"]):
        raise ValueError("supervised inputs must contain only system/user messages")
    name = row.get("tool", "submit_action")
    if name not in ("submit_action", "update_scratchpad"):
        raise ValueError("unsupported target tool")
    target = row["target"]
    if name == "submit_action" and target.get("action") not in (
        "fold",
        "check",
        "call",
        "bet",
        "raise",
    ):
        raise ValueError("invalid action target")
    if name == "submit_action" and target["action"] in ("bet", "raise"):
        amount = target.get("amount")
        if type(amount) is not int or amount <= 0:
            raise ValueError("bet/raise requires a positive integer amount")
        legal = row.get("legal")
        if legal and (
            not legal["raise_type"]
            or not legal["min_raise_to"] <= amount <= legal["max_raise_to"]
        ):
            raise ValueError("target amount is outside the legal raise bounds")
    if name == "update_scratchpad" and (
        not isinstance(target.get("contents"), str) or len(target["contents"]) > 5000
    ):
        raise ValueError("invalid scratchpad target")
    return Task(
        input=[Message.model_validate(item) for item in row["input"]]
        + [
            # An empty reasoning block starts with a merged double-newline token in
            # managed SFT. Official inference prefills a single newline after <think>,
            # which led the first run to omit </think>. A nonempty protocol marker
            # makes that single newline an ordinary target-prefix token. This is a
            # serialization scaffold, never a claimed explanation from the teacher.
            Reasoning(content=PROTOCOL_MARKER),
            FunctionCall(call_id="decision", name=name, arguments=json.dumps(target)),
        ],
        env_params={"tools": TOOLS, "target_format": SFT_TARGET_FORMAT}
        | ({"sampling_copy": row["sampling_copy"]} if "sampling_copy" in row else {}),
        tags={"provenance": row.get("provenance", {}), "split": row["split"]},
    )
