"""
Author: Usama Yasir Khan
Date: December 27, 2024

Description:
This script covers the complete pipeline:
1. Crawl and download PDFs
2. Extract text from PDFs
3. Clean and process text
4. Generate QA pairs
5. Fine-tune GPT-2 on the generated QA pairs
"""

import os
import re
import json
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from collections import Counter
import nltk

# Download necessary NLTK resources
nltk.download("punkt")
nltk.download("stopwords")
nltk.download("wordnet")

# Directories for storing intermediate and final results
PDF_DIR = "pdfs"
EXTRACTED_DIR = "extracted_text"
CLEANED_DIR = "cleaned_text"
RESULTS_DIR = "results"
QA_FILE = "qa_pairs.json"

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(EXTRACTED_DIR, exist_ok=True)
os.makedirs(CLEANED_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


# Step 1: Crawl ArXiv for PDF links
def crawl_arxiv(search_query="battery", max_papers=5):
    """Crawl ArXiv for PDFs related to the search query."""
    base_url = "https://arxiv.org/search/"
    query_params = {"query": search_query, "searchtype": "all", "source": "header"}
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
            pdf_url = "https://arxiv.org" + pdf_link_tag["href"]
            pdf_links.append(pdf_url)

    print(f"Found {len(pdf_links)} PDFs.")
    return pdf_links


# Step 2: Download PDFs
def download_pdfs(pdf_links):
    """Download PDFs from the given list of links."""
    for idx, pdf_url in enumerate(pdf_links, start=1):
        try:
            response = requests.get(pdf_url)
            pdf_path = os.path.join(PDF_DIR, f"paper_{idx}.pdf")
            with open(pdf_path, "wb") as file:
                file.write(response.content)
            print(f"Downloaded: {pdf_url} -> {pdf_path}")
        except Exception as e:
            print(f"Failed to download {pdf_url}: {e}")


# Step 3: Extract text from PDFs
def extract_text_from_pdfs():
    """Extract text content from downloaded PDFs."""
    for pdf_file in os.listdir(PDF_DIR):
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        text_path = os.path.join(EXTRACTED_DIR, pdf_file.replace(".pdf", ".txt"))
        try:
            reader = PdfReader(pdf_path)
            with open(text_path, "w", encoding="utf-8") as text_file:
                for page in reader.pages:
                    text_file.write(page.extract_text())
            print(f"Extracted text: {pdf_file}")
        except Exception as e:
            print(f"Failed to extract text from {pdf_file}: {e}")


# Step 4: Clean and process text
def clean_text(text):
    """Clean the text by removing noise and normalizing content."""
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9.,\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_extracted_texts():
    """Clean all extracted text files and save them."""
    for text_file in os.listdir(EXTRACTED_DIR):
        input_path = os.path.join(EXTRACTED_DIR, text_file)
        output_path = os.path.join(CLEANED_DIR, text_file)
        with open(input_path, "r", encoding="utf-8") as file:
            raw_text = file.read()
        cleaned_text = clean_text(raw_text)
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(cleaned_text)
        print(f"Cleaned: {text_file}")


# Step 5: Generate QA pairs
def generate_qa_pairs_from_cleaned_texts():
    """Generate QA pairs from cleaned text and save as JSON."""
    qa_pairs = []
    for text_file in os.listdir(CLEANED_DIR):
        file_path = os.path.join(CLEANED_DIR, text_file)
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()

        # Example QA generation
        sections = sent_tokenize(text)[:5]  # Limit to first 5 sentences for QA
        for i, section in enumerate(sections):
            qa_pairs.append({
                "question": f"What is discussed in section {i + 1}?",
                "answer": section.strip()
            })

    # Save QA pairs
    with open(QA_FILE, "w", encoding="utf-8") as json_file:
        json.dump(qa_pairs, json_file, indent=4)
    print(f"QA pairs saved to {QA_FILE}")


# Step 6: Fine-tune GPT-2
def fine_tune_gpt2(model_checkpoint="gpt2", output_dir="fine_tuned_model"):
    """Fine-tune GPT-2 model on generated QA pairs."""
    # Load dataset
    with open(QA_FILE, "r", encoding="utf-8") as f:
        qa_pairs = json.load(f)
    data = [{"text": f"Q: {item['question']}\nA: {item['answer']}"} for item in qa_pairs]
    dataset = Dataset.from_dict({"text": [item["text"] for item in data]})

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
    tokenizer.pad_token = tokenizer.eos_token
    tokenized_dataset = dataset.map(lambda x: tokenizer(x["text"], truncation=True, padding="max_length", max_length=512), batched=True)
    model = AutoModelForCausalLM.from_pretrained(model_checkpoint)

    # Define training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        evaluation_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=4,
        num_train_epochs=3,
        save_steps=500,
        save_total_limit=2,
        logging_dir="./logs",
        logging_steps=10,
    )

    # Train model
    trainer = Trainer(model=model, args=training_args, train_dataset=tokenized_dataset)
    print("Starting fine-tuning...")
    trainer.train()
    print(f"Fine-tuning completed. Model saved to {output_dir}")


# Main Function
if __name__ == "__main__":
    print("Crawling PDFs...")
    pdf_links = crawl_arxiv()

    print("Downloading PDFs...")
    download_pdfs(pdf_links)

    print("Extracting text from PDFs...")
    extract_text_from_pdfs()

    print("Cleaning extracted text...")
    clean_extracted_texts()

    print("Generating QA pairs...")
    generate_qa_pairs_from_cleaned_texts()

    print("Fine-tuning GPT-2...")
    fine_tune_gpt2()
