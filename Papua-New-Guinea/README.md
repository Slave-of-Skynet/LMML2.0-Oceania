# Papua New Guinea — Bihainim Angkol (Follow Your Uncle)

Use finite-horizon backward induction over lagoon states; main.py contains the exported policy.

## Run

Use a separate Python environment. Run from this country directory.

```bash
python -m pip install -r requirements.txt
mkdir -p outputs
python main.py
# Rebuild the exact policy:
python solve.py
```

## Input and output

The organizer input CSV and lagoon simulator contract.

Obtain task materials from the organizer task card; preserve their original filenames. Generated results belong in `outputs/` or another directory outside Git.

Organizer material: [source 1](https://drive.google.com/drive/folders/1bwIZTzYD5i5H26CWYzCm3kgDBlQ-qtF2).

## Files

- [`lagoon.py`](lagoon.py)
- [`main.py`](main.py)
- [`requirements.txt`](requirements.txt)
- [`solve.py`](solve.py)

Keep submission values on the organizer platform. No final submission value is supplied in these files.
