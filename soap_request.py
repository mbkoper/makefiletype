import base64
import mimetypes
import os
import re
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

MIMETYPE_MAP = {
    "pdf": "application/pdf",
    "tiff": "image/tiff",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "text": "text/plain",
    "html": "text/html",
    "xml": "application/xml",
}


def build_soap_body(file_path, mimetype, doc_name, **kwargs):
    username = os.getenv("SOAP_USERNAME")
    password = os.getenv("SOAP_PASSWORD")

    with open(file_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")

    wetscluster = kwargs.get("wetscluster", "VV")
    mediumkanaal = kwargs.get("mediumkanaal", "P")
    richting = kwargs.get("richting", "I")
    scanlocatie = kwargs.get("scanlocatie", "ZS")
    taalcodes = kwargs.get("taalcodes", "N")
    regeling = kwargs.get("regeling", "BB80")

    soap_body = f"""<soapenv:Envelope xmlns:dos="http://www.svb.nl/DossiersService/" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
<soapenv:Header>
    <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
        <wsse:UsernameToken wsu:Id="UsernameToken-32E7CBEE26ABDEDCFD169155847769816">
            <wsse:Username>{username}</wsse:Username>
            <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{password}</wsse:Password>
        </wsse:UsernameToken>
    </wsse:Security>
</soapenv:Header>
<soapenv:Body>
    <dos:registrerenNieuwDocumentRequest>
        <document>
            <indexrubrieken>
                <barcode/>
                <briefcode>{regeling}</briefcode>
                <briefstatus/>
                <datumNietRelevant>2025-02-18</datumNietRelevant>
                <datumStuk>2025-01-21</datumStuk>
                <documentomschrijving>{doc_name}</documentomschrijving>
                <mediumkanaal>{mediumkanaal}</mediumkanaal>
                <richting>{richting}</richting>
                <scanbatchID>07:58:24 04-02-2025</scanbatchID>
                <scanlocatie>{wetscluster}</scanlocatie>
                <schoningsdatum>2025-02-11</schoningsdatum>
                <soortBericht>S001</soortBericht>
                <taalcodeBrief>{taalcodes}</taalcodeBrief>
                <userID>AVJMETER</userID>
                <wetscluster>{wetscluster}</wetscluster>
                <klantnummerWaarbijBehandeling>PA12345672</klantnummerWaarbijBehandeling>
                <vkWaarvoorBestemd>{scanlocatie}</vkWaarvoorBestemd>
            </indexrubrieken>
            <resource>
                <mimetype>{mimetype}</mimetype>
                <contentstream>{content_b64}</contentstream>
            </resource>
        </document>
    </dos:registrerenNieuwDocumentRequest>
</soapenv:Body>
</soapenv:Envelope>"""
    return soap_body


def send_soap_request(filename, **kwargs):
    basename = os.path.basename(filename)
    file_path = kwargs.get("file_path") or os.path.join("test-files", basename)
    name_only, _ = os.path.splitext(basename)

    mimetype = MIMETYPE_MAP.get(name_only.lower()) or mimetypes.guess_type(filename)[0] or "application/octet-stream"

    soap_body = build_soap_body(file_path, mimetype, name_only, **kwargs)

    url = "https://dms-dossier-service-dms-tst.apps.ocp-dta.esp.svb.org/generic/dossiers"
    response = requests.post(url, data=soap_body.encode("utf-8"), headers={"Content-Type": "text/xml; charset=utf-8"}, timeout=120)

    match = re.search(r"<(?:[^:>]+:)?(?:documentID|registratieKenmerk)[^>]*>([^<]+)<", response.text, re.I)
    return match.group(1).strip() if match else None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python soap_request.py <filename> [wetscluster] [mediumkanaal] [richting] [scanlocatie] [taalcodes] [regeling]")

    keys = ["wetscluster", "mediumkanaal", "richting", "scanlocatie", "taalcodes", "regeling"]
    args = dict(zip(keys, sys.argv[2:]))

    print(send_soap_request(sys.argv[1], **args))
