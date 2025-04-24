# test_retrieval.py

from app.retriever.ask import Retriever
import pprint

retriever = Retriever()

query = "Who is John Ashenhurst?"
results = retriever.query(query, n_results=5)

pprint.pprint(results)
