# Python Virtual Environment Starter

## 🔧 Setup

1. Clone the repo and navigate to the folder:

    ```bash
    git clone https://github.com/your-repo-name.git
    cd your-repo-name
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
    CHROMA_DB_PATH=./chroma_db
    SECRET_KEY=your-secret-key
    ```

## ▶️ Run the app

Start the FastAPI server:

```bash
uvicorn main:app --reload