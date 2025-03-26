import os
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import requests
from bs4 import BeautifulSoup
import warnings
import re
import streamlit as st

# Try to import the google search function
try:
    from googlesearch import search
except ImportError:
    try:
        from googlesearch_python.googlesearch import search
    except ImportError:
        st.error("Google search module not found. Please install googlesearch-python using pip.")
        search = None

# Suppress SSL warnings (for testing only)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

### VECTOR DATABASE FUNCTIONS ###
VECTOR_STORE_PATH = r"C:\Users\surya\Desktop\webcrawling\vector_store.pkl"

def load_vector_database(pickle_file=VECTOR_STORE_PATH):
    with open(pickle_file, "rb") as f:
        vector_store = pickle.load(f)
    # Your build_vector_database created keys: "vectorizer", "doc_vectors", "metadata", "corpus"
    return (vector_store["vectorizer"],
            vector_store["doc_vectors"],
            vector_store["metadata"],
            vector_store["corpus"])

def query_vector_database(query, vectorizer, doc_vectors, metadata, corpus, threshold=0.05, top_n=5):
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
                "title": metadata[idx].get("title", "No Title"),
                "similarity": similarities[idx]
            })
    return results

def filter_results_by_query(results, query):
    query_terms = query.lower().split()
    filtered = []
    for res in results:
        # Check in URL (and optionally title) for exact query term matches
        url_text = res["url"].lower()
        if all(re.search(r'\b' + re.escape(term) + r'\b', url_text) for term in query_terms):
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

def simple_summary(text, word_limit=100):
    words = text.split()
    if len(words) <= word_limit:
        return text
    return " ".join(words[:word_limit]) + "..."

def google_search_and_scrape(query, domain="acg-world.com", num_results=2):
    if search is None:
        return []
    search_query = f"site:{domain} {query}"
    st.write(f"Performing Google search fallback: {search_query}")
    raw_urls = list(search(search_query, num_results=num_results))
    urls = [u for u in raw_urls if u.startswith("http")]
    results = []
    for url in urls:
        content = scrape_content(url)
        if content:
            results.append({
                "url": url,
                "content": content,
                "title": url,  # use URL as title if no title available
                "summary": simple_summary(content, word_limit=100)
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
            "Answer questions in a clear, professional, and confident tone using only the provided context. "
            "If the context does not cover the query in detail, instruct the user to ask a more topic-specific question."
        )
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {query}\n\nContext:\n{context}"}
            ],
            model=model,
            temperature=0.1,
            max_completion_tokens=300,
            top_p=1,
            stream=False,
            stop=None
        )
        return chat_completion.choices[0].message.content
    except GroqError as e:
        return f"Groq API Error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

### EMBED REFERENCE LINKS ###
def embed_reference_links(answer, ref_info):
    # Append a reference list at the end with a link symbol (here just a numbered list)
    ref_list = "\n".join([f"[{i+1}. {info['title']}]({info['url']})" for i, info in enumerate(ref_info)])
    return answer + "\n\n**Reference Links:**\n" + ref_list

### PROCESS QUERY FUNCTION ###
def process_query(query, num_docs=5):
    try:
        vectorizer, doc_vectors, metadata, corpus = load_vector_database()
    except Exception as e:
        return f"Error loading vector database: {e}", ""
    
    vector_results = query_vector_database(query, vectorizer, doc_vectors, metadata, corpus, top_n=num_docs)
    vector_results = filter_results_by_query(vector_results, query)
    
    ref_info = []  # List to store dictionaries with 'title' and 'url'
    context = ""
    if len(vector_results) == 0:
        google_results = google_search_and_scrape(query)
        if google_results:
            for res in google_results[:2]:
                context += f"Title: {res['title']}\nURL: {res['url']}\nSummary: {simple_summary(res['content'], 100)}\n\n"
                ref_info.append({"title": res["title"], "url": res["url"]})
        else:
            return "No relevant content found.", ""
    elif len(vector_results) == 2:
        for res in vector_results:
            context += f"Title: {res['title']}\nURL: {res['url']}\nContent: {res['content']}\n\n"
            ref_info.append({"title": res["title"], "url": res["url"]})
    else:
        # If more than 2 documents are found, send only the title and URL (and a brief summary) for up to 5 documents
        context += "We found multiple documents on this topic:\n"
        for i, res in enumerate(vector_results[:min(num_docs, 5)], start=1):
            context += f"{i}. Title: {res['title']}\nURL: {res['url']}\nSummary: {simple_summary(res['content'], 50)}\n"
            ref_info.append({"title": res["title"], "url": res["url"]})
        context += "\nFor more details, please ask a more topic-specific question.\n"
    
    ref_info = ref_info[:5]
    answer = query_groq_api(query, context)
    final_answer = embed_reference_links(answer, ref_info)
    return final_answer, ref_info

### STREAMLIT UI ###
if 'conversation' not in st.session_state:
    st.session_state.conversation = []

st.set_page_config(page_title="ACG World Chatbot", layout="wide")
st.title("ACG World Chatbot")
st.markdown("Ask questions about ACG World and receive concise answers with embedded reference links.\n\n*If you need more detailed information, please ask a more topic-specific question.*")

# Sidebar: Number of documents to use from the vector DB
num_docs = st.sidebar.slider("Number of documents to use from vector DB", min_value=1, max_value=10, value=5)
try:
    _, _, _, corpus = load_vector_database()
    st.sidebar.markdown(f"**Total documents in vector DB:** {len(corpus)}")
except Exception as e:
    st.sidebar.error(f"Error loading vector database: {e}")

# Main: Query input
query_input = st.text_input("Enter your query about ACG World:")

if st.button("Submit Query") and query_input:
    with st.spinner("Processing your query..."):
        final_answer, references = process_query(query_input, num_docs=num_docs)
        st.session_state.conversation.append({"query": query_input, "answer": final_answer, "refs": references})

# Display conversation history (latest at the bottom)
if st.session_state.conversation:
    st.subheader("Conversation History")
    for chat in st.session_state.conversation:
        st.markdown(f"**Q:** {chat['query']}")
        st.markdown(f"**A:** {chat['answer']}")
        if chat['refs']:
            refs_str = ' | '.join([f"[{i+1}. {info['title']}]({info['url']})" for i, info in enumerate(chat['refs'])])
            st.markdown(f"**References:** {refs_str}")
        st.markdown("---")
