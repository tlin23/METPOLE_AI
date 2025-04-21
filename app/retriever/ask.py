"""
Retriever module for querying and retrieving information from embeddings.
"""

import os
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from pathlib import Path
import openai

from app.vector_store.init_chroma import init_chroma_db

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Initialize OpenAI client with proper error handling for proxy settings
try:
    client = openai.OpenAI(api_key=openai_api_key)
except TypeError as e:
    if "unexpected keyword argument 'proxies'" in str(e):
        # If the error is about proxies, initialize without proxy settings
        import openai._base_client
        original_init = openai._base_client.SyncHttpxClientWrapper.__init__
        
        def patched_init(self, *args, **kwargs):
            # Remove 'proxies' from kwargs if present
            if 'proxies' in kwargs:
                del kwargs['proxies']
            return original_init(self, *args, **kwargs)
        
        # Apply the patch
        openai._base_client.SyncHttpxClientWrapper.__init__ = patched_init
        
        # Try initializing again
        client = openai.OpenAI(api_key=openai_api_key)
    else:
        # If it's a different TypeError, re-raise it
        raise


class Retriever:
    """
    Class for retrieving information from embeddings and generating answers using OpenAI.
    """
    
    def __init__(self):
        """
        Initialize the retriever.
        """
        # Get the path for the Chroma database
        self.chroma_db_path = os.getenv("CHROMA_DB_PATH", "./data/index")
        
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
    
    def query(self, query_text, n_results=5):
        """
        Query the embeddings database.
        
        Args:
            query_text (str): The query text.
            n_results (int, optional): Number of results to return. Defaults to 5.
            
        Returns:
            list: List of matching documents.
        """
        # Query using cosine similarity
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        
        return results
    
    def get_document(self, doc_id):
        """
        Retrieve a specific document by ID.
        
        Args:
            doc_id (str): Document ID.
            
        Returns:
            dict: Document data.
        """
        result = self.collection.get(ids=[doc_id])
        return result
    
    def generate_answer(self, question, chunks, model="gpt-3.5-turbo"):
        """
        Generate an answer to a question using OpenAI's GPT model and retrieved chunks.
        
        Args:
            question (str): The user's question.
            chunks (list): List of text chunks retrieved from the vector store.
            model (str, optional): The OpenAI model to use. Defaults to "gpt-3.5-turbo".
            
        Returns:
            dict: A dictionary containing the generated answer, source information, and flags.
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
        is_general_knowledge = "general knowledge" in answer_text.lower() or "i don't have specific information" in answer_text.lower()
        contains_diy_advice = any(phrase in answer_text.lower() for phrase in ["diy", "do it yourself", "you can try", "you could try", "steps to", "how to"])
        
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
        if source_info and not is_general_knowledge:
            source_trace = "\n\nSource: " + source_info
            answer_text += source_trace
        
        return {
            "answer": answer_text,
            "is_general_knowledge": is_general_knowledge,
            "contains_diy_advice": contains_diy_advice,
            "source_info": source_info
        }
    
    def _prepare_source_info(self, chunks):
        """
        Prepare source information from chunks.
        
        Args:
            chunks (list): List of text chunks retrieved from the vector store.
            
        Returns:
            str: Formatted source information.
        """
        sources = []
        for i, chunk in enumerate(chunks):
            # Extract metadata
            metadata = chunk.metadata if hasattr(chunk, 'metadata') and chunk.metadata else {}
            chunk_id = metadata.get('chunk_id', f'unknown-{i}')
            page_title = metadata.get('page_title', 'Unknown Page')
            section = metadata.get('section_header', '')
            
            # Format source info
            source_info = f"Chunk {chunk_id}"
            if section:
                source_info += f" ({section})"
            source_info += f" from {page_title}"
            
            sources.append(source_info)
        
        return "; ".join(sources)
    
    def _construct_prompt(self, question, chunks):
        """
        Construct a prompt for the OpenAI model that includes the question and retrieved chunks.
        
        Args:
            question (str): The user's question.
            chunks (list): List of text chunks retrieved from the vector store.
            
        Returns:
            str: The constructed prompt.
        """
        # Start with the question
        prompt = f"Question: {question}\n\n"
        
        # Add the building content from the retrieved chunks
        prompt += "Building Content:\n"
        for i, chunk in enumerate(chunks):
            # Extract text and metadata
            text = chunk.text if hasattr(chunk, 'text') else chunk
            metadata = chunk.metadata if hasattr(chunk, 'metadata') and chunk.metadata else {}
            
            # Add source information if available
            chunk_id = metadata.get('chunk_id', f'unknown-{i}')
            page_title = metadata.get('page_title', 'Unknown Page')
            section = metadata.get('section_header', '')
            url = metadata.get('url', '')
            
            source_info = f" (ID: {chunk_id}"
            if section:
                source_info += f", Section: {section}"
            if page_title:
                source_info += f", Page: {page_title}"
            if url:
                source_info += f", URL: {url}"
            source_info += ")"
            
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
    print(f"Query results: {results}")
