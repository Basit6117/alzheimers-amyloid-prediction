# Constitution (final, unchangeable decisions)

1. **Stack is fixed:** raw HTML + CSS frontend, FastAPI backend, SQLite + `sqlite-vec` (single local `.db` file), LangChain for RAG with local `all-MiniLM-L6-v2` embeddings, ML model loaded from a `.joblib` file. No Docker or extra frameworks. Google Gemini is the sole permitted external service, and only for chatbot answer generation from retrieved literature. Its API key must be supplied through `GEMINI_API_KEY`, never source code, the database, logs, or Git.
2. **Prediction and chatbot are decoupled.** No prediction output, input value or patient data is ever sent to the chatbot, Gemini, its prompt, its retrieval query or its history. They share only the page, never data or code paths.
3. **Chatbot is educational only.** It answers from the embedded medical PDF corpus and cites those sources when they support the answer. When the corpus does not answer a general Alzheimer's question, it may use Gemini's general educational knowledge, but must clearly label that answer as not from the loaded source and show no source chips. It never diagnoses or interprets a user's own results.
4. **Explain the prediction.** The risk result always appears with a plain-language category and a screening-aid disclaimer.
5. **Standalone.** The whole project runs from the project directory with `uvicorn app.main:app`.
6. **Accessible.** Contrast 4.5:1, keyboard navigable, colour never the only signal of risk.
7. **Keep it simple.** Nothing outside specify.md.
