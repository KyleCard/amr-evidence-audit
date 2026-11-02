# AMR Evidence Audit

A small, reproducible [Inspect AI](https://inspect.aisi.org.uk/) evaluation of whether a locally served language model distinguishes **supported**, **contradicted**, and **insufficient-evidence** claims in fictional antimicrobial-susceptibility studies.

The project combines domain-informed item design, custom Python scoring, exhaustive answer-choice permutations, and analysis of missing answers and token-limit failures.

**[Read the report](amr_evidence_audit_report.md)** · **[Inspect the held-out dataset](data/heldout.json)** · **[View per-response results](results/heldout.csv)**

## Main findings

The recorded assessment used `ollama/gemma4:12b` on November 2, 2026: **four scenarios, 12 claims, and six answer orders per claim**, for 72 responses.

| Scenario | Correct responses | Claims correct under all six orders |
|---|---:|---:|
| Replication structure | 18/18 | 3/3 |
| Direction and magnitude | 14/18 | 1/3 |
| Genetic-background scope | 18/18 | 3/3 |
| Clinical translation | 18/18 | 3/3 |
| **Total** | **68/72 (94.4%)** | **10/12 (83.3%)** |

All 68 delivered final answers were correct and properly formatted. Four responses in the mean-change scenario reached the 2,048-token output limit without producing a final answer. Those failures remain in the overall accuracy denominator.

These are 12 related claims from four authored scenarios, not 72 independent scientific questions. The pilot evaluates interpretation of supplied evidence and answer delivery under a fixed budget. It does not establish broad biological competence, clinical utility, misuse capability, or safeguard effectiveness. See the report for limitations and failure analysis.

## Evaluation design

Each item supplies a fictional study summary and one claim. The model chooses among:

- **Supported:** The evidence establishes the claim.
- **Contradicted:** The evidence establishes something incompatible with the claim.
- **Insufficient:** The evidence establishes neither the claim nor its contradiction.

The evaluation uses all six permutations of the answer choices and remaps reference letters to preserve their meanings. A built-in correctness scorer and a custom final-response format scorer assess the same output separately. Reference labels and rationales are retained outside the model prompt.

Development examples informed the implementation and item review. Held-out labels and rationales were reviewed before the evaluated model ran on those items; the held-out result was preserved without post-result revision. The examples use synthetic measurements and omit actionable biological procedures, sequences, and resistance-engineering guidance. No browsing or biological tools are supplied to the model.

## Setup

The recorded environment used Python 3.14.8, Inspect AI 0.3.287, and Ollama 0.40.9. The lock file captures the Python environment used for the assessment; installation on other environments has not been verified.

```bash
git clone https://github.com/KyleCard/amr-evidence-audit.git
cd amr-evidence-audit
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`.

For new inference runs, install [Ollama](https://ollama.com/) and ensure its local server is running with the intended model available:

```bash
ollama ls
ollama ps
```

If the server is not already running, start `ollama serve` in a separate terminal. Inspect's Ollama integration uses the default local endpoint `http://localhost:11434/v1`.

The model tag alone does not identify an exact build. The recorded model digest and quantization are in [the held-out snapshot](results/heldout_snapshot.json). The active context allocation observed before assessment was 4,096 tokens; check it with `ollama ps` while the model is loaded. Matching these settings supports comparison but does not guarantee identical outputs.

## Analyze the bundled assessment

These commands read existing results without making model calls:

```bash
python analyze_log.py \
  logs/2026-11-02T16-50-22-00-00_evidence-order-audit_336UG5dUAsfbYNsyMr68Vx.eval \
  results/heldout_reanalysis.csv
```

```bash
python summarize_log.py \
  logs/2026-11-02T16-50-22-00-00_evidence-order-audit_336UG5dUAsfbYNsyMr68Vx.eval
```

Expected diagnostics are **68 correct, four missing final answers, and four truncated responses**. The grouped summary reports **10/12 claims correct under every order**. `summarize_log.py` expects complete six-order groups and their metadata; use it with the order-audit logs.

## Run a new assessment

From the repository root:

```bash
inspect eval --run-config configs/heldout.json \
  --log-dir logs/reproduction
```

The configuration uses temperature 0, a 2,048-token output limit, one concurrent connection, and one epoch. It evaluates all 72 variants. To use a different available model, add `--model ollama/YOUR_MODEL_NAME`; report that run as a separate condition.

Use the new log path with the analysis scripts. Inspect responses interactively with:

```bash
inspect view
```

Keep the bundled assessment and snapshot as the historical evidence record. The held-out examples are now public, so subsequent development using their results should be distinguished from the original assessment.

## Files

| Path | Purpose |
|---|---|
| `evidence_audit.py` | Tasks, dataset loading, choice permutations, and custom format scorer |
| `data/` | Development datasets and reviewed held-out claims |
| `configs/heldout.json` | Recorded held-out run configuration |
| `analyze_log.py` | Per-response diagnostics and CSV export |
| `summarize_log.py` | Correctness summaries grouped across answer orders |
| `snapshot_config.py` | Environment, local model metadata, and file fingerprint capture |
| `requirements-lock.txt` | Recorded Python package versions |
| `logs/` | Development and held-out evaluation logs |
| `results/` | CSV outputs and configuration snapshots |
| `amr_evidence_audit_report.md` | Methods, findings, failure analysis, and limitations |

## Development and attribution

Created by **Kyle J. Card** as a guided Python and Inspect AI project, with ChatGPT assistance in code, task design, item review, analysis, and report drafting. Kyle authored and reviewed claims and ran the evaluations locally. The project is an exploratory pilot with author-reviewed reference labels; independent benchmark validation was not performed.
