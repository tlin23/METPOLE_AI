# METPOLE_AI

A project for crawling, processing, and retrieving content from the Metropole Ballard website.

## 🔧 Setup

1. Clone the repo and navigate to the folder:

    ```bash
    git clone https://github.com/your-username/METPOLE_AI.git
    cd METPOLE_AI
    ```

2. Create and activate a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file:

    ```env
    OPENAI_API_KEY=your-openai-api-key
    CHROMA_DB_PATH=./data/index
    SECRET_KEY=your-secret-key
    ```

## 🗄️ Vector Store

The project uses Chroma as a persistent vector store for embeddings. The vector store is initialized at `./data/index` by default, but this can be changed in the `.env` file.

To initialize the vector store:

```bash
python -m app.vector_store.init_chroma
```

To run a demo of the vector store:

```bash
python -m app.vector_store.demo
```

## ▶️ Run the app

Start the FastAPI server:

```bash
uvicorn main:app --reload
