import json
import re

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

if __name__ == "__main__":
    json_file = r"C:\Users\surya\Desktop\webcrawling\vector_data.json"  # Update path if needed
    data = load_json(json_file)
    
    query = input("Enter your query (search in URLs): ").strip()
    matches = filter_records_by_url(data, query)
    
    print(f"Found {len(matches)} matching records in URLs:")
    for record in matches:
        title = record.get("title", "No Title")
        url = record.get("url", "No URL")
        print(f"Title: {title}\nURL: {url}\n")















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
