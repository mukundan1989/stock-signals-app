import streamlit as st
import http.client
import json
import time
import csv
import os
import pandas as pd
from datetime import datetime, date
import shutil
import platform
import concurrent.futures
from queue import Queue
from typing import List, Dict, Any, Tuple, Set
import re
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline
import warnings
warnings.filterwarnings("ignore")

# Required packages for this enhanced version:
# pip install beautifulsoup4 vaderSentiment transformers torch streamlit pandas

# Default paths based on OS
def get_default_output_dir():
    system = platform.system()
    if system == "Windows":
        return os.path.join(os.path.expanduser("~"), "Documents", "NewsData")
    elif system == "Darwin":  # macOS
        return os.path.join(os.path.expanduser("~"), "Documents", "NewsData")
    else:  # Linux and others
        return os.path.join(os.path.expanduser("~"), "NewsData")

# Get previous month's date range
def get_previous_month_range():
    today = date.today()
    if today.month == 1:
        prev_month = 12
        year = today.year - 1
    else:
        prev_month = today.month - 1
        year = today.year
    
    first_day = date(year, prev_month, 1)
    import calendar
    _, last_day_num = calendar.monthrange(year, prev_month)
    last_day = date(year, prev_month, last_day_num)
    
    return first_day, last_day

# Configuration
API_HOST_SEEKING_ALPHA = "seeking-alpha.p.rapidapi.com"
API_HOST_GPT = "gpt-4o.p.rapidapi.com"
DEFAULT_API_KEY = "4eab47a1bfmsh51c8a20cf14a71fp13947bjsnbff888983296"
SYMBOL_FILE = "data/symbollist.txt"
MAX_WORKERS = 4
ARTICLES_PER_REQUEST = 40  # Max from API

# Initialize sentiment analyzer and summarizer
@st.cache_resource
def load_sentiment_analyzer():
    return SentimentIntensityAnalyzer()

@st.cache_resource  
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn")

# Initialize session state
if "output_dir" not in st.session_state:
    st.session_state["output_dir"] = get_default_output_dir()
if "directories" not in st.session_state:
    st.session_state["directories"] = {}
if "status_table" not in st.session_state:
    st.session_state["status_table"] = []
if "process_status" not in st.session_state:
    st.session_state["process_status"] = []
if "failed_symbols" not in st.session_state:
    st.session_state["failed_symbols"] = set()
if "completed_symbols" not in st.session_state:
    st.session_state["completed_symbols"] = set()
if "api_keys" not in st.session_state:
    st.session_state["api_keys"] = []
if "ids_fetched" not in st.session_state:
    st.session_state["ids_fetched"] = False
if "content_fetched" not in st.session_state:
    st.session_state["content_fetched"] = False
if "content_cleaned" not in st.session_state:
    st.session_state["content_cleaned"] = False
if "python_sentiment_done" not in st.session_state:
    st.session_state["python_sentiment_done"] = False
if "content_summarized" not in st.session_state:
    st.session_state["content_summarized"] = False
if "chatgpt_sentiment_done" not in st.session_state:
    st.session_state["chatgpt_sentiment_done"] = False
if "collected_article_summary" not in st.session_state:
    st.session_state["collected_article_summary"] = {}
if "chatgpt_api_keys" not in st.session_state:
    st.session_state["chatgpt_api_keys"] = []
if "failed_keywords" not in st.session_state:
    st.session_state["failed_keywords"] = []

# UI
st.title("News Data Fetcher - Seeking Alpha")
st.write("Fetch news articles for symbols and their content using Seeking Alpha API.")

# Output directory configuration
st.session_state["output_dir"] = st.text_input(
    "Output Directory",
    value=st.session_state["output_dir"],
    help="Directory where all files will be saved"
)

def ensure_directories():
    """Create necessary directories"""
    try:
        os.makedirs(st.session_state["output_dir"], exist_ok=True)
        dirs = {
            "main": st.session_state["output_dir"],
            "symbol_json": os.path.join(st.session_state["output_dir"], "symbol_json"),
            "symbol_csv": os.path.join(st.session_state["output_dir"], "symbol_csv"),
            "final_output": os.path.join(st.session_state["output_dir"], "final_output"),
            "logs": os.path.join(st.session_state["output_dir"], "logs")
        }
        for dir_name, dir_path in dirs.items():
            os.makedirs(dir_path, exist_ok=True)
            if not os.path.exists(dir_path):
                raise Exception(f"Failed to create directory: {dir_path}")
        return dirs
    except Exception as e:
        st.error(f"Error creating directories: {e}")
        return {}

st.session_state["directories"] = ensure_directories()
dirs = st.session_state["directories"]

def fetch_article_ids_for_symbol(symbol, since_timestamp, until_timestamp, api_key):
    """Fetch all article IDs for a symbol with pagination"""
    try:
        conn = http.client.HTTPSConnection(API_HOST_SEEKING_ALPHA)
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': API_HOST_SEEKING_ALPHA
        }
        
        all_articles = []
        seen_ids = set()
        page = 1
        
        while True:
            try:
                endpoint = f"/news/v2/list-by-symbol?size={ARTICLES_PER_REQUEST}&number={page}&id={symbol}&since={since_timestamp}&until={until_timestamp}"
                conn.request("GET", endpoint, headers=headers)
                res = conn.getresponse()
                data_bytes = res.read()
                
                if not data_bytes:
                    break
                
                data = json.loads(data_bytes.decode("utf-8"))
                
                if not data.get('data') or len(data['data']) == 0:
                    break
                
                # Process articles and deduplicate
                new_articles_count = 0
                for article in data['data']:
                    article_id = article.get('id')
                    if article_id and article_id not in seen_ids:
                        seen_ids.add(article_id)
                        all_articles.append({
                            'id': article_id,
                            'title': article['attributes'].get('title', ''),
                            'publish_date': article['attributes'].get('publishOn', ''),
                            'author_id': article['relationships']['author']['data'].get('id', ''),
                            'comment_count': article['attributes'].get('commentCount', 0),
                            'symbol': symbol
                        })
                        new_articles_count += 1
                
                if new_articles_count == 0:
                    break
                    
                page += 1
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                return {"articles": all_articles, "error": f"Error on page {page}: {e}"}
        
        conn.close()
        return {"articles": all_articles, "error": None}
        
    except Exception as e:
        return {"articles": [], "error": str(e)}

def fetch_article_content(article_id, api_key):
    """Fetch content for a specific article ID"""
    try:
        conn = http.client.HTTPSConnection(API_HOST_SEEKING_ALPHA)
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': API_HOST_SEEKING_ALPHA
        }
        
        endpoint = f"/news/get-details?id={article_id}"
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data_bytes = res.read()
        conn.close()
        
        if not data_bytes:
            return {"content": "", "error": "Empty response"}
        
        data = json.loads(data_bytes.decode("utf-8"))
        
        # Extract content from the response
        content = ""
        if 'data' in data and 'attributes' in data['data']:
            content = data['data']['attributes'].get('content', '')
        
        return {"content": content, "error": None}
        
    except Exception as e:
        return {"content": "", "error": str(e)}

