# test_retrieval.py

from app.retriever.ask import Retriever
import pprint

retriever = Retriever()

query = "What is metropole?"
results = retriever.query(query, n_results=5)

pprint.pprint(results)
