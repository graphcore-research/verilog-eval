import re
import tempfile
from pathlib import Path

from ..async_util import run_with_timeout
from ..evaluator import EvalResult, Sample
from .verilog_eval.data import read_problems

_THIS_DIR = Path(__file__).parent

# Load problem data at module import time
_PROBLEMS = read_problems(str(_THIS_DIR / "data" / "VerilogEval_Human.jsonl"))


async def evaluate(sample: Sample) -> EvalResult:
    problem = _PROBLEMS.get(sample.problem)
    if problem is None:
        raise ValueError(f"Unknown problem: {sample.problem}")

    # Extract code from markdown code fences if present
    code = sample.code
    if "```verilog" in code or "```systemverilog" in code or "```" in code:
        # Find the first code block
        for fence in ["```verilog", "```systemverilog", "```"]:
            if fence in code:
                parts = code.split(fence, 1)
                if len(parts) >= 2:
                    # Take the content after the fence, up to the closing ```
                    remaining = parts[1]
                    if "```" in remaining:
                        code = remaining.split("```", 1)[0].strip()
                        break

    # Combine test + prompt + completion
    verilog_code = problem["test"] + "\n" + problem["prompt"] + "\n" + code
    log_parts = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        sv_file = tmp_dir / f"{sample.problem}.sv"
        sv_file.write_text(verilog_code)

        # Compile with iverilog
        compile_cmd = f"iverilog -Wall -Winfloop -Wno-timescale -g2012 -s tb -o test.vvp {sample.problem}.sv"
        completed, compile_output = await run_with_timeout(compile_cmd, cwd=tmp_dir)
        log_parts.append(f"=== compile ===\n{compile_output}")

        if not completed:
            return EvalResult(
                passed=False,
                details={"reason": "compile timeout", "log": "\n\n".join(log_parts)},
            )

        vvp_file = tmp_dir / "test.vvp"
        if not vvp_file.exists():
            return EvalResult(
                passed=False,
                details={"reason": "compile error", "log": "\n\n".join(log_parts)},
            )

        # Simulate with vvp
        completed, sim_output = await run_with_timeout("vvp -n test.vvp", cwd=tmp_dir)
        log_parts.append(f"=== simulate ===\n{sim_output}")

        if not completed:
            return EvalResult(
                passed=False,
                details={"reason": "simulation timeout", "log": "\n\n".join(log_parts)},
            )

        # Parse simulation output
        match = re.search(r"Mismatches: (\d+) in (\d+) samples", sim_output)
        if match:
            mismatches, total = int(match.group(1)), int(match.group(2))
            passed = mismatches == 0
            reason = "passed" if passed else f"{mismatches}/{total} mismatches"
        else:
            reason = "output not matched"
            passed = False

        return EvalResult(
            passed=passed,
            details={"reason": reason, "log": "\n\n".join(log_parts)},
        )
