import base64
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

MIME_TYPES = {
    ".pdf": "application/pdf",
    ".tiff": "image/tiff",
    ".jpg": "image/jpeg",
    ".html": "text/html",
    ".txt": "text/plain",
    ".xml": "application/xml",
}


def get_mimetype(filename):
    _, ext = os.path.splitext(filename)
    return MIME_TYPES.get(ext.lower(), "application/octet-stream")


def build_soap_body(file_path: str, mimetype: str, doc_name: str) -> str:
    username = os.getenv("SOAP_USERNAME")
    password = os.getenv("SOAP_PASSWORD")

    if not username or not password:
        raise ValueError("Missing SOAP_USERNAME or SOAP_PASSWORD in environment variables.")

    try:
        with open(file_path, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {file_path}")

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
                <briefcode>BB80</briefcode>
                <briefstatus/>
                <datumNietRelevant>2025-02-18</datumNietRelevant>
                <datumStuk>2025-01-21</datumStuk>
                <documentomschrijving>{doc_name}</documentomschrijving>
                <mediumkanaal>P</mediumkanaal>
                <richting>I</richting>
                <scanbatchID>07:58:24 04-02-2025</scanbatchID>
                <scanlocatie>AA</scanlocatie>
                <schoningsdatum>2025-02-11</schoningsdatum>
                <soortBericht>S001</soortBericht>
                <taalcodeBrief>N</taalcodeBrief>
                <userID>AVJMETER</userID>
                <wetscluster>VV</wetscluster>
                <klantnummerWaarbijBehandeling>PA12345672</klantnummerWaarbijBehandeling>
                <vkWaarvoorBestemd>ZS</vkWaarvoorBestemd>
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


def send_soap_request(filename: str):
    filename = os.path.basename(filename)
    file_path = os.path.join("test-files", filename)
    mimetype = get_mimetype(filename)
    doc_name, _ = os.path.splitext(filename)

    soap_body = build_soap_body(file_path, mimetype, doc_name)

    url = "https://dms-dossier-service-dms-tst.apps.ocp-dta.esp.svb.org/generic/dossiers"
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
    }

    try:
        response = requests.post(
            url,
            data=soap_body.encode("utf-8"),
            headers=headers,
            timeout=120,
        )
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"SOAP request failed: {e}") from e

    print(f"Status: {response.status_code}")
    print("Response:")
    print(response.text)
    return response


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python soap_request.py <filename>")
        print("Example: python soap_request.py 250k.txt")
        sys.exit(1)

    send_soap_request(sys.argv[1])
