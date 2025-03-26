import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

def build_vector_database(json_file, output_file):
    # Load the JSON data from the file
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    corpus = []      # List to store document content
    metadata = []    # List to store corresponding metadata (URL, title)
    
    # Iterate over each record and extract cleaned content
    for record in data:
        # Use 'content_clean' if available, otherwise fallback to 'content'
        text = record.get("content_clean") or record.get("content", "")
        if text.strip():
            corpus.append(text)
            metadata.append({
                "url": record.get("url", ""),
                "title": record.get("title", "")
            })
    
    # Build TF-IDF vectorizer with English stop words removed
    vectorizer = TfidfVectorizer(stop_words="english")
    doc_vectors = vectorizer.fit_transform(corpus)
    
    # Save the vectorizer, document vectors, metadata, and corpus in a pickle file
    vector_store = {
        "vectorizer": vectorizer,
        "doc_vectors": doc_vectors,
        "metadata": metadata,
        "corpus": corpus
    }
    
    with open(output_file, "wb") as f:
        pickle.dump(vector_store, f)
    
    print(f"Vector database saved to {output_file}")
    
if __name__ == "__main__":
    # Update the paths as needed
    json_file = r"C:\Users\surya\Desktop\webcrawling\vector_data.json"  # or your JSON file name
    output_file = r"C:\Users\surya\Desktop\webcrawling\vector_store.pkl"
    build_vector_database(json_file, output_file)
