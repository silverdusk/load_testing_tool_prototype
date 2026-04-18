# Research Phase — `fio` and `iperf3`

This document explains how I would use `fio` and `iperf3` in the research phase of the assignment when evaluating a storage system or a storage protocol similar to S3.

> **Note:** The values below are starting points for a prototype. In a real test, they should be adjusted for the target system, storage media, and network path.

## 1. Tool comparison

| Aspect | `fio` | `iperf3` |
|---|---|---|
| Purpose | Generate and measure storage I/O workloads | Measure network throughput and network behavior |
| What it tests | Storage path: file system, block device, object access engine, I/O scheduler | Network path between client and server |
| Use in this assignment | Run OLTP-like and streaming-like storage tests | Check whether the network is the main bottleneck |
| Main outputs | Throughput, IOPS, latency, percentiles, per-job statistics | Throughput, interval statistics, JSON output, and protocol-specific network statistics |
| Strength | Flexible workload definition: random or sequential I/O, read/write mix, block size, queue depth, parallel jobs, direct I/O | Simple way to validate the network separately from storage |
| Limitation | Does not measure network quality by itself | Does not model storage I/O patterns |
| Machine-readable output | Yes (`--output-format=json`, `json+`) | Yes (`-J` / `--json`) |

`fio` is the main tool for the storage workload. `iperf3` is the supporting tool to check whether poor results may be caused by the network.

## 2. Recommended `fio` configurations

| Workload | Goal | Recommended parameters | Reason |
|---|---|---|---|
| **OLTP database-like** | Small random mixed I/O with low latency | `rw=randrw`, `rwmixread=70` to `80`, `bs=4k`, `direct=1`, `ioengine=libaio` or `io_uring`, `iodepth=16` to `64`, `numjobs=4` to `16`, `time_based=1`, `runtime=60`+ | OLTP workloads usually use small random reads and writes with concurrency. |
| **Streaming video service-like** | Large sequential reads with multiple consumers | `rw=read`, `bs=128k` to `1m`, `direct=1`, `ioengine=libaio` or `io_uring`, `iodepth=8` to `32`, `numjobs=4` to `16`, `time_based=1`, `runtime=60`+ | Video streaming is mainly a sequential read and throughput workload. |

### Example `fio` profile snippets

> The examples below use `ioengine=libaio`, which is Linux-only. On macOS, `posixaio` is a more portable alternative.

#### OLTP-like workload

```ini
[oltp_like]
ioengine=libaio
direct=1
rw=randrw
rwmixread=70
bs=4k
iodepth=32
numjobs=8
group_reporting=1
time_based=1
runtime=60
filename=/path/to/testfile
size=4G
```

#### Streaming-like workload

```ini
[streaming_like]
ioengine=libaio
direct=1
rw=read
bs=256k
iodepth=16
numjobs=8
group_reporting=1
time_based=1
runtime=60
filename=/path/to/testfile
size=8G
```

### S3-like note

The assignment mentions a storage protocol similar to S3. In `fio`, the `http` I/O engine supports HTTP(S), WebDAV, and S3-style access. According to the documentation, this engine supports direct I/O only with `iodepth=1`. Because of that, concurrency is mainly increased with `numjobs`, not with queue depth.

## 3. Difference between `iodepth`, `numjobs`, and `direct=1`

### `iodepth`

`iodepth` is the number of I/O operations one job tries to keep in flight at the same time.

A higher `iodepth` can increase throughput when the storage system benefits from queueing. With synchronous I/O engines, increasing `iodepth` usually does not help. The requested depth may also be limited by the operating system or the selected I/O engine.

### `numjobs`

`numjobs` is the number of identical jobs that run in parallel.

It is used to simulate multiple workers or multiple clients. `iodepth` controls concurrency inside one job, while `numjobs` controls concurrency across several jobs.

The requested total concurrency is roughly `iodepth × numjobs`, although the actual number of in-flight I/O operations can be lower.

### `direct=1`

`direct=1` tells `fio` to use non-buffered I/O, usually through `O_DIRECT`.

This helps avoid the operating system page cache. As a result, the test is closer to the real storage behavior instead of measuring cached memory effects.

It also matters for Linux asynchronous I/O. The `fio` documentation notes that with `libaio`, buffered I/O is not truly asynchronous on Linux, so `iodepth` may not behave as expected unless `direct=1` is used.

Note: `libaio` is Linux-only. On macOS or other POSIX systems, `posixaio` is the portable alternative and works the same way with `direct=1`.

### `group_reporting`

`group_reporting` tells `fio` to merge the per-job statistics into a single aggregated result when `numjobs > 1`.

Without it, `fio` emits one separate stats block for each job. With `numjobs=8`, that means eight output sections instead of one. `group_reporting=1` collapses them into a single summary, which is easier to read and parse.

## 4. References

- `fio` documentation: <https://fio.readthedocs.io/en/latest/fio_doc.html>
- `iperf3` homepage: <https://software.es.net/iperf/>
- `iperf3` manual: <https://software.es.net/iperf/invoking.html>
