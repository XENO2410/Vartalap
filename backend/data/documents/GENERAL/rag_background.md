# Background: Retrieval-Augmented Generation (RAG)

Retrieval-Augmented Generation (RAG) is a technique that enables large
language models (LLMs) to retrieve and incorporate new information from
external data sources at inference time, instead of relying solely on their
pre-training data.

At a high level, a RAG system operates in three stages:

1. **Indexing.** External data (documents, tables, knowledge graphs) is
   converted into vector embeddings and stored in a vector database.
2. **Retrieval.** For a given user query, a retriever selects the most
   relevant documents from the vector store. Reranking, hybrid search
   (sparse + dense) and late-interaction models such as ColBERT are common
   accuracy improvements.
3. **Generation.** The retrieved passages are supplied to the LLM through
   prompt engineering ("prompt stuffing"), so the model prioritises the
   retrieved context over its parametric memory when producing an answer.

RAG improves factuality, allows citing sources for verification, and removes
the need to retrain the base model when knowledge changes. It does not
eliminate hallucinations: models can still misinterpret retrieved context,
combine outdated and updated information, or generate false claims when
retrieval quality is poor ("RAG poisoning"). Robust RAG systems therefore
depend heavily on chunking strategy, retriever quality, reranking, and
downstream guardrails.

_Source: Adapted from Wikipedia's "Retrieval-augmented generation" article,
Creative Commons Attribution-ShareAlike 4.0._
