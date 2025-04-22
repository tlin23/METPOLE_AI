## 🧱 Metropole.AI – Step-by-Step Build Plan with LLM Prompts

This blueprint breaks down the project into a series of safe, iterative chunks. Each chunk builds on the last, enabling rapid development and testing. Each chunk also includes a test-driven prompt you can use with a code-generation LLM.

---

### 🔨 PHASE 1: Project Scaffolding & Setup

**Chunk 1: Initialize Local Dev Environment**
- Create a Python virtual environment
- Install required packages: `requests`, `beautifulsoup4`, `chromadb`, `fastapi`, `keybert`, `uvicorn`, `openai`, `python-dotenv`
- Create `.env` for secrets (e.g. OpenAI key)
- Verify all dependencies install cleanly

```prompt
You are a Python developer. Set up a new virtual environment and install the following packages: requests, beautifulsoup4, chromadb, fastapi, keybert, uvicorn, openai, python-dotenv. Generate a .env file with placeholder secrets. Output a README with setup instructions and verify the environment works.
```

**Chunk 2: Project Directory Structure**
Create the following scaffold:
```
metropole_ai/
├── app/
│   ├── api/
│   ├── crawler/
│   ├── embedder/
│   ├── retriever/
│   └── utils/
├── data/
├── .env
├── main.py
└── requirements.txt
```

```prompt
Create the directory structure above. Include dummy __init__.py files where appropriate and create placeholder files (e.g., crawl.py, embed.py, ask.py). Add a working FastAPI app that returns "hello world" on root.
```

---

### 🕸️ PHASE 2: Crawling & Corpus Generation

**Chunk 3: Crawl Internal Pages**

```prompt
Create a crawler using requests and BeautifulSoup that starts from https://www.metropoleballard.com/home and recursively collects all internal links. Store the HTML content of each visited page in memory or a file.
```

**Chunk 4: Extract and Chunk Content**

```prompt
From each HTML page, extract the page title, main section headers (h2, h3), and content in paragraphs and list items. Group chunks by section and return structured Python objects. Each chunk should have: content, content_html, and section header.
```

**Chunk 5: Add Metadata + Auto Tagging**

```prompt
For each chunk, assign a page_id, section header, and unique chunk_id. Then use KeyBERT + MiniLM to extract 3-5 tags per chunk. Store everything in a structured JSON file named metropole_corpus.json.
```

**Chunk 6: Validate Output**

```prompt
Write a test suite to validate metropole_corpus.json. Check required fields exist, chunk IDs are unique, and tags are generated. Use JSON schema or custom assertions.
```

---

### 🧠 PHASE 3: Embedding + Indexing

**Chunk 7: Setup Chroma Index**

```prompt
Create a Chroma persistent vector store. Add a script that initializes a new index and connects it to your FastAPI backend. Use a local file path (e.g., ./data/index).
```

**Chunk 8: Embed Chunks**

```prompt
Write a function that loads metropole_corpus.json and embeds each chunk using all-MiniLM-L6-v2. Store text and metadata in Chroma. Include logging to show how many embeddings were created.
```

**Chunk 9: Test Indexing Pipeline**

```prompt
Write tests to ensure that embeddings are added to Chroma correctly. Retrieve a known chunk and verify it matches the expected metadata. Check for embedding count, ID presence, and similarity rank.
```

---

### 💬 PHASE 4: Chatbot + Query Engine

**Chunk 10: Basic Retrieval API**

```prompt
Create a /ask FastAPI endpoint that accepts a question as input and returns the top-k most relevant chunks from Chroma. Use cosine similarity. Include metadata in the response.
```

**Chunk 11: Integrate OpenAI API**

```prompt
Modify /ask to pass the retrieved chunks + question into OpenAI's gpt-3.5-turbo. Construct a prompt that includes the building content and ask the model to answer based on it. Return the model response.
```

**Chunk 12: Add Disclaimers & Source Tracing**

```prompt
Extend the /ask response to include the disclaimer if applicable, and show chunk IDs + page source. Detect if the answer is based on building data or general knowledge. Append source trace to the message.
```

---

### 🗂️ PHASE 5: Admin Tools + Feedback

**Chunk 13: Crawler API**

```prompt
Create a /crawl endpoint that runs the crawler and overwrites metropole_corpus.json. Return summary of how many pages and chunks were parsed.
```

**Chunk 14: Embedding API**

```prompt
Create a /embed endpoint that re-embeds the contents of metropole_corpus.json and updates the Chroma index.
```

**Chunk 15: Feedback Logging**

```prompt
Add a /feedback endpoint that logs question, response, timestamp, and chunk IDs to a local JSONL file. Include a helper function for saving logs and rotating log files.
```

---

### 🎛️ PHASE 6: Frontend Hookup & Polish

**Chunk 16: Connect UI to Backend**

```prompt
Modify the existing frontend to call /ask with the user's question and render the response. Include a welcome message on load and reset button to clear chat.
```

**Chunk 17: Source Display**

```prompt
Update the frontend to optionally show the source chunk ID and section title as a tooltip, collapsible panel, or footer below each bot response.
```

---

## 🔁 Final Iteration: Polish, Test, Optimize

**Chunk 18: Unit + Integration Testing**

```prompt
Write a full test suite covering crawling, chunking, embedding, retrieval, and LLM output. Use pytest. Include edge cases like missing tags, blank chunks, or missing API keys.
```

**Chunk 19: Dockerize Project**

```prompt
Write a Dockerfile that builds the FastAPI app, installs dependencies, and mounts a volume for the Chroma index. Add a docker-compose file with services for app and local volume.
```

**Chunk 20: Deploy MVP**

```prompt
Deploy the frontend to Render as a static site. Deploy the backend to Render or Fly.io with Docker. Connect both. Test end-to-end flow including source display and feedback logging.
```
