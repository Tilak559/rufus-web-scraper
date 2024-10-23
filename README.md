# Rufus Web Scraper

## Overview
Rufus is a powerful web scraping tool built with **Playwright**, **BeautifulSoup**, and **spaCy**. It allows for the extraction of web data using **custom CSS selectors** and **recursive crawling**. This project serves multiple purposes, such as building datasets for HR chatbots or automating data extraction workflows.

This repository contains **two versions**:
1. **`rufus.py` (Basic Web Scraper)**: Extracts data from websites using CSS selectors.
2. **`rufus_rag.py` (Advanced RAG with FAISS Indexing)**: Enhances the scraping capabilities with NLP filtering and FAISS indexing to support **retrieval-augmented generation (RAG)** pipelines.

---

## Features

### Rufus (Basic Scraper)
- **Recursive Web Scraping**: Crawl multiple pages and follow internal links.
- **CSS-based Element Extraction**: Use CSS selectors to target relevant content.
- **Error Handling**: Manage timeouts and retries gracefully.
- **Data Export**: Extracted content saved in `output.json`.

### Rufus_RAG (NLP and FAISS-enhanced Scraper)
- **NLP-based Filtering**: Uses **spaCy** to identify job-related content.
- **FAISS Index Creation**: Generates FAISS indexes for fast retrieval in RAG systems.
- **Exponential Backoff Retries**: Manage retries with increasing delays.
- **Error Handling**: Handles browser closures and navigation issues gracefully.

---

## Prerequisites

1. **Python 3.7+**  
   Make sure Python is installed on your system. You can download it from [python.org](https://www.python.org).

2. **Install Dependencies:**  
   Use the following commands to install all required dependencies.

   ```bash
   pip install -r requirements.txt
   python -m playwright install
   python -m spacy download en_core_web_sm
   ```

---

## Usage

### Running Rufus (Basic Scraper)

```bash
python rufus.py
```

This will extract data from the target website based on CSS selectors and store the results in `output.json`.

### Running Rufus_RAG (Advanced RAG Scraper)

```bash
python rufus_rag.py
```

This version builds a **FAISS index** after scraping and filtering relevant content using **spaCy NLP models**. The index is saved for integration into RAG pipelines.

---

## Project Structure

```
.
├── README.md               # Project documentation
├── rufus.py                # Basic web scraper
├── rufus_rag.py            # RAG-enhanced scraper with FAISS
├── requirements.txt        # Python dependencies
├── output.json             # Example output file
└── .gitignore              # Ignore unnecessary files (e.g., .venv)
```

---

## Handling Errors

- **Timeouts:** Increase timeout values if pages take longer to load.
- **Navigation Issues:** Ensure CSS selectors target the correct elements on the website.
- **FAISS or NLP Errors:** Verify dependencies and models are installed correctly.

---

## Example Use Case: Integrating with a RAG Pipeline

1. **Scrape Relevant Data:** Use `rufus_rag.py` to collect job-related content.
2. **Build FAISS Index:** The scraper generates a FAISS index for fast retrieval.
3. **Query the Index:** Use the FAISS index within your chatbot or RAG-based system to provide contextual responses to user queries.

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## Author

**Tilak Mudgal**  
2024
