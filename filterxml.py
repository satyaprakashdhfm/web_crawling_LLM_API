import xml.etree.ElementTree as ET

def filter_sitemap(input_file, output_file):
    # Parse the input XML file
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    # Use a set to collect unique URLs
    seen = set()
    unique_urls = []
    
    # The sitemap namespace
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    
    # Iterate over each <url> element and extract <loc> text
    for url_element in root.findall("sm:url", ns):
        loc_element = url_element.find("sm:loc", ns)
        if loc_element is not None:
            url_text = loc_element.text.strip()
            if url_text not in seen:
                seen.add(url_text)
                unique_urls.append(url_text)
    
    print(f"Found {len(unique_urls)} unique URLs.")
    
    # Create a new XML structure for the filtered sitemap
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url in unique_urls:
        url_el = ET.SubElement(urlset, "url")
        loc_el = ET.SubElement(url_el, "loc")
        loc_el.text = url
    
    # Write the new XML to a file
    new_tree = ET.ElementTree(urlset)
    new_tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"Filtered sitemap saved as: {output_file}")

if __name__ == "__main__":
    filter_sitemap("expanded_sitemap.xml", "filtered_sitemap.xml")
