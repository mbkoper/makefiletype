"""run_matrix.py – Send a SOAP request for every row in matrix.csv."""

import csv
import os
import tempfile

from makefiletype import GENERATORS, parse_size
from soap_request import send_soap_request

CSV_FILE = os.path.join(os.path.dirname(__file__), "matrix.csv")

TYPE_MAP = {
    "pdf":  ("pdf",  ".pdf"),
    "tiff": ("tiff", ".tiff"),
    "jpeg": ("jpg",  ".jpg"),
    "text": ("txt",  ".txt"),
    "html": ("html", ".html"),
    "xml":  ("xml",  ".xml"),
}

with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        wetscluster  = row["Wetscluster"]
        mediumkanaal = row["Mediumkanaal"]
        mimetype     = row["Mimetype"].lower()
        richting     = row["Richting"]
        scanlocatie  = row["Scanlocatie"]
        taalcodes    = row["Taalcodes"]
        regeling     = row["Regeling"]
        grootte      = row["Grootte"]

        gen_key, ext = TYPE_MAP[mimetype]
        data = GENERATORS[gen_key](parse_size(grootte))

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        try:
            doc_id = send_soap_request(
                filename=os.path.basename(tmp_path),
                wetscluster=wetscluster,
                mediumkanaal=mediumkanaal,
                richting=richting,
                scanlocatie=scanlocatie,
                taalcodes=taalcodes,
                regeling=regeling,
                file_path=tmp_path,
            )
            print(f"{wetscluster},{mediumkanaal},{mimetype}: doc_id={doc_id}")
        finally:
            os.unlink(tmp_path)

