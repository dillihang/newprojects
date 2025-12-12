import json
import csv
import logging
from pathlib import Path


# -----------------------------
# Logging Setup
# -----------------------------
logging.basicConfig(
    filename="merge.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


# -----------------------------
# File Loading
# -----------------------------
def load_file(path: str) -> list[dict]:
    """
    Load JSON or CSV and return a list of dicts.

    - Detect format by extension.
    - Handle file errors.
    - Handle bad JSON/CSV.
    """
    p = Path(path)
    if not p.exists():
        logging.error(f"File not found: {path}")
        return []

    if p.suffix.lower() == ".json":
        return load_json(path)
    elif p.suffix.lower() == ".csv":
        return load_csv(path)
    else:
        logging.error(f"Unsupported file format: {path}")
        return []


def load_json(path: str) -> list[dict]:
    """Load and parse a JSON file safely."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to read JSON ({path}): {e}")
        return []


def load_csv(path: str) -> list[dict]:
    """Load CSV and return rows as list of dicts."""
    rows = []
    try:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except Exception as e:
        logging.error(f"Failed to read CSV ({path}): {e}")
    return rows


# -----------------------------
# Normalization / Cleaning
# -----------------------------
def normalize_record(record: dict) -> dict | None:
    """
    Normalize field names and clean data.

    - Convert variants (user_id → user, headline → title, etc.)
    - Convert types (string IDs → int)
    - Remove invalid entries (no user, empty title, etc.)
    - Return None if record is invalid.
    """
    # TODO: Implement normalization rules
    return record  # placeholder


def normalize_dataset(dataset: list[dict]) -> list[dict]:
    """Apply normalize_record() to each entry."""
    normalized = []
    for r in dataset:
        clean = normalize_record(r)
        if clean:
            normalized.append(clean)
    return normalized


# -----------------------------
# Merging Logic
# -----------------------------
def merge_datasets(a: list[dict], b: list[dict], strategy="keep_last") -> list[dict]:
    """
    Merge two datasets with duplicate resolution.

    strategy options:
        - keep_first
        - keep_last
        - merge (field-by-field combine)
        - skip (remove duplicates entirely)
    """
    # TODO: Implement merge behaviour
    return a + b  # placeholder


# -----------------------------
# Saving Output
# -----------------------------
def save_json(path: str, data: list[dict]):
    """Save merged data to JSON file."""
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to save JSON: {e}")


def save_csv(path: str, data: list[dict]):
    """Save merged data to CSV file."""
    if not data:
        logging.error("No data to save.")
        return

    try:
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    except Exception as e:
        logging.error(f"Failed to save CSV: {e}")


# -----------------------------
# Main Pipeline
# -----------------------------
def run_merge(file_a: str, file_b: str, out: str, strategy="keep_last"):
    """
    Full merge pipeline:
    1. Load files
    2. Normalize/clean
    3. Merge
    4. Save output
    """
    logging.info("=== Merge Start ===")

    data_a = load_file(file_a)
    data_b = load_file(file_b)

    data_a = normalize_dataset(data_a)
    data_b = normalize_dataset(data_b)

    merged = merge_datasets(data_a, data_b, strategy=strategy)

    if out.endswith(".json"):
        save_json(out, merged)
    elif out.endswith(".csv"):
        save_csv(out, merged)
    else:
        logging.error("Unsupported output format.")

    logging.info("=== Merge Complete ===")


# Example usage:
# run_merge("posts_a.json", "posts_b.json", "merged.json", strategy="keep_last")
