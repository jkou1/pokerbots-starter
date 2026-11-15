from __future__ import annotations

from ac2.sdk import Client, ExperimentConfig, RunConfig
from ac2.sdk.run_config import (
    EvalConfig,
    EvalDatasetConfig,
    StepConfig,
    TasksConfig,
    TrainDatasetConfig,
)
from prettygoodpoker.agent import ConciseAgent
from prettygoodpoker.environment import BasicEnvironment
from prettygoodpoker.grader import SubstringGrader


def main() -> None:
    config = RunConfig(
        model="Qwen/Qwen3-4B",
        experiment_cfg=ExperimentConfig(
            step=StepConfig(problem_batch_size=1, samples_per_problem=2),
            tasks=TasksConfig(
                datasets=(TrainDatasetConfig(ac2_dataset_name="prettygoodpoker-dataset"),),
                agent=ConciseAgent(),
                env=BasicEnvironment(),
                grader=SubstringGrader(),
            ),
            eval=EvalConfig(datasets=(EvalDatasetConfig(ac2_dataset_name="prettygoodpoker-dataset"),)),
        ),
    )
    Client(project="prettygoodpoker").train.run(config)


if __name__ == "__main__":
    main()
