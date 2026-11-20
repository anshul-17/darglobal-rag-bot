# DarGlobal & Wasalt Real Estate RAG Chatbot

An end-to-end **Retrieval-Augmented Generation (RAG)** chatbot built to answer questions about **DarGlobal** luxury developments and **Wasalt** property listings across Saudi Arabia, Oman, the UAE, Qatar, and Spain.

- **Live Demo (Hugging Face Spaces):** [Launch App](https://YOUR-USERNAME-darglobal-rag-bot.hf.space)
- **Source Code:** [GitHub Repository](https://github.com/anshul-17/darglobal-rag-bot)

---

## Architecture & Workflow

1. **Data Collection & Chunking (`src/scraper.py`):**
   - Extracts public property details, project descriptions, locations, and amenities from **DarGlobal** (`darglobal.co.uk`) and **Wasalt** (`wasalt.sa`).
   - Cleans HTML boilerplate and splits text into overlapping ~800-character segments stored in `data/data.json` with source URL metadata.
2. **Vector Indexing (`app.py`):**
   - Generates 384-dimensional dense embeddings locally using `sentence-transformers` (`all-MiniLM-L6-v2`) and indexes them in an in-memory **FAISS (`IndexFlatL2`)** vector store.
3. **Grounded Generation & Citations:**
   - Retrieves the top-$k$ semantically relevant property chunks per query and passes them to **OpenRouter (`openrouter/free`)** with strict grounding instructions to prevent hallucination.
   - Displays clickable source URLs beneath each response in the **Streamlit** interface.
4. **Containerization & Cloud Deployment (`Dockerfile`):**
   - Packaged as a portable non-root Docker container (`UID 1000`, port `7860`) with the embedding model pre-cached at build time for fast cold starts on **Hugging Face Spaces**.

---

## Project Structure

```text
darglobal-rag-bot/
├── data/
│   └── data.json          # Structured & chunked real estate dataset
├── src/
│   └── scraper.py         # Data ingestion & text chunking pipeline
├── app.py                 # Streamlit UI + FAISS retrieval + OpenRouter LLM
├── Dockerfile             # Production container image (port 7860)
├── requirements.txt       # Python dependencies
├── .dockerignore          # Excludes local environment files from image
└── .gitignore             # Excludes .env, venv/, and raw HTML snapshots
