# AMR Evidence Audit

## A pilot evaluation of evidence interpretation with Inspect AI

**Author:** Kyle J. Card  
**Assessment date:** November 2, 2026

### Summary

In a small evaluation using Inspect AI, a locally served `gemma4` model with 12B parameters returned correct classifications for **68 of 72 responses (94.4%)**. The remaining four responses reached the configured 2,048-token output limit without producing a final answer. All delivered final answers were correct. **Ten of 12 claims (83.3%) were answered correctly under all six answer-choice orders.**

Failures occurred in a scenario that required interpreting the mean of signed score changes. This pilot demonstrates an evaluation workflow that distinguishes classification outcomes from answer-delivery failures and checks sensitivity to answer-choice presentation. Its small, closely related examples support conclusions about the tested items and configuration. Importantly, they do not establish broad biological reasoning ability or biosecurity risk.

### Evaluation question and scope

The evaluation asks whether a model can classify a claim as **Supported**, **Contradicted**, or **Insufficient**, using only a supplied fictional study summary:

- **Supported:** The supplied evidence establishes the claim within its stated scope.
- **Contradicted:** The supplied evidence establishes something incompatible with the claim.
- **Insufficient:** The supplied evidence establishes neither the claim nor its contradiction.

The examples use antimicrobial-susceptibility framing to test evidence interpretation. They contain fictional backgrounds and synthetic measurements, without organism-specific experimental procedures, sequences, resistance-conferring mutations, selection conditions, or biological optimization advice. The model receives no browsing or biological tools. This is an evidence-interpretation evaluation, rather than an assessment of misuse capability, clinical decision quality, refusal behavior, or safeguard effectiveness.

### Design and implementation

Development examples were used to implement and inspect the evaluation before the held-out assessment. The final dataset contains **four newly authored scenarios, each with three claims: one per reference label**. The scenarios address:

| Scenario | Evidence and inference tested |
|---|---|
| Replication structure | Eight independently maintained populations contribute three measurements each; counts establish biological replication but do not establish sources of variability. |
| Direction and magnitude | Seven populations change by −2 units and three by +6 units; the mean signed change is +0.4, while percentage changes require unreported baseline values. |
| Genetic-background scope | H1 and H2 have opposite measured score changes; H3 is unmeasured. |
| Clinical translation | A laboratory score decreases in K1, while patient outcomes and a validated link to recovery rates are absent. |

The 12 reference labels and rationales were reviewed before the evaluated model was run on these items. Each claim was presented under all six permutations of the three answer choices, yielding **72 evaluation responses**. Each correct label therefore occupied positions A, B, and C twice per claim. Reference targets were remapped with the choices. Unique variant IDs and `base_id` metadata linked each response to its original claim.

These items were held out from model-driven development before this assessment. They use familiar reasoning categories and a shared task template, so they represent a small transfer assessment within the pilot, rather than an independent external benchmark.

JSON records were converted into Inspect `Sample` objects. The prompt included the instructions, shared context, study summary, claim, and answer choices. Reference labels and rationales were excluded from model messages. The solver requested a final response in the form `ANSWER: A`, `ANSWER: B`, or `ANSWER: C`.

Two scorers operated on the same generated response:

1. Inspect's built-in `choice()` scorer extracted the selected letter and compared it with the reference target.
2. A custom Python scorer checked the final completion against `ANSWER: [ABC]`, allowing surrounding whitespace and rejecting additional final-response text. Separately recorded reasoning was outside this formatting check.

Analysis scripts extracted per-response results, missing or unparsed answers, formatting outcomes, stop reasons, and reported token usage. Checks established unique IDs, balanced label positions, complete permutation coverage, and preservation of semantic answer mappings.

### Configuration and evidence record

| Component | Recorded setting |
|---|---|
| Model/provider | `ollama/gemma4:12b` |
| Quantization | `Q4_K_M` |
| Inspect AI | 0.3.287 |
| Ollama server | 0.40.9 |
| Python | 3.14.8 |
| OpenAI-compatible client package | 3.42.0 |
| Temperature | 0 |
| Maximum generated output | 2,048 tokens |
| Maximum concurrent connections | 1 |
| Epochs | 1 response per variant |
| Allocated context | 4,096 tokens observed with `ollama ps` before assessment; not independently recorded in the evaluation log |

Other generation settings retained defaults and were not exhaustively controlled. Temperature zero does not establish determinism across environments or repeated runs.

The snapshot was captured at **16:49:41 UTC**, before the evaluation began at **16:50:22 UTC**. It records package versions, model metadata, and SHA-256 fingerprints of code, datasets, the package lock file, and run configuration. The recorded model digest is:

```text
6114515d63c17436a7c0417d82820ac65ad643e2806c5a3c89cb62846436ed0b
```

The reviewed `data/heldout.json` matches its snapshot fingerprint:

```text
ef68281cf4fb7097f948b544755c5e698d1dd395ec003b795e9408a5dfe58083
```