def clean_html_content(html_content):
    """Clean HTML content and extract just the article text"""
    try:
        if not html_content or pd.isna(html_content):
            return ""
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Find content boundaries - stop at "more-link"
        if "more-link" in text.lower():
            text = text.split("more-link")[0]
        
        # Clean up whitespace and formatting
        lines = (line.strip() for line in text.splitlines())
        cleaned_lines = []
        
        for line in lines:
            if line and len(line) > 10:  # Skip very short lines (likely navigation/UI elements)
                # Remove URLs
                line = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', line)
                # Remove email addresses
                line = re.sub(r'\S+@\S+', '', line)
                # Clean extra whitespace
                line = re.sub(r'\s+', ' ', line).strip()
                if line:
                    cleaned_lines.append(line)
        
        # Join and clean final text
        clean_text = ' '.join(cleaned_lines)
        
        # Remove common UI text patterns
        ui_patterns = [
            r'subscribe.*?newsletter', r'sign up.*?alerts', r'follow.*?twitter',
            r'share.*?facebook', r'download.*?app', r'view.*?comments',
            r'read.*?more', r'click.*?here', r'terms.*?service'
        ]
        
        for pattern in ui_patterns:
            clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
        
        # Final cleanup
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text if len(clean_text) > 50 else ""  # Return empty if too short
        
    except Exception as e:
        return f"Error cleaning content: {e}"

def analyze_sentiment_python(text):
    """Analyze sentiment using VADER"""
    try:
        if not text or len(text) < 10:
            return "neutral"
        
        analyzer = load_sentiment_analyzer()
        scores = analyzer.polarity_scores(text)
        
        # Use compound score for classification
        if scores['compound'] >= 0.05:
            return 'positive'
        elif scores['compound'] <= -0.05:
            return 'negative'
        else:
            return 'neutral'
            
    except Exception as e:
        return f"error: {e}"

