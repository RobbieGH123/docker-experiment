import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed # Designed to run multiple concurrent tests

"""
   This is a script to test how my API performs (latency) under concurrent requests
   as opposed to latency_test.py which tests sequential requests
   This is more reflective of real world traffic
"""

URL = "http://127.0.0.1:8000/predict"
NUM_REQUESTS = 500
CONCURRENCY = 50  # start small

latencies = []

def send_request():

    start = time.time()
    response = requests.post(URL, json={"value": 5})
    end = time.time()

    # If successful, return the time in milliseconds
    if response.status_code == 200:

        # Return the total time, in Ms
        return (end-start) * 1000
    return None

# Always deal with 10 requests at a time
with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:

    # Pass in the function
    # Create a total workload of NUM_REQUESTS (100) tasks
    futures = [executor.submit(send_request) for _ in range(NUM_REQUESTS)]

    # Loop through the completed functions
    for future in as_completed(futures):

        # Grab the actual function output
        result = future.result()

        #  Ensure None does not get added to the list
        if result is not None:
            latencies.append(result)

#-----------------
# PERCENTILES
#------------------------

# Sort from low to high, for percentile selection
latencies.sort()

def percentile(data, p):
    k = int(len(data) * (p/100))

    # Prevent out of bounds errors
    return data[min(k, len(data) -1)]

p50 = percentile(latencies, 50)
p95 = percentile(latencies, 95)
p99 = percentile(latencies, 99)

print("\n--- Stress Test Report ---")
print(f"Concurrency: {CONCURRENCY}")
print(f"Requests: {len(latencies)}")
print(f"p50: {p50:.2f} ms")
print(f"p95: {p95:.2f} ms")
print(f"p99: {p99:.2f} ms")