from __future__ import annotations

from ac2.runtime import EnvironmentProtocol, Grader, GraderOutput, Trace


class SubstringGrader(Grader):
    """Scores 1.0 when the agent's final message contains the expected string."""

    async def _grade(
        self,
        grader_params: dict | None,
        trace: Trace,
        env: EnvironmentProtocol | None,
    ) -> GraderOutput:
        expected = str((grader_params or {}).get("expected", ""))
        final = str(trace[-1].get_items()[-1].content)
        hit = expected.lower() in final.lower()
        return GraderOutput(
            score=1.0 if hit else 0.0,
            reasoning=f"expected {expected!r}: {'found' if hit else 'missing'}",
        )
