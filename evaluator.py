import re
import tempfile
from pathlib import Path

from post_training_torchtitan.app.grading import FormatReward, FormatRewardResult

from ..async_util import run_with_timeout
from ..evaluator import EvalResult, Sample

_THIS_DIR = Path(__file__).parent
_DATASET_DIR = _THIS_DIR / "dataset_spec-to-rtl"

# Build lookup table: problem name -> problem directory
_PROBLEMS: dict[str, Path] = {}
for test_file in _DATASET_DIR.glob("*_test.sv"):
    # Extract problem name from e.g. "Prob001_zero_test.sv" -> "Prob001_zero"
    problem_name = test_file.name.removesuffix("_test.sv")
    _PROBLEMS[problem_name] = _DATASET_DIR

_FORMAT_REWARD = FormatReward()


def _score_format(completion: str) -> FormatRewardResult:
    return _FORMAT_REWARD.score(completion)


def _format_details(format_result: FormatRewardResult) -> dict[str, object]:
    return {
        "format_passed": format_result.passed,
        "format_reward": format_result.reward,
        "format_failure_reason": format_result.failure_reason,
        "extracted_code": format_result.code,
    }


async def evaluate(sample: Sample) -> EvalResult:
    if sample.problem not in _PROBLEMS:
        raise ValueError(f"Unknown problem: {sample.problem}")

    format_result = _score_format(sample.code)
    code = format_result.code
    format_details = _format_details(format_result)
    if not format_result.passed:
        reason = "format error"
        log = f"=== format ===\n{format_result.failure_reason}"
        return EvalResult(
            passed=False,
            details={**format_details, "reason": reason, "log": log},
        )

    problem_dir = _PROBLEMS[sample.problem]
    test_file = problem_dir / f"{sample.problem}_test.sv"
    ref_file = problem_dir / f"{sample.problem}_ref.sv"
    log_parts = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)

        # Write the sample code
        sample_file = tmp_dir / "sample.sv"
        sample_file.write_text(code)

        # Compile with iverilog
        compile_cmd = f"iverilog -Wall -Winfloop -Wno-timescale -g2012 -s tb -o test.vvp {sample_file} {test_file} {ref_file}"
        completed, compile_output = await run_with_timeout(
            compile_cmd, timeout=30, cwd=tmp_dir
        )
        log_parts.append(f"=== compile ===\n{compile_output}")

        if not completed:
            return EvalResult(
                passed=False,
                details={**format_details, "reason": "compile timeout", "log": "\n\n".join(log_parts)},
            )

        vvp_file = tmp_dir / "test.vvp"
        if not vvp_file.exists():
            return EvalResult(
                passed=False,
                details={**format_details, "reason": "compile error", "log": "\n\n".join(log_parts)},
            )

        # Simulate with vvp (longer timeout since testbench has internal timeout)
        completed, sim_output = await run_with_timeout(
            "./test.vvp", timeout=60, cwd=tmp_dir
        )
        log_parts.append(f"=== simulate ===\n{sim_output}")

        if not completed or "TIMEOUT" in sim_output:
            return EvalResult(
                passed=False,
                details={**format_details, "reason": "simulation timeout", "log": "\n\n".join(log_parts)},
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
            details={**format_details, "reason": reason, "log": "\n\n".join(log_parts)},
        )
