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

```Bash
python main.py run --profile oltp_like --target ./fio_testfile.dat
```

Run one profile with a custom runtime and output directory:

```Bash
python main.py run --profile streaming_like --target ./fio_testfile.dat --runtime 60 --output-dir ./results
```

Run two profiles concurrently:

```Bash
python main.py run-concurrent --profile1 streaming_like --profile2 background_backup --target ./fio_testfile.dat
```

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

Combined:
- Total throughput
- Total IOPS

## Limitation about combined percentiles

Exact combined P95/P99 for two separate fio JSON summaries are not shown.

Reason: percentiles cannot be aggregated correctly from already summarized outputs alone. Exact combined latency percentiles would require more detailed histogram-style data, for example fio `json+`.

## Notes
- The exact fio JSON structure may vary slightly by fio version.
- This prototype prioritizes clarity and correctness over advanced architecture.