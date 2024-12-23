"""
Battery Data Pipeline for LLM Preparation
=========================================
This script automates the process of crawling data from battery-related articles, preprocessing the text, and preparing it for fine-tuning a large language model (LLM).

Author: Usama Yasir Khan
GitHub: yasirusama61
Date: 2024-12-23
"""


import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import json

# Step 1: Crawl Data from Battery Articles
def crawl_articles(base_url, max_pages=5):
    """
    Crawl data from a website containing battery-related articles.

    Args:
        base_url (str): The base URL of the website to scrape.
        max_pages (int): Maximum number of pages to crawl.

    Returns:
        list of dict: List of articles with title and content.
    """
    articles = []

    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}"
        print(f"Crawling page: {url}")
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to access {url}")
            continue

        soup = BeautifulSoup(response.content, "html.parser")

        # Example: Locate article containers (update selectors as needed)
        article_elements = soup.find_all("div", class_="article-container")
        for article in article_elements:
            title = article.find("h2").text.strip()
            content = article.find("p").text.strip()
            articles.append({"title": title, "content": content})

    return articles

# Step 2: Preprocess Text Data
def preprocess_text(articles):
    """
    Preprocess crawled article data for fine-tuning.

    Args:
        articles (list of dict): List of articles with title and content.

    Returns:
        list of dict: Preprocessed articles.
    """
    processed_articles = []

    for article in articles:
        title = re.sub(r"\s+", " ", article["title"]).strip()
        content = re.sub(r"\s+", " ", article["content"]).strip()
        processed_articles.append({"title": title, "content": content})

    return processed_articles

# Step 3: Prepare Data for Fine-Tuning
def prepare_qa_pairs(articles):
    """
    Convert articles into QA pairs for fine-tuning.

    Args:
        articles (list of dict): List of articles with title and content.

    Returns:
        list of dict: QA pairs for fine-tuning.
    """
    qa_pairs = []

    for article in articles:
        qa_pairs.append({
            "question": f"What is the key information in '{article['title']}'?",
            "answer": article["content"]
        })

    return qa_pairs

# Step 4: Save Data as JSON
def save_to_json(data, filename):
    """
    Save data to a JSON file.

    Args:
        data (list of dict): Data to save.
        filename (str): File name to save the data.
    """
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Data saved to {filename}")

# Main Function
def main():
    """
    Main function to run the data pipeline.
    """
    # Define the base URL (update as per the target website)
    base_url = "https://arxiv.org/pdf/2410.23303"

    # Crawl articles
    print("Starting data crawling...")
    articles = crawl_articles(base_url)
    print(f"Crawled {len(articles)} articles.")

    # Preprocess text
    print("Starting text preprocessing...")
    processed_articles = preprocess_text(articles)

    # Prepare QA pairs
    print("Preparing QA pairs for fine-tuning...")
    qa_pairs = prepare_qa_pairs(processed_articles)

    # Save data
    save_to_json(qa_pairs, "qa_pairs.json")

    print("Data pipeline completed successfully!")

if __name__ == "__main__":
    main()
