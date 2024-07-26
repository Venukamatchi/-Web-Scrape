import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tenacity import retry, wait_exponential, stop_after_attempt
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from colorama import init, Fore, Style

init(autoreset=True)
banner = f"""
{Fore.RED}{Style.BRIGHT}                                      
██    ██ ███████ ███    ██ ██    ██ ██   ██  █████  ███    ███  █████  ████████  ██████ ██   ██ ██ 
██    ██ ██      ████   ██ ██    ██ ██  ██  ██   ██ ████  ████ ██   ██    ██    ██      ██   ██ ██ 
██    ██ █████   ██ ██  ██ ██    ██ █████   ███████ ██ ████ ██ ███████    ██    ██      ███████ ██ 
 ██  ██  ██      ██  ██ ██ ██    ██ ██  ██  ██   ██ ██  ██  ██ ██   ██    ██    ██      ██   ██ ██ 
  ████   ███████ ██   ████  ██████  ██   ██ ██   ██ ██      ██ ██   ██    ██     ██████ ██   ██ ██ 
                                                                                                   
                                                                                                                                                     
"""
print(banner)


# Configure logging
import json_log_formatter
formatter = json_log_formatter.JSONFormatter()
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Database setup
Base = declarative_base()

class WebData(Base):
    __tablename__ = 'webdata'
    url = Column(String, primary_key=True)
    title = Column(String)
    meta_description = Column(String)
    headings = Column(Text)

engine = create_engine('sqlite:///webdata.db')

# Ensure the table schema is created or recreated
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# Asynchronous HTTP requests
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
async def fetch(session, url):
    """Fetch static content from a URL."""
    try:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            logging.info(f"Fetched static content from {url}")
            return await response.text()
    except aiohttp.ClientError as e:
        logging.error(f"ClientError fetching {url}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching {url}: {e}")
        return None

async def fetch_all(urls):
    """Fetch static and dynamic content from URLs."""
    async with aiohttp.ClientSession() as session:
        static_tasks = [fetch(session, url) for url in urls]
        static_results = await asyncio.gather(*static_tasks)

        with ThreadPoolExecutor() as executor:
            dynamic_results = await asyncio.get_event_loop().run_in_executor(
                executor, lambda: [fetch_dynamic_content(url) for url in urls]
            )
        return static_results, dynamic_results

# Parse HTML content
def parse(html):
    """Extract the title, meta description, and headings from HTML content."""
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.select_one('title').text if soup.select_one('title') else 'No Title'
        meta_description = soup.select_one('meta[name="description"]')['content'] if soup.select_one('meta[name="description"]') else 'No Meta Description'
        headings = ', '.join([heading.text for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])])
        return title, meta_description, headings
    return 'Failed to parse', '', ''

# Handle dynamic content with Selenium
def fetch_dynamic_content(url):
    """Fetch dynamic content from a URL using Selenium."""
    try:
        options = Options()
        options.headless = True
        service = Service('/usr/local/bin/geckodriver')  # Adjust path if needed
        driver = webdriver.Firefox(service=service, options=options)
        driver.set_page_load_timeout(10)
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))  # Adjust selector if needed
        )
        content = driver.page_source
        driver.quit()
        logging.info(f"Fetched dynamic content from {url}")
        return content
    except Exception as e:
        logging.error(f"Error fetching dynamic content from {url}: {e}")
        return None

# Store data in SQLite using SQLAlchemy
def store_data(data):
    """Store data in the SQLite database."""
    try:
        for url, title, meta_description, headings in data:
            webdata = WebData(url=url, title=title, meta_description=meta_description, headings=headings)
            session.merge(webdata)
        session.commit()
        logging.info("Data stored in SQLite database")
    except Exception as e:
        logging.error(f"Database error: {e}")

# Compare static and dynamic content
def compare_content(static_data, dynamic_data):
    """Compare static and dynamic content to find differences."""
    differences = []
    
    # Convert static_data to a dictionary with URL as the key and data as the value
    static_data_dict = {url: (title, meta_description, headings) for url, title, meta_description, headings in static_data}
    
    for dynamic_url, dynamic_title, dynamic_meta_description, dynamic_headings in dynamic_data:
        static_title, static_meta_description, static_headings = static_data_dict.get(dynamic_url, ('', '', ''))
        if (static_title and static_title != dynamic_title) or (static_meta_description and static_meta_description != dynamic_meta_description) or (static_headings and static_headings != dynamic_headings):
            differences.append((dynamic_url, static_title, dynamic_title, static_meta_description, dynamic_meta_description, static_headings, dynamic_headings))
    
    return differences

# Send notification
def send_notification(differences):
    """Send notification email if differences are detected."""
    if differences:
        sender = 'your_email@example.com'
        receiver = 'recipient@example.com'
        subject = 'Content Differences Detected'
        body = f"Differences detected:\n\n{json.dumps(differences, indent=4)}"

        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP('smtp.example.com', 587) as server:
                server.starttls()
                server.login('your_email@example.com', 'your_password')
                server.sendmail(sender, receiver, msg.as_string())
                logging.info("Notification email sent")
        except Exception as e:
            logging.error(f"Failed to send email: {e}")

# Main execution
def run(urls, config):
    """Main function to run the web scraping process."""
    loop = asyncio.get_event_loop()
    static_pages, dynamic_pages = loop.run_until_complete(fetch_all(urls))

    static_data = [(url, *parse(page)) for url, page in zip(urls, static_pages)]
    logging.info("Completed static content fetching")

    dynamic_data = []
    for url, dynamic_page in zip(urls, dynamic_pages):
        if dynamic_page:
            dynamic_data.append((url, *parse(dynamic_page)))

    logging.info("Completed dynamic content fetching")

    differences = compare_content(static_data, dynamic_data)
    if differences:
        logging.info("Content differences detected:")
        for url, static_title, dynamic_title, static_meta_description, dynamic_meta_description, static_headings, dynamic_headings in differences:
            logging.info(f"{url} - Static: {static_title}, Dynamic: {dynamic_title}\nMeta Description - Static: {static_meta_description}, Dynamic: {dynamic_meta_description}\nHeadings - Static: {static_headings}, Dynamic: {dynamic_headings}")
        send_notification(differences)
    else:
        logging.info("No content differences detected")

    dynamic_data_with_content = [(url, title, meta_description, headings) for url, title, meta_description, headings in dynamic_data]
    store_data(static_data + dynamic_data_with_content)

    # Output results
    results = {
        "static_data": static_data,
        "dynamic_data": dynamic_data,
        "differences": differences
    }
    print(json.dumps(results, indent=4))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Web scraper script for fetching and comparing content.')
    parser.add_argument('urls', metavar='URL', type=str, nargs='+', help='URLs to scrape')
    parser.add_argument('--config', type=str, help='Path to configuration JSON file')
    args = parser.parse_args()

    urls = args.urls
    config = {}

    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load configuration file: {e}")

    if not urls:
        parser.print_help()
        print("No URLs provided.")
    else:
        run(urls, config)
