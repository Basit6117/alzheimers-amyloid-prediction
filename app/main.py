"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import DATABASE_PATH, MODEL_VERSION
from app.predict import load_model, predict_probability, risk_category, top_factors
from app.rag import RagUnavailableError, answer_question
from app.schemas import ChatRequest, ChatResponse, PredictionInput, PredictionResponse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_ROOT / "static"


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Load the immutable prediction artifact once for this API process."""
    application.state.model = load_model()
    yield


app = FastAPI(title="Preclinical Alzheimer's Dashboard", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the dashboard's static entry page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Return the API process status and model initialization state."""
    database_status = "ready" if DATABASE_PATH.exists() else "not initialized"
    return {"status": "ok", "model": "loaded", "database": database_status}


@app.post("/api/predict", response_model=PredictionResponse)
def predict(payload: PredictionInput, request: Request) -> PredictionResponse:
    """Return an isolated prediction without accessing the chatbot path."""
    feature_values = payload.model_dump()
    model = request.app.state.model
    probability = predict_probability(model, feature_values)

    return PredictionResponse(
        probability=probability,
        category=risk_category(probability),
        top_factors=top_factors(model, feature_values),
        model_version=MODEL_VERSION,
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    """Answer an educational question without importing or calling prediction code."""
    try:
        answer, sources = answer_question(payload.message)
    except RagUnavailableError as error:
        return ChatResponse(answer=str(error), sources=[])
    return ChatResponse(answer=answer, sources=sources)
