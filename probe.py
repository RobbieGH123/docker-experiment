import time
import requests
import logging
from pythonjsonlogger.json import JsonFormatter

#
# LOGGING
#

logger = logging.getLogger()
handler = logging.StreamHandler()

formatter = JsonFormatter()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.setLevel(logging.INFO)

#
# PROBE CONFIG
#

URL = "http://localhost:8000/predict"

TEST_INPUT = {"value": 5}
EXPECTED_OUTPUT = {"prediction": 10.0}


def run_probe():
    try:  # Simulate a request
        response = requests.post(URL, json=TEST_INPUT, timeout=2)
        result = response.json()

        if result != EXPECTED_OUTPUT:
            logger.error(
                {"probe": "failed", "expected": EXPECTED_OUTPUT, "got": result}
            )

        else:
            logger.info({"probe": "passed"})

    except Exception as e:
        logger.error({"probe": "error", "message": str(e)})


def main():
    while True:
        run_probe()
        time.sleep(30)


if __name__ == "__main__":
    main()
