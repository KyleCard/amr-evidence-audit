import sys

from inspect_ai.log import read_eval_log
from collections import defaultdict
from inspect_ai.scorer import CORRECT


log = read_eval_log(sys.argv[1])

if log.status != "success":
    raise ValueError(f"Evaluation did not complete: {log.status}")

print(f"Model: {log.eval.model}")

for sample in log.samples or []:
    scores = sample.scores or {}
    correctness = scores["choice"]
    formatting = scores["answer_format"]

    print(
        f"{sample.id}: "
        f"target={sample.target}, "
        f"answer={correctness.answer}, "
        f"correctness={correctness.value}, "
        f"format={formatting.value}"
    )

groups = defaultdict(list)

for sample in log.samples or []:
    base_id = sample.metadata["base_id"]
    groups[base_id].append(sample)

consistent_items = 0

for base_id, samples in sorted(groups.items()):
    orders = {
        sample.metadata["choice_order"]
        for sample in samples
    }

    if len(samples) != 6 or len(orders) != 6:
        raise ValueError(f"Incomplete permutation coverage: {base_id}")

    correct_count = sum(
        sample.scores["choice"].value == CORRECT
        for sample in samples
    )

    if correct_count == 6:
        consistent_items += 1

    print(f"{base_id}: {correct_count}/6 correct")

print(
    f"Correct under every order: "
    f"{consistent_items}/{len(groups)} items"
)