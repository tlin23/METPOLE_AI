# 🛠️ Metropole.AI Codebase Polishing Plan

This document provides a detailed, iterative blueprint for polishing the codebase without adding new capabilities. It prioritizes clarity, consistency, refactoring, and developer experience to make the project cleaner, easier to maintain, and more accessible to junior developers.

---

## 📌 Phase 1: High-Level Objectives

1. **Clean Up Unused Code**
2. **Consolidate Configuration**
3. **Standardize Logging**
4. **Add Type Annotations & Docstrings**
5. **Stitch Together a Single Pipeline Script**
6. **Add Developer Experience Tools (Makefile, Pre-commit)**
7. **Write Contributing Guide**

---

## 🔁 Phase 2: Iterative Work Breakdown

### ✅ Step 1: Remove Dead Code

- [ ] Delete `example_usage.py`, `example_usage_corpus.py` from `backend/crawler/`
- [ ] Confirm they're unused by grepping for imports/references

### ✅ Step 2: Audit & Consolidate FastAPI Routes

- [ ] Inventory `/crawl`, `/embed`, `/ask`, `/feedback`, etc.
- [ ] Remove unused ones after confirming with `grep` or frontend usage
- [ ] Clean up unused models and imports

### ✅ Step 3: Create `config.py`

- [ ] Move all `os.getenv(...)` into `backend/config.py`
- [ ] Replace usages across backend (crawler, embedder, routes)

### ✅ Step 4: Standardize Logging

- [ ] Create `backend/logging_config.py`
- [ ] Replace `print(...)` and `logging.basicConfig(...)` with shared logger
- [ ] Verify logging works consistently across scripts

### ✅ Step 5: Type Hinting & Docstrings

- [ ] Add type hints to `crawl.py`, `ask.py`, `embed.py`, `helpers.py`
- [ ] Use Google-style docstrings to clarify purpose and parameters
- [ ] Run `mypy` and `ruff check` to catch issues

### ✅ Step 6: Add `run_pipeline.py`

- [ ] Crawl → Extract → Tag → Embed pipeline
- [ ] Clean progress logs and I/O
- [ ] Use `config.py` + `logging_config.py`

### ✅ Step 7: Add `Makefile`

- [ ] Define tasks: `run`, `test`, `lint`, `format`, `embed`, `crawl`, `serve`
- [ ] Test each command works cleanly

### ✅ Step 8: Add Pre-commit Hooks

- [ ] Create `.pre-commit-config.yaml` (Black, Ruff, whitespace checks)
- [ ] Run `pre-commit install`
- [ ] Run `pre-commit run --all-files`

### ✅ Step 9: Add `CONTRIBUTING.md`

- [ ] Install steps
- [ ] Dev commands (`make`)
- [ ] Pre-commit setup
- [ ] Best practices summary

---

## 🔨 Final Iteration: Chunked LLM Prompts

Each of the steps above can be implemented via LLM prompts. Here's how you would break it into fine-grained prompts for a codegen model:

### ✳️ Prompt Series for Step 3 (`config.py`)

```text
1. Create a new file `backend/config.py` that centralizes the following env vars... (list them).
2. Refactor `routes.py` to import from `config.py` instead of using `os.getenv` inline.
3. Repeat for `embed_corpus.py` and `crawl.py`.
4. Add type annotations to all values in `config.py`.
```

### ✳️ Prompt Series for Step 4 (Logging)

```text
1. Create `logging_config.py` that sets up a logger called `metropole_ai`...
2. Replace print() statements in `embed_corpus.py` with `logger.info` or `logger.error`.
3. Repeat for `crawl.py`, `routes.py`, and `add_metadata_and_tags.py`.
4. Confirm that duplicate log configs are removed.
```

### ✳️ Prompt Series for Type Hinting

```text
1. Add type hints to all public methods in `backend/retriever/ask.py`.
2. Add Google-style docstrings to each function.
3. Run `mypy` and fix any errors.
```

Each task is scoped to a file or small surface area. All of them build toward a maintainable and production-quality codebase.

---

## ✅ Deliverables Recap

- `run_pipeline.py`: Full end-to-end orchestration
- `config.py`: Env var centralization
- `logging_config.py`: Unified logger
- `Makefile`: Developer CLI
- `.pre-commit-config.yaml`: Enforced style
- `CONTRIBUTING.md`: Onboarding guide

You now have a clean, testable, documented, and maintainable codebase ready for internal or open-source collaboration.
