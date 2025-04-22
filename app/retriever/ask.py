"""Retriever module for querying and retrieving information from embeddings."""

from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from pathlib import Path
import openai
from typing import Dict, List, Any

from app.config import OPENAI_API_KEY, CHROMA_DB_PATH
from app.logging_config import get_logger

# Get logger for this module
logger = get_logger("retriever.ask")

# Load environment variables
load_dotenv()

# Initialize OpenAI client
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Initialize OpenAI client with proper error handling for proxy settings
try:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
except TypeError as e:
    if "unexpected keyword argument 'proxies'" in str(e):
        # If the error is about proxies, initialize without proxy settings
        # Create a client with default settings
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Log the issue
        logger.warning("Proxy settings were ignored when initializing OpenAI client")
    else:
        # If it's a different TypeError, re-raise it
        raise


class Retriever:
    """Class for retrieving information from embeddings and generating answers using OpenAI.
    
    This class provides methods to query a vector database for relevant documents
    and generate answers to user questions using OpenAI's language models.
    """
    
    def __init__(self) -> None:
        """Initialize the retriever with ChromaDB connection.
        
        Sets up connection to the ChromaDB vector database and initializes
        the documents collection.
        """
        # Get the path for the Chroma database
        self.chroma_db_path = CHROMA_DB_PATH
        
        # Create the directory if it doesn't exist
        Path(self.chroma_db_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize the persistent client
        self.chroma_client = chromadb.PersistentClient(
            path=self.chroma_db_path,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        # Get the collection
        self.collection = self.chroma_client.get_or_create_collection("documents")
    
    def query(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        """Query the embeddings database for relevant documents.
        
        Args:
            query_text: The query text to search for.
            n_results: Number of results to return. Defaults to 5.
            
        Returns:
            Dictionary containing query results with documents, metadatas, and distances.
        """
        # Query using cosine similarity
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        
        # Convert to a standard dictionary
        return dict(results)
    
    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """Retrieve a specific document by ID.
        
        Args:
            doc_id: Document ID to retrieve.
            
        Returns:
            Dictionary containing the document data.
        """
        result = self.collection.get(ids=[doc_id])
        # Convert to a standard dictionary
        return dict(result)
    
    def generate_answer(self, question: str, chunks: List[Any], 
                       model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
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
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided building content. If the answer cannot be found in the provided content, indicate that you're using general knowledge. If you provide DIY advice, indicate this as well."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more factual responses
            max_tokens=1000   # Limit response length
        )
        
        answer_text = response.choices[0].message.content
        
        # Process the answer to detect if it's based on building data or general knowledge
        # and if it contains DIY advice
        answer_lower = answer_text.lower() if answer_text else ""
        is_general_knowledge = "general knowledge" in answer_lower or "i don't have specific information" in answer_lower
        contains_diy_advice = any(phrase in answer_lower for phrase in ["diy", "do it yourself", "you can try", "you could try", "steps to", "how to"])
        
        # Prepare source information
        source_info = self._prepare_source_info(chunks)
        
        # Add appropriate disclaimers
        if contains_diy_advice:
            disclaimer = "\n\nDisclaimer: This is based on past residents' experience and should not be considered professional advice. When in doubt, contact the board or a licensed professional."
            answer_text += disclaimer
        
        if is_general_knowledge:
            disclaimer = "\n\nNote: This answer is based on general knowledge, not Metropole-specific content."
            answer_text += disclaimer
        
        # Add source trace
        if source_info and not is_general_knowledge and answer_text:
            answer_text += f"\n\nSource: {source_info}"
        
        return {
            "answer": answer_text,
            "is_general_knowledge": is_general_knowledge,
            "contains_diy_advice": contains_diy_advice,
            "source_info": source_info
        }
    
    def _prepare_source_info(self, chunks: List[Any]) -> str:
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
            metadata = chunk.metadata if hasattr(chunk, 'metadata') and chunk.metadata else {}
            chunk_id = str(metadata.get('chunk_id', f'unknown-{i}'))
            page_title = str(metadata.get('page_title', 'Unknown Page'))
            section = metadata.get('section_header', '')
            
            # Format source info using f-strings to avoid None concatenation
            if section and isinstance(section, str):
                source_info = f"Chunk {chunk_id} ({section}) from {page_title}"
            else:
                source_info = f"Chunk {chunk_id} from {page_title}"
            
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
        
        # Add the building content from the retrieved chunks
        prompt += "Building Content:\n"
        for i, chunk in enumerate(chunks):
            # Extract text and metadata
            text = str(chunk.text if hasattr(chunk, 'text') else chunk)
            metadata = chunk.metadata if hasattr(chunk, 'metadata') and chunk.metadata else {}
            
            # Add source information if available
            chunk_id = str(metadata.get('chunk_id', f'unknown-{i}'))
            page_title = str(metadata.get('page_title', 'Unknown Page'))
            section = metadata.get('section_header', '')
            url = metadata.get('url', '')
            
            # Build source info parts
            source_parts = [f"ID: {chunk_id}"]
            if section and isinstance(section, str):
                source_parts.append(f"Section: {section}")
            if page_title:
                source_parts.append(f"Page: {page_title}")
            if url and isinstance(url, str):
                source_parts.append(f"URL: {url}")
            
            # Join parts with commas
            source_info = f" ({', '.join(source_parts)})"
            
            prompt += f"Chunk {i+1}{source_info}:\n{text}\n\n"
        
        # Add instructions for the model
        prompt += """Based on the building content provided above, please answer the question. 
If the answer cannot be found in the provided content, please state that you're using general knowledge and provide the best answer you can.
If you're providing DIY advice, please indicate this in your answer.
Always reference the specific chunks you used to formulate your answer."""
        
        return prompt


if __name__ == "__main__":
    # Example usage
    retriever = Retriever()
    results = retriever.query("sample query")
    logger.info(f"Query results: {results}")