def summarize_content(text, max_words=150):
    """Summarize content using transformers"""
    try:
        if not text or len(text) < 10:
            return ""
        
        word_count = len(text.split())
        
        # If already short enough, return as-is
        if word_count <= max_words:
            return text
        
        summarizer = load_summarizer()
        
        # Calculate target length for transformer
        # BART works better with character limits
        max_length = min(142, max(50, word_count // 4))  # Leave room for 150 word limit
        min_length = max(30, max_length // 2)
        
        # Split very long text into chunks if needed
        if len(text) > 4000:  # BART has token limits
            text = text[:4000]
        
        summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        summarized_text = summary[0]['summary_text']
        
        # Ensure it's within word limit
        summary_words = summarized_text.split()
        if len(summary_words) > max_words:
            summarized_text = ' '.join(summary_words[:max_words])
        
        return summarized_text
        
    except Exception as e:
        return f"Error summarizing: {e}"

def analyze_sentiment_chatgpt(text, symbol, api_key):
    """Analyze sentiment using ChatGPT"""
    try:
        if not text or len(text) < 10:
            return "neutral"
        
        conn = http.client.HTTPSConnection(API_HOST_GPT)
        
        prompt = f"As a financial analyst, determine the sentiment of this news article about {symbol}. Be objective and avoid positive bias. Respond with only one word: positive, negative, or neutral. Article: {text}"
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 10,
            "temperature": 0
        }
        
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': API_HOST_GPT,
            'Content-Type': "application/json"
        }
        
        conn.request("POST", "/chat/completions", json.dumps(payload), headers)
        res = conn.getresponse()
        data_bytes = res.read()
        conn.close()
        
        if not data_bytes:
            return "error: empty response"
        
        data = json.loads(data_bytes.decode("utf-8"))
        
        if 'choices' in data and len(data['choices']) > 0:
            sentiment = data['choices'][0]['message']['content'].strip().lower()
            
            # Clean response to get just the sentiment word
            sentiment = re.sub(r'[^\w\s]', '', sentiment)
            
            if 'positive' in sentiment:
                return 'positive'
            elif 'negative' in sentiment:
                return 'negative'
            elif 'neutral' in sentiment:
                return 'neutral'
            else:
                return sentiment  # Return raw response if unclear
        else:
            return "error: no response content"
            
    except Exception as e:
        return f"error: {e}"

def compare_sentiments(py_sentiment, gpt_sentiment):
    """Compare Python and ChatGPT sentiments"""
    if py_sentiment in ['positive', 'negative', 'neutral'] and gpt_sentiment in ['positive', 'negative', 'neutral']:
        if py_sentiment == gpt_sentiment:
            return f"agree_{py_sentiment}"
        else:
            return f"disagree_{py_sentiment}_vs_{gpt_sentiment}"
    else:
        return "error_in_comparison"

def process_symbol_ids_worker(worker_id: int, symbols: List[str], since_timestamp, until_timestamp, 
                             api_key: str, status_queue: Queue, result_queue: Queue, output_dirs: dict):
    """Worker to process article ID collection for multiple symbols"""
    try:
        for symbol in symbols:
            status_queue.put(f"Worker {worker_id}: Collecting IDs for {symbol}")
            
            result = fetch_article_ids_for_symbol(symbol, since_timestamp, until_timestamp, api_key)
            
            if result["error"]:
                status_queue.put(f"Worker {worker_id}: ❌ {symbol} failed - {result['error']}")
                add_failure_record("Phase 1 - Article IDs", symbol, symbol, result["error"])
                result_queue.put(("failed", symbol, 0))
            else:
                articles = result["articles"]
                
                if articles:
                    # Save symbol JSON with article IDs
                    symbol_json_path = os.path.join(output_dirs["symbol_json"], f"{symbol.upper()}_ids.json")
                    try:
                        with open(symbol_json_path, "w", encoding="utf-8") as f:
                            json.dump({
                                "symbol": symbol.upper(),
                                "total_articles": len(articles),
                                "date_range": f"{since_timestamp}-{until_timestamp}",
                                "articles": articles
                            }, f, indent=2)
                        
                        status_queue.put(f"Worker {worker_id}: ✅ {symbol} completed - {len(articles)} articles")
                        result_queue.put(("success", symbol, len(articles)))
                    except Exception as e:
                        status_queue.put(f"Worker {worker_id}: ❌ Error saving {symbol}: {e}")
                        result_queue.put(("failed", symbol, 0))
                else:
                    status_queue.put(f"Worker {worker_id}: ⚠️ {symbol} - No articles found")
                    result_queue.put(("success", symbol, 0))
                    
    except Exception as e:
        status_queue.put(f"Worker {worker_id}: Fatal error: {e}")
        for symbol in symbols:
            result_queue.put(("failed", symbol, 0))

def process_content_worker(worker_id: int, article_batch: List[Dict], api_key: str, 
                          status_queue: Queue, result_queue: Queue):
    """Worker to fetch content for multiple articles"""
    try:
        for article in article_batch:
            article_id = article['id']
            symbol = article['symbol']
            
            status_queue.put(f"Worker {worker_id}: Fetching content for {symbol} - Article {article_id}")
            
            result = fetch_article_content(article_id, api_key)
            
            if result["error"]:
                status_queue.put(f"Worker {worker_id}: Content failed for {article_id}: {result['error']}")
                article['content'] = f"Error: {result['error']}"
                article['content_status'] = "failed"
            else:
                article['content'] = result["content"]
                article['content_status'] = "success"
            
            result_queue.put(("article_processed", symbol, article))
            time.sleep(0.5)  # Rate limiting
            
    except Exception as e:
        status_queue.put(f"Worker {worker_id}: Fatal error: {e}")
        for article in article_batch:
            result_queue.put(("article_failed", article['symbol'], article))

def process_content_cleaning_worker(worker_id: int, csv_files: List[str], status_queue: Queue, 
                                   result_queue: Queue, dirs: dict):
    """Worker to clean HTML content from CSV files"""
    try:
        for csv_file in csv_files:
            symbol = csv_file.replace("_news_complete.csv", "")
            csv_path = os.path.join(dirs["symbol_csv"], csv_file)
            
            status_queue.put(f"Worker {worker_id}: Cleaning content for {symbol}")
            
            # Read CSV
            df = pd.read_csv(csv_path, encoding="utf-8")
            
            # Clean HTML content
            extracted_content = []
            for idx, row in df.iterrows():
                content = row.get('Content', '')
                cleaned = clean_html_content(content)
                extracted_content.append(cleaned)
                
                if (idx + 1) % 10 == 0:
                    status_queue.put(f"Worker {worker_id}: {symbol} - Cleaned {idx + 1}/{len(df)} articles")
            
            # Add new column
            df['ExtractedContent'] = extracted_content
            
            # Save updated CSV
            df.to_csv(csv_path, index=False, encoding="utf-8")
            
            status_queue.put(f"Worker {worker_id}: ✅ {symbol} content cleaning completed")
            result_queue.put(("cleaned", symbol, len(df)))
            
    except Exception as e:
        status_queue.put(f"Worker {worker_id}: Error cleaning content: {e}")
        for csv_file in csv_files:
            symbol = csv_file.replace("_news_complete.csv", "")
            result_queue.put(("failed", symbol, 0))

def process_python_sentiment_worker(worker_id: int, csv_files: List[str], status_queue: Queue,
                                   result_queue: Queue, dirs: dict):
    """Worker to analyze sentiment using Python/VADER"""
    try:
        for csv_file in csv_files:
            symbol = csv_file.replace("_news_complete.csv", "")
            csv_path = os.path.join(dirs["symbol_csv"], csv_file)
            
            status_queue.put(f"Worker {worker_id}: Analyzing Python sentiment for {symbol}")
            
            # Read CSV
            df = pd.read_csv(csv_path, encoding="utf-8")
            
            # Analyze sentiment
            py_sentiments = []
            for idx, row in df.iterrows():
                extracted_content = row.get('ExtractedContent', '')
                sentiment = analyze_sentiment_python(extracted_content)
                py_sentiments.append(sentiment)
                
                if (idx + 1) % 10 == 0:
                    status_queue.put(f"Worker {worker_id}: {symbol} - Analyzed {idx + 1}/{len(df)} articles")
            
            # Add new column
            df['PySentiment'] = py_sentiments
            
            # Save updated CSV
            df.to_csv(csv_path, index=False, encoding="utf-8")
            
            status_queue.put(f"Worker {worker_id}: ✅ {symbol} Python sentiment completed")
            result_queue.put(("sentiment_done", symbol, len(df)))
            
    except Exception as e:
        status_queue.put(f"Worker {worker_id}: Error with Python sentiment: {e}")
        for csv_file in csv_files:
            symbol = csv_file.replace("_news_complete.csv", "")
            result_queue.put(("failed", symbol, 0))

def process_summarization_worker(worker_id: int, csv_files: List[str], status_queue: Queue,
                                result_queue: Queue, dirs: dict):
    """Worker to summarize content using transformers"""
    try:
        for csv_file in csv_files:
            symbol = csv_file.replace("_news_complete.csv", "")
            csv_path = os.path.join(dirs["symbol_csv"], csv_file)
            
            status_queue.put(f"Worker {worker_id}: Summarizing content for {symbol}")
            
            # Read CSV
            df = pd.read_csv(csv_path, encoding="utf-8")
            
            # Summarize content
            summaries = []
            for idx, row in df.iterrows():
                extracted_content = row.get('ExtractedContent', '')
                summary = summarize_content(extracted_content)
                summaries.append(summary)
                
                if (idx + 1) % 5 == 0:  # Update less frequently for summarization
                    status_queue.put(f"Worker {worker_id}: {symbol} - Summarized {idx + 1}/{len(df)} articles")
            
            # Add new column
            df['SummarizedContent'] = summaries
            
            # Save updated CSV
            df.to_csv(csv_path, index=False, encoding="utf-8")
            
            status_queue.put(f"Worker {worker_id}: ✅ {symbol} summarization completed")
            result_queue.put(("summarized", symbol, len(df)))
            
    except Exception as e:
        status_queue.put(f"Worker {worker_id}: Error with summarization: {e}")
        for csv_file in csv_files:
            symbol = csv_file.replace("_news_complete.csv", "")
            result_queue.put(("failed", symbol, 0))

def process_chatgpt_sentiment_worker(worker_id: int, csv_files: List[str], api_key: str, 
                                    status_queue: Queue, result_queue: Queue, dirs: dict):
    """Worker to analyze sentiment using ChatGPT"""
    try:
        for csv_file in csv_files:
            symbol = csv_file.replace("_news_complete.csv", "")
            csv_path = os.path.join(dirs["symbol_csv"], csv_file)
            
            status_queue.put(f"Worker {worker_id}: Analyzing ChatGPT sentiment for {symbol}")
            
            # Read CSV
            df = pd.read_csv(csv_path, encoding="utf-8")
            
            # Analyze sentiment with ChatGPT
            gpt_sentiments = []
            comparisons = []
            failed_articles = 0
            
            for idx, row in df.iterrows():
                summarized_content = row.get('SummarizedContent', '')
                py_sentiment = row.get('PySentiment', 'neutral')
                article_id = row.get('ID', f'article_{idx}')
                
                gpt_sentiment = analyze_sentiment_chatgpt(summarized_content, symbol, api_key)
                
                # Track failures with detailed reasons
                if gpt_sentiment.startswith('error:'):
                    add_failure_record("Phase 6 - ChatGPT Sentiment", symbol, f"Article {article_id}", gpt_sentiment)
                    failed_articles += 1
                
                comparison = compare_sentiments(py_sentiment, gpt_sentiment)
                
                gpt_sentiments.append(gpt_sentiment)
                comparisons.append(comparison)
                
                if (idx + 1) % 5 == 0:
                    status_queue.put(f"Worker {worker_id}: {symbol} - GPT analyzed {idx + 1}/{len(df)} articles")
                
                time.sleep(0.5)  # Rate limiting for ChatGPT API
            
            # Add new columns
            df['ChatGPTSentiment'] = gpt_sentiments
            df['SentimentComparison'] = comparisons
            
            # Save final CSV
            df.to_csv(csv_path, index=False, encoding="utf-8")
            
            if failed_articles > 0:
                status_queue.put(f"Worker {worker_id}: ⚠️ {symbol} completed with {failed_articles} ChatGPT failures")
            else:
                status_queue.put(f"Worker {worker_id}: ✅ {symbol} ChatGPT sentiment completed")
            
            result_queue.put(("gpt_sentiment_done", symbol, len(df)))
            
    except Exception as e:
        status_queue.put(f"Worker {worker_id}: Error with ChatGPT sentiment: {e}")
        for csv_file in csv_files:
            symbol = csv_file.replace("_news_complete.csv", "")
            add_failure_record("Phase 6 - ChatGPT Sentiment", symbol, "Entire symbol", str(e))
            result_queue.put(("failed", symbol, 0))

def fetch_article_ids_parallel(symbols, since_timestamp, until_timestamp, api_keys):
    """Phase 1: Collect article IDs for all symbols"""
    if not symbols:
        st.warning("No symbols to process")
        return False
    
    if not api_keys:
        st.error("No API keys provided!")
        return False
    
    # Clear previous data
    for dir_path in [dirs["symbol_json"], dirs["symbol_csv"], dirs["final_output"]]:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        os.makedirs(dir_path, exist_ok=True)
    
    # Reset state
    st.session_state["status_table"] = []
    st.session_state["process_status"] = []
    st.session_state["failed_symbols"] = set()
    st.session_state["completed_symbols"] = set()
    st.session_state["collected_article_summary"] = {}
    
    # Distribute symbols among API keys
    num_workers = min(len(api_keys), len(symbols))
    symbols_per_worker = len(symbols) // num_workers
    symbol_assignments = []
    
    for i in range(num_workers):
        start_idx = i * symbols_per_worker
        if i == num_workers - 1:  # Last worker gets remaining symbols
            end_idx = len(symbols)
        else:
            end_idx = (i + 1) * symbols_per_worker
        symbol_assignments.append(symbols[start_idx:end_idx])
    
    st.write(f"🔄 Starting Phase 1: Collecting article IDs")
    st.write(f"📊 Distribution: {[len(assignment) for assignment in symbol_assignments]} symbols per worker")
    
    # Progress tracking
    total_symbols = len(symbols)
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    # Start workers
    status_queue = Queue()
    result_queue = Queue()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all worker tasks
        futures = []
        for worker_id, (symbol_list, api_key) in enumerate(zip(symbol_assignments, api_keys)):
            if symbol_list:
                future = executor.submit(
                    process_symbol_ids_worker,
                    worker_id + 1,
                    symbol_list,
                    since_timestamp,
                    until_timestamp,
                    api_key,
                    status_queue,
                    result_queue,
                    dirs
                )
                futures.append(future)
        
        # Monitor progress
        completed_symbols = 0
        
        while completed_symbols < total_symbols:
            # Update status
            while not status_queue.empty():
                status_msg = status_queue.get()
                st.session_state["process_status"].append(f"{datetime.now().strftime('%H:%M:%S')} - {status_msg}")
            
            # Check results
            while not result_queue.empty():
                status, symbol, article_count = result_queue.get()
                if status == "success":
                    st.session_state["completed_symbols"].add(symbol)
                    st.session_state["collected_article_summary"][symbol] = article_count
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Status": "✅ IDs Collected",
                        "Articles": article_count
                    })
                else:
                    st.session_state["failed_symbols"].add(symbol)
                    st.session_state["status_table"].append({
                        "Symbol": symbol,
                        "Status": "❌ Failed",
                        "Articles": 0
                    })
                
                completed_symbols += 1
                progress_bar.progress(completed_symbols / total_symbols)
            
            # Update display
            status_container.write(f"Progress: {completed_symbols}/{total_symbols} symbols processed")
            time.sleep(1)
        
        # Wait for all workers to complete
        concurrent.futures.wait(futures)
    
    # Calculate totals
    total_articles = sum(st.session_state["collected_article_summary"].values())
    successful_symbols = len(st.session_state["completed_symbols"])
    failed_symbols = len(st.session_state["failed_symbols"])
    
    st.success(f"✅ Phase 1 Complete! {successful_symbols} symbols processed, {total_articles} articles collected")
    
    return True

