import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

def load_vector_database(pickle_file):
    with open(pickle_file, "rb") as f:
        vector_db = pickle.load(f)
    return vector_db

def query_vector_database(query, model, doc_vectors, metadata, threshold=0.5, top_n=1):
    # Encode the query to get its embedding.
    query_vec = model.encode([query])
    # Compute cosine similarities between query and all document embeddings.
    similarities = cosine_similarity(query_vec, doc_vectors).flatten()
    max_sim = np.max(similarities)
    if max_sim < threshold:
        return None, max_sim
    else:
        # Get indices sorted by similarity (descending)
        sorted_idx = np.argsort(similarities)[::-1]
        results = []
        for idx in sorted_idx[:top_n]:
            results.append({
                "url": metadata[idx]["url"],
                "content": metadata[idx].get("content", ""),  # summary is stored here
                "similarity": similarities[idx]
            })
        return results, max_sim

def main():
    # Path to your vector database pickle file.
    vector_db_file = r"C:\Users\surya\Desktop\webcrawling\vector_store_final.pkl"
    vector_db = load_vector_database(vector_db_file)
    
    # Retrieve stored data.
    doc_vectors = vector_db["doc_vectors"]
    metadata = vector_db["metadata"]
    corpus = vector_db["corpus"]
    
    # Ensure that each metadata dictionary has the 'content' field.
    for i, md in enumerate(metadata):
        if "content" not in md:
            md["content"] = corpus[i]
    
    # Load the same SentenceTransformer model used during embedding creation.
    # The model name is stored in vector_db["model_name"]. If missing, default to "all-MiniLM-L6-v2".
    model_name = vector_db.get("model_name", "all-MiniLM-L6-v2")
    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    
    threshold = 0.5  # Adjust threshold as needed.
    
    print("Enter your query (press Ctrl+C to exit):")
    try:
        while True:
            query = input("Query: ").strip()
            if not query:
                continue  # skip empty query
            
            results, max_sim = query_vector_database(query, model, doc_vectors, metadata, threshold=threshold)
            
            if results is None:
                print(f"No match found. Maximum similarity {max_sim:.4f} is below threshold {threshold}.\n")
            else:
                print("Top matching record(s):")
                for res in results:
                    print(f"URL: {res['url']}")
                    print(f"Summary: {res['content'][:300]}...")  # Display first 300 characters of summary.
                    print(f"Similarity Score: {res['similarity']:.4f}")
                    print("-" * 60)
    except KeyboardInterrupt:
        print("\nExiting query loop. Goodbye!")

if __name__ == "__main__":
    main()
