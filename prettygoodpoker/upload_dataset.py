from __future__ import annotations

from ac2.runtime import Message
from ac2.sdk import Client, Task


PROJECT = "prettygoodpoker"
DATASET = "prettygoodpoker-dataset"


def build_tasks() -> list[Task]:
    return [
        Task(
            name="two-plus-two",
            input=[Message(role="user", content="What is 2 + 2?")],
            grader_params={"expected": "4"},
        ),
        Task(
            name="capital-of-france",
            input=[Message(role="user", content="What is the capital of France?")],
            grader_params={"expected": "Paris"},
        ),
    ]


def main() -> None:
    client = Client(project=PROJECT)
    if DATASET not in {dataset.name for dataset in client.datasets.list()}:
        client.datasets.create(DATASET)
        print(f"Created dataset {DATASET!r}.")

    tasks = build_tasks()
    client.datasets.add_tasks(dataset=DATASET, tasks=tasks)
    print(f"Uploaded {len(tasks)} task(s) to {DATASET!r}.")


if __name__ == "__main__":
    main()
