# Tasks (in order; one task at a time; tick when its check passes)

## Phase 0: Setup
- [ ] T01 Project folders per architecture.md, virtualenv, `requirements.txt` (fastapi, uvicorn, joblib, scikit-learn, langchain, langchain-community, sentence-transformers, sqlite-vec, pypdf, pytest)
- [x] T02 FastAPI app serving `/static` and `GET /api/health`

## Phase 1: Prediction backend
- [x] T03 Pydantic schema with ranges and units for each feature
- [x] T04 Load `model.joblib` at startup; `predict.py` returns probability. *Check: known sample gives the same output as in your notebook*
- [x] T05 Category thresholds in `config.py`; top-factor computation
- [x] T06 `POST /api/predict` + tests (valid, out-of-range, missing field)

## Phase 2: Static UI, left panel
- [x] T07 `styles.css` with tokens, cards, dual-panel grid, responsive stacking
- [x] T08 Biomarker form with unit hints and inline validation
- [x] T09 Result banner (3 colour states + empty state) and factor bars
- [x] T10 `app.js` predict handler with loading, error and reset. *Check: FR1-FR7*

## Phase 3: RAG backend
- [x] T11 Put the medical PDFs in `data/pdfs/`
- [x] T12 `ingest.py`: load PDFs, split, embed, write to SQLite with sqlite-vec; idempotent
- [x] T13 `rag.py`: retriever (top-4, similarity threshold) and strict-context prompt
- [x] T14 Configure the LLM and generate the answer with sources
- [x] T15 "Couldn't find" and "no personal diagnosis" replies
- [x] T16 `POST /api/chat` + tests, including the decoupling test (no biomarker or prediction fields in the payload)

## Phase 4: Chat UI, right panel
- [x] T17 Chat layout, welcome message, starter chips
- [x] T18 `app.js` chat handler (independent of the form), typing indicator, source chips. *Check: FR8-FR14*

## Phase 5: Finish
- [x] T19 Responsive and accessibility pass
- [ ] T20 End-to-end run from a clean clone (delete `app.db`, ingest, start server); README
