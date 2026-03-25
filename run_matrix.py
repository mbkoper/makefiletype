"""run_matrix.py – Send SOAP requests for every row in the test matrix.

For each row the script:
1. Generates a temporary file of the correct type and size using the
   generators from makefiletype.py.
2. Calls soap_request.send_soap_request() with all metadata columns.
3. Extracts the document ID from the SOAP response.
4. Collects all returned doc IDs and writes them to ``doc_ids.json``.

Usage
-----
    python run_matrix.py

Environment variables required (same as soap_request.py):
    SOAP_USERNAME   – SOAP service username
    SOAP_PASSWORD   – SOAP service password

Output
------
    doc_ids.json    – JSON array of objects, one per matrix row, containing
                      the row metadata and the returned doc ID (or null when
                      the request failed or no ID could be extracted).
"""

import json
import os
import tempfile

from makefiletype import GENERATORS, parse_size
from soap_request import extract_doc_id, send_soap_request

# ---------------------------------------------------------------------------
# Test matrix
# Columns: wetscluster, mediumkanaal, mimetype, richting, scanlocatie,
#          taalcodes, regeling, size
# ---------------------------------------------------------------------------
MATRIX = [
    # Wetscluster AA
    ("AA", "D", "pdf",  "I", "CP", "D", "P01, P02, P04", "5k"),
    ("AA", "F", "tiff", "U", "ZS", "E", "P05, P06",      "250k"),
    ("AA", "H", "jpeg", "N", "AG", "F", "E05, E06",      "5000k"),
    ("AA", "O", "text", "I", "AV", "I", "P07, P08",      "25k"),
    ("AA", "I", "html", "U", "CP", "M", "E01, E04",      "500k"),
    ("AA", "P", "xml",  "N", "ZS", "N", "P07",           "10000k"),
    # Wetscluster KW
    ("KW", "D", "tiff", "U", "AG", "P", "P13",           "50000k"),
    ("KW", "F", "jpeg", "I", "AV", "Q", "P13",           "2500k"),
    ("KW", "H", "text", "N", "CP", "S", "P13",           "100k"),
    ("KW", "O", "html", "U", "ZS", "T", "P13",           "25000k"),
    ("KW", "I", "xml",  "I", "AG", "X", "P13",           "1000k"),
    ("KW", "P", "pdf",  "N", "AV", "D", "P13",           "50k"),
    # Wetscluster TP
    ("TP", "D", "jpeg", "N", "CP", "E", "P09, P10, P11", "5k"),
    ("TP", "F", "text", "I", "ZS", "F", "P12, P99",      "250k"),
    ("TP", "H", "html", "U", "AG", "I", "E01",           "5000k"),
    ("TP", "O", "xml",  "N", "AV", "M", "P05",           "25k"),
    ("TP", "I", "pdf",  "I", "CP", "N", "E05, E07",      "500k"),
    ("TP", "P", "tiff", "U", "ZS", "P", "P01, P04, P07", "10000k"),
    # Wetscluster VV
    ("VV", "D", "text", "I", "AG", "Q", "E50",           "50000k"),
    ("VV", "F", "html", "N", "AV", "S", "E50",           "2500k"),
    ("VV", "H", "xml",  "U", "CP", "T", "E50",           "100k"),
    ("VV", "O", "pdf",  "I", "ZS", "X", "E50",           "25000k"),
    ("VV", "I", "tiff", "N", "AG", "D", "E50",           "1000k"),
    ("VV", "P", "jpeg", "U", "AV", "E", "E50",           "50k"),
]

# Map matrix mimetype names to makefiletype generator keys and file extensions
_TYPE_MAP = {
    "pdf":  ("pdf",  ".pdf"),
    "tiff": ("tiff", ".tiff"),
    "jpeg": ("jpg",  ".jpg"),
    "text": ("txt",  ".txt"),
    "html": ("html", ".html"),
    "xml":  ("xml",  ".xml"),
}


def run_matrix() -> list[dict]:
    results = []

    for idx, row in enumerate(MATRIX, start=1):
        wetscluster, mediumkanaal, mime_name, richting, scanlocatie, taalcodes, regeling, size_str = row

        gen_key, ext = _TYPE_MAP[mime_name]
        target_size = parse_size(size_str)

        print(f"\n[{idx}/{len(MATRIX)}] {wetscluster} | {mediumkanaal} | {mime_name} | "
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


def _build_result(row: tuple, *, doc_id: str | None, error: str | None = None) -> dict:
    wetscluster, mediumkanaal, mimetype, richting, scanlocatie, taalcodes, regeling, size = row
    entry = {
        "wetscluster": wetscluster,
        "mediumkanaal": mediumkanaal,
        "mimetype": mimetype,
        "richting": richting,
        "scanlocatie": scanlocatie,
        "taalcodes": taalcodes,
        "regeling": regeling,
        "grootte": size,
        "doc_id": doc_id,
    }
    if error:
        entry["error"] = error
    return entry


if __name__ == "__main__":
    results = run_matrix()

    output_file = "doc_ids.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    total = len(results)
    ok = sum(1 for r in results if r["doc_id"] is not None)
    print(f"\nDone. {ok}/{total} requests succeeded.")
    print(f"Doc IDs written to {output_file}")
