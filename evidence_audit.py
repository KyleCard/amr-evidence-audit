from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.scorer import (
    CORRECT,
    INCORRECT,
    Score,
    Target,
    accuracy,
    choice,
    scorer,
)
from inspect_ai.solver import TaskState, multiple_choice
import re
import json
from pathlib import Path
from copy import deepcopy
from itertools import permutations

SUMMARY = """
Eight bacterial isolates each have a baseline and follow-up
antimicrobial susceptibility score. A lower score represents
greater measured susceptibility. Six isolates have lower
follow-up scores, while the remaining two have higher follow-up
scores. No numerical scores or patient outcomes are supplied.
"""

DECREASE_SUMMARY = """
Eight bacterial isolates each have a baseline and
follow-up susceptibility score. Lower scores represent greater
measured susceptibility.

The exact changes, defined as follow-up minus baseline, are:
-1, -1, -1, -1, -1, -1, +1, +1.

No patient outcomes are supplied.
"""

INCREASE_SUMMARY = """
Eight bacterial isolates each have a baseline and
follow-up susceptibility score. Lower scores represent greater
measured susceptibility.

The exact changes, defined as follow-up minus baseline, are:
-1, -1, -1, -1, -1, -1, +5, +5.

No patient outcomes are supplied.
"""

INSTRUCTIONS = """
Assess the claim using only the supplied evidence.

SUPPORTED: The evidence establishes the claim.
CONTRADICTED: The evidence establishes something incompatible
with the claim.
INSUFFICIENT: The evidence establishes neither the claim nor
its contradiction.
"""

LABELS = ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT"]

def make_sample(
    sample_id: str,
    claim: str,
    target: str,
    summary: str = SUMMARY,
    evidence_condition: str = "direction_only",
) -> Sample:
    return Sample(
        id=sample_id,
        input=f"{INSTRUCTIONS}\nStudy:\n{summary}\nClaim:\n{claim}",
        choices=LABELS,
        target=target,
        metadata={
            "scenario_id": "direction_of_change",
            "evidence_condition": evidence_condition,
        },
    )

def valid_answer_format(text: str) -> bool:
    return re.fullmatch(r"ANSWER: [ABC]", text.strip()) is not None

@scorer(metrics=[accuracy()])
def answer_format():
    async def score(state: TaskState, target: Target) -> Score:
        response = state.output.completion
        valid = valid_answer_format(response)

        return Score(
            value=CORRECT if valid else INCORRECT,
            answer=response,
            explanation=(
                "Matches the required answer format."
                if valid
                else "Does not match the required answer format."
            ),
        )

    return score

def load_samples(filename: str) -> list[Sample]:
    path = Path(__file__).resolve().parent / filename
    data = json.loads(path.read_text(encoding="utf-8"))

    context = data["context"]
    samples = []
    seen_ids = set()

    for record in data["samples"]:
        sample_id = record["id"]
        label = record["label"]

        if sample_id in seen_ids:
            raise ValueError(f"Duplicate sample ID: {sample_id}")

        if label not in LABELS:
            raise ValueError(f"Unknown label for {sample_id}: {label}")

        seen_ids.add(sample_id)

        samples.append(
            Sample(
                id=sample_id,
                input=(
                    f"{INSTRUCTIONS}\n"
                    f"Context:\n{context}\n"
                    f"Study:\n{record['summary']}\n"
                    f"Claim:\n{record['claim']}"
                ),
                choices=LABELS,
                target="ABC"[LABELS.index(label)],
                metadata={
                    "scenario_id": record["scenario_id"],
                    "evidence_condition": record["evidence_condition"],
                    "reference_rationale": record["rationale"],
                    "reasoning_skill": record.get("reasoning_skill", "unspecified"),
                },
            )
        )

    return samples

def build_choice_permutations(filename: str) -> list[Sample]:
    variants = []

    for sample in load_samples(filename):
        original_target_index = "ABC".index(sample.target)

        for order in permutations(range(3)):
            variant = deepcopy(sample)

            variant.choices = [
                sample.choices[index] for index in order
            ]

            new_target_index = order.index(original_target_index)
            variant.target = "ABC"[new_target_index]

            order_id = "".join(str(index) for index in order)
            variant.id = f"{sample.id}__order_{order_id}"

            variant.metadata = {
                **(sample.metadata or {}),
                "base_id": sample.id,
                "choice_order": order_id,
            }

            variants.append(variant)

    return variants

@task
def evidence_audit() -> Task:
    return Task(
        dataset=[
            make_sample(
                "majority_decreased",
                "Most of these eight isolates had lower follow-up scores.",
                "A",
            ),
            make_sample(
                "all_decreased",
                "All eight isolates had lower follow-up scores.",
                "B",
            ),
            make_sample(
                "mean_decreased",
                "The mean score across the eight isolates decreased.",
                "C",
            ),
            make_sample(
                sample_id="mean_decreased_with_values",
                claim="The mean score across the eight isolates decreased.",
                target="A",
                summary=DECREASE_SUMMARY,
                evidence_condition="numeric_mean_decrease",
            ),
            make_sample(
                sample_id="mean_increased_with_values",
                claim="The mean score across the eight isolates decreased.",
                target="B",
                summary=INCREASE_SUMMARY,
                evidence_condition="numeric_mean_increase",
            ),
        ],
        solver=multiple_choice(),
        scorer=[choice(), answer_format()],
    )

@task
def replication_audit(choice_seed: int = -1) -> Task:
    dataset = MemoryDataset(
        load_samples("data/replication.json")
    )

    if choice_seed >= 0:
        dataset.shuffle_choices(seed=choice_seed)

    return Task(
        dataset=dataset,
        solver=multiple_choice(),
        scorer=[choice(), answer_format()],
    )

@task
def replication_order_audit() -> Task:
    return Task(
        dataset=build_choice_permutations(
            "data/replication.json"
        ),
        solver=multiple_choice(),
        scorer=[choice(), answer_format()],
    )

@task
def evidence_order_audit(
    dataset_file: str = "data/generalization.json",
) -> Task:
    return Task(
        dataset=build_choice_permutations(dataset_file),
        solver=multiple_choice(),
        scorer=[choice(), answer_format()],
    )