def fetch_content_parallel(api_keys):
    """Phase 2: Fetch content for all collected article IDs"""
    # Load all collected articles
    json_files = [f for f in os.listdir(dirs["symbol_json"]) if f.endswith("_ids.json")]
    
    if not json_files:
        st.error("No article IDs found. Please run Phase 1 first.")
        return False
    
    all_articles = []
    symbol_article_map = {}
    
    # Load all articles from JSON files
    for json_file in json_files:
        try:
            with open(os.path.join(dirs["symbol_json"], json_file), "r", encoding="utf-8") as f:
                data = json.load(f)
                symbol = data["symbol"]
                articles = data["articles"]
                
                symbol_article_map[symbol] = []
                for article in articles:
                    article['symbol'] = symbol  # Ensure symbol is in article data
                    all_articles.append(article)
                    symbol_article_map[symbol].append(article)
        except Exception as e:
            st.error(f"Error loading {json_file}: {e}")
    
    if not all_articles:
        st.warning("No articles to process for content fetching")
        return False
    
    st.write(f"🔄 Starting Phase 2: Fetching content for {len(all_articles)} articles")
    
    # Distribute articles among workers
    num_workers = min(len(api_keys), len(all_articles))
    articles_per_worker = len(all_articles) // num_workers
    article_assignments = []
    
    for i in range(num_workers):
        start_idx = i * articles_per_worker
        if i == num_workers - 1:
            end_idx = len(all_articles)
        else:
            end_idx = (i + 1) * articles_per_worker
        article_assignments.append(all_articles[start_idx:end_idx])
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    # Start workers
    status_queue = Queue()
    result_queue = Queue()
    
    # Track processed articles by symbol
    processed_articles = {symbol: [] for symbol in symbol_article_map.keys()}
    total_processed = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all worker tasks
        futures = []
        for worker_id, (article_batch, api_key) in enumerate(zip(article_assignments, api_keys)):
            if article_batch:
                future = executor.submit(
                    process_content_worker,
                    worker_id + 1,
                    article_batch,
                    api_key,
                    status_queue,
                    result_queue
                )
                futures.append(future)
        
        # Monitor progress
        while total_processed < len(all_articles):
            # Update status
            while not status_queue.empty():
                status_msg = status_queue.get()
                st.session_state["process_status"].append(f"{datetime.now().strftime('%H:%M:%S')} - {status_msg}")
            
            # Check results
            while not result_queue.empty():
                result_type, symbol, article = result_queue.get()
                processed_articles[symbol].append(article)
                total_processed += 1
                progress_bar.progress(total_processed / len(all_articles))
            
            # Update display
            status_container.write(f"Content Progress: {total_processed}/{len(all_articles)} articles processed")
            time.sleep(1)
        
        # Wait for all workers to complete
        concurrent.futures.wait(futures)
    
    # Save results to CSV files
    for symbol, articles in processed_articles.items():
        if articles:
            csv_path = os.path.join(dirs["symbol_csv"], f"{symbol}_news_complete.csv")
            
            # Create DataFrame
            records = []
            for article in articles:
                records.append({
                    'ID': article['id'],
                    'Title': article['title'],
                    'Publish_Date': article['publish_date'],
                    'Author_ID': article['author_id'],
                    'Comment_Count': article['comment_count'],
                    'Content': article.get('content', ''),
                    'Content_Status': article.get('content_status', 'unknown'),
                    'Symbol': symbol
                })
            
            df = pd.DataFrame(records)
            df.to_csv(csv_path, index=False, encoding="utf-8")
    
    # Create master CSV
    create_master_csv()
    # Save failed symbols to a file
    if st.session_state["failed_symbols"]:
        failed_path = os.path.join(dirs["final_output"], "Failed_Symbols.txt")
        with open(failed_path, "w", encoding="utf-8") as f:
            f.write("Failed Symbols:\n")
            f.write("==============\n\n")
            for symbol in st.session_state["failed_symbols"]:
                f.write(f"{symbol}\n")
        st.info(f"📝 Saved {len(st.session_state['failed_symbols'])} failed symbols to Failed_Symbols.txt")
    
    st.success(f"✅ Phase 2 Complete! Content fetched for {total_processed} articles")
    return True

