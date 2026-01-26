import os
from typing import Iterable, Tuple

from .verilog_eval.data import read_problems


class VerilogEvalV1EvalSet:
    def __init__(self, jsonl_path: str | None = None):
        if jsonl_path is None:
            # Default to the Human descriptions file relative to this module
            base_dir = os.path.dirname(os.path.abspath(__file__))
            jsonl_path = os.path.join(base_dir, "descriptions", "VerilogDescription_Human.jsonl")
        self.jsonl_path = jsonl_path
        self._problems = None

    def get_prompts(self) -> Iterable[Tuple[str, str]]:
        if self._problems is None:
            self._problems = read_problems(self.jsonl_path)

        for task_id, task in self._problems.items():
            yield (task_id, task["detail_description"])
