import os
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import json
import matplotlib.pyplot as plt

# Create directories for storing results
os.makedirs("pdfs", exist_ok=True)
os.makedirs("extracted_text", exist_ok=True)
os.makedirs("results", exist_ok=True)

# Step 1: Crawl ArXiv for PDF links
def crawl_arxiv(search_query, max_papers=5):
    base_url = "https://arxiv.org/search/"
    query_params = {
        "query": search_query,
        "searchtype": "all",
        "source": "header"
    }
    pdf_links = []

    response = requests.get(base_url, params=query_params)
    if response.status_code != 200:
        print("Failed to access ArXiv search page.")
        return pdf_links

    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.find_all("li", class_="arxiv-result")[:max_papers]

    for result in results:
        pdf_link_tag = result.find("a", string="pdf")
        if pdf_link_tag:
            pdf_url = pdf_link_tag["href"]
            if not pdf_url.startswith("http"):
                pdf_url = "https://arxiv.org" + pdf_url
            pdf_links.append(pdf_url)

    print(f"Found {len(pdf_links)} PDFs.")
    return pdf_links

# Step 2: Download PDFs
def download_pdfs(pdf_links):
    for idx, pdf_url in enumerate(pdf_links, start=1):
        try:
            response = requests.get(pdf_url)
            pdf_path = os.path.join("pdfs", f"paper_{idx}.pdf")
            with open(pdf_path, "wb") as file:
                file.write(response.content)
            print(f"Downloaded: {pdf_url} -> {pdf_path}")
        except Exception as e:
            print(f"Failed to download {pdf_url}: {e}")

# Step 3: Extract text from PDFs
def extract_text_from_pdfs():
    pdf_files = [f for f in os.listdir("pdfs") if f.endswith(".pdf")]
    for pdf_file in pdf_files:
        pdf_path = os.path.join("pdfs", pdf_file)
        text_path = os.path.join("extracted_text", pdf_file.replace(".pdf", ".txt"))

        try:
            reader = PdfReader(pdf_path)
            with open(text_path, "w", encoding="utf-8") as text_file:
                for page in reader.pages:
                    text_file.write(page.extract_text())
            print(f"Extracted text: {pdf_path} -> {text_path}")
        except Exception as e:
            print(f"Failed to extract text from {pdf_path}: {e}")

# Step 4: Generate QA pairs
def generate_qa_pairs():
    qa_pairs = []
    for text_file in os.listdir("extracted_text"):
        text_path = os.path.join("extracted_text", text_file)
        with open(text_path, "r", encoding="utf-8") as file:
            text = file.read()

        sections = text.split(". ")
        for i, section in enumerate(sections[:10]):  # Limit to 10 pairs per file
            qa_pairs.append({
                "question": f"What is discussed in section {i+1}?",
                "answer": section.strip()
            })

    with open("results/qa_pairs.json", "w", encoding="utf-8") as json_file:
        json.dump(qa_pairs, json_file, indent=4)
    print("QA pairs saved to results/qa_pairs.json")

# Step 5: Analyze word counts
def analyze_word_counts():
    word_counts = []
    file_names = []
    for text_file in os.listdir("extracted_text"):
        text_path = os.path.join("extracted_text", text_file)
        with open(text_path, "r", encoding="utf-8") as file:
            text = file.read()
            word_counts.append(len(text.split()))
            file_names.append(text_file)

    # Plot word count distribution
    plt.figure(figsize=(10, 6))
    plt.bar(file_names, word_counts, color="skyblue")
    plt.xlabel("Text Files")
    plt.ylabel("Word Count")
    plt.title("Word Count of Extracted Texts")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("results/word_count_distribution.png")
    print("Word count distribution saved to results/word_count_distribution.png")
    plt.show()

# Step 6: Visualize QA pair statistics
def visualize_qa_statistics():
    with open("results/qa_pairs.json", "r", encoding="utf-8") as file:
        qa_pairs = json.load(file)

    question_lengths = [len(qa['question'].split()) for qa in qa_pairs]
    answer_lengths = [len(qa['answer'].split()) for qa in qa_pairs]

    plt.figure(figsize=(10, 6))
    plt.hist(question_lengths, bins=10, alpha=0.7, label="Question Lengths")
    plt.hist(answer_lengths, bins=10, alpha=0.7, label="Answer Lengths")
    plt.xlabel("Word Count")
    plt.ylabel("Frequency")
    plt.title("Distribution of Question and Answer Lengths")
    plt.legend()
    plt.tight_layout()
    plt.savefig("results/qa_pair_statistics.png")
    print("QA pair statistics saved to results/qa_pair_statistics.png")
    plt.show()

# Main function to orchestrate the process
def main():
    search_query = "battery"
    max_papers = 5

    print("Crawling ArXiv for PDFs...")
    pdf_links = crawl_arxiv(search_query, max_papers)

    print("Downloading PDFs...")
    download_pdfs(pdf_links)

    print("Extracting text from PDFs...")
    extract_text_from_pdfs()

    print("Generating QA pairs...")
    generate_qa_pairs()

    print("Analyzing word counts...")
    analyze_word_counts()

    print("Visualizing QA pair statistics...")
    visualize_qa_statistics()

    print("Process completed. Check the 'results/' directory for outputs.")

if __name__ == "__main__":
    main()