The log records the intended dataset, all 72 samples, one epoch, no sample filter, and the generation settings above. Inputs and semantic targets were checked against the reviewed dataset. The snapshot documents the model identity reported by Ollama at capture time; the evaluation log does not independently attest the weight digest.

### Results

| Scenario | Correct responses | Claims correct under every order | Empty final answers |
|---|---:|---:|---:|
| Replication structure | 18/18 | 3/3 | 0 |
| Direction and magnitude | 14/18 | 1/3 | 4 |
| Genetic-background scope | 18/18 | 3/3 | 0 |
| Clinical translation | 18/18 | 3/3 | 0 |
| **Total** | **68/72 (94.4%)** | **10/12 (83.3%)** | **4/72 (5.6%)** |

All 68 delivered final answers matched their reference labels and passed the formatting rule. The four empty final answers received Inspect's `N` correctness value for no answer and failed the formatting check. They remain in the denominator of overall accuracy. Among delivered final answers, accuracy was 68/68; this conditional figure does not replace the overall result.

The mean-change Supported claim succeeded under five of six orders; its Contradicted claim succeeded under three of six. The Insufficient claim about percentage changes succeeded under all six.

| Failed claim | Choice-order code | Reference letter |
|---|---|---|
| Mean follow-up score was 0.4 units higher | `021` | A |
| Mean follow-up score was lower | `021` | C |
| Mean follow-up score was lower | `201` | C |
| Mean follow-up score was lower | `210` | B |

Order codes give the original zero-based choice positions: `0` = Supported, `1` = Contradicted, `2` = Insufficient. For example, `021` presents Supported, Insufficient, Contradicted.

Each failed response contained recorded reasoning, generated exactly **2,048 output tokens**, and ended with `max_tokens` without a final completion. Total reported token usage was 2,311–2,316 for those responses. These observations identify the configured output cap as the observed stopping boundary, rather than the previously observed 4,096-token context allocation. They do not establish whether a larger budget would have produced a correct final answer.

Inspect reported a successful run with 72 completed samples. That execution status means the evaluation finished; it does not mean every response supplied an answer.

### Interpretation and limitations

The model supplied correct classifications whenever it delivered a final answer, but answer delivery failed on four mean-change variants within the fixed output budget. Delivery varied across answer orders in this run. With one response per variant, this does not establish a stable position bias or isolate the cause of the variation.

The primary limitations are:

- **Small, related item set:** The 72 responses comprise six presentations of each of 12 claims from four scenarios. They are not 72 independent scientific questions. No independence-based confidence interval is reported.
- **Narrow construct:** The task supplies concise summaries, explicit definitions, and three answer labels. It does not assess literature retrieval, open-ended scientific review, experimental planning, or real-world biological risk.
- **Limited coverage within categories:** Supported and Contradicted claims in the clinical scenario concern laboratory score direction; only its Insufficient claim directly tests translation to recovery rates. Category totals therefore mix different inference demands.
- **Author-reviewed references:** Labels were reviewed before execution, but were not independently adjudicated by a blinded external reviewer. Development and held-out examples share a template and reasoning categories.
- **Single model and configuration:** Findings are conditional on this local model build, quantization, budget, and one response per presentation. No cross-model comparison or repeated-run reliability estimate was performed.
- **Scoring scope:** Letter matching measures classification, and the format scorer measures syntax. Neither independently establishes the quality of the model's reasoning. Missing answers do not establish a particular incorrect belief.

Development had already exposed the importance of item wording: an initial clinical claim about what a study “establishes” admitted competing interpretations. A direct conditional patient-outcome claim was retained for subsequent work. That exploratory revision informed item design; it was not evidence of a causal effect of wording. The held-out dataset and results were preserved without post-result revision or budget expansion.

### Reproduction and supporting files

From the project environment, the held-out run is invoked with:

```bash
inspect eval --run-config configs/heldout.json
```

The configuration selects `evidence_audit.py@evidence_order_audit` and `data/heldout.json`. The local Ollama model must be available. Reproduction should retain the recorded settings and model identity, check the active context allocation, and preserve any new run as a separate result.

The evidence package consists of:

- `data/heldout.json` and `configs/heldout.json`;
- `evidence_audit.py`, `analyze_log.py`, `summarize_log.py`, and `requirements-lock.txt`;
- `results/heldout_snapshot.json`;
- `logs/2026-11-02T16-50-22-00-00_evidence-order-audit_336UG5dUAsfbYNsyMr68Vx.eval`;
- per-response CSV output generated from that log.

**Development disclosure:** This project was developed as a guided Python and Inspect AI exercise with ChatGPT assistance in code, task design, item review, analysis, and report drafting. Kyle authored and reviewed claims and ran the evaluations locally. The resulting artifact demonstrates an implemented pilot workflow; it should not be represented as independently validated benchmark research.

Future work could separately compare output budgets, repeat runs, add independently reviewed scenarios, or evaluate another model. Each would extend the evidence beyond the frozen result reported here.
