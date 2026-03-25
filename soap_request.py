import base64
import os
import re
import sys
import xml.etree.ElementTree as ET

import requests
from dotenv import load_dotenv

load_dotenv()

MIME_TYPES = {
    ".pdf": "application/pdf",
    ".tiff": "image/tiff",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".html": "text/html",
    ".txt": "text/plain",
    ".xml": "application/xml",
}

# Map short mimetype names (as used in the matrix) to MIME_TYPES keys
MIMETYPE_NAME_MAP = {
    "pdf": "application/pdf",
    "tiff": "image/tiff",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "text": "text/plain",
    "html": "text/html",
    "xml": "application/xml",
}


def get_mimetype(filename):
    _, ext = os.path.splitext(filename)
    return MIME_TYPES.get(ext.lower(), "application/octet-stream")


def build_soap_body(
    file_path: str,
    mimetype: str,
    doc_name: str,
    wetscluster: str = "VV",
    mediumkanaal: str = "P",
    richting: str = "I",
    scanlocatie: str = "ZS",
    taalcodes: str = "N",
    regeling: str = "BB80",
) -> str:
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


def extract_doc_id(response_text: str) -> str | None:
    """Extract the document ID from a successful SOAP response.

    Tries several common element names used by DMS services.
    Returns the doc ID string, or None if not found.
    """
    candidate_tags = [
        "documentId",
        "docId",
        "id",
        "documentIdentifier",
        "registratieKenmerk",
        "kenmerk",
    ]
    try:
        # Strip SOAP envelope namespaces for easier parsing
        clean = re.sub(r' xmlns[^"]*"[^"]*"', "", response_text)
        root = ET.fromstring(clean)
        for elem in root.iter():
            local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if local in candidate_tags and elem.text and elem.text.strip():
                return elem.text.strip()
    except ET.ParseError:
        pass

    # Fallback: regex search for any of the candidate tags
    for tag in candidate_tags:
        match = re.search(rf"<(?:[^:>]+:)?{tag}[^>]*>([^<]+)<", response_text)
        if match:
            return match.group(1).strip()

    return None


def send_soap_request(
    filename: str,
    wetscluster: str = "VV",
    mediumkanaal: str = "P",
    richting: str = "I",
    scanlocatie: str = "ZS",
    taalcodes: str = "N",
    regeling: str = "BB80",
    file_path: str | None = None,
):
    """Send a SOAP request to register a document.

    Parameters
    ----------
    filename:
        Base name of the file (used to derive mimetype and doc name).
    wetscluster:
        Wetscluster code (e.g. 'AA', 'KW', 'TP', 'VV').
    mediumkanaal:
        Mediumkanaal code (e.g. 'D', 'F', 'H', 'O', 'I', 'P').
    richting:
        Richting code ('I'=inkomend, 'U'=uitgaand, 'N'=neutraal).
    scanlocatie:
        Scanlocatie / vkWaarvoorBestemd code (e.g. 'CP', 'ZS', 'AG', 'AV').
    taalcodes:
        Taalcode (e.g. 'D', 'E', 'F', 'I', 'M', 'N', 'P', 'Q', 'S', 'T', 'X').
    regeling:
        Regeling / briefcode (e.g. 'P01', 'E05').
    file_path:
        Absolute or relative path to the file. If omitted, defaults to
        ``test-files/<filename>``.

    Returns
    -------
    requests.Response
    """
    basename = os.path.basename(filename)
    if file_path is None:
        file_path = os.path.join("test-files", basename)

    mime_name, _ = os.path.splitext(basename)
    # Resolve mimetype: prefer the short name map, then file-extension map
    mime_short = mime_name.lower()
    if mime_short in MIMETYPE_NAME_MAP:
        mimetype = MIMETYPE_NAME_MAP[mime_short]
    else:
        mimetype = get_mimetype(basename)

    doc_name, _ = os.path.splitext(basename)

    soap_body = build_soap_body(
        file_path,
        mimetype,
        doc_name,
        wetscluster=wetscluster,
        mediumkanaal=mediumkanaal,
        richting=richting,
        scanlocatie=scanlocatie,
        taalcodes=taalcodes,
        regeling=regeling,
    )

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
    if len(sys.argv) < 2:
        print("Usage: python soap_request.py <filename> [wetscluster] [mediumkanaal] "
              "[richting] [scanlocatie] [taalcodes] [regeling]")
        print("Example: python soap_request.py 250k.txt AA D I CP N P01")
        sys.exit(1)

    kwargs = {}
    param_names = ["wetscluster", "mediumkanaal", "richting", "scanlocatie", "taalcodes", "regeling"]
    for i, name in enumerate(param_names, start=2):
        if len(sys.argv) > i:
            kwargs[name] = sys.argv[i]

    send_soap_request(sys.argv[1], **kwargs)
