# Architecture and Technical Plan

## Stack
| Layer | Choice |
|-------|--------|
| Frontend | `index.html` + `styles.css`, plus ~50 lines of vanilla JS for the two `fetch` calls |
| Backend | FastAPI (Python), serves the static files and the API |
| ML | Pre-trained model, `models/model.joblib`, loaded with `joblib.load` at startup |
| Database + vectors | SQLite file `data/app.db` with the `sqlite-vec` extension |
| RAG | LangChain (`SQLiteVec` vector store from `langchain_community`, `HuggingFaceEmbeddings("all-MiniLM-L6-v2")`) |
| LLM for answers | Google Gemini (`gemini-3.5-flash-lite`, with `gemini-3.7-flash` fallback); key supplied through `GEMINI_API_KEY` |

## Diagram
```
Browser (index.html)
 +-- Left panel --POST /api/predict--> FastAPI --> model.joblib
 +-- Right panel --POST /api/chat----> FastAPI --> LangChain --> sqlite-vec (data/app.db) --> Google Gemini
 (no connection between the two paths)
```

## API
- `GET /` returns the page.
- `GET /api/health` returns model and DB status.
- `POST /api/predict`: body is the feature dict; returns `{probability, category, top_factors, model_version}`.
- `POST /api/chat`: body is `{message, history[]}`; retrieves local PDF context and sends only that context, the message, and permitted browser-only history to Gemini; returns `{answer, sources: [{doc, page}]}`.

## Database (single file)
- `chunks(id, doc_name, page, text)`
- `vec_chunks` virtual table (`vec0`), `embedding float[384]`, linked by chunk id
- Created by `ingest.py`; no migrations needed.

## Folder layout
```
/app        main.py  predict.py  rag.py  schemas.py  config.py
/static     index.html  styles.css  app.js
/models     model.joblib
/data       pdfs/  app.db
/scripts    ingest.py
/tests
/spec       constitution.md specify.md architecture.md design-guidelines.md tasks.md
```

## Known risks
- `sqlite-vec` needs a Python `sqlite3` build that allows extension loading (the default macOS Python often does not); use a python.org or conda build.
- Make sure the `scikit-learn` version used for training matches the one installed, or the `.joblib` may not load.
- Keep the literature-backed prompt strict. A separate, clearly labelled Gemini-only educational fallback may answer general Alzheimer's questions when the retrieved context does not cover them.
