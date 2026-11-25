# NeuroRisk: Preclinical Alzheimer's Screening Dashboard

NeuroRisk is a local FastAPI dashboard with two independent tools:

- a blood-biomarker screening aid powered by the supplied immutable SVM model;
- an educational chatbot that retrieves from local medical PDFs and asks Gemini to answer only from that context.

The screening tool is not a diagnosis. The chatbot does not receive biomarker values, prediction results, or patient data.

## Requirements

- Python 3.13 recommended (the saved model requires `scikit-learn==1.6.1`)
- A Gemini API key for educational chat generation

## Setup

From the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create `.env` from `.env.example`, then set your real key:

```text
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.7-flash
GEMINI_TIMEOUT_SECONDS=45
```

Never commit `.env` or a real key.

## Build the local literature database

Put medical PDFs in `data/pdfs/`, then run:

```powershell
python scripts\ingest.py
```

This creates `data/app.db`. Re-running it rebuilds the same local corpus without duplicating chunks. The embedding model is `all-MiniLM-L6-v2`; its files must be available locally after the first download.

## Run

```powershell
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Verify

```powershell
python -m pytest -q
```

Health endpoint: `GET /api/health`.

## Privacy and separation

- `POST /api/predict` accepts only the six raw screening fields and performs its two required ratio calculations internally.
- `POST /api/chat` accepts only `{message, history}`.
- Chat history stays in the browser for the current session. Prediction data is never sent to the chatbot, vector store, Gemini, or chat history.
