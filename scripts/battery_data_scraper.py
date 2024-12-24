# battery_data_scraper.py

"""
Battery Data and Articles Scraper
=================================
This script automates the process of web scraping battery-related data and articles
from the Materials for Batteries website or similar sources. It is tailored for
LLM Engineers and developers to create datasets for AI model training.

Author: Usama Yasir Khan
GitHub: yasirusama61
Date: 2024-10-20
"""

import requests
from bs4 import BeautifulSoup
import os
import pandas as pd

def create_directory(directory_name):
    """
    Create a directory if it doesn't exist.

    Args:
        directory_name (str): Name of the directory to create.
    """
    os.makedirs(directory_name, exist_ok=True)
    print(f"Directory '{directory_name}' is ready.")

def fetch_html_content(url):
    """
    Fetch the HTML content of a webpage.

    Args:
        url (str): URL of the webpage to scrape.

    Returns:
        BeautifulSoup: Parsed HTML content of the webpage.
    """
    try:
        print(f"Fetching content from {url}...")
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch content: {e}")
        return None

def scrape_table_data(soup, table_selector):
    """
    Scrape data from a table in the HTML content.

    Args:
        soup (BeautifulSoup): Parsed HTML content.
        table_selector (str): CSS selector for the table.

    Returns:
        list of dict: List of rows with column data.
    """
    table = soup.select_one(table_selector)
    if not table:
        print("Table not found!")
        return []

    headers = [th.text.strip() for th in table.select("thead th")]
    rows = []
    for tr in table.select("tbody tr"):
        cells = [td.text.strip() for td in tr.select("td")]
        rows.append(dict(zip(headers, cells)))

    return rows

def save_data_as_csv(data, file_path):
    """
    Save scraped data as a CSV file.

    Args:
        data (list of dict): Data to save.
        file_path (str): Path to save the CSV file.
    """
    if not data:
        print("No data to save!")
        return

    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    print(f"Data saved to {file_path}")

if __name__ == "__main__":
    # URL and directory settings
    target_url = "https://www.materialsforbatteries.org/data/"
    data_directory = "scraped_battery_data"
    create_directory(data_directory)

    # Fetch webpage content
    soup = fetch_html_content(target_url)

    if soup:
        # Scrape table data
        table_selector = "table"  # Adjust selector as needed
        scraped_data = scrape_table_data(soup, table_selector)

        # Save the data
        save_data_as_csv(scraped_data, os.path.join(data_directory, "battery_articles.csv"))

    print("Web scraping completed successfully!")
