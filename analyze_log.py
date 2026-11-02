import csv
import sys
from collections import Counter
from pathlib import Path

from inspect_ai.log import read_eval_log
from inspect_ai.scorer import CORRECT

def sample_to_row(sample):
    metadata = sample.metadata or {}
    scores = sample.scores or {}
    correctness = scores.get("choice")
    formatting = scores.get("answer_format")

    output = sample.output
    response = output.completion
    stop_reason = (
        output.choices[0].stop_reason
        if output.choices
        else None
    )

    if sample.error is not None:
        outcome = "execution_error"
    elif not response.strip():
        outcome = "missing_final"
    elif correctness is None:
        outcome = "unscored"
    elif not correctness.answer:
        outcome = "unparsed_answer"
    elif correctness.value == CORRECT:
        outcome = "correct"
    else:
        outcome = "incorrect"

    return {
        "sample_id": sample.id,
        "base_id": metadata.get("base_id", sample.id),
        "scenario_id": metadata.get("scenario_id", ""),
        "reasoning_skill": metadata.get(
            "reasoning_skill", "unspecified"
        ),
        "choice_order": metadata.get("choice_order", ""),
        "target": sample.target,
        "answer": correctness.answer if correctness else None,
        "outcome": outcome,
        "format_pass": (
            formatting.value == CORRECT
            if formatting else None
        ),
        "stop_reason": stop_reason,
        "truncated": stop_reason == "max_tokens",
        "output_tokens": (
            output.usage.output_tokens
            if output.usage else None
        ),
    }

def main():
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: python analyze_log.py INPUT.eval OUTPUT.csv"
        )

    log = read_eval_log(sys.argv[1])

    if log.status != "success":
        raise ValueError(
            f"Expected a successful run; found {log.status}"
        )

    rows = [
        sample_to_row(sample)
        for sample in log.samples or []
    ]

    if not rows:
        raise ValueError("The log contains no samples.")

    output_path = Path(sys.argv[2])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0])
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Model: {log.eval.model}")
    print(f"Responses: {len(rows)}")
    print("Outcomes:", dict(Counter(
        row["outcome"] for row in rows
    )))
    print("Truncated:", sum(
        row["truncated"] for row in rows
    ))
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()