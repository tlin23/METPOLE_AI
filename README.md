# METPOLE_AI

A project for crawling, processing, and retrieving content from the Metropole Ballard website.

## 📋 Components

- **Crawler**: Fetches and processes web content
- **Chunking**: Breaks content into manageable chunks
- **Embedding**: Converts text to vector embeddings
- **Retrieval**: Queries the vector store and generates answers using LLM

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

### Local Development

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

### Docker

You can also run the application using Docker:

```bash
# Build and start the containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the containers
docker-compose down
```

The API will be available at http://localhost:8000.

#### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
OPENAI_API_KEY=your-openai-api-key
SECRET_KEY=your-secret-key
```

These variables will be automatically loaded by docker-compose.

## 🧪 Testing

The project includes a comprehensive test suite covering all components:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
./run_tests.py

# Run with coverage report
./run_tests.py -c

# Run specific test categories
./run_tests.py -m unit
./run_tests.py -m integration
./run_tests.py -m crawler
./run_tests.py -m embedding
./run_tests.py -m retrieval
./run_tests.py -m edge_case

# Run tests with verbose output
./run_tests.py -v
```

For more details on the test suite, see [tests/README.md](tests/README.md).
