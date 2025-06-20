import os
import pickle
import numpy as np
import requests
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from bs4 import BeautifulSoup
from googlesearch import search
import urllib3
import streamlit as st

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
# GROQ CLOUD API FUNCTIONS
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
# STREAMLIT UI
# ------------------------------

# Cache the model to avoid reloading on each run
@st.cache_resource
def load_model(model_name):
    return SentenceTransformer(model_name)

# Streamlit app
st.title("ACG World Query System")
st.write("Enter your query below to get information from ACG World's knowledge base.")

pickle_file = r"C:\Users\surya\Desktop\webcrawling\vector_store_final.pkl"

# Load vector database (fresh each run to reflect updates)
vector_db = load_vector_database(pickle_file)
model_name = vector_db.get("model_name", "all-MiniLM-L6-v2")
model = load_model(model_name)

# Form for query input
with st.form(key='query_form'):
    query = st.text_input("Enter your query:")
    submit_button = st.form_submit_button(label='Submit')

# Process query on submission
if submit_button and query.strip():
    results, max_sim = query_vector_database(query, model, vector_db["doc_vectors"], vector_db["metadata"], threshold=0.5, top_n=5)
    context = ""
    ref_links = []
    source_label = ""

    if results is not None:
        source_label = "retrieved"
        for res in results:
            snippet = res["content"][:1000]
            context += f"URL: {res['url']}\nSummary: {snippet}\n\n"
            ref_links.append(res["url"])
    else:
        google_results = google_search_and_scrape(query)
        if google_results:
            source_label = "googled"
            top_google = google_results[0]
            summarized = summarize_text(top_google["content"])
            if summarized != "NO CONTENT":
                new_record = {"url": top_google["url"], "content": summarized}
                context += f"URL: {new_record['url']}\nSummary: {new_record['content']}\n\n"
                ref_links.append(new_record["url"])
                vector_db = update_vector_database(vector_db, [new_record], model)
                save_vector_database(vector_db, pickle_file)

    # Limit reference links to 2
    ref_links = ref_links[:2]
    final_answer = generate_final_answer(query, context)

    # Display results
    st.write("### Final Answer")
    st.write(final_answer)
    if ref_links:
        st.write("### Reference Links")
        for link in ref_links:
            st.write(f"{link} ({source_label})")
elif submit_button:
    st.write("Please enter a query.")