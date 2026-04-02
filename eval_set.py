from pathlib import Path
from typing import Iterable

from ..eval_set import Problem

_BASE_DIR = Path(__file__).parent
_DATASET_DIR = _BASE_DIR / "dataset_spec-to-rtl"

SYSTEM_PROMPT = (
    "You are a Verilog RTL designer that only writes code using correct Verilog syntax."
)


class VerilogEvalV2EvalSet:
    def get_problems(self) -> Iterable[Problem]:
        problems_file = _DATASET_DIR / "problems.txt"

        for line in problems_file.read_text().splitlines():
            problem_name = line.strip()
            if not problem_name:
                continue

            prompt_file = _DATASET_DIR / f"{problem_name}_prompt.txt"
            spec = prompt_file.read_text()

            user_prompt = f"""Question:
{spec}

Enclose your code with [BEGIN] and [DONE]. Only output the code snippet and do NOT output anything else.

Answer:"""

            yield Problem(
                eval_set="verilog_eval_v2",
                name=problem_name,
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
