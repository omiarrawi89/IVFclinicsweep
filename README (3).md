# Web Scraper Tool

A Streamlit application for scraping websites using CSS selectors or XPath.

## Features

- Extract data from websites using CSS selectors or basic XPath
- Crawl multiple pages on the same domain
- Multithreaded scraping for better performance
- Export results to CSV
- Detailed error reporting and debugging information

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   streamlit run app.py
   ```

## Deployment

### Local Deployment

```bash
streamlit run app.py
```

### Streamlit Cloud Deployment

1. Push these files to a GitHub repository
2. Connect the repository to Streamlit Cloud at https://streamlit.io/cloud
3. Set the main file path to app.py

### Heroku Deployment

1. Push these files to a GitHub repository
2. Connect the repository to Heroku
3. Deploy the application

## Troubleshooting

If you encounter the "ModuleNotFoundError" for BeautifulSoup or any other dependency:

1. Make sure all dependencies are installed:
   ```
   pip install -r requirements.txt
   ```
2. Check if the package is properly imported in the code
3. For Streamlit Cloud deployment, ensure requirements.txt is in the root directory

## Performance Optimization

The application uses multithreading to improve scraping performance. You can adjust the number of concurrent workers in the sidebar settings.
