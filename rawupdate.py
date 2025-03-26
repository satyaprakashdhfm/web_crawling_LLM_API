import os
import pickle

def load_vector_database(pickle_file):
    with open(pickle_file, "rb") as f:
        vector_db = pickle.load(f)
    return vector_db

def save_vector_database(vector_db, pickle_file):
    with open(pickle_file, "wb") as f:
        pickle.dump(vector_db, f)

def update_records(vector_db, target_url_substring, additional_text):
    """
    For each record in vector_db whose URL contains target_url_substring,
    if the record's 'content' does not already include additional_text, append the additional_text.
    Returns the number of records updated.
    """
    updated_count = 0
    for record in vector_db["metadata"]:
        url = record.get("url", "")
        if target_url_substring in url:
            current_content = record.get("content", "")
            if additional_text not in current_content:
                record["content"] = current_content.strip() + "\n\n" + additional_text.strip()
                updated_count += 1
                print(f"Updated record for URL: {url}")
            else:
                print(f"Record for URL: {url} is already updated. Skipping.")
    return updated_count

def main():
    # Path to your vector database pickle file.
    pickle_file = r"C:\Users\surya\Desktop\webcrawling\vector_store_final.pkl"
    vector_db = load_vector_database(pickle_file)
    
    # Update the leadership record (only leadership info).
    leadership_target = "https://www.acg-world.com/leadership"
    leadership_text = (
        "ACG was founded in 1961 by brothers Ajit Singh and Jasjit Singh to manufacture empty hard capsules for Indian "
        "pharmaceutical companies. It is important to note that our founders are only Ajit Singh and Jasjit Singh. "
        "Karan Singh, who now serves as our Chairman, represents the next generation leading ACG forward. "
        "For more details, please visit our official website at https://www.acg-world.com."
    )
    leadership_updates = update_records(vector_db, leadership_target, leadership_text)
    
    # Update the history record (only pure history, excluding leadership details).
    history_target = "https://www.acg-world.com/#main-content"
    history_text = (
        "ACG is a multinational pharmaceutical company with origins dating back to 1961. Over the decades, "
        "the company has grown from a small family-run business into one of the world's largest integrated suppliers "
        "of solid dosage products. Early on, the company focused on manufacturing empty hard capsules and gradually expanded "
        "its operations to include equipment manufacturing, packaging, inspection, and testing. Key milestones include "
        "the establishment of our R&D hub in Mumbai in 1971, the acquisition of a capsule shell manufacturing plant in Croatia in 2007, "
        "and strategic expansions that have propelled us onto the global stage. For further details, please visit https://www.acg-world.com."
    )
    history_updates = update_records(vector_db, history_target, history_text)
    
    if leadership_updates or history_updates:
        save_vector_database(vector_db, pickle_file)
        print(f"\nVector database updated: {leadership_updates} leadership record(s) and {history_updates} history record(s) modified.")
    else:
        print("\nNo record required updating. All records are already updated.")

if __name__ == "__main__":
    main()

# import os
# import pickle

# def load_vector_database(pickle_file):
#     with open(pickle_file, "rb") as f:
#         vector_db = pickle.load(f)
#     return vector_db

# def save_vector_database(vector_db, pickle_file):
#     with open(pickle_file, "wb") as f:
#         pickle.dump(vector_db, f)

# def update_leadership_summary(vector_db, target_url, additional_text):
#     """
#     Find the record whose URL contains the target_url substring.
#     If found and additional_text is not already in its 'content',
#     append the additional_text to the current content.
#     """
#     updated = False
#     for meta in vector_db["metadata"]:
#         # Check if the target URL is in the record's URL
#         if target_url in meta.get("url", ""):
#             original_content = meta.get("content", "")
#             if additional_text not in original_content:
#                 meta["content"] = original_content + "\n\n" + additional_text
#                 updated = True
#                 print(f"Updated record for URL: {meta['url']}")
#     return vector_db, updated

# def main():
#     # Path to your vector database pickle file.
#     pickle_file = r"C:\Users\surya\Desktop\webcrawling\vector_store_final.pkl"
#     vector_db = load_vector_database(pickle_file)
    
#     # The target URL substring (for the leadership page).
#     target_url = "https://www.acg-world.com/leadership#main-content"
    
#     # Additional summarization text to add.
#     additional_text = (
#         "ACG was founded in 1961 by brothers Ajit Singh and Jasjit Singh to manufacture empty hard capsules for Indian pharmaceutical companies. "
#         "Subsequently, the company expanded to other countries and diversified into related businesses in the pharmaceutical sector.[14] These include equipment manufacturing, packaging, inspection, testing, research and development.[15]\n\n"
#         "In 1971, SciTech Centre was incorporated in Mumbai as the R&D center of ACG.[16][17] The Centre trains around 2,000 pharma professionals every year and also hosts scientific conferences.[18]\n\n"
#         "In 2007, ACG acquired the capsule shell manufacturing plant of Lukaps in Croatia, making it the first Indian company from the pharmaceutical sector to establish a presence in Croatia.[19][20] After successfully turning around the plant's operations, ACG announced further expansion plans worth 50 million Euros.[21]\n\n"
#         "In 2014, ACG Europe was listed among the top 41 fast-growing Indian companies in UK.[22]\n\n"
#         "In 2017, Nova Nordeplast, a Brazilian company that produces films and foils, was acquired by ACG.\n\n"
#         "In 2017, ACG acquired In2trace, a Croatia-based startup with proprietary technology in the track-and-trace business.[23] 90% of production at ACG’s plant in Croatia is exported to the USA, Russia, and European countries.[24]"
#     )
    
#     # Update the leadership summary if the target URL is found.
#     vector_db, updated = update_leadership_summary(vector_db, target_url, additional_text)
    
#     if updated:
#         save_vector_database(vector_db, pickle_file)
#         print("Vector database updated with the additional leadership summary.")
#     else:
#         print("No record found for the target URL or the summary was already updated.")

# if __name__ == "__main__":
#     main()
