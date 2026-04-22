from pydantic import BaseModel, Field, field_validator
from contextlib import asynccontextmanager
import logging
from pythonjsonlogger.json import JsonFormatter
from fastapi.exceptions import RequestValidationError
import time
import uuid
import hashlib
import math
import json
import os
from fastapi import FastAPI, Request, Header, HTTPException, Depends
from dotenv import load_dotenv
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, generate_latest
from slowapi import Limiter  # Class that manages rate limits
from slowapi.util import (
    get_ipaddr,
)  # Identifies users by IP, passed to Limit to track limits per IP
from slowapi.errors import (
    RateLimitExceeded,
)  # An automatically raised exception when a user goes over their allowed request count
from fastapi.responses import (
    JSONResponse,
)  # Class that allows you to return a response explicitly formatted as JSON

# ────────────────────────────────
# CONFIGURE LOGGING
# ────────────────────────────────────

logger = logging.getLogger()  # Get the root logger instance
handler = logging.StreamHandler()  # Create a handler that outputs to the console

formatter = JsonFormatter()  # Instantiate a JSON formatter
handler.setFormatter(formatter)  # Attach the formatter to the handler

logger.addHandler(handler)  # Register the handler with the root logger
logger.setLevel(logging.INFO)  #  Set the minimum logging level to INFO

# ────────────────────────────────
# PROMETHEUS METRICS
# ────────────────────────────────────

# Adds 1 every time is called
# Also stores details on nature of (Method, endpoint)
REQUEST_COUNT = Counter(
    "request_count", "Total number of requests received", ["method", "endpoint"]
)

# Distributes recorded latency into buckets
# Tracks latency per endpoint
REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "Latency of HTTP requests in seconds",
    ["endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1, 2),
)

model_loaded = False


def load_model():
    global model_loaded
    model_loaded = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Everything before 'yield' happens on startup
    load_model()
    yield
    # Everything after 'yield' happens on teardown


# Tells the API to use the lifespan function to manage its life cycle
app = FastAPI(lifespan=lifespan)

load_dotenv()
API_KEY = os.getenv("API_KEY")

limiter = Limiter(key_func=get_ipaddr)
app.state.limiter = limiter


# Tells FastAPI to extract x_api_key from request headers
# Injects it into the function
def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    return x_api_key


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Request and error details passed in

    # Ensure any NaN values in the error details are turned into strings
    details = exc.errors()  # Store the list of dicts

    for error in details:
        if "input" in error and isinstance(error["input"], float):
            if math.isnan(error["input"]) or math.isinf(error["input"]):
                error["input"] = str(error["input"])  # NaN was creating an error

    return JSONResponse(
        status_code=422,
        content={"detail": details},
    )


# Global Safety Net for RateLimitExceeded
@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request, exc):  # Required for exception_handler
    return JSONResponse(  # Response type
        status_code=429, content={"detail": "Rate limit exceeded"}  # Too many requests
    )


def redact_email(email: str):
    return "***@***.com"


def sanitize_log(data: dict):
    if not isinstance(data, dict):
        return data

    SENSITIVE_KEYS = {"password", "token", "api_key"}
    sanitized = {}

    # If the data contains a sensitive value, redact it
    for key, value in data.items():

        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            sanitized[key] = str(value)

        elif key.lower() == "email":
            sanitized[key] = redact_email(str(value))

        elif key.lower() in SENSITIVE_KEYS:
            sanitized[key] = "***REDACTED***"

        elif isinstance(value, dict):
            sanitized[key] = sanitize_log(value)  # Recursive call for nested dicts

        elif isinstance(
            value, list
        ):  # Loop over every item in list, recursive call if dict
            sanitized[key] = [
                sanitize_log(item) if isinstance(item, dict) else item for item in value
            ]

        else:
            sanitized[key] = value

    return sanitized


def sanitize_headers(headers):
    SENSITIVE = {"authorization", "x-api-key"}

    return {
        k: ("***REDACTED***" if k.lower() in SENSITIVE else v)
        for k, v in headers.items()
    }


def store_prediction(prediction: float):

    stored = {"prediction": prediction}

    print("STORED:", stored)
    return stored


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())  # ID for the request

    body_bytes = await request.body()  # Do not continue until request is derived
    checksum = hashlib.sha256(body_bytes).hexdigest()  # Scramble it into int, then hd

    sanitized_body = {}
    if body_bytes:
        try:  # Remove any sensitive keys
            sanitized_body = sanitize_log(json.loads(body_bytes))
        except (json.JSONDecodeError, TypeError):
            sanitized_body = {"info": "Non-JSON or empty body"}

    # Header Sanitization
    sanitized_headers = sanitize_headers(dict(request.headers))

    async def receive():
        # Tells Flask its a request body
        return {"type": "http.request", "body": body_bytes}

    # Swap out the real request callable with mine (body_bytes)
    request._receive = receive

    start_time = time.time()

    response = await call_next(request)

    latency_seconds = time.time() - start_time  # Times the request
    latency_ms = latency_seconds * 1000

    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(latency_seconds)

    # Logs for each request
    # Removed checksum log for now
    logger.info(
        "request_log",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "latency_ms": round(latency_ms, 2),
            "input_checksum": checksum,
            "status_code": response.status_code,
            "body": sanitized_body,
            "headers": sanitized_headers,
        },
    )

    return response


@app.get("/metrics")
def metrics():
    # generate_latest() gathers every metric currently stored in app's memory
    # media_type tells Prometheus what data it's receving
    return Response(generate_latest(), media_type="text/plain")


def model_predict(x):
    return x * 2


# Inheritance transfroms the class into a Pydantic model
# Defines expected input format
class Input(BaseModel):

    # Looks for a key called 'value'
    # Type checks it. Accepts, corrects or rejects it.
    value: float = Field(
        description="Numeric field for prediction",
        examples=[10.5],
        allow_inf_nan=False,  # Stops NaN and returns 422
    )

    # Passed here once it passes the beginning checks, for further validation
    @field_validator("value")
    def validate_value(cls, v: float):

        # Reject NaN and infinity
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Value must be a finite number")

        # Reject absurd values
        if abs(v) > 1e9:
            raise ValueError("Value too large to ensure safe handling")

        return v


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    if model_loaded:
        return {"status": "ready"}
    return {"status": "not ready"}


@app.post("/predict")
@limiter.limit("5/minute")  # Max 5 per minute
async def predict(
    request: Request, data: Input, api_key: str = Depends(verify_api_key)
):
    # Request needed to know who to rate limit
    # Automatically checks, parses and stores incoming request data
    # under the data variable

    result = model_predict(data.value)

    store_prediction(result)

    logger.info("prediction_made", extra={"status": "success"})

    return {"prediction": result}


print("CI run")
