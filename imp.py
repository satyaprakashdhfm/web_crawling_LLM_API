import os
import pickle
import numpy as np
import requests
import re
import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from bs4 import BeautifulSoup
from googlesearch import search
import urllib3

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ------------------------------
# VECTOR DATABASE FUNCTIONS
# ------------------------------

def load_vector_database(pickle_file=r"C:\Users\surya\Desktop\webcrawling\vector_store_final.pkl"):
    with open(pickle_file, "rb") as f:
        vector_db = pickle.load(f)
    return vector_db

def save_vector_database(vector_db, pickle_file=r"C:\Users\surya\Desktop\webcrawling\vector_store_final.pkl"):
    with open(pickle_file, "wb") as f:
        pickle.dump(vector_db, f)

def query_vector_database(query, model, doc_vectors, metadata, threshold=0.5, top_n=5):
    """
    Encode the query, compute cosine similarities, and return top_n records
    if the maximum similarity is above the threshold; else return None.
    """
    query_vec = model.encode([query])
    similarities = cosine_similarity(query_vec, doc_vectors).flatten()
    max_sim = np.max(similarities)
    if max_sim < threshold:
        return None, max_sim
    else:
        sorted_idx = np.argsort(similarities)[::-1]
        results = []
        for idx in sorted_idx[:top_n]:
            results.append({
                "url": metadata[idx]["url"],
                "content": metadata[idx]["content"],
                "similarity": similarities[idx]
            })
        return results, max_sim

def update_vector_database(vector_db, new_records, model):
    """
    Compute embeddings for new_records and append them to the existing vector database.
    Each new record should have 'url' and 'content'.
    """
    new_contents = [rec["content"] for rec in new_records]
    new_embeddings = model.encode(new_contents)
    vector_db["doc_vectors"] = np.vstack([vector_db["doc_vectors"], new_embeddings])
    for rec in new_records:
        vector_db["metadata"].append({"url": rec["url"], "content": rec["content"]})
        vector_db["corpus"].append(rec["content"])
    return vector_db

# ------------------------------
# GOOGLE SEARCH & SCRAPING FUNCTIONS
# ------------------------------

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
    search_query = f"site:{domain} {query}"
    raw_urls = list(search(search_query, num_results=num_results))
    urls = [u for u in raw_urls if u.startswith("http")]
    results = []
    for url in urls:
        content = scrape_content(url)
        if content:
            results.append({"url": url, "content": content})
    return results

# ------------------------------
# GROQ CLOUD API FUNCTIONS (for summarization and final answer)
# ------------------------------

def query_groq_api(prompt, model="llama-3.3-70b-versatile"):
    """
    Use Groq Cloud API to process a prompt.
    Returns the API's text response.
    """
    from groq import Groq, GroqError
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise Exception("GROQ_API_KEY not set in environment variables.")
    client = Groq(api_key=api_key)
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model=model,
            temperature=0.1,
            max_completion_tokens=3000,
            top_p=1,
            stream=False,
            stop=None
        )
        # Use dot notation instead of subscript:
        return chat_completion.choices[0].message.content
    except GroqError as e:
        print(f"Groq API Error: {e}")
        return "NO CONTENT"
    except Exception as e:
        print(f"Unexpected error in Groq API: {e}")
        return "NO CONTENT"

def summarize_text(text):
    """
    Summarize text using Groq Cloud API.
    """
    prompt = f"Please summarize the following content concisely:\n\n{text}"
    summary = query_groq_api(prompt)
    if len(summary.strip()) < 20 or not re.search(r"[a-zA-Z]", summary):
        return "NO CONTENT"
    return summary.strip()

def generate_final_answer(query, context):
    """
    Generate a final answer using Groq Cloud API with a system prompt.
    """
    system_prompt = (
    "You are an official representative of ACG World, a global leader in pharmaceutical and nutraceutical solutions. "
    "Speak confidently in the first-person plural (using 'we', 'our', and 'us') and avoid repeating information. "
    "Ensure that your response reflects our commitment to quality, innovation, and customer satisfaction while addressing the query professionally."
    )

    prompt = f"{system_prompt}\n\nQuestion: {query}\n\nContext:\n{context}"
    answer = query_groq_api(prompt)
    return answer

# ------------------------------
# MAIN QUERY LOOP
# ------------------------------

def main():
    # Load the vector database.
    pickle_file = r"C:\Users\surya\Desktop\webcrawling\vector_store_final.pkl"
    vector_db = load_vector_database(pickle_file)
    
    # Retrieve stored data.
    doc_vectors = vector_db["doc_vectors"]
    metadata = vector_db["metadata"]
    corpus = vector_db["corpus"]
    
    # Ensure each metadata dictionary has 'content'
    for i, md in enumerate(metadata):
        if "content" not in md:
            md["content"] = corpus[i]
    
    # Load the SentenceTransformer model used for embeddings.
    emb_model_name = vector_db.get("model_name", "all-MiniLM-L6-v2")
    print(f"Loading embedding model: {emb_model_name}")
    model = SentenceTransformer(emb_model_name)
    
    threshold = 0.5  # Adjust similarity threshold as needed.
    
    print("Enter your query (press Ctrl+C to exit):")
    try:
        while True:
            query = input("Query: ").strip()
            if not query:
                continue
            
            # First, try to retrieve local matches (top 5).
            results, max_sim = query_vector_database(query, model, doc_vectors, metadata, threshold=threshold, top_n=5)
            context = ""
            ref_links = []
            source_label = ""
            
            if results is not None:
                source_label = "retrieved"
                for res in results:
                    snippet = res["content"][:1000]  # Adjust snippet length if desired.
                    context += f"URL: {res['url']}\nSummary: {snippet}\n\n"
                    ref_links.append(res["url"])
                print("Local matches found:")
                for res in results:
                    print(f"URL: {res['url']} | Similarity: {res['similarity']:.4f}")
            else:
                print(f"No local match found (max similarity {max_sim:.4f} below threshold {threshold}).")
                print("Falling back to Google search...")
                google_results = google_search_and_scrape(query)
                if google_results:
                    source_label = "googled"
                    # Use only the top result from Google search.
                    top_google = google_results[0]
                    summarized = summarize_text(top_google["content"])
                    if summarized != "NO CONTENT":
                        new_record = {"url": top_google["url"], "content": summarized}
                        context += f"URL: {new_record['url']}\nSummary: {new_record['content']}\n\n"
                        ref_links.append(new_record["url"])
                        # Update vector database with the new record.
                        vector_db = update_vector_database(vector_db, [new_record], model)
                        save_vector_database(vector_db, pickle_file)
                        print("Vector database updated with new Google result:")
                        print(f"Added URL: {new_record['url']}")
                    else:
                        print("Google search yielded no summarizable content.")
                else:
                    print("Google search found no results.")
            
            # Limit reference links to 2 for the final answer.
            ref_links = ref_links[:2]
            final_answer = generate_final_answer(query, context)
            print("\nFinal Answer:")
            print(final_answer)
            if ref_links:
                print("\nReference Links:")
                for link in ref_links:
                    print(f"{link} ({source_label})")
            print("-" * 80)
    except KeyboardInterrupt:
        print("\nExiting query loop. Goodbye!")

if __name__ == "__main__":
    main()