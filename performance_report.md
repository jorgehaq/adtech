# Performance Benchmark Report

This document tracks results from Locust load tests and key backend benchmarks.

## How To Run

- UI mode: `make load-test` (opens http://localhost:8089)
- Headless: `make load-test-headless U=50 R=10 T=2m HOST=http://localhost:8070 CSV=out`

## Scenarios

- List campaigns: GET `/api/v1/campaigns/`
- List ads: GET `/api/v1/ads/`
- Analytics performance: GET `/api/v1/analytics/performance/`
- Cohort analysis: GET `/api/v1/analytics/cohorts/`
- Real-time dashboard: GET `/api/v1/analytics/realtime/dashboard/`

## Results Template

### Scenario: List campaigns
- Users: 100
- Spawn rate: 10/s
- Avg response time: N/A
- 95th percentile: N/A
- RPS: N/A
- Failure rate: N/A

### Scenario: Real-time dashboard
- Endpoint: `/api/v1/analytics/realtime/dashboard/`
- Users: 50
- Spawn rate: 5/s
- Avg time: N/A
- Notes: N/A

## CSV Output
Run headless with `--csv` to generate `out_stats.csv`, `out_failures.csv`, and `out_distribution.csv`.

