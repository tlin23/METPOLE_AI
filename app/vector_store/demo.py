"""
Demo script for using the Chroma vector store.
"""

import sys
from pathlib import Path
import uuid

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.vector_store.init_chroma import init_chroma_db
from app.embedder.embed import Embedder
from app.retriever.ask import Retriever


def demo_vector_store():
    """
    Demonstrate the use of the Chroma vector store.
    """
    print("Initializing Chroma vector store...")

    # Initialize the Chroma DB
    init_chroma_db()

    # Create an embedder
    embedder = Embedder()

    # Create a retriever
    retriever = Retriever()

    # Sample documents
    documents = [
        "Metropole Ballard is a community-focused coworking space in Seattle.",
        "The Metropole building was constructed in 1923 and has a rich history.",
        "Coworking spaces provide flexible work environments for professionals.",
        "Seattle is known for its coffee culture and tech industry.",
        "Ballard is a neighborhood in Seattle with Scandinavian heritage.",
    ]

    # Embed the documents
    print("\nEmbedding sample documents...")
    doc_ids = []
    for doc in documents:
        doc_id = str(uuid.uuid4())
        embedder.embed_text(doc, doc_id)
        doc_ids.append(doc_id)
        print(f"Embedded document with ID: {doc_id}")

    # Query the vector store
    print("\nQuerying the vector store...")
    queries = [
        "Tell me about Metropole",
        "What is coworking?",
        "Information about Seattle",
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = retriever.query(query, n_results=2)

        # Print the results
        if results and "documents" in results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                print(f"  Result {i+1}: {doc}")
        else:
            print("  No results found")

    # Get a specific document
    print("\nRetrieving a specific document...")
    if doc_ids:
        doc_id = doc_ids[0]
        result = retriever.get_document(doc_id)
        if result and "documents" in result and result["documents"]:
            print(f"Document with ID {doc_id}: {result['documents'][0]}")
        else:
            print(f"Document with ID {doc_id} not found")

    print("\nDemo completed successfully!")


if __name__ == "__main__":
    demo_vector_store()
