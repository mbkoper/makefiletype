# makefiletype

A collection of Python utilities for generating test files of specific types
and sizes and submitting them to a DMS SOAP service.

---

## Source files

### `makefiletype.py`

Generates a file of a specified type with an **exact** target size.

**Supported types:** `pdf`, `tiff`, `jpg`, `html`, `txt`, `xml`

**Usage**

```bash
python makefiletype.py --type <type> --size <size> [--output <filename>]
```

| Argument | Description |
|----------|-------------|
| `--type` / `-t` | File type to generate (`pdf`, `tiff`, `jpg`, `html`, `txt`, `xml`) |
| `--size` / `-s` | Target size – plain integer (bytes) or with suffix `k`/`m`/`g` (e.g. `250k`, `5m`) |
| `--output` / `-o` | Output filename (default: `<size>.<ext>`, e.g. `250k.pdf`) |

**Examples**

```bash
python makefiletype.py --type pdf  --size 5k
python makefiletype.py --type tiff --size 250k --output sample.tiff
python makefiletype.py --type html --size 1m
```

---

### `soap_request.py`

Builds and sends a SOAP request to the DMS document registration service for a
single file. All document metadata fields are parameterised.

**Environment variables** (stored in a `.env` file or exported):

| Variable | Description |
|----------|-------------|
| `SOAP_USERNAME` | SOAP service username |
| `SOAP_PASSWORD` | SOAP service password |

**Command-line usage**

```bash
python soap_request.py <filename> [wetscluster] [mediumkanaal] [richting] [scanlocatie] [taalcodes] [regeling]
```

Positional arguments (all optional after `filename`):

| Position | Parameter | Example values |
|----------|-----------|----------------|
| 1 | `filename` | `250k.pdf` |
| 2 | `wetscluster` | `AA`, `KW`, `TP`, `VV` |
| 3 | `mediumkanaal` | `D`, `F`, `H`, `O`, `I`, `P` |
| 4 | `richting` | `I` (inkomend), `U` (uitgaand), `N` (neutraal) |
| 5 | `scanlocatie` | `CP`, `ZS`, `AG`, `AV` |
| 6 | `taalcodes` | `D`, `E`, `F`, `I`, `M`, `N`, `P`, `Q`, `S`, `T`, `X` |
| 7 | `regeling` | `P01`, `E05`, `P01, P02, P04` |

**Example**

```bash
python soap_request.py 250k.pdf AA D I CP N P01
```

**Importable API**

```python
from soap_request import send_soap_request, extract_doc_id

response = send_soap_request(
    filename="250k.pdf",
    file_path="/path/to/250k.pdf",   # optional, defaults to test-files/<filename>
    wetscluster="AA",
    mediumkanaal="D",
    richting="I",
    scanlocatie="CP",
    taalcodes="N",
    regeling="P01",
)

doc_id = extract_doc_id(response.text)
```

---

### `run_matrix.py`

Iterates over a 24-row test matrix covering all combinations of
`Wetscluster × Mediumkanaal × Mimetype × Richting × Scanlocatie × Taalcodes × Regeling × Grootte`,
generates each test file on the fly, sends it via `soap_request.py`, and
collects all returned document IDs.

**Usage**

```bash
python run_matrix.py
```

**Output**

`doc_ids.json` – a JSON array, one object per matrix row:

```json
[
  {
    "wetscluster": "AA",
    "mediumkanaal": "D",
    "mimetype": "pdf",
    "richting": "I",
    "scanlocatie": "CP",
    "taalcodes": "D",
    "regeling": "P01, P02, P04",
    "grootte": "5k",
    "doc_id": "<id returned by service>"
  }
]
```

A `null` `doc_id` means the request failed or the service response did not
contain a recognisable document ID. Failed rows also include an `"error"` key.

---

### `makepdf.py`

Legacy stub – redirects to `makefiletype.py --type pdf --size 5120`.
Use `makefiletype.py` directly instead.

---

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
SOAP_USERNAME=your_username
SOAP_PASSWORD=your_password
```