def process_content_cleaning_parallel():
    """Phase 3: Clean HTML content from all CSV files"""
    csv_files = [f for f in os.listdir(dirs["symbol_csv"]) if f.endswith("_news_complete.csv")]
    
    if not csv_files:
        st.error("No CSV files found. Please run Phase 2 first.")
        return False
    
    st.write(f"🔄 Starting Phase 3: Cleaning HTML content for {len(csv_files)} symbols")
    
    # Distribute files among workers
    num_workers = min(MAX_WORKERS, len(csv_files))
    files_per_worker = len(csv_files) // num_workers
    file_assignments = []
    
    for i in range(num_workers):
        start_idx = i * files_per_worker
        if i == num_workers - 1:
            end_idx = len(csv_files)
        else:
            end_idx = (i + 1) * files_per_worker
        file_assignments.append(csv_files[start_idx:end_idx])
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    # Start workers
    status_queue = Queue()
    result_queue = Queue()
    
    completed_symbols = 0
    total_symbols = len(csv_files)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for worker_id, file_batch in enumerate(file_assignments):
            if file_batch:
                future = executor.submit(
                    process_content_cleaning_worker,
                    worker_id + 1,
                    file_batch,
                    status_queue,
                    result_queue,
                    dirs
                )
                futures.append(future)
        
        # Monitor progress
        while completed_symbols < total_symbols:
            while not status_queue.empty():
                status_msg = status_queue.get()
                st.session_state["process_status"].append(f"{datetime.now().strftime('%H:%M:%S')} - {status_msg}")
            
            while not result_queue.empty():
                result_type, symbol, count = result_queue.get()
                completed_symbols += 1
                progress_bar.progress(completed_symbols / total_symbols)
            
            status_container.write(f"Cleaning Progress: {completed_symbols}/{total_symbols} symbols processed")
            time.sleep(1)
        
        concurrent.futures.wait(futures)
    
    st.success(f"✅ Phase 3 Complete! Content cleaned for {completed_symbols} symbols")
    return True

def process_python_sentiment_parallel():
    """Phase 4: Analyze sentiment using Python/VADER"""
    csv_files = [f for f in os.listdir(dirs["symbol_csv"]) if f.endswith("_news_complete.csv")]
    
    if not csv_files:
        st.error("No CSV files found. Please run previous phases first.")
        return False
    
    st.write(f"🔄 Starting Phase 4: Python sentiment analysis for {len(csv_files)} symbols")
    
    # Distribute files among workers
    num_workers = min(MAX_WORKERS, len(csv_files))
    files_per_worker = len(csv_files) // num_workers
    file_assignments = []
    
    for i in range(num_workers):
        start_idx = i * files_per_worker
        if i == num_workers - 1:
            end_idx = len(csv_files)
        else:
            end_idx = (i + 1) * files_per_worker
        file_assignments.append(csv_files[start_idx:end_idx])
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    # Start workers
    status_queue = Queue()
    result_queue = Queue()
    
    completed_symbols = 0
    total_symbols = len(csv_files)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for worker_id, file_batch in enumerate(file_assignments):
            if file_batch:
                future = executor.submit(
                    process_python_sentiment_worker,
                    worker_id + 1,
                    file_batch,
                    status_queue,
                    result_queue,
                    dirs
                )
                futures.append(future)
        
        # Monitor progress
        while completed_symbols < total_symbols:
            while not status_queue.empty():
                status_msg = status_queue.get()
                st.session_state["process_status"].append(f"{datetime.now().strftime('%H:%M:%S')} - {status_msg}")
            
            while not result_queue.empty():
                result_type, symbol, count = result_queue.get()
                completed_symbols += 1
                progress_bar.progress(completed_symbols / total_symbols)
            
            status_container.write(f"Python Sentiment Progress: {completed_symbols}/{total_symbols} symbols processed")
            time.sleep(1)
        
        concurrent.futures.wait(futures)
    
    st.success(f"✅ Phase 4 Complete! Python sentiment analyzed for {completed_symbols} symbols")
    return True

