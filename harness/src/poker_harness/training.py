"""Opt-in training routing. The official event configuration never enables it."""

import copy
import json
import re


def current_street(messages):
    latest = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
    streets = re.findall(r"^Street: (preflop|flop|turn|river)$", latest, re.MULTILINE)
    return streets[-1] if streets else None


def action_args(reply):
    calls = [c for c in reply.tool_calls if c.get("function", {}).get("name") == "submit_action"]
    if len(calls) != 1 or len(reply.tool_calls) != 1 or reply.truncated:
        raise ValueError("expected one complete submit_action call")
    value = calls[0]["function"]["arguments"]
    return json.loads(value) if isinstance(value, str) else dict(value)


def betting_action(args):
    return {"action": args["action"]} | ({"amount": args.get("amount")} if args["action"] in ("bet", "raise") else {})


def with_say(reply, message):
    from .prompts import sanitize_talk

    result = copy.deepcopy(reply)
    args = action_args(result)
    args["say"] = sanitize_talk(message)
    result.tool_arguments = json.dumps(args)
    result.tool_calls[0]["function"]["arguments"] = result.tool_arguments
    return result


def message_completion(policy, frozen):
    nominated = False

    async def complete(messages):
        nonlocal nominated
        street = current_street(messages)
        if street not in ("flop", "turn", "river") or nominated:
            return await frozen(messages)
        nominated = True
        baseline = await frozen(messages)
        expected = action_args(baseline)
        fixed = betting_action(expected)
        helper = {
            "role": "user",
            "content": "Betting action already selected: "
            + json.dumps(fixed)
            + ". Call submit_action with these exact action and amount fields and choose optional say.",
        }
        candidate = await policy([*messages, helper])
        try:
            actual = action_args(candidate)
            if betting_action(actual) != fixed:
                raise ValueError("message policy changed the fixed betting action")
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError("message policy changed or invalidated the fixed betting action") from exc
        return candidate

    return complete


def stage_completion(policy, frozen, stage):
    if stage not in ("preflop", "postflop"):
        raise ValueError(f"unknown training stage: {stage}")

    async def complete(messages):
        street = current_street(messages)
        if not street:
            raise ValueError("training decision has no current street")
        active = (street == "preflop") == (stage == "preflop")
        return await (policy if active else frozen)(messages)

    return complete
