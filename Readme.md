# TransformoDocs - Intelligent Document Conversion & RAG Analysis Platform ⚡

TransformoDocs is an advanced Agentic Workflow and MLOps platform designed to convert complex, non-machine-readable documents (PDFs, Word files, Excel sheets, Images) into highly structured Data Engineering formats (JSON/XML). The platform utilizes **CrewAI** multi-agent systems and an advanced **LangChain HyDE RAG** pipeline to allow deep analytical querying against your ingested documents.

The monolithic codebase has been fully upgraded to a modern decoupled Service-Oriented Architecture (SOA) utilizing **FastAPI** for a robust Python backend, and **Next.js** for a premium React frontend user interface.

## Tech Stack Overview

- **Frontend**: Next.js, React, TailwindCSS, Lucide Icons, Axios.
- **Backend**: FastAPI, Uvicorn, Python.
- **Data Engineering / Extraction**: PyTesseract, Pandas, pdfplumber, PyPDF2.
- **LLM / Analytics Engine**: LangChain, OpenAI Embeddings, ChromaDB, CrewAI (Multi-Agent framework).
- **MLOps & Telemetry**: MLFlow, Keras, TensorFlow.

## Features

- **Document Extraction (Data Engineering)**: PyTesseract and Pandas pipelines efficiently extract data from complex files, drastically reducing token overhead while maintaining 95% original structural accuracy.
- **Advanced HyDE RAG Pipeline**: Implements Hypothetical Document Embeddings for query decomposition, ensuring the AI strictly answers from factual context without hallucination.
- **Multi-Agent System**: Utilizes CrewAI to deploy dual agents ("Senior Document Analyst" and "Data Reporting Specialist") utilizing specific Chain-of-Thought methodologies to provide precise answers.
- **MLFlow Telemetry**: Every ingestion and query acts as a telemetry trace to measure execution speed, success rates, and token efficiency for future SLM optimization.
- **Premium User Interface**: A Next.js frontend offering drag-and-drop mechanics, real-time analytics dashboards, and a seamless chat interface.

---

## Getting Started

### Prerequisites

You need `python (>= 3.9)` and `node (>= 18)` installed on your machine. You will also need an active OpenAI API key.

### 1. Setup the Python Backend (FastAPI)

1. Open a terminal in the root of the project.
2. Setup your virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Export your LLM API Key:
   ```bash
   # On Windows PowerShell
   $env:OPENAI_API_KEY="your-api-key-here"
   
   # On Mac/Linux
   export OPENAI_API_KEY="your-api-key-here"
   ```
5. Start the FastAPI Server:
   ```bash
   uvicorn backend.main:app --reload
   ```

*The backend will now serve RESTful endpoints securely on `http://127.0.0.1:8000`.*

### 2. Setup the React Frontend (Next.js)

1. Open a **second** terminal window.
2. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
3. Install the React dependencies (Axios, Lucide, etc.):
   ```bash
   npm install
   ```
4. Start the Development Server:
   ```bash
   npm run dev
   ```

*The frontend UI will now be live at `http://localhost:3000`.*

---

## Architecture Design

### Next.js UI (`frontend/src/app/page.tsx`)
A modern interface communicating over `axios` via standard HTTP REST to the Python proxy layer. Handles parsing states, MLOps telemetry readouts, and UI rendering of agent chat logs.

### Backend Handlers (`backend/`)
- `main.py`: Entry point setting up generic FastAPI scaffolding, middleware, and CORS policies specifically opening access to `localhost:3000`.
- `routes.py`: Orchestrates endpoints (`/upload`, `/document`, `/chat`) and binds them to the core AI analytical engines.

### Source Integrations (`src/`)
- `data_engineering.py`: Data loaders parsing byte streams (`.pdf`, `.docx`, image objects via Tesseract) directly into structural Python dictionaries serialization-ready for JSON/XML formats.
- `rag_pipeline.py`: The document chunker and ChromaDB indexer. Constructs the complex LangChain PromptTemplates enabling the Hypothetical retrieval technique.
- `agents.py`: Holds the definitions, backstory definitions, and execution tasks required to kick off the precise CrewAI task loop.
- `mlops.py`: Local `mlruns` database tracker ensuring analytical processing duration vs structural byte length metrics are accurately measured to prove runtime efficiencies.

---

### MLOps Integration

MLFlow records are stored locally in the `mlruns` directory. Once you process a few documents, you can view your real-time processing performance metrics over your CLI:

```bash
mlflow ui
```
*Navigate to `http://127.0.0.1:5000` to see your run history and telemetry data.*

---

## License

This project is licensed under the MIT License. Contributions and architectural tweaks for specialized models are highly encouraged!
