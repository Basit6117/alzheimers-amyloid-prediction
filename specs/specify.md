# Specification: Explainable AI Dashboard for Preclinical Alzheimer's Detection

## 1. Purpose
A single-page dashboard with two independent tools: (left) a diagnostic tool that predicts preclinical Alzheimer's risk from blood biomarkers; (right) an educational chatbot that answers general questions about preclinical Alzheimer's from medical literature.

## 2. Users
Clinicians, researchers and students evaluating the FYP. No accounts.

## 3. User stories
| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US1 | user | type biomarker values and click Predict | I get a risk assessment |
| US2 | user | see a colour-coded banner with category and probability | I understand it at a glance |
| US3 | user | see which inputs influenced the result most | the model is explainable |
| US4 | user | ask open-ended questions about preclinical Alzheimer's | I learn the topic |
| US5 | user | see which document and page each answer came from | I can verify it |

## 4. Decoupling rule (critical)
The two panels are separate features. Rules:
- `/api/chat` accepts only `{message, history}`. It has no field for biomarker values or predictions.
- `/api/predict` never calls the RAG service. The RAG service never imports the model.
- Front-end JS keeps two independent handlers; the chat handler never reads the form or the banner.
- Test: change the form and the prediction; the chatbot's request payload stays identical.

## 5. Functional requirements
**Left panel: Diagnostic tool**
- FR1 Numeric inputs collect only direct values in this order: `pT217_F`, `AB42_AB40_F`, `GFAP_Q`, `APOE4`, `AGE`, `SEX`. The backend derives `GFAP_to_AB_ratio = GFAP_Q / (AB42_AB40_F + 1e-6)` and `pT217_to_AB_ratio = pT217_F / (AB42_AB40_F + 1e-6)`, then builds model input in the saved-model order. Units and clinically valid ranges are pending the training-data dictionary and must not be invented; until supplied, the UI must not claim them. Invalid input shows an inline message.
- FR2 "Predict" button calls `POST /api/predict`. The backend loads the `.joblib` model once at startup, runs it and returns the result.
- FR3 Response: `{probability, category, top_factors: [{feature, contribution}], model_version}`.
- FR4 UI shows a risk banner: Low (green), Moderate (amber), Elevated (orange), each with text label, percentage and one-sentence meaning. It displays the class-1 (Amyloid Positive) probability. The Amyloid Positive/Negative label comes from the model's native `predict()` decision, never from a probability cutoff. Presentation-category thresholds live in `config.py`.
- FR5 Top-factor bars under the banner (explainability; from SHAP or the model's feature contributions).
- FR6 Disclaimer: "Screening aid, not a diagnosis."
- FR7 "Reset" clears the form and banner.

**Right panel: Educational chatbot**
- FR8 Free-text chat box with message history for the current session (kept in the browser only).
- FR9 `POST /api/chat` embeds the question with local `all-MiniLM-L6-v2`, retrieves top-4 chunks from `sqlite-vec` via LangChain, and asks Google Gemini to generate an answer constrained to those chunks. If those chunks do not answer a general educational question, Gemini may instead give a general educational answer from the question alone. That answer must start with `General Gemini information (not from the loaded literature):` and has no source chips. Gemini never receives prediction or form data. Its key is read only from `GEMINI_API_KEY`.
- FR10 Each answer lists source chips (document + page).
- FR11 If no chunk meets the similarity threshold, give the clearly labelled general Gemini educational answer from FR9. If Gemini is unavailable, return its unavailable error instead.
- FR12 Requests for personal diagnosis or interpretation of someone's numbers get a fixed reply pointing to the diagnostic tool and a clinician.
- FR13 A few suggested starter questions (e.g. "What is preclinical Alzheimer's?").
- FR14 Footer: "Educational information, not medical advice."

**Corpus ingestion**
- FR15 `scripts/ingest.py` reads PDFs from `data/pdfs/`, splits them (about 500 tokens, 50 overlap), embeds them and writes them to `data/app.db`. It can be re-run without duplicating chunks.

## 6. Non-functional requirements
- Prediction < 1 s; chat first response < 5 s.
- Works on current Chrome/Edge/Firefox; below 900 px the panels stack (diagnostic first).
- Runs offline except for the Google Gemini answer-generation call.
- Error states: model file missing, invalid input, empty database, LLM unavailable.

## 7. Out of scope
User accounts, patient storage, history, PDF export, patient-aware chatbot, retraining UI, Docker, any JS framework.

## 8. Acceptance criteria
- Given valid inputs, Predict updates the banner and factors without a page reload.
- Given an unrelated general Alzheimer's question, the chatbot returns the clearly labelled general Gemini answer and no sources.
- The `/api/chat` payload contains no biomarker or prediction fields (automated test).
- Deleting `data/app.db` and running `ingest.py` restores chatbot behaviour.
