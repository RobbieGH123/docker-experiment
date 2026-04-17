from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager

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


def model_predict(x):
    return x * 2


# Inheritance transfroms the class into a Pydantic model
# Defines expected input format
class Input(BaseModel):

    # Looks for a key called 'value'
    # Type checks it. Accepts, corrects or rejects it.
    value: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    if model_loaded:
        return {"status": "ready"}
    return {"status": "not ready"}


@app.post("/predict")
def predict(data: Input):
    # Automatically checks, parses and stores incoming request data
    # under the data variable

    result = model_predict(data.value)
    return {"prediction": result}
