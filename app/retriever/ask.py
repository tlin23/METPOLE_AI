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

client = openai.OpenAI(api_key=openai_api_key)


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
            str: The generated answer.
        """
        # Construct the prompt with the retrieved chunks
        prompt = self._construct_prompt(question, chunks)
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided building content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more factual responses
            max_tokens=1000   # Limit response length
        )
        
        # Return the model's response
        return response.choices[0].message.content
    
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
            source_info = ""
            if metadata and "url" in metadata:
                source_info = f" (Source: {metadata['url']})"
            
            prompt += f"Chunk {i+1}{source_info}:\n{text}\n\n"
        
        # Add instructions for the model
        prompt += "Based on the building content provided above, please answer the question. If the answer cannot be found in the provided content, please state that the information is not available."
        
        return prompt


if __name__ == "__main__":
    # Example usage
    retriever = Retriever()
    results = retriever.query("sample query")
    print(f"Query results: {results}")
