import requests
import time
import statistics

URL = "http://127.0.0.1:8000/predict"
NUM_REQUESTS = 500

latencies = [] # Recording speeds for averaging

# 500 Requests to the predict endpoint
for _ in range(NUM_REQUESTS):
    start = time.time()

    response = requests.post(URL, json={"value": 5})

    end= time.time()

    if response.status_code != 200:
        print("Request failed:", response.status_code)
        continue

    # Convert from decimal seconds to ms
    latency_ms = (end-start) * 1000
    latencies.append(latency_ms)

# Sort from low to high
latencies.sort()

def percentile(data, p):

    # Calculate the percentile position
    k = int(len(data) * (p / 100))

    # Prevents outof bounds if k = len(data)
    # Grab the kth position value
    return data[min(k, len(data) -1)]

p50 = percentile(latencies, 50)
p95 = percentile(latencies, 95)
p99 = percentile(latencies, 99)

print(f"Requests: {len(latencies)}")
print(f"p50: {p50:.2f} ms")
print(f"p95: {p95:.2f} ms")
print(f"p99: {p99:.2f} ms")