# Performance Tests

Performance tests ensure system meets speed and scalability requirements.

## Purpose
- Validate response times
- Test system under load
- Identify performance bottlenecks
- Monitor resource usage

## Test Structure
```
test_api_performance.py        # API endpoint performance benchmarks
test_summary_generation.py     # Summary generation performance
test_concurrent_requests.py    # Concurrent user simulation
test_memory_usage.py          # Memory usage monitoring
```

## Running Performance Tests
```bash
# Run all performance tests
pytest -m performance

# Run with benchmarking
pytest -m performance --benchmark-only

# Generate performance report
pytest -m performance --html=reports/performance.html
```

## Performance Targets
- API responses: < 2 seconds (95th percentile)
- Summary generation: < 30 seconds
- Concurrent users: 100+ simultaneous
- Memory usage: < 512MB under normal load
- CPU usage: < 80% under normal load

## What to Test
- API endpoint response times
- Summary generation duration
- Database query performance  
- External API call latency
- Memory leak detection
- CPU usage patterns

## Test Configuration
- Use production-like data volumes
- Test with realistic network conditions
- Monitor system resources
- Vary load patterns (ramp up, sustained, spike)

## Benchmarking
- Use pytest-benchmark for micro-benchmarks
- Track performance over time
- Set performance regression alerts
- Profile code hot spots