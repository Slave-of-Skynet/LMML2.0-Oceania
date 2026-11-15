# Australia — The Drunken Mario Adventures

Order annotated decisions spatially, compare behavior against the competent baseline and decode five-bit groups.

## Run

Use a separate Python environment. Run from this country directory.

```bash
python -m pip install -r requirements.txt
mkdir -p outputs
python decode.py /path/to/inventory.tsv
```

## Input and output

The recorded run and its primary inventory.tsv annotations. The original video and complete inventory were not available in this packaging workspace.

Obtain task materials from the organizer task card; preserve their original filenames. Generated results belong in `outputs/` or another directory outside Git.

The original recording and full inventory are not included because they were unavailable. The decoder can be inspected and run against independently recorded annotations; a full original-run reproduction is not established.

## Files

- [`decode.py`](decode.py)
- [`requirements.txt`](requirements.txt)

Keep submission values on the organizer platform. No final submission value is supplied in these files.
