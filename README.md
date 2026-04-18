# fio Load Testing Tool

Small Python prototype that uses `fio` as the load generation engine, captures JSON results, runs one or two workloads, and prints an analytical report.

## Purpose

This project is a compact prototype for evaluating storage performance using `fio`.

## Prerequisites

- Python 3.11+
- `fio` installed and available in `PATH`

Check fio:

```bash
fio --version
```

## Project structure

- `main.py` — CLI
- `profiles.py` — fio workload profiles
- `runner.py` — fio command building and execution
- `fio_parser.py` — fio JSON parsing
- `report.py` — report formatting
- `tests/` — minimal parser tests

## Example commands

Run one profile:

```bash
python main.py run --profile oltp_like --target ./fio_testfile.dat
```

Run one profile with a custom runtime and output directory:

```bash
python main.py run --profile streaming_like --target ./fio_testfile.dat --runtime 60 --output-dir ./results
```

Run two profiles concurrently:

```bash
python main.py run-concurrent --profile1 streaming_like --profile2 background_backup --target ./fio_testfile.dat
```

Enable verbose logging (shows fio command, stderr, and parsing details):

```bash
python main.py --verbose run --profile oltp_like --target ./fio_testfile.dat
```

## Output files

fio JSON outputs are timestamped to avoid overwriting previous runs.

Use `--write-summary-json` to write an additional app-generated summary JSON file.

Example:

```bash
python main.py run-concurrent \
  --profile1 streaming_like \
  --profile2 background_backup \
  --target ./fio_testfile.dat \
  --runtime 5 \
  --output-dir ./results \
  --write-summary-json
```

This can produce files such as:
- `streaming-like_20260418_120000.json`
- `background_backup_20260418_120000.json`
- `summary_20260418_120000.json`

## Profiles

- `oltp_like` — random mixed read/write, small blocks, direct I/O
- `streaming_like` — sequential reads, larger blocks, multiple jobs 
- `background_backup` — sequential write workload intended for concurrent execution

## Report contents

Per profile:
- Throughput (MiB/s)
- IOPS
- P95 latency
- P99 latency
- Runtime

Combined (concurrent runs only):
- Total throughput
- Total IOPS

## Limitation about combined percentiles

Exact combined P95/P99 for two separate fio JSON summaries are not shown.

Reason: percentiles cannot be aggregated correctly from already summarized outputs alone. Exact combined latency percentiles would require more detailed histogram-style data, for example fio `json+`.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Unexpected internal error |
| 2 | Invalid argument (e.g. unknown profile, bad runtime, invalid path) |
| 3 | fio not found in PATH |
| 4 | fio process failed (non-zero exit) |
| 5 | fio JSON output could not be parsed |

## Notes
- The exact fio JSON structure may vary slightly by fio version.
- This prototype prioritizes clarity and correctness over advanced architecture.