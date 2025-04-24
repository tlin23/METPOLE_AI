# test_retrieval.py

from app.retriever.ask import Retriever
import pprint

retriever = Retriever()

query = "Who are the board members?"
results = retriever.query(query, n_results=10)

pprint.pprint(results)
