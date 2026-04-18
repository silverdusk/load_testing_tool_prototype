# Analytical Theory

## 1. Low Average Latency but Extremely High P99

**Question:**  
If the Average Latency is low, but the 99th Percentile (P99) is extremely high, what does this tell you about the storage system?

**Answer:**  
This indicates a **tail-latency problem**.

Most I/O requests are completing quickly, so the average latency looks good. However, a small portion of requests are much slower, which pushes P99 very high. This means the storage system is not consistently responsive under load.

In practice, this usually suggests intermittent stalls, queueing, background work, or contention. So even if the average looks acceptable, some operations can still experience noticeable delays.

### Related official documentation:
- [fio documentation — Interpreting the output (completion latency and latency distribution)](https://fio.readthedocs.io/en/latest/fio_doc.html#interpreting-the-output)
- [fio documentation — Measurements and reporting (`clat_percentiles`, `lat_percentiles`, `percentile_list`)](https://fio.readthedocs.io/en/latest/fio_doc.html#measurements-and-reporting)

---

## 2. iperf3 Metrics to Check Whether the Network Is the Main Bottleneck

**Question:**  
Which metrics from iperf3 would you include in your report to determine if the network is the primary bottleneck?

**Answer:**  
I would include the following:

- **Achieved throughput / bitrate**
- **Per-interval results**
- **Final sender and receiver summaries**
- **Results in both directions**, including reverse mode
- **Retransmits** (TCP only)

These metrics help show whether the network can sustain the expected transfer rate and whether performance is stable over time. Per-interval results are important because a single final average can hide short drops or instability. Sender and receiver summaries help confirm whether both sides see the same result. Reverse testing is useful because the bottleneck may exist only in one direction. Retransmits are reported per interval and in the final summary; a high retransmit count alongside lower-than-expected throughput is a strong signal of congestion or packet loss.

If the measured network throughput is clearly below the expected link capacity, or if throughput is unstable during the run, the network becomes a strong bottleneck candidate.

### Related official documentation:
- [iperf3 official documentation — Invoking iperf3 (interval reports, average bitrate, sender/receiver summaries, reverse mode, JSON output, and `-F` for checking whether storage is the bottleneck)](https://software.es.net/iperf/invoking.html)

---

## 3. Data Aggregation for a 24-Hour Soak Test

**Question:**  
How would you handle data aggregation for a 24-hour "Soak Test"?

**Answer:**  
I would **not** reduce a 24-hour soak test to one final average only.

Instead, I would keep the raw time-series data and also build **time-based summaries**, for example 1-minute or 5-minute buckets. This makes it possible to see long-term trends, short performance drops, degradation over time, and anomaly periods.

The final report should include:
- overall totals
- min / average / max values over time
- time-bucketed throughput and latency summaries
- highlighted anomaly periods

For fio specifically, this should be handled carefully. `--status-interval` gives **cumulative values from job start**, not true per-period measurements, so it is useful for progress visibility but not enough by itself for exact bucket-level aggregation. For long tests, it is better to keep raw logs and generate summarized views during post-processing. For percentile accuracy over time, histogram-style data is preferable to averages of interval data.

### Related official documentation:
- [fio documentation — `--status-interval` behavior and JSON caveat](https://fio.readthedocs.io/en/latest/fio_doc.html#cmdoption-status-interval)
- [fio documentation — histogram logging and percentile accuracy (`log_hist_msec`)](https://fio.readthedocs.io/en/latest/fio_doc.html#measurements-and-reporting)
- [iperf3 official documentation — interval reporting and JSON / JSON-stream output](https://software.es.net/iperf/invoking.html)
