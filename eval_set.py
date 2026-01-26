from pathlib import Path
from typing import Iterable, Literal, Tuple


class VerilogEvalV2EvalSet:
    def __init__(self, task: Literal["spec-to-rtl", "code-complete"] = "spec-to-rtl"):
        self._base_dir = Path(__file__).parent
        if task == "spec-to-rtl":
            self._dataset_dir = self._base_dir / "dataset_spec-to-rtl"
        elif task == "code-complete":
            self._dataset_dir = self._base_dir / "dataset_code-complete-iccad2023"
        else:
            raise ValueError(f"Unknown task: {task}")

    def get_prompts(self) -> Iterable[Tuple[str, str]]:
        problems_file = self._dataset_dir / "problems.txt"

        for line in problems_file.read_text().splitlines():
            problem_name = line.strip()
            if not problem_name:
                continue

            prompt_file = self._dataset_dir / f"{problem_name}_prompt.txt"
            spec = prompt_file.read_text()
            wrapped_prompt = f"""You are a Verilog RTL designer that only writes code using correct Verilog syntax.

Question:
{spec}

Enclose your code with [BEGIN] and [DONE]. Only output the code snippet
and do NOT output anything else.

Answer:"""
            yield (problem_name, wrapped_prompt)
