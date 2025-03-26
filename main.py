import os
import pickle
import numpy as np 
from sklearn.metrics.pairwise import cosine_similarity
import requests
from bs4 import BeautifulSoup
import warnings
import time
import re
import streamlit as st
from googlesearch import search

# Suppress SSL warnings for testing only
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

### VECTOR DATABASE FUNCTIONS ###
def load_vector_database(pickle_file=r"C:\Users\surya\Desktop\webcrawling\vector_store.pkl"):
    with open(pickle_file, "rb") as f:
        vector_store = pickle.load(f)
    return vector_store["vectorizer"], vector_store["doc_vectors"], vector_store["metadata"], vector_store["corpus"]

def query_vector_database(query, vectorizer, doc_vectors, metadata, corpus, threshold=0.0000000000000005, top_n=2):
    query_vec = vectorizer.transform([query])
    similarities = cosine_similarity(query_vec, doc_vectors).flatten()
    indices = np.where(similarities >= threshold)[0]
    results = []
    if len(indices) > 0:
        sorted_indices = indices[np.argsort(similarities[indices])[::-1]]
        for idx in sorted_indices[:top_n]:
            results.append({
                "url": metadata[idx]["url"],
                "content": corpus[idx],
                "similarity": similarities[idx]
            })
    return results

def filter_results_by_query(results, query):
    query_terms = query.lower().split()
    filtered = []
    for res in results:
        content_lower = res["content"].lower()
        if all(re.search(r'\b' + re.escape(term) + r'\b', content_lower) for term in query_terms):
            filtered.append(res)
    return filtered

### GOOGLE SEARCH FALLBACK FUNCTIONS ###
def scrape_content(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        st.error(f"Error scraping {url}: {e}")
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
                "content": content,
                "summary": simple_summary(content, word_limit=1000)
            })
    return results

### GROQ CLOUD API FUNCTION ###
def query_groq_api(query, context, model="llama-3.3-70b-versatile"):
    from groq import Groq, GroqError
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "API key not set."
    client = Groq(api_key=api_key)
    try:
        system_prompt = (
            "You are an official representative of ACG World, a leader in pharmaceutical and nutraceutical solutions. "
            "Answer questions in a clear, professional, and confident tone, providing detailed insights about our products, "
            "services, and events."
        )
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {query}\n\nContext:\n{context}"}
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
        return f"Groq API Error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

### MAIN PIPELINE ###
def process_query(query):
    try:
        vectorizer, doc_vectors, metadata, corpus = load_vector_database()
    except Exception as e:
        return f"Error loading vector database: {e}", [], ""
    
    vector_results = query_vector_database(query, vectorizer, doc_vectors, metadata, corpus)
    vector_results = filter_results_by_query(vector_results, query)
    
    context = ""
    ref_links = []
    source_label = ""
    
    if vector_results:
        source_label = "retrieved"
        for res in vector_results:
            summary = simple_summary(res["content"], word_limit=1000)
            context += f"URL: {res['url']}\nSummary: {summary}\n\n"
            ref_links.append(res["url"])
    else:
        google_results = google_search_and_scrape(query)
        if google_results:
            source_label = "googled"
            for res in google_results:
                summary = simple_summary(res["content"], word_limit=1000)
                context += f"URL: {res['url']}\nSummary: {summary}\n\n"
                ref_links.append(res["url"])
        else:
            return "No relevant content found.", [], ""
    
    ref_links = ref_links[:2]
    answer = query_groq_api(query, context)
    return answer, ref_links, source_label

### STREAMLIT UI ###
st.title("ACG World Chatbot")
st.markdown("Ask questions about ACG World and get concise answers with reference links at the end.")

query_input = st.text_input("Enter your query about ACG World:")

if st.button("Submit Query") and query_input:
    with st.spinner("Processing your query..."):
        final_answer, references, source_label = process_query(query_input)
    st.subheader("Final Answer:")
    st.markdown(final_answer)
    if references:
        st.subheader("Reference Links:")
        for link in references:
            st.markdown(f"[{link}]({link}) ({source_label})")