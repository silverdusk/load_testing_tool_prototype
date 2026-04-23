# fio Load Testing Tool

Small Python prototype that uses `fio` as the load generation engine, captures JSON results, runs one or two workloads, and prints an analytical report.

## Quick start

**Requirements:** Python 3.11+, [fio 3.x](https://fio.readthedocs.io/en/latest/) in PATH, `pytest` and `ruff` for tests and linting.

```bash
fio --version          # verify fio is available
pip install pytest ruff
```

```bash
# Run a single OLTP-like profile (30 s, creates ./fio_testfile.dat)
make run

# Run two profiles concurrently
make run-concurrent
```

Or directly:

```bash
python main.py run --profile oltp_like --target ./fio_testfile.dat
```

## Report output

Latency percentiles are shown separately for read and write I/O. Only directions that produced I/O appear in the output.

Example output from a concurrent run:

```
Profile: streaming_like
  Throughput : 1842.57 MiB/s
  IOPS       : 1842.57
  Read  P95  : 8.91 ms
  Read  P99  : 11.53 ms
  Runtime    : 30.1 s

Profile: background_backup
  Throughput : 643.21 MiB/s
  IOPS       : 643.21
  Write P95  : 47.18 ms
  Write P99  : 89.40 ms
  Runtime    : 30.2 s

Combined summary:
  Total throughput : 2485.78 MiB/s
  Total IOPS       : 2485.78
  Note             : Exact combined P95/P99 are not shown because they cannot be calculated correctly from separate fio JSON summaries alone. Exact aggregation would require histogram-style data such as json+.
```

For mixed read/write profiles (e.g. `oltp_like`) both directions are shown:

```
Profile: oltp_like
  Throughput : 346.25 MiB/s
  IOPS       : 88641.02
  Read  P95  : 2.50 ms
  Read  P99  : 5.10 ms
  Write P95  : 3.78 ms
  Write P99  : 9.63 ms
  Runtime    : 30.0 s
```

## Profiles

| CLI key | Workload | Block size | Jobs | I/O depth | Runtime |
|---------|----------|------------|------|-----------|---------|
| `oltp_like` | Random mixed read/write (70/30), direct I/O | 4K | 4 | 16 | 30 s |
| `streaming_like` | Sequential reads — foreground throughput workload | 1M | 2 | 8 | 30 s |
| `background_backup` | Sequential writes — background workload, run alongside another profile | 1M | 2 | 8 | 30 s |

All profiles use `posixaio` engine and `group_reporting`. Runtime can be overridden with `--runtime <seconds>`.


## CLI reference

Run one profile with a custom runtime and output directory:

```bash
python main.py run --profile streaming_like --target ./fio_testfile.dat --runtime 5 --output-dir ./results
```

Run two profiles concurrently:

```bash
python main.py run-concurrent --profile1 streaming_like --profile2 background_backup --target ./fio_testfile.dat
```

Enable verbose logging (shows fio command, stderr, and parsing details):

```bash
python main.py --verbose run --profile oltp_like --target ./fio_testfile.dat
```

## Makefile shortcuts

| Target | Description |
|--------|-------------|
| `make help` | Show available targets and overridable variables |
| `make test` | Run all tests with pytest |
| `make lint` | Lint source files with ruff |
| `make run` | Run the `oltp_like` profile (30 s, `./fio_testfile.dat`) |
| `make run-concurrent` | Run `streaming_like` + `background_backup` concurrently |

Override defaults inline:

```bash
make run TARGET=/tmp/test.dat RUNTIME=10      # RUNTIME in seconds
make run-concurrent RESULTS=/tmp/out RUNTIME=60
```

## Output files

**Concurrent mode target files:** each profile gets its own test file derived from the base `--target` path. For example, `--target ./fio_testfile.dat` produces `./fio_testfile.dat.streaming-like.dat` and `./fio_testfile.dat.background_backup.dat`. This keeps the two workloads from interfering at the file level.

fio JSON outputs are timestamped to avoid overwriting previous runs.

Use `--write-summary-json` to write an additional app-generated summary JSON file:

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
- `streaming_like_20260418_120000.json`
- `background_backup_20260418_120000.json`
- `summary_20260418_120000.json`

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Unexpected internal error |
| 2 | Invalid argument (e.g. unknown profile, bad runtime, invalid path) |
| 3 | fio not found in PATH |
| 4 | fio process failed (non-zero exit) |
| 5 | fio JSON output could not be parsed |

## Project structure

- `main.py` — CLI
- `profiles.py` — fio workload profiles
- `runner.py` — fio command building and execution
- `fio_parser.py` — fio JSON parsing
- `report.py` — report formatting
- `tests/` — unit tests

## Notes
- The exact fio JSON structure may vary slightly by fio version. See [fio JSON output docs](https://fio.readthedocs.io/en/latest/fio_doc.html#json-output).
- This prototype prioritizes clarity and correctness over advanced architecture.