def process_summarization_parallel():
    """Phase 5: Summarize content using transformers"""
    csv_files = [f for f in os.listdir(dirs["symbol_csv"]) if f.endswith("_news_complete.csv")]
    
    if not csv_files:
        st.error("No CSV files found. Please run previous phases first.")
        return False
    
    st.write(f"🔄 Starting Phase 5: Content summarization for {len(csv_files)} symbols")
    
    # Distribute files among workers (fewer workers for heavy AI processing)
    num_workers = min(2, len(csv_files))  # Limit workers for transformer models
    files_per_worker = len(csv_files) // num_workers
    file_assignments = []
    
    for i in range(num_workers):
        start_idx = i * files_per_worker
        if i == num_workers - 1:
            end_idx = len(csv_files)
        else:
            end_idx = (i + 1) * files_per_worker
        file_assignments.append(csv_files[start_idx:end_idx])
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    # Start workers
    status_queue = Queue()
    result_queue = Queue()
    
    completed_symbols = 0
    total_symbols = len(csv_files)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for worker_id, file_batch in enumerate(file_assignments):
            if file_batch:
                future = executor.submit(
                    process_summarization_worker,
                    worker_id + 1,
                    file_batch,
                    status_queue,
                    result_queue,
                    dirs
                )
                futures.append(future)
        
        # Monitor progress
        while completed_symbols < total_symbols:
            while not status_queue.empty():
                status_msg = status_queue.get()
                st.session_state["process_status"].append(f"{datetime.now().strftime('%H:%M:%S')} - {status_msg}")
            
            while not result_queue.empty():
                result_type, symbol, count = result_queue.get()
                completed_symbols += 1
                progress_bar.progress(completed_symbols / total_symbols)
            
            status_container.write(f"Summarization Progress: {completed_symbols}/{total_symbols} symbols processed")
            time.sleep(1)
        
        concurrent.futures.wait(futures)
    
    st.success(f"✅ Phase 5 Complete! Content summarized for {completed_symbols} symbols")
    return True

def process_chatgpt_sentiment_parallel(chatgpt_api_keys):
    """Phase 6: Analyze sentiment using ChatGPT"""
    csv_files = [f for f in os.listdir(dirs["symbol_csv"]) if f.endswith("_news_complete.csv")]
    
    if not csv_files:
        st.error("No CSV files found. Please run previous phases first.")
        return False
    
    if not chatgpt_api_keys:
        st.error("No ChatGPT API keys provided! Please enter ChatGPT API keys.")
        return False
    
    st.write(f"🔄 Starting Phase 6: ChatGPT sentiment analysis for {len(csv_files)} symbols")
    st.write(f"🤖 Using {len(chatgpt_api_keys)} ChatGPT API keys")
    
    # Distribute files among available ChatGPT API keys
    num_workers = min(len(chatgpt_api_keys), len(csv_files))
    files_per_worker = len(csv_files) // num_workers
    file_assignments = []
    
    for i in range(num_workers):
        start_idx = i * files_per_worker
        if i == num_workers - 1:
            end_idx = len(csv_files)
        else:
            end_idx = (i + 1) * files_per_worker
        file_assignments.append(csv_files[start_idx:end_idx])
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    # Start workers
    status_queue = Queue()
    result_queue = Queue()
    
    completed_symbols = 0
    total_symbols = len(csv_files)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for worker_id, (file_batch, api_key) in enumerate(zip(file_assignments, chatgpt_api_keys)):
            if file_batch:
                future = executor.submit(
                    process_chatgpt_sentiment_worker,
                    worker_id + 1,
                    file_batch,
                    api_key,
                    status_queue,
                    result_queue,
                    dirs
                )
                futures.append(future)
        
        # Monitor progress
        while completed_symbols < total_symbols:
            while not status_queue.empty():
                status_msg = status_queue.get()
                st.session_state["process_status"].append(f"{datetime.now().strftime('%H:%M:%S')} - {status_msg}")
            
            while not result_queue.empty():
                result_type, symbol, count = result_queue.get()
                completed_symbols += 1
                progress_bar.progress(completed_symbols / total_symbols)
            
            status_container.write(f"ChatGPT Sentiment Progress: {completed_symbols}/{total_symbols} symbols processed")
            time.sleep(1)
        
        concurrent.futures.wait(futures)
    
    # Update master CSV and save failure list after all processing
    create_master_csv()
    save_failed_keywords_list()
    
    st.success(f"✅ Phase 6 Complete! ChatGPT sentiment analyzed for {completed_symbols} symbols")
    return True

def create_master_csv():
    """Create master CSV with all symbols"""
    csv_files = [f for f in os.listdir(dirs["symbol_csv"]) if f.endswith(".csv")]
    
    if not csv_files:
        st.warning("No CSV files to combine")
        return
    
    all_dataframes = []
    
    for csv_file in csv_files:
        try:
            csv_path = os.path.join(dirs["symbol_csv"], csv_file)
            df = pd.read_csv(csv_path, encoding="utf-8")
            if not df.empty:
                all_dataframes.append(df)
        except Exception as e:
            st.error(f"Error reading {csv_file}: {e}")
    
    if all_dataframes:
        master_df = pd.concat(all_dataframes, ignore_index=True)
        master_path = os.path.join(dirs["final_output"], "Master_All_Symbols_News.csv")
        master_df.to_csv(master_path, index=False, encoding="utf-8")
        st.success(f"✅ Created master CSV with {len(master_df)} total articles")

def save_failed_keywords_list():
    """Save detailed list of failed keywords with reasons"""
    if st.session_state["failed_keywords"]:
        failed_path = os.path.join(dirs["final_output"], "Failed_Keywords.txt")
        with open(failed_path, "w", encoding="utf-8") as f:
            f.write("Failed Keywords with Reasons:\n")
            f.write("============================\n\n")
            
            # Group by phase
            phases = {}
            for failure in st.session_state["failed_keywords"]:
                phase = failure["phase"]
                if phase not in phases:
                    phases[phase] = []
                phases[phase].append(failure)
            
            for phase, failures in phases.items():
                f.write(f"Phase {phase}:\n")
                f.write("-" * 40 + "\n")
                for failure in failures:
                    f.write(f"Symbol: {failure['symbol']}\n")
                    f.write(f"Keyword: {failure['keyword']}\n")
                    f.write(f"Reason: {failure['reason']}\n")
                    f.write(f"Timestamp: {failure['timestamp']}\n")
                    f.write("\n")
                f.write("\n")
        
        st.info(f"📝 Saved {len(st.session_state['failed_keywords'])} failed keywords to Failed_Keywords.txt")

