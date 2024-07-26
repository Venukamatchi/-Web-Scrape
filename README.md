# Web-Scraper
A powerful tool for evaluating and comparing web data, combining static HTML scraping with static and dynamic content fetching and analysis.

## Features

- Fetch static content asynchronously using `aiohttp`.
- Fetch dynamic content with Selenium.
- Parse HTML to extract titles, meta descriptions, and headings.
- Store data in an SQLite database.
- Compare static and dynamic content for discrepancies.
- Send email notifications if differences are detected.

## Requirements

- Python 3.7 or higher
- Required Python packages (see `requirements.txt` for details)
- GeckoDriver for Selenium (Firefox WebDriver)
- `aiohttp`
- `beautifulsoup4`
- `sqlalchemy`
- `selenium`
- `tenacity`
- `json-log-formatter`

## Step-by-Step Instructions

### Download GeckoDriver

Navigate to a directory where you want to download and extract geckodriver:

```bash
wget https://github.com/mozilla/geckodriver/releases/download/v0.32.0/geckodriver-v0.32.0-linux64.tar.gz
```
### Extract the Tarball

Extract the downloaded tarball:

```bash
tar -xvzf geckodriver-v0.32.0-linux64.tar.gz
```

### Move GeckoDriver to /usr/local/bin/

Move the geckodriver binary to a directory included in your PATH:

```bash
sudo mv geckodriver /usr/local/bin/
```

### Verify the Installation

Verify that geckodriver is in the correct directory and is executable:

```bash
which geckodriver

```
This should output /usr/local/bin/geckodriver.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/VEXMAN-hacks/Web-Scraper.git
   cd WebScraper
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use "venv\Scripts\activate"
   ```

# Run the script:

```bash
python scraper.py <url1> <url2> ... 
```

## Output
![WhatsApp Image 2024-07-27 at 00 16 32_781f98f9](https://github.com/user-attachments/assets/8cc43d2a-3340-4df6-b0de-4fb416dfe2cc)

- static_data: Data fetched from static HTML content.
- dynamic_data: Data fetched from dynamic content.
- differences: List of differences between static and dynamic content.

## License

**This project is licensed under the MIT License. See the LICENSE file for details.
Contributing**

For bug reports or feature requests, please open an issue.
Contact

For any questions or feedback, you can reach out to www.linkedin.com/in/venukamatchi-p




