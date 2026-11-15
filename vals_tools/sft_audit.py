"""Audit actual managed-SFT target boundaries before accepting a poker checkpoint."""

import argparse
import json
from pathlib import Path

from ac2.sdk import Client
from ac2.sdk.analytics.types import ColumnSpec, QuerySpec

from vals_tools.arena import write_json
from vals_tools.training import PROTOCOL_MARKER


def audit_target(payload):
    tokens = payload["sampled_tokens"]
    mask = payload["loss_mask"]
    text = "".join(tokens)
    # Current managed SFT includes the one newline in student_prompt; older
    # token samples included it in the supervised target instead. Audit their
    # combined boundary so both match official inference's <think>\n prefill.
    prompt = payload.get("student_prompt", "<think>")
    if prompt.endswith("<think>\n"):
        expected_prefix = PROTOCOL_MARKER
        newline_location = "prompt"
    elif prompt.endswith("<think>"):
        expected_prefix = "\n" + PROTOCOL_MARKER
        newline_location = "target"
    else:
        raise ValueError("unsupported reasoning prefill in training prompt")
    if not tokens or not text.startswith(expected_prefix):
        raise ValueError(
            "combined boundary must match the official single-newline thinking prefill: one newline after <think>, then the protocol marker"
        )
    if len(mask) != len(tokens):
        raise ValueError("target tokens and loss mask must have matching lengths")
    if "</think>" not in tokens or mask[tokens.index("</think>")] != 1:
        raise ValueError("reasoning close must be an explicitly supervised token")
    if "<tool_call>" not in tokens:
        raise ValueError("target must contain a tool call")
    if text.index("</think>") > text.index("<tool_call>"):
        raise ValueError("tool call occurs before reasoning closes")
    return {
        "response_tokens": len(tokens),
        "first_target_token": tokens[0],
        "prefill_newline_location": newline_location,
        "combined_boundary_verified": True,
        "prompt_matches_thinking_prefill": True,
        "reasoning_close_supervised": True,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--train", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = Client(project="vals-hackathon").analytics.query(
        spec=QuerySpec(
            source="token_viz",
            job_ids=[args.train],
            columns=[
                ColumnSpec(field=x)
                for x in ("step", "payload", "response_length", "loss")
            ],
            sort_by="step",
            limit=8,
        )
    )
    if not result.rows:
        raise SystemExit(
            "No trainer token samples yet; retry after an optimizer update"
        )
    samples = [
        {"step": row["step"], "payload": json.loads(row["payload"])}
        for row in result.rows
    ]
    write_json(args.out, {"train_id": args.train, "samples": samples})
    report = [audit_target(row["payload"]) for row in samples]
    print(
        json.dumps(
            {"train_id": args.train, "audited_samples": len(report), "results": report},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
