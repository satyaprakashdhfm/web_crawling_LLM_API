import os
import json
import pickle
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import requests
from bs4 import BeautifulSoup
import warnings
from googlesearch import search

# Suppress SSL warnings for testing only
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

def load_json(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def filter_records_by_url(data, query):
    """
    Returns records where every word in the query appears as an exact match in the URL.
    """
    query_terms = query.lower().split()
    matching_records = []
    for record in data:
        url = record.get("url", "").lower()
        if all(re.search(r'\b' + re.escape(term) + r'\b', url) for term in query_terms):
            matching_records.append(record)
    return matching_records

def load_vector_database(pickle_file):
    with open(pickle_file, "rb") as f:
        vector_store = pickle.load(f)
    # Expected keys: "vectorizer", "doc_vectors", "metadata", "corpus"
    return (vector_store["vectorizer"], 
            vector_store["doc_vectors"], 
            vector_store["metadata"], 
            vector_store["corpus"])

def query_vector_subset(query, vectorizer, doc_vectors, metadata, corpus, valid_urls, top_n=2):
    """
    Filters the vector database to only those documents whose URL is in valid_urls,
    then computes cosine similarity for the query on that subset and returns the top_n.
    """
    # Compute similarity scores for all documents
    query_vec = vectorizer.transform([query])
    similarities = cosine_similarity(query_vec, doc_vectors).flatten()
    
    # Gather candidate indices whose URL is in the valid set
    candidates = []
    for idx in range(len(metadata)):
        record_url = metadata[idx]["url"].lower()
        if record_url in valid_urls:
            candidates.append((idx, similarities[idx]))
    
    # Sort candidates by similarity in descending order
    candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
    
    results = []
    for idx, sim in candidates[:top_n]:
        results.append({
            "url": metadata[idx]["url"],
            "title": metadata[idx].get("title", "No Title"),
            "content": corpus[idx],
            "similarity": sim
        })
    return results

### GOOGLE SEARCH FALLBACK FUNCTIONS ###
def scrape_content(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    return ""

def simple_summary(text, word_limit=1000):
    words = text.split()
    if len(words) <= word_limit:
        return text
    return " ".join(words[:word_limit]) + "..."

def google_search_and_scrape(query, domain="acg-world.com", num_results=2):
    if search is None:
        return []
    search_query = f"site:{domain} {query}"
    raw_urls = list(search(search_query, num_results=num_results))
    urls = [u for u in raw_urls if u.startswith("http")]
    results = []
    for url in urls:
        content = scrape_content(url)
        if content:
            results.append({
                "url": url,
                "title": "Google Search Result",  # You could add title extraction here if needed
                "content": content,
                "summary": simple_summary(content, word_limit=1000)
            })
    return results

if __name__ == "__main__":
    # Load local JSON data file
    json_file = r"C:\Users\surya\Desktop\webcrawling\vector_data.json"
    data = load_json(json_file)
    
    # Load the vector database from the pickle file
    vector_pickle_file = r"C:\Users\surya\Desktop\webcrawling\vector_store.pkl"
    vectorizer, doc_vectors, metadata, corpus = load_vector_database(vector_pickle_file)
    
    print("Enter your query (type 'exit' to quit):")
    while True:
        query = input("Query: ").strip()
        if query.lower() == "exit":
            print("Exiting.")
            break
        
        # First, filter records using word filtering on the URL from local JSON data.
        filtered_records = filter_records_by_url(data, query)
        
        if len(filtered_records) == 0:
            # Fallback to Google search if no local records found.
            print("\nNo records found in local JSON matching the query in the URL. Falling back to Google search...")
            google_results = google_search_and_scrape(query, domain="acg-world.com", num_results=2)
            if len(google_results) == 0:
                print("No records found via Google search.")
            else:
                print(f"\nFound {len(google_results)} record(s) from Google search:")
                for record in google_results:
                    title = record.get("title", "No Title")
                    url = record.get("url", "No URL")
                    content = record.get("content", "No Content")
                    print(f"Title: {title}\nURL: {url}\n")
                    print("Content:")
                    print(content)
                    print("-" * 80)
        elif len(filtered_records) <= 2:
            # If 2 or fewer records are found locally, show them directly.
            print(f"\nFound {len(filtered_records)} record(s) from local URL filtering:")
            for record in filtered_records:
                title = record.get("title", "No Title")
                url = record.get("url", "No URL")
                content = record.get("content", "No Content")
                print(f"Title: {title}\nURL: {url}\n")
                print("Content:")
                print(content)
                print("-" * 80)
        else:
            # If more than 2 local records are found, narrow them down using vector similarity.
            valid_urls = set(record["url"].lower() for record in filtered_records)
            vector_results = query_vector_subset(query, vectorizer, doc_vectors, metadata, corpus, valid_urls, top_n=2)
            
            print(f"\nFound {len(filtered_records)} records after local URL filtering.")
            print(f"Displaying top {len(vector_results)} record(s) based on similarity:")
            for record in vector_results:
                title = record["title"]
                url = record["url"]
                content = record["content"]
                sim_score = record["similarity"]
                print(f"Title: {title}\nURL: {url}\nSimilarity Score: {sim_score:.4f}\n")
                print("Content:")
                print(content)
                print("-" * 80)

# import json
# import re
# from collections import Counter

# def count_top_words(json_file=r"C:\Users\surya\Desktop\webcrawling\vector_data.json", content_key="content_clean", fallback_key="content", top_n=20):
#     # Load the JSON data
#     with open(json_file, "r", encoding="utf-8") as f:
#         data = json.load(f)
    
#     # Combine all text using content_key if available, otherwise fallback_key
#     all_text = " ".join(record.get(content_key, record.get(fallback_key, "")) for record in data)
    
#     # Convert text to lowercase for uniformity
#     all_text = all_text.lower()
    
#     # Use regex to extract words (alphanumeric sequences)
#     words = re.findall(r'\b\w+\b', all_text)
    
#     # Count word frequencies
#     word_counts = Counter(words)
    
#     # Get the top N most common words
#     top_words = word_counts.most_common(top_n)
#     return top_words

# if __name__ == "__main__":
#     top_words = count_top_words()
#     print("Top 20 most repeated words:")
#     for word, count in top_words:
#         print(f"{word}: {count}")
