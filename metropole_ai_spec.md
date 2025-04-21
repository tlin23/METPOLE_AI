# 📘 Metropole.AI – Developer Specification (v1)

## 🧭 Overview
Metropole.AI is a web-based AI chatbot that answers practical, building-specific questions for residents of the Metropole Ballard apartment complex. The goal is to preserve and surface collective knowledge in a conversational, transparent, and user-friendly format.

---

## 🔍 Data Collection

### Source
- Website: https://www.metropoleballard.com/home
- Internal pages only (no external links, PDFs, calendar invites, etc.)

### Crawler Logic
- Use Python + BeautifulSoup + requests
- Extract all internal links and iterate over them
- For each page:
  - Get `page_id`, `page_title`, `section_header`, `subsection_header`
  - Chunk content by `<p>` and `<li>`
  - Include clean text and raw HTML in each chunk
  - Assign a unique `chunk_id`
  - Auto-generate `tags` using KeyBERT (MiniLM)

### Output
- JSON format: `metropole_corpus.json`

```json
{
  "page_id": "rules-and-policies",
  "page_title": "Rules and Policies",
  "source_url": "https://...",
  "section_header": "Pets",
  "last_updated": "2025-04-20T00:00:00Z",
  "tags": ["pets", "animals", "policy"],
  "chunks": [
    {
      "chunk_id": "rules-pets-001",
      "content": "Cats are allowed.",
      "content_html": "<p>Cats are allowed.</p>"
    },
    {
      "chunk_id": "rules-pets-002",
      "content": "Dogs are not allowed.",
      "content_html": "<p>Dogs are not allowed.</p>"
    }
  ]
}
```

---

## 🧠 Knowledge Retrieval (RAG)

### Embedding Model
- `sentence-transformers/all-MiniLM-L6-v2`

### Vector Store
- `Chroma` (local, file-backed)

### Retrieval
- Similarity-based semantic search using embedded question vs chunk vectors
- Include top-k (e.g., 3–5) most relevant chunks in final prompt

### Auto-Tagging
- Use `KeyBERT` + MiniLM to extract 3–5 semantic tags per chunk

---

## 💬 Chatbot Behavior

### LLM
- **Phase 1**: OpenAI `gpt-3.5-turbo`
- **Phase 2 (optional)**: Swap to local `Mistral-7B-Instruct` via Ollama, Hugging Face, or LM Studio

### Prompting
- Inject retrieved chunks into prompt along with user question
- Emphasize factual, building-specific answers
- Style: friendly, conversational, utility-focused

### Disclaimers
If the bot gives DIY advice:
> "This is based on past residents' experience and should not be considered professional advice. When in doubt, contact the board or a licensed professional."

If info is not from building data:
> "This answer is based on general knowledge, not Metropole-specific content."

### Source Tracing
- Responses must cite chunk ID, section, and page source

---

## 🖥️ Frontend

### Chat UI
- Keep current web-based UI
- Add:
  - Welcome message
  - "Start Over" button
  - Source info display (optional dropdown or link)

### Backend
- FastAPI app with endpoints:
  - `/crawl`: run crawler and output JSON
  - `/embed`: load and index JSON to Chroma
  - `/ask`: RAG query + OpenAI response + source trace
  - `/feedback`: log question/answer/session

---

## 📊 Feedback Loop

### Storage
- Log:
  - User question
  - Bot response
  - Matched chunk IDs
  - Timestamp
  - Session metadata (if needed)

### Purpose
- QA & debugging
- Improve chunking or prompts
- Build dataset for optional fine-tuning later

---

## 🚀 Deployment Plan

### Dev Environment
- Local-first: run on VS Code or Jupyter
- Test crawl, embedding, querying

### MVP Hosting
- Frontend: Render (free tier)
- Backend: Optional Docker container on Fly.io or Railway

### Future-proof
- Migrate to local LLM for privacy/cost
- Expand data (minutes, new rules, messages)
- Add user feedback rating