import json

def load_json(json_file):
    """Load JSON file."""
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, output_file):
    """Save JSON data to a file."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clean_data(data):
    """Remove records with 'NO CONTENT' and remove 'title' from the rest."""
    cleaned_data = []
    for record in data:
        if record.get("content") != "NO CONTENT":
            record.pop("title", None)  # Remove 'title' if it exists
            cleaned_data.append(record)
    return cleaned_data

def main():
    input_file = r"C:\Users\surya\Desktop\webcrawling\vector_data_summarized.json"
    output_file = r"C:\Users\surya\Desktop\webcrawling\vector_data_final.json"
    
    data = load_json(input_file)
    print(f"Total records before cleaning: {len(data)}")

    cleaned_data = clean_data(data)
    print(f"Total records after cleaning: {len(cleaned_data)}")

    save_json(cleaned_data, output_file)
    print(f"Final cleaned records saved to {output_file}")

if __name__ == "__main__":
    main()
