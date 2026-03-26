"""run_matrix.py – Send a SOAP request for every row in matrix.csv."""

import csv
import os

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

        ext = ".jpg" if mimetype == "jpeg" else "." + mimetype
        filename = grootte + ext

        doc_id = send_soap_request(
            filename=filename,
            wetscluster=wetscluster,
            mediumkanaal=mediumkanaal,
            richting=richting,
            scanlocatie=scanlocatie,
            taalcodes=taalcodes,
            regeling=regeling,
        )
        print(f"{wetscluster},{mediumkanaal},{mimetype}: doc_id={doc_id}")

