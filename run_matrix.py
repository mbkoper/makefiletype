"""run_matrix.py – Send a SOAP request for every row in matrix.csv."""

import csv
import os
import tempfile

from makefiletype import GENERATORS, parse_size
from soap_request import send_soap_request

CSV_FILE = os.path.join(os.path.dirname(__file__), "matrix.csv")

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

        gen_key = "jpg" if mimetype == "jpeg" else mimetype
        ext = "." + gen_key
        data = GENERATORS[gen_key](parse_size(grootte))

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        try:
            print(f"[DEBUG] send_soap_request(filename={os.path.basename(tmp_path)!r}, wetscluster={wetscluster!r}, mediumkanaal={mediumkanaal!r}, richting={richting!r}, scanlocatie={scanlocatie!r}, taalcodes={taalcodes!r}, regeling={regeling!r}, file_path={tmp_path!r})")
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

