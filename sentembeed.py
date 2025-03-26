import os
import json
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm  # for progress reporting

def load_json(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_vector_database(vector_db, output_file):
    with open(output_file, "wb") as f:
        pickle.dump(vector_db, f)

def create_vector_database(json_file, model_name="all-mpnet-base-v2"):
    # Load the final JSON file
    data = load_json(json_file)
    print(f"Loaded {len(data)} records from {json_file}")

    # Extract content and create metadata (here, we keep URL as metadata)
    corpus = []
    metadata = []
    for record in data:
        corpus.append(record.get("content", ""))
        metadata.append({
            "url": record.get("url", "No URL")
        })
    
    # Load the embedding model and report time/memory if needed.
    print(f"Loading embedding model: {model_name} ...")
    model = SentenceTransformer(model_name)
    print("Model loaded successfully.")
    
    # Generate embeddings with a progress bar.
    print("Generating embeddings for the corpus...")
    doc_vectors = model.encode(corpus, show_progress_bar=True)
    
    # Convert embeddings to a numpy array if needed.
    doc_vectors = np.array(doc_vectors)
    print(f"Embeddings generated. Shape: {doc_vectors.shape}")
    
    # Create the vector database dictionary.
    vector_db = {
        "model_name": model_name,
        "doc_vectors": doc_vectors,   # This is a numpy array or list of embeddings.
        "metadata": metadata,
        "corpus": corpus
    }
    return vector_db

def main():
    input_file = r"C:\Users\surya\Desktop\webcrawling\vector_data_final.json"
    output_file = r"C:\Users\surya\Desktop\webcrawling\vector_store_final.pkl"
    
    vector_db = create_vector_database(input_file, model_name="all-mpnet-base-v2")
    save_vector_database(vector_db, output_file)
    print(f"Vector database created and saved to {output_file}")

if __name__ == "__main__":
    main()