import hashlib
import json
import platform
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
MODEL_NAME = "gemma4:12b"
OLLAMA_URL = "http://localhost:11434"


def get_json(endpoint):
    with urlopen(
        f"{OLLAMA_URL}{endpoint}", timeout=10
    ) as response:
        return json.load(response)


def main():
    models = get_json("/api/tags")["models"]
    model = next(
        (
            entry for entry in models
            if entry["name"] == MODEL_NAME
        ),
        None,
    )

    if model is None:
        raise ValueError(f"Model not found: {MODEL_NAME}")

    files = [
        ROOT / "evidence_audit.py",
        ROOT / "summarize_log.py",
        ROOT / "analyze_log.py",
        ROOT / "snapshot_config.py",
        ROOT / "requirements-lock.txt",
    ]
    files += sorted((ROOT / "data").glob("*.json"))
    files += sorted((ROOT / "configs").glob("*.json"))

    hashes = {
        str(path.relative_to(ROOT)): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in files
    }

    snapshot = {
        "captured_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "python_version": platform.python_version(),
        "inspect_ai_version": version("inspect-ai"),
        "openai_client_version": version("openai"),
        "ollama_version": get_json("/api/version")["version"],
        "model_name": MODEL_NAME,
        "model_digest": model["digest"],
        "model_details": model.get("details", {}),
        "file_sha256": hashes,
    }

    destination = ROOT / "results" / "heldout_snapshot.json"
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("x", encoding="utf-8") as handle:
        json.dump(snapshot, handle, indent=2)
        handle.write("\n")

    print(f"Saved: {destination}")


if __name__ == "__main__":
    main()