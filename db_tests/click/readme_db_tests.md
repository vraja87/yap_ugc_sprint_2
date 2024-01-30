# Test Results Comparison: Vertica vs Clickhouse

## Overview
Vertica is ~2.5 times slower than Clickhouse. This is all true because of the load distribution in clickhouse between the host processor cores.

Record/reading fixed 10,000,000 lines.

### Vertica
- **Record**:
  - Minimum: `0:07:11.041434`
  - Maximum: `0:07:50.666096`
  - Average: `0:07:30`
- **Reading**:
  - Minimum: `0:01:24.391322`
  - Maximum: `0:01:30.640823`
  - Average: `0:01:27`
- **Parallel Write/Read**:
  - Write:
    - Minimum: `0:07:18.520855`
    - Maximum: `0:08:04.717404`
    - Average: `0:07:49`
  - Read:
    - Minimum: `0:01:24.391322`
    - Maximum: `0:01:30.640823`
    - Average: `0:01:27`

### Clickhouse
- **Record**:
  - Minimum: `0:02:43.500633`
  - Maximum: `0:03:13.980911`
  - Average: `0:02:56`
- **Reading**:
  - Minimum: `0:00:32.690581`
  - Maximum: `0:00:43.691335`
  - Average: `0:00:36`
- **Parallel Write/Read**:
  - Write:
    - Minimum: `0:03:06.400142`
    - Maximum: `0:03:35.588837`
    - Average: `0:03:16`
  - Read:
    - Minimum: `0:01:27.012247`
    - Maximum: `0:01:59.529604`
    - Average: `0:01:33`
