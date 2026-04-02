from pathlib import Path
from typing import Iterable

from ..eval_set import Problem
from .verilog_eval.data import read_problems

_BASE_DIR = Path(__file__).parent

SYSTEM_PROMPT = (
    "You only complete chats with syntax correct Verilog code. End the Verilog module "
    "code completion with 'endmodule'. Do not include module, input and output definitions."
)

QUESTION_PROMPT = (
    "Implement the Verilog module based on the following description. Assume that "
    "signals are positive clock/clk edge triggered unless otherwise stated."
)


class VerilogEvalV1EvalSet:
    def get_problems(self) -> Iterable[Problem]:
        descriptions = read_problems(
            str(_BASE_DIR / "descriptions" / "VerilogDescription_Human.jsonl")
        )
        evals = read_problems(str(_BASE_DIR / "data" / "VerilogEval_Human.jsonl"))

        for task_id, desc_task in descriptions.items():
            eval_task = evals.get(task_id)
            if eval_task is None:
                continue

            user_prompt = "\n\n".join(
                [
                    QUESTION_PROMPT,
                    desc_task["detail_description"],
                    eval_task["prompt"],
                ]
            )

            yield Problem(
                eval_set="verilog_eval_v1",
                name=task_id,
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
