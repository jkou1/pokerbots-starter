from __future__ import annotations

import asyncio

from ac2.sdk import Client, EvalConfig
from prettygoodpoker.agent import ConciseAgent
from prettygoodpoker.environment import BasicEnvironment
from prettygoodpoker.grader import SubstringGrader


async def main() -> None:
    config = EvalConfig(
        agent=ConciseAgent(),
        env=BasicEnvironment(),
        grader=SubstringGrader(),
        dataset="prettygoodpoker-dataset",
    )
    await Client(project="prettygoodpoker").eval.run(config)


if __name__ == "__main__":
    asyncio.run(main())