def add_failure_record(phase, symbol, keyword, reason):
    """Add a failure record to the tracking list"""
    failure_record = {
        "phase": phase,
        "symbol": symbol,
        "keyword": keyword,
        "reason": reason,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state["failed_keywords"].append(failure_record)

# UI Configuration
col1, col2 = st.columns(2)

with col1:
    from_date = st.date_input("From Date", value=get_previous_month_range()[0])

with col2:
    to_date = st.date_input("To Date", value=get_previous_month_range()[1])

# Convert dates to timestamps
since_timestamp = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_timestamp = int(datetime.combine(to_date, datetime.min.time()).timestamp())

# API Keys input
st.subheader("API Keys Configuration")

col1, col2 = st.columns(2)

with col1:
    st.write("**Seeking Alpha API Keys**")
    api_keys_text = st.text_area(
        "Enter Seeking Alpha API Keys (one per line)",
        help="Enter multiple RapidAPI Seeking Alpha keys, one per line. Symbols will be distributed among these keys.",
        height=100,
        key="seeking_alpha_keys"
    )

    if api_keys_text.strip():
        st.session_state["api_keys"] = [key.strip() for key in api_keys_text.strip().split('\n') if key.strip()]
    else:
        st.session_state["api_keys"] = [DEFAULT_API_KEY] if DEFAULT_API_KEY else []

    st.write(f"📊 **{len(st.session_state['api_keys'])} Seeking Alpha keys configured**")

with col2:
    st.write("**ChatGPT API Keys**")
    chatgpt_keys_text = st.text_area(
        "Enter ChatGPT API Keys (one per line)",
        help="Enter multiple RapidAPI ChatGPT keys, one per line. Used for Phase 6 sentiment analysis.",
        height=100,
        key="chatgpt_keys"
    )

    if chatgpt_keys_text.strip():
        st.session_state["chatgpt_api_keys"] = [key.strip() for key in chatgpt_keys_text.strip().split('\n') if key.strip()]
    else:
        st.session_state["chatgpt_api_keys"] = []

    st.write(f"🤖 **{len(st.session_state['chatgpt_api_keys'])} ChatGPT keys configured**")

# Load symbols
symbols = []
if os.path.exists(SYMBOL_FILE):
    with open(SYMBOL_FILE, "r") as file:
        symbols = [line.strip() for line in file if line.strip()]
else:
    os.makedirs(os.path.dirname(SYMBOL_FILE), exist_ok=True)
    with open(SYMBOL_FILE, "w") as file:
        file.write("AAPL\nMSFT\nGOOGL\nAMZN\nTSLA")
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    st.info(f"Created sample symbols file at {SYMBOL_FILE}")

if symbols:
    st.write(f"📋 **{len(symbols)} symbols loaded from {SYMBOL_FILE}**")
    st.write(f"Symbols: {', '.join(symbols)}")
    
    # Show distribution
    if st.session_state["api_keys"]:
        num_workers = min(len(st.session_state["api_keys"]), len(symbols))
        symbols_per_worker = len(symbols) // num_workers
        remaining = len(symbols) % num_workers
        
        st.write("**Seeking Alpha Work Distribution:**")
        for i in range(num_workers):
            symbols_for_this_worker = symbols_per_worker + (1 if i < remaining else 0)
            st.write(f"- Seeking Alpha Key {i+1}: {symbols_for_this_worker} symbols")
    
    if st.session_state["chatgpt_api_keys"]:
        chatgpt_workers = min(len(st.session_state["chatgpt_api_keys"]), len(symbols))
        symbols_per_chatgpt = len(symbols) // chatgpt_workers
        remaining_chatgpt = len(symbols) % chatgpt_workers
        
        st.write("**ChatGPT Work Distribution (Phase 6):**")
        for i in range(chatgpt_workers):
            symbols_for_this_chatgpt = symbols_per_chatgpt + (1 if i < remaining_chatgpt else 0)
            st.write(f"- ChatGPT Key {i+1}: {symbols_for_this_chatgpt} symbols")

# Main processing button
st.subheader("Data Fetching")

if st.button("🚀 Fetch Complete News Data", type="primary"):
    if from_date <= to_date and symbols and st.session_state["api_keys"]:
        # Phase 1: Fetch Article IDs
        phase1_success = fetch_article_ids_parallel(
            symbols,
            since_timestamp,
            until_timestamp,
            st.session_state["api_keys"]
        )
        
        if phase1_success:
            # Show Phase 1 summary and countdown
            total_articles = sum(st.session_state["collected_article_summary"].values())
            
            st.write("## 📊 Phase 1 Summary:")
            for symbol, count in st.session_state["collected_article_summary"].items():
                st.write(f"- **{symbol}**: {count} articles")
            st.write(f"- **Total**: {total_articles} articles ready for processing")
            
            if total_articles > 0:
                # 15-second countdown with stop option
                countdown_placeholder = st.empty()
                stop_button_placeholder = st.empty()
                
                user_stopped = False
                for i in range(15, 0, -1):
                    countdown_placeholder.info(f"⏱️ Proceeding to Phase 2 (Content Fetching) in {i} seconds...")
                    
                    with stop_button_placeholder:
                        if st.button("🛑 Stop Here (Only Article IDs)", key=f"stop_phase1_{i}"):
                            user_stopped = True
                            break
                    
                    time.sleep(1)
                
                countdown_placeholder.empty()
                stop_button_placeholder.empty()
                
                if user_stopped:
                    st.warning("⏹️ Process stopped by user. Article IDs have been collected.")
                    st.session_state["ids_fetched"] = True
                else:
                    # Phase 2: Fetch Content
                    st.info("🔄 Starting Phase 2: Fetching article content...")
                    phase2_success = fetch_content_parallel(st.session_state["api_keys"])
                    
                    if phase2_success:
                        st.session_state["ids_fetched"] = True
                        st.session_state["content_fetched"] = True
                        
                        # Phase 2 to 3 countdown
                        countdown_placeholder = st.empty()
                        stop_button_placeholder = st.empty()
                        
                        user_stopped = False
                        for i in range(15, 0, -1):
                            countdown_placeholder.info(f"⏱️ Proceeding to Phase 3 (HTML Cleaning) in {i} seconds...")
                            
                            with stop_button_placeholder:
                                if st.button("🛑 Stop Here (Only Raw Content)", key=f"stop_phase2_{i}"):
                                    user_stopped = True
                                    break
                            
                            time.sleep(1)
                        
                        countdown_placeholder.empty()
                        stop_button_placeholder.empty()
                        
                        if user_stopped:
                            st.warning("⏹️ Process stopped by user. Raw content has been fetched.")
                        else:
                            # Phase 3: Clean Content
                            st.info("🔄 Starting Phase 3: Cleaning HTML content...")
                            phase3_success = process_content_cleaning_parallel()
                            
                            if phase3_success:
                                st.session_state["content_cleaned"] = True
                                
                                # Phase 3 to 4 countdown
                                countdown_placeholder = st.empty()
                                stop_button_placeholder = st.empty()
                                
                                user_stopped = False
                                for i in range(15, 0, -1):
                                    countdown_placeholder.info(f"⏱️ Proceeding to Phase 4 (Python Sentiment) in {i} seconds...")
                                    
                                    with stop_button_placeholder:
                                        if st.button("🛑 Stop Here (Only Cleaned Content)", key=f"stop_phase3_{i}"):
                                            user_stopped = True
                                            break
                                    
                                    time.sleep(1)
                                
                                countdown_placeholder.empty()
                                stop_button_placeholder.empty()
                                
                                if user_stopped:
                                    st.warning("⏹️ Process stopped by user. Content has been cleaned.")
                                else:
                                    # Phase 4: Python Sentiment Analysis
                                    st.info("🔄 Starting Phase 4: Python sentiment analysis...")
                                    phase4_success = process_python_sentiment_parallel()
                                    
                                    if phase4_success:
                                        st.session_state["python_sentiment_done"] = True
                                        
                                        # Phase 4 to 5 countdown
                                        countdown_placeholder = st.empty()
                                        stop_button_placeholder = st.empty()
                                        
                                        user_stopped = False
                                        for i in range(15, 0, -1):
                                            countdown_placeholder.info(f"⏱️ Proceeding to Phase 5 (Summarization) in {i} seconds...")
                                            
                                            with stop_button_placeholder:
                                                if st.button("🛑 Stop Here (Only Python Sentiment)", key=f"stop_phase4_{i}"):
                                                    user_stopped = True
                                                    break
                                            
                                            time.sleep(1)
                                        
                                        countdown_placeholder.empty()
                                        stop_button_placeholder.empty()
                                        
                                        if user_stopped:
                                            st.warning("⏹️ Process stopped by user. Python sentiment analysis completed.")
                                        else:
                                            # Phase 5: Summarization
                                            st.info("🔄 Starting Phase 5: Content summarization...")
                                            phase5_success = process_summarization_parallel()
                                            
                                            if phase5_success:
                                                st.session_state["content_summarized"] = True
                                                
                                                # Phase 5 to 6 countdown
                                                countdown_placeholder = st.empty()
                                                stop_button_placeholder = st.empty()
                                                
                                                user_stopped = False
                                                for i in range(15, 0, -1):
                                                    countdown_placeholder.info(f"⏱️ Proceeding to Phase 6 (ChatGPT Sentiment) in {i} seconds...")
                                                    
                                                    with stop_button_placeholder:
                                                        if st.button("🛑 Stop Here (Only Summarized)", key=f"stop_phase5_{i}"):
                                                            user_stopped = True
                                                            break
                                                    
                                                    time.sleep(1)
                                                
                                                countdown_placeholder.empty()
                                                stop_button_placeholder.empty()
                                                
                                                if user_stopped:
                                                    st.warning("⏹️ Process stopped by user. Content summarization completed.")
                                                else:
                                                    # Phase 6: ChatGPT Sentiment Analysis
                                                    st.info("🔄 Starting Phase 6: ChatGPT sentiment analysis...")
                                                    phase6_success = process_chatgpt_sentiment_parallel(st.session_state["chatgpt_api_keys"])
                                                    
                                                    if phase6_success:
                                                        st.session_state["chatgpt_sentiment_done"] = True
                                                        st.balloons()
                                                        st.success("🎉 All 6 phases completed successfully! Complete sentiment analysis pipeline finished.")
            else:
                st.warning("No articles collected. Please check your date range and symbols.")
    else:
        st.warning("⚠️ Please check: valid date range, symbols loaded, and API keys provided!")

# Manual phase buttons (for recovery/testing)
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📋 Fetch IDs Only"):
        if from_date <= to_date and symbols and st.session_state["api_keys"]:
            fetch_article_ids_parallel(symbols, since_timestamp, until_timestamp, st.session_state["api_keys"])

with col2:
    if st.button("📰 Fetch Content Only", disabled=not st.session_state["ids_fetched"]):
        fetch_content_parallel(st.session_state["api_keys"])

with col3:
    if st.button("🗑️ Clear All Data"):
        for dir_path in [dirs["symbol_json"], dirs["symbol_csv"], dirs["final_output"]]:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
            os.makedirs(dir_path, exist_ok=True)
        st.session_state["status_table"] = []
        st.session_state["process_status"] = []
        st.session_state["failed_symbols"] = set()
        st.session_state["completed_symbols"] = set()
        st.session_state["collected_article_summary"] = {}
        st.session_state["ids_fetched"] = False
        st.session_state["content_fetched"] = False
        st.session_state["content_cleaned"] = False
        st.session_state["python_sentiment_done"] = False
        st.session_state["content_summarized"] = False
        st.session_state["chatgpt_sentiment_done"] = False
        st.session_state["failed_keywords"] = []
        st.success("🗑️ All data cleared!")

# Display results
if st.session_state["status_table"]:
    st.subheader("📊 Symbol Processing Status")
    status_df = pd.DataFrame(st.session_state["status_table"])
    st.dataframe(status_df, hide_index=True)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ Successful", len(st.session_state["completed_symbols"]))
    with col2:
        st.metric("❌ Failed", len(st.session_state["failed_symbols"]))
    with col3:
        total_articles = sum([row["Articles"] for row in st.session_state["status_table"] if row["Articles"] > 0])
        st.metric("📰 Total Articles", total_articles)

# Process status
if st.session_state["process_status"]:
    with st.expander("📝 Process Log", expanded=False):
        for status in st.session_state["process_status"][-50:]:
            st.text(status)

# Download section
if os.path.exists(dirs["final_output"]):
    files = os.listdir(dirs["final_output"])
    if files:
        st.subheader("📥 Download Results")
        
        # Master CSV download
        master_file = "Master_All_Symbols_News.csv"
        if master_file in files:
            with open(os.path.join(dirs["final_output"], master_file), "rb") as f:
                st.download_button(
                    label="📊 Download Master CSV (All Symbols)",
                    data=f.read(),
                    file_name=master_file,
                    mime="text/csv",
                    type="primary"
                )
        
        # Individual symbol downloads
        csv_files = [f for f in os.listdir(dirs["symbol_csv"]) if f.endswith(".csv")]
        if csv_files:
            with st.expander("📁 Download Individual Symbol Files"):
                cols = st.columns(3)
                for i, csv_file in enumerate(csv_files):
                    with cols[i % 3]:
                        symbol_name = csv_file.replace("_news_complete.csv", "")
                        with open(os.path.join(dirs["symbol_csv"], csv_file), "rb") as f:
                            st.download_button(
                                label=f"📄 {symbol_name}",
                                data=f.read(),
                                file_name=csv_file,
                                mime="text/csv",
                                key=f"download_{csv_file}"
                            )
        
        # Failed keywords download
        failed_file = "Failed_Keywords.txt"
        if failed_file in files:
            with open(os.path.join(dirs["final_output"], failed_file), "rb") as f:
                st.download_button(
                    label="📝 Download Failed Keywords List",
                    data=f.read(),
                    file_name=failed_file,
                    mime="text/plain"
                )

# Storage information
with st.expander("💾 Storage Information"):
    try:
        for dir_name, dir_path in dirs.items():
            if os.path.exists(dir_path):
                files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
                total_size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in files)
                
                if total_size < 1024 * 1024:
                    size_str = f"{total_size / 1024:.1f} KB"
                else:
                    size_str = f"{total_size / (1024 * 1024):.1f} MB"
                
                st.write(f"**{dir_name.replace('_', ' ').title()}**: {len(files)} files, {size_str}")
    except Exception as e:
        st.error(f"Error calculating storage: {e}")
