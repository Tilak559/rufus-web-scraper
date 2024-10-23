# Rufus Web Scraper

## Overview
Rufus is a powerful web scraping tool built with **Playwright**, **BeautifulSoup**, and **spaCy**. It allows for the extraction of web data using **custom CSS selectors** and **recursive crawling**. This project is designed to help you build datasets for HR chatbots or other automation tools by extracting job-related information and filtering it using NLP techniques.

---

## Features
- **Recursive Web Scraping**: Crawl multiple pages and follow links.
- **NLP-based Filtering**: Extract relevant job-related content using spaCy.
- **Robust Error Handling**: Handle timeouts, retries, and page closures gracefully.
- **Exponential Backoff**: Retry failed page loads with increasing delays.
- **Parallel Crawling**: (Optional) Enhance scraping performance by loading pages concurrently.

---

## Prerequisites
1. **Python 3.7+**  
   Ensure you have Python installed. You can download it from [python.org](https://www.python.org).

2. **Install Dependencies:**
   Use the following commands to install the required libraries:

   ```bash
   pip install -r requirements.txt
   python -m playwright install
   python -m spacy download en_core_web_sm
