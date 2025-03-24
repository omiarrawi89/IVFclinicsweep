
# Web Scraper Tool - Optimized for performance
import sys
import traceback
import concurrent.futures
import time
import re
import os
from urllib.parse import urlparse, urljoin

# Function to check if required packages are installed
def check_dependencies():
    required_packages = {
        'streamlit': 'streamlit',
        'requests': 'requests',
        'bs4': 'beautifulsoup4',
        'pandas': 'pandas'
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"Error: Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install " + " ".join(missing_packages))
        sys.exit(1)

# Check dependencies before importing
check_dependencies()

# Now import all required packages
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Set page configuration
st.set_page_config(
    page_title="Web Scraper Tool",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to check if a URL is valid
def is_valid_url(url):
    """Check if the URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

# Function to get all links from a webpage
def get_all_links(url, base_domain):
    """Extract all links from a webpage that belong to the same domain."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(url, href)
            
            # Only include links from the same domain
            if urlparse(full_url).netloc == base_domain:
                links.append(full_url)
                
        return list(set(links))  # Remove duplicates
    except Exception as e:
        st.error(f"Error getting links from {url}: {str(e)}")
        return []

# Function to parse XPath expressions
def parse_xpath(xpath):
    """Very basic XPath-like parser (only handles simple cases)."""
    match = re.match(r'//(\w+)(?:\[@(\w+)="([^"]+)"\])?', xpath)
    if match:
        tag = match.group(1)
        if match.group(2) and match.group(3):
            attrs = {match.group(2): match.group(3)}
        else:
            attrs = {}
        return tag, attrs
    return 'div', {}  # Default fallback

# Function to extract data from a webpage
def extract_data(url, selectors):
    """Extract data from a webpage based on CSS selectors."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return {selector: "N/A" for selector in selectors}, f"Error: HTTP {response.status_code}"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = {}
        
        for selector_name, selector_info in selectors.items():
            selector_type = selector_info.get('type', 'css')
            selector_value = selector_info.get('value', '')
            
            if selector_type == 'css':
                elements = soup.select(selector_value)
            elif selector_type == 'xpath':
                # Basic XPath-like functionality
                tag, attrs = parse_xpath(selector_value)
                elements = soup.find_all(tag, attrs)
            else:
                elements = []
            
            if elements:
                results[selector_name] = elements[0].get_text(strip=True)
            else:
                results[selector_name] = "N/A"
                
        return results, None
    
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        return {selector: "N/A" for selector in selectors}, error_msg

# Function to scrape a website with multithreading for better performance
def scrape_website(start_url, selectors, max_pages=10, crawl_same_domain=False):
    """Scrape data from a website using multithreading for better performance."""
    if not is_valid_url(start_url):
        return pd.DataFrame(), "Invalid URL provided"
    
    all_data = []
    visited_urls = set()
    urls_to_visit = [start_url]
    base_domain = urlparse(start_url).netloc
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    error_log = []
    
    try:
        # First, collect all URLs to visit if crawling is enabled
        if crawl_same_domain:
            status_text.text("Collecting URLs to crawl...")
            new_links = get_all_links(start_url, base_domain)
            for link in new_links:
                if link not in urls_to_visit:
                    urls_to_visit.append(link)
        
        # Limit to max_pages
        urls_to_visit = urls_to_visit[:max_pages]
        total_urls = len(urls_to_visit)
        
        status_text.text(f"Found {total_urls} URLs to scrape")
        
        # Use ThreadPoolExecutor for parallel scraping
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all scraping tasks
            future_to_url = {
                executor.submit(extract_data, url, selectors): url 
                for url in urls_to_visit
            }
            
            # Process results as they complete
            for i, future in enumerate(concurrent.futures.as_completed(future_to_url)):
                url = future_to_url[future]
                visited_urls.add(url)
                
                try:
                    data, error = future.result()
                    if error:
                        error_log.append(f"Error on {url}: {error}")
                    
                    data['url'] = url
                    all_data.append(data)
                    
                    # Update progress
                    progress = (i + 1) / total_urls
                    progress_bar.progress(progress)
                    status_text.text(f"Scraped {i+1}/{total_urls} pages")
                    
                except Exception as e:
                    error_log.append(f"Error processing {url}: {str(e)}")
    
    except Exception as e:
        error_msg = f"Error during scraping: {str(e)}"
        if error_log:
            error_msg += f"\nAdditional errors: {', '.join(error_log)}"
        return pd.DataFrame(all_data), error_msg
    
    result_msg = f"Successfully scraped {len(all_data)} pages"
    if error_log:
        result_msg += f"\nWarnings: {len(error_log)} pages had errors"
    
    return pd.DataFrame(all_data), result_msg

# Main app function
def main():
    try:
        st.title("Web Scraper Tool")
        st.write("Extract information from websites and save to CSV")
        
        # Sidebar for settings and debug info
        with st.sidebar:
            st.header("About")
            st.write("This tool allows you to extract data from websites using CSS selectors or XPath.")
            
            st.header("Debug Information")
            st.write(f"**Python:** {sys.version}")
            st.write(f"**Streamlit:** {st.__version__}")
            st.write(f"**Requests:** {requests.__version__}")
            st.write(f"**BeautifulSoup:** {BeautifulSoup.__version__}")
            st.write(f"**Pandas:** {pd.__version__}")
            
            st.header("Performance Settings")
            max_workers = st.slider("Max concurrent requests", 1, 10, 5)
            timeout = st.slider("Request timeout (seconds)", 1, 30, 5)
        
        # Main form
        with st.form("scraper_form"):
            start_url = st.text_input("Starting URL", "https://example.com")
            
            st.subheader("Define what to extract")
            st.write("Add selectors for the data you want to extract (CSS selectors or basic XPath)")
            
            # Dynamic selector fields
            num_selectors = st.number_input("Number of data fields to extract", min_value=1, max_value=10, value=3)
            
            selectors = {}
            for i in range(num_selectors):
                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    field_name = st.text_input(f"Field name #{i+1}", f"field_{i+1}")
                with col2:
                    selector_value = st.text_input(f"CSS Selector #{i+1}", f"h1" if i==0 else f"p:nth-of-type({i})")
                with col3:
                    selector_type = st.selectbox(f"Type #{i+1}", ["css", "xpath"], key=f"type_{i}")
                
                selectors[field_name] = {"type": selector_type, "value": selector_value}
            
            max_pages = st.number_input("Maximum pages to scrape", min_value=1, max_value=100, value=10)
            crawl_same_domain = st.checkbox("Crawl links on the same domain", value=False)
            
            submitted = st.form_submit_button("Start Scraping")
        
        if submitted:
            st.subheader("Scraping Results")
            
            with st.spinner("Scraping in progress..."):
                df, message = scrape_website(start_url, selectors, max_pages, crawl_same_domain)
            
            st.write(message)
            
            if not df.empty:
                st.dataframe(df)
                
                # Save to CSV
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="scraped_data.csv",
                    mime="text/csv"
                )
        
        st.markdown("""
        ### Instructions:
        1. Enter the URL of the website you want to scrape
        2. Define the data fields you want to extract using CSS selectors or basic XPath
           - CSS selector examples: `h1`, `.classname`, `#idname`, `table tr td:first-child`
           - XPath examples: `//h1`, `//div[@class="content"]`
        3. Set the maximum number of pages to scrape
        4. Enable crawling if you want to follow links on the same domain
        5. Click "Start Scraping"
        
        If the requested information is not found, "N/A" will be displayed.
        """)
    
    except Exception as e:
        st.error("An error occurred in the application")
        st.error(f"Error details: {str(e)}")
        st.code(traceback.format_exc())
        
        st.subheader("Troubleshooting")
        st.write("""
        If you're seeing this error, try the following:
        1. Check your internet connection
        2. Make sure all dependencies are installed: `pip install -r requirements.txt`
        3. Try with a different URL
        4. If the issue persists, please report it with the error details above
        """)

# Run the app
if __name__ == "__main__":
    main()
