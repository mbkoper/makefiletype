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
from soap_request import send_soap_request

doc_id = send_soap_request(
    filename="250k.pdf",
    file_path="/path/to/250k.pdf",   # optional, defaults to test-files/<filename>
    wetscluster="AA",
    mediumkanaal="D",
    richting="I",
    scanlocatie="CP",
    taalcodes="N",
    regeling="P01",
)
```

---

### `run_matrix.py`

Iterates over a test matrix loaded from a CSV file, generates each test file
on the fly, sends it via `soap_request.py`, and collects all returned document
IDs.

**Usage**

```bash
python run_matrix.py [--csv <path>] [--output <path>]
```

| Argument | Description |
|----------|-------------|
| `--csv` / `-c` | Path to the matrix CSV file (default: `matrix.csv`) |
| `--output` / `-o` | Path for the JSON output file (default: `doc_ids.json`) |

**Examples**

```bash
python run_matrix.py                          # uses matrix.csv
python run_matrix.py --csv my_matrix.csv
python run_matrix.py --csv my_matrix.csv --output results.json
```

**CSV format**

The CSV must have a header row with the following columns (case-insensitive,
comma- or tab-delimited). Columns may appear in any order.

```
Wetscluster,Mediumkanaal,Mimetype,Richting,Scanlocatie,Taalcodes,Regeling,Grootte
```

| Column | Accepted values |
|--------|----------------|
| `Wetscluster` | `AA`, `KW`, `TP`, `VV`, … |
| `Mediumkanaal` | `D`, `F`, `H`, `O`, `I`, `P` |
| `Mimetype` | `pdf`, `tiff`, `jpeg`, `text`, `html`, `xml` |
| `Richting` | `I` (inkomend), `U` (uitgaand), `N` (neutraal) |
| `Scanlocatie` | `CP`, `ZS`, `AG`, `AV`, … |
| `Taalcodes` | `D`, `E`, `F`, `I`, `M`, `N`, `P`, `Q`, `S`, `T`, `X` |
| `Regeling` | Single or comma-separated codes, e.g. `P01` or `P01, P02, P04` |
| `Grootte` | Size with suffix: `5k`, `250k`, `5000k`, … |

**Sample CSV (`matrix.csv`)**

```csv
Wetscluster,Mediumkanaal,Mimetype,Richting,Scanlocatie,Taalcodes,Regeling,Grootte
AA,D,pdf,I,CP,D,"P01, P02, P04",5k
AA,F,tiff,U,ZS,E,"P05, P06",250k
AA,H,jpeg,N,AG,F,"E05, E06",5000k
AA,O,text,I,AV,I,"P07, P08",25k
AA,I,html,U,CP,M,"E01, E04",500k
AA,P,xml,N,ZS,N,P07,10000k
KW,D,tiff,U,AG,P,P13,50000k
KW,F,jpeg,I,AV,Q,P13,2500k
KW,H,text,N,CP,S,P13,100k
KW,O,html,U,ZS,T,P13,25000k
KW,I,xml,I,AG,X,P13,1000k
KW,P,pdf,N,AV,D,P13,50k
TP,D,jpeg,N,CP,E,"P09, P10, P11",5k
TP,F,text,I,ZS,F,"P12, P99",250k
TP,H,html,U,AG,I,E01,5000k
TP,O,xml,N,AV,M,P05,25k
TP,I,pdf,I,CP,N,"E05, E07",500k
TP,P,tiff,U,ZS,P,"P01, P04, P07",10000k
VV,D,text,I,AG,Q,E50,50000k
VV,F,html,N,AV,S,E50,2500k
VV,H,xml,U,CP,T,E50,100k
VV,O,pdf,I,ZS,X,E50,25000k
VV,I,tiff,N,AG,D,E50,1000k
VV,P,jpeg,U,AV,E,E50,50k
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
