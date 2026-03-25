"""run_matrix.py – Send SOAP requests for every row in the test matrix.

For each row the script:
1. Generates a temporary file of the correct type and size using the
   generators from makefiletype.py.
2. Calls soap_request.send_soap_request() with all metadata columns.
3. Extracts the document ID from the SOAP response.
4. Collects all returned doc IDs and writes them to ``doc_ids.json``.

Usage
-----
    python run_matrix.py [--csv <path>] [--output <path>]

    When --csv is omitted the script falls back to ``matrix.csv`` in the
    same directory, which contains the default 24-row test matrix.

CSV format
----------
The CSV file must have a header row with (case-insensitive) column names:

    Wetscluster,Mediumkanaal,Mimetype,Richting,Scanlocatie,Taalcodes,Regeling,Grootte

Columns may appear in any order.  The delimiter is auto-detected (comma or
tab).  Rows that are completely empty are silently skipped.

Environment variables required (same as soap_request.py):
    SOAP_USERNAME   – SOAP service username
    SOAP_PASSWORD   – SOAP service password

Output
------
    doc_ids.json (default) – JSON array of objects, one per matrix row,
    containing the row metadata and the returned doc ID (or null when the
    request failed or no ID could be extracted).
"""

import argparse
import csv
import json
import os
import sys
import tempfile

from makefiletype import GENERATORS, parse_size
from soap_request import extract_doc_id, send_soap_request

# Default CSV shipped with the project
_DEFAULT_CSV = os.path.join(os.path.dirname(__file__), "matrix.csv")

# Required CSV column names (case-insensitive)
_REQUIRED_COLUMNS = {"wetscluster", "mediumkanaal", "mimetype", "richting",
                     "scanlocatie", "taalcodes", "regeling", "grootte"}

# Map matrix mimetype names to makefiletype generator keys and file extensions
_TYPE_MAP = {
    "pdf":  ("pdf",  ".pdf"),
    "tiff": ("tiff", ".tiff"),
    "jpeg": ("jpg",  ".jpg"),
    "text": ("txt",  ".txt"),
    "html": ("html", ".html"),
    "xml":  ("xml",  ".xml"),
}


def load_csv(path: str) -> list[dict]:
    """Read the matrix CSV and return a list of row dicts with lower-case keys."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        # Sniff delimiter (comma or tab)
        sample = fh.read(4096)
        fh.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
        except csv.Error:
            dialect = csv.excel  # fall back to comma

        reader = csv.DictReader(fh, dialect=dialect)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file appears to be empty: {path}")

        # Normalise header names to lower-case
        reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]

        missing = _REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"CSV is missing required column(s): {', '.join(sorted(missing))}"
            )

        rows = []
        for raw in reader:
            # Skip blank rows
            if not any(v and v.strip() for v in raw.values()):
                continue
            rows.append({k.strip().lower(): (v or "").strip() for k, v in raw.items()})

    if not rows:
        raise ValueError(f"CSV file contains no data rows: {path}")

    return rows


def run_matrix(rows: list[dict]) -> list[dict]:
    results = []

    for idx, row in enumerate(rows, start=1):
        wetscluster = row["wetscluster"]
        mediumkanaal = row["mediumkanaal"]
        mime_name    = row["mimetype"].lower()
        richting     = row["richting"]
        scanlocatie  = row["scanlocatie"]
        taalcodes    = row["taalcodes"]
        regeling     = row["regeling"]
        size_str     = row["grootte"]

        if mime_name not in _TYPE_MAP:
            msg = f"Unknown mimetype '{mime_name}'; supported: {', '.join(_TYPE_MAP)}"
            print(f"\n[{idx}/{len(rows)}] SKIP – {msg}")
            results.append(_build_result(row, doc_id=None, error=msg))
            continue

        gen_key, ext = _TYPE_MAP[mime_name]

        try:
            target_size = parse_size(size_str)
        except Exception as exc:
            msg = f"Invalid size '{size_str}': {exc}"
            print(f"\n[{idx}/{len(rows)}] SKIP – {msg}")
            results.append(_build_result(row, doc_id=None, error=msg))
            continue

        print(f"\n[{idx}/{len(rows)}] {wetscluster} | {mediumkanaal} | {mime_name} | "
              f"{richting} | {scanlocatie} | {taalcodes} | {regeling} | {size_str}")

        # Generate the file content
        try:
            data = GENERATORS[gen_key](target_size)
        except Exception as exc:
            print(f"  ERROR generating file: {exc}")
            results.append(_build_result(row, doc_id=None, error=str(exc)))
            continue

        # Write to a named temp file so soap_request can read it
        suffix = f"_{wetscluster}_{mediumkanaal}_{size_str}{ext}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        try:
            response = send_soap_request(
                filename=os.path.basename(tmp_path),
                wetscluster=wetscluster,
                mediumkanaal=mediumkanaal,
                richting=richting,
                scanlocatie=scanlocatie,
                taalcodes=taalcodes,
                regeling=regeling,
                file_path=tmp_path,
            )

            if response.ok:
                doc_id = extract_doc_id(response.text)
                print(f"  OK  – doc_id: {doc_id}")
                results.append(_build_result(row, doc_id=doc_id))
            else:
                msg = f"HTTP {response.status_code}"
                print(f"  FAIL – {msg}")
                results.append(_build_result(row, doc_id=None, error=msg))

        except Exception as exc:
            print(f"  ERROR sending request: {exc}")
            results.append(_build_result(row, doc_id=None, error=str(exc)))
        finally:
            os.unlink(tmp_path)

    return results


def _build_result(row: dict, *, doc_id: str | None, error: str | None = None) -> dict:
    entry = {
        "wetscluster": row.get("wetscluster", ""),
        "mediumkanaal": row.get("mediumkanaal", ""),
        "mimetype":     row.get("mimetype", ""),
        "richting":     row.get("richting", ""),
        "scanlocatie":  row.get("scanlocatie", ""),
        "taalcodes":    row.get("taalcodes", ""),
        "regeling":     row.get("regeling", ""),
        "grootte":      row.get("grootte", ""),
        "doc_id":       doc_id,
    }
    if error:
        entry["error"] = error
    return entry


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run SOAP requests for every row in a matrix CSV file."
    )
    parser.add_argument(
        "--csv", "-c",
        default=_DEFAULT_CSV,
        metavar="FILE",
        help=f"Path to the matrix CSV file (default: matrix.csv)",
    )
    parser.add_argument(
        "--output", "-o",
        default="doc_ids.json",
        metavar="FILE",
        help="Path for the JSON output file (default: doc_ids.json)",
    )
    args = parser.parse_args()

    try:
        rows = load_csv(args.csv)
    except (OSError, ValueError) as exc:
        print(f"Error reading CSV: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(rows)} row(s) from {args.csv}")

    results = run_matrix(rows)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    total = len(results)
    ok = sum(1 for r in results if r["doc_id"] is not None)
    print(f"\nDone. {ok}/{total} requests succeeded.")
    print(f"Doc IDs written to {args.output}")
