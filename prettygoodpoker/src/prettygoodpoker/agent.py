from __future__ import annotations

from ac2.runtime import Agent, ModelConfiguration


class ConciseAgent(Agent):
    """A concise agent for eval and training configs."""

    description = "Answers questions concisely."
    model_configuration = ModelConfiguration(model="gpt-4o-mini")
    system_prompt = "You are a helpful assistant. Answer concisely."
