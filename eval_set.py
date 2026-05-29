from pathlib import Path
from typing import Iterable

from ..eval_set import Problem
from .verilog_eval.data import read_problems

_BASE_DIR = Path(__file__).parent

SYSTEM_PROMPT = """\
You are an expert Verilog hardware designer.

Complete the given Verilog module.

Return your final answer in a single markdown block formatted with triple backticks followed by the programming language specification.

The module declaration and port list are already provided in the prompt. Do not repeat the module declaration, module name, ports, widths, or parameters. Return only the Verilog statements needed to complete the module, ending with endmodule.
"""


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
