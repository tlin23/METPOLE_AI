"""Retriever module for querying and retrieving information from embeddings."""

from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from pathlib import Path
from openai import OpenAI
from typing import Dict, List, Any

from backend.api.models import ChunkResult
from backend.configer.config import (
    OPENAI_API_KEY,
    WEB_COLLECTION_NAME,
    OFFLINE_COLLECTION_NAME,
)
from backend.configer.logging_config import get_logger

# Get logger for this module
logger = get_logger("retriever.ask")

# Load environment variables
load_dotenv()

# Initialize OpenAI client
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Initialize OpenAI client with proper error handling for proxy settings
client = OpenAI(api_key=OPENAI_API_KEY)


class Retriever:
    """Class for retrieving information from embeddings and generating answers using OpenAI.

    This class provides methods to query a vector database for relevant documents
    and generate answers to user questions using OpenAI's language models.
    """

    def __init__(self, chroma_path: str = None) -> None:
        """Initialize the retriever with ChromaDB connection.

        Sets up connection to the ChromaDB vector database and initializes
        both web and offline document collections. Allows overriding path for testing.
        """
        # Allow override from parameter or fallback to env
        self.chroma_db_path = chroma_path
        # Create the directory if it doesn't exist
        Path(self.chroma_db_path).mkdir(parents=True, exist_ok=True)

        # Initialize the persistent client
        self.chroma_client = chromadb.PersistentClient(
            path=self.chroma_db_path, settings=Settings(anonymized_telemetry=False)
        )

        # Get both collections
        self.web_collection = self.chroma_client.get_or_create_collection(
            WEB_COLLECTION_NAME
        )
        self.offline_collection = self.chroma_client.get_or_create_collection(
            OFFLINE_COLLECTION_NAME
        )

        logger.info(
            f"Collections loaded: {self.web_collection.count()} web documents, "
            f"{self.offline_collection.count()} offline documents found"
        )

    def query(self, query_text: str, n_results: int) -> chromadb.QueryResult:
        """Query both web and offline collections for relevant documents.

        Args:
            query_text: The query text to search for.
            n_results: Number of results to return per collection. Defaults to 5.

        Returns:
            Dictionary containing combined query results with documents, metadatas, and distances.
        """
        # Query both collections
        web_results = self.web_collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        offline_results = self.offline_collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        # Combine results, prioritizing by distance
        combined_results = self._combine_results(
            web_results, offline_results, n_results
        )

        return combined_results

    def _combine_results(
        self,
        web_results: chromadb.QueryResult,
        offline_results: chromadb.QueryResult,
        n_results: int,
    ) -> chromadb.QueryResult:
        """Combine and sort results from both collections based on distance.

        Args:
            web_results: Results from web collection
            offline_results: Results from offline collection
            n_results: Number of results to return

        Returns:
            Combined and sorted results
        """
        # Extract results from both collections
        web_docs = web_results["documents"][0]
        web_metadatas = web_results["metadatas"][0]
        web_distances = web_results["distances"][0]

        offline_docs = offline_results["documents"][0]
        offline_metadatas = offline_results["metadatas"][0]
        offline_distances = offline_results["distances"][0]

        # Combine all results with their distances
        all_results = []
        for i in range(len(web_docs)):
            all_results.append((web_docs[i], web_metadatas[i], web_distances[i], "web"))
        for i in range(len(offline_docs)):
            all_results.append(
                (offline_docs[i], offline_metadatas[i], offline_distances[i], "offline")
            )

        # Sort by distance
        all_results.sort(key=lambda x: x[2])

        # Take top n_results
        top_results = all_results[:n_results]

        # Reconstruct the result format
        return {
            "documents": [[r[0] for r in top_results]],
            "metadatas": [[r[1] for r in top_results]],
            "distances": [[r[2] for r in top_results]],
            "source_types": [[r[3] for r in top_results]],
        }

    def generate_answer(
        self, question: str, chunks: List[ChunkResult], model: str = "gpt-3.5-turbo"
    ) -> Dict[str, Any]:
        """Generate an answer to a question using OpenAI's GPT model and retrieved chunks.

        Uses the provided text chunks to generate a contextually relevant answer
        to the user's question. Adds appropriate disclaimers based on the nature
        of the answer.

        Args:
            question: The user's question.
            chunks: List of text chunks retrieved from the vector store.
            model: The OpenAI model to use. Defaults to "gpt-3.5-turbo".

        Returns:
            A dictionary containing:
                - answer: The generated answer text
                - is_general_knowledge: Flag indicating if answer is based on general knowledge
                - contains_diy_advice: Flag indicating if answer contains DIY advice
                - source_info: Information about the sources used
        """
        # Construct the prompt with the retrieved chunks
        prompt = self._construct_prompt(question, chunks)

        # Call the OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on the provided building content.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # Lower temperature for more factual responses
            max_tokens=1000,  # Limit response length
        )

        answer_text = response.choices[0].message.content

        # Process the answer to detect if it's based on building data or general knowledge
        # and if it contains DIY advice
        answer_lower = answer_text.lower() if answer_text else ""
        is_general_knowledge = (
            "general knowledge" in answer_lower
            or "i don't have specific information" in answer_lower
        )
        contains_diy_advice = any(
            phrase in answer_lower
            for phrase in [
                "diy",
                "do it yourself",
                "you can try",
                "you could try",
                "steps to",
                "how to",
            ]
        )

        # Prepare source information
        source_info = self._prepare_source_info(chunks)

        return {
            "answer": answer_text,
            "is_general_knowledge": is_general_knowledge,
            "contains_diy_advice": contains_diy_advice,
            "source_info": source_info,
            "prompt": prompt,
        }

    def _prepare_source_info(self, chunks: List[ChunkResult]) -> str:
        """Prepare formatted source information from chunks.

        Extracts metadata from chunks and formats it into a readable source citation.

        Args:
            chunks: List of text chunks retrieved from the vector store.

        Returns:
            Formatted string containing source information.
        """
        sources = []
        for i, chunk in enumerate(chunks):
            # Extract metadata
            metadata = (
                chunk.metadata if hasattr(chunk, "metadata") and chunk.metadata else {}
            )
            chunk_id = str(metadata.get("chunk_id", f"unknown-{i}"))
            document_title = str(
                metadata.get("document_title")
                or metadata.get("document_name")
                or "Unknown Page"
            )
            section = metadata.get("section", "")

            # Format source info using f-strings to avoid None concatenation
            if section and isinstance(section, str):
                source_info = f"Chunk {chunk_id} ({section}) from {document_title}"
            else:
                source_info = f"Chunk {chunk_id} from {document_title}"

            sources.append(source_info)

        return "; ".join(sources)

    def _construct_prompt(self, question: str, chunks: List[Any]) -> str:
        """Construct a prompt for the OpenAI model that includes the question and retrieved chunks.

        Creates a detailed prompt that includes the user's question, relevant content
        chunks with their metadata, and instructions for the model on how to formulate
        the answer.

        Args:
            question: The user's question.
            chunks: List of text chunks retrieved from the vector store.

        Returns:
            The constructed prompt string ready to be sent to the OpenAI API.
        """
        # Start with the question
        prompt = f"Question: {question}\n\n"

        prompt += """Based on the context provided below, please answer the question. Use only information that you deem relevant. Do not reference the specific chunks you used to formulate your answer. \n\n"""

        # Add the building content from the retrieved chunks
        prompt += "Building Content:\n"
        for i, chunk in enumerate(chunks):
            # Extract text and metadata
            text = str(chunk.text if hasattr(chunk, "text") else chunk)
            metadata = (
                chunk.metadata if hasattr(chunk, "metadata") and chunk.metadata else {}
            )

            # Add source information if available
            document_title = str(
                metadata.get("document_title")
                or metadata.get("document_name")
                or "Unknown Page"
            )
            section = metadata.get("section", "")

            # Build source info parts
            source_parts = []
            if section and isinstance(section, str):
                source_parts.append(f"Section: {section}")
            if document_title:
                source_parts.append(f"Page: {document_title}")

            # Join parts with commas
            source_info = f" ({', '.join(source_parts)})"

            prompt += f"Chunk {i+1}{source_info}:\n{text}\n\n"

        return prompt


if __name__ == "__main__":
    # Example usage
    retriever = Retriever()
    results = retriever.query("sample query")
    logger.info(f"Query results: {results}")
