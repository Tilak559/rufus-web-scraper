import asyncio
import re
import logging
import json
import spacy
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Load the NLP model
nlp = spacy.load("en_core_web_sm")

class RufusClient:
    def __init__(self, verbose=True, max_retries=3):
        self.verbose = verbose
        self.max_retries = max_retries
        self.all_data = []  # Initialize the data list
        logging.basicConfig(level=logging.INFO)

    async def scrape(self, url, prompt, css_selector, pages=3, timeout=30000):
        """Scrape website data based on user-defined prompts and CSS selectors."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            visited = set()

            try:
                await self._crawl_links(page, url, visited, css_selector, prompt, pages, timeout)
            finally:
                await context.close()  # Ensure the context is closed properly

            return self.filter_data(self.all_data)

    async def _crawl_links(self, page, url, visited, css_selector, prompt, pages, timeout):
        """Recursively crawl pages and extract data."""
        if len(visited) >= pages or url in visited:
            return

        visited.add(url)
        await self._navigate_to_url(page, url, timeout)

        try:
            await self._extract_data_from_page(page, prompt, css_selector, len(visited))
        except PlaywrightTimeoutError as e:
            logging.error(f"TimeoutError on page {len(visited)}: {e}")
            return
        except Exception as e:
            logging.error(f"Error on page {len(visited)}: {type(e).__name__}: {e}")
            return

        links = await page.query_selector_all('a[href]')
        for link in links:
            try:
                next_url = await link.get_attribute('href')
                if next_url and next_url.startswith('http') and next_url not in visited:
                    new_page = await page.context.new_page()
                    try:
                        await new_page.goto(next_url, timeout=timeout)
                        await self._crawl_links(new_page, next_url, visited, css_selector, prompt, pages, timeout)
                    finally:
                        await new_page.close()  # Close new pages after processing
            except PlaywrightTimeoutError as e:
                logging.error(f"TimeoutError while fetching link: {e}")
            except Exception as e:
                logging.error(f"Unexpected error while fetching link: {type(e).__name__}: {e}")

    async def _navigate_to_url(self, page, url, timeout):
        """Navigate to the given URL with retries and backoff."""
        for attempt in range(self.max_retries):
            try:
                await page.goto(url, timeout=timeout)
                await page.wait_for_load_state('networkidle')
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(3000)
                return
            except PlaywrightTimeoutError:
                logging.error(f"Timeout navigating to {url}, retrying... ({attempt + 1}/{self.max_retries})")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logging.error(f"Unexpected error during navigation: {type(e).__name__}: {e}")
                return

        logging.error("Failed to load the page after multiple retries.")

    async def _extract_data_from_page(self, page, prompt, css_selector, page_num):
        """Extract data from the page using BeautifulSoup."""
        await page.wait_for_selector(css_selector, timeout=30000)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        elements = soup.select(css_selector)

        for element in elements:
            text_content = element.get_text(strip=True)
            logging.info(f"Extracted text content: {text_content}")

            structured_data = {
                "prompt": prompt,
                "page": page_num,
                "content": re.sub(r'\s+', ' ', text_content)
            }
            self.all_data.append(structured_data)

    def filter_data(self, data):
        """Filter relevant content."""
        keywords = ["job", "employment", "career", "internship", "fellowship"]
        filtered_data = []

        seen = set()
        for item in data:
            content = item["content"].lower()
            if self._is_relevant(content, keywords) and content not in seen:
                filtered_data.append(item)
                seen.add(content)

        return filtered_data

    def _is_relevant(self, text, keywords):
        """Check if the content is relevant using NLP."""
        doc = nlp(text)
        return any(token.lemma_ in keywords for token in doc)

    def save_to_json(self, data, filename="output.json"):
        """Save the extracted data to a JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Data saved to {filename}")

class RufusAPI:
    def __init__(self):
        self.client = RufusClient()

    def scrape(self, url, prompt, css_selector, pages=3):
        """Scrape data using the RufusClient."""
        return asyncio.run(self.client.scrape(url, prompt, css_selector, pages))

if __name__ == "__main__":
    api = RufusAPI()

    url = "https://sf.gov/"
    css_selector = ".sfgov-container-item a[href*='/topics/jobs'], .sfgov-container-item p"
    prompt = "We're making a chatbot for the HR in San Francisco."

    scraped_data = api.scrape(url, prompt, css_selector, pages=3)
    api.client.save_to_json(scraped_data)
