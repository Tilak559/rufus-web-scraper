import asyncio
import re
import logging
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Initialize SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

class RufusClient:
    def __init__(self, verbose=True, max_retries=3):
        self.verbose = verbose
        self.max_retries = max_retries
        self.all_data = []
        logging.basicConfig(level=logging.INFO)

    async def scrape(self, url, prompt, css_selector, pages=3, timeout=30000):
        """Main scraping function."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            try:
                page = await context.new_page()
                visited = set()
                await self._crawl_links(page, url, visited, css_selector, prompt, pages, timeout)
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
            finally:
                await context.close()

            return self.filter_data(self.all_data)

    async def _crawl_links(self, page, url, visited, css_selector, prompt, pages, timeout):
        """Recursively crawl pages."""
        if len(visited) >= pages or url in visited:
            return  # Stop if limit reached or already visited

        visited.add(url)
        await self._navigate_to_url(page, url, timeout)

        try:
            await self._extract_data_from_page(page, prompt, css_selector, len(visited))
        except PlaywrightTimeoutError as e:
            logging.error(f"TimeoutError on page {len(visited)}: {e}")
        except Exception as e:
            logging.error(f"Error on page {len(visited)}: {e}")

        links = await page.query_selector_all('a[href]')
        for link in links:
            next_url = await self._get_link_href(link)
            if next_url and next_url.startswith('http') and next_url not in visited:
                await self._retry_navigation(page, next_url, visited, css_selector, prompt, pages, timeout)

    async def _navigate_to_url(self, page, url, timeout):
        """Navigate to a URL with retries."""
        for attempt in range(self.max_retries):
            try:
                await page.goto(url, timeout=timeout)
                await page.wait_for_load_state('networkidle')
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(3000)  # Allow lazy loading to complete
                return
            except PlaywrightTimeoutError:
                logging.warning(f"Timeout navigating to {url}, retrying ({attempt + 1}/{self.max_retries})...")
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logging.error(f"Unexpected error during navigation: {e}")
                return

        logging.error(f"Failed to load {url} after multiple retries.")

    async def _retry_navigation(self, page, next_url, visited, css_selector, prompt, pages, timeout):
        """Retry navigation to handle transient issues."""
        for attempt in range(3):
            try:
                await page.goto(next_url, timeout=timeout)
                await page.wait_for_load_state('networkidle')
                await self._crawl_links(page, next_url, visited, css_selector, prompt, pages, timeout)
                break  # Success, exit retry loop
            except PlaywrightTimeoutError:
                logging.warning(f"Retry {attempt + 1}: Timeout navigating to {next_url}")
                await asyncio.sleep(2)
            except Exception as e:
                logging.error(f"Retry {attempt + 1}: Error navigating to {next_url}: {e}")

    async def _get_link_href(self, link):
        """Safely get the href attribute of a link."""
        try:
            return await link.get_attribute('href')
        except Exception as e:
            logging.error(f"Error while fetching link: {e}")
            return None

    async def _extract_data_from_page(self, page, prompt, css_selector, page_num):
        """Extract and structure content from the page."""
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
        """Filter relevant job-related content."""
        keywords = ["job", "employment", "career", "internship", "fellowship"]
        filtered_data = [item for item in data if any(keyword in item['content'].lower() for keyword in keywords)]
        return filtered_data

    def save_to_json(self, data, filename="output.json"):
        """Save data to a JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Data saved to {filename}")

class RufusAPI:
    def __init__(self):
        self.client = RufusClient()

    def scrape(self, url, prompt, css_selector, pages=3):
        """Run the scraping process."""
        return asyncio.run(self.client.scrape(url, prompt, css_selector, pages))

    def generate_embeddings(self, data):
        """Convert content to vector embeddings."""
        return [model.encode(item['content']) for item in data]

    def create_faiss_index(self, embeddings):
        """Create and save a FAISS index."""
        dimension = len(embeddings[0])
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(embeddings))
        faiss.write_index(index, "rufus_index.faiss")
        logging.info("FAISS index created and saved.")

if __name__ == "__main__":
    api = RufusAPI()

    # Set scraping parameters
    url = "https://sf.gov/"
    css_selector = ".sfgov-container-item a[href*='/topics/jobs'], .sfgov-container-item p"
    prompt = "We're making a chatbot for the HR in San Francisco."

    # Scrape data and save to JSON
    scraped_data = api.scrape(url, prompt, css_selector, pages=3)
    api.client.save_to_json(scraped_data)

    # Generate embeddings and create FAISS index
    embeddings = api.generate_embeddings(scraped_data)
    api.create_faiss_index(embeddings)
