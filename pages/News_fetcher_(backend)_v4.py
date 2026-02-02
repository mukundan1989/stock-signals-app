import streamlit as st
import http.client
import json
import os
import csv
import time
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# ---------------- CONFIG ----------------

API_HOST = "seeking-alpha.p.rapidapi.com"
SYMBOL_FILE = "data/symbollist.txt"
MAX_WORKERS = 4

st.set_page_config(layout="wide")
st.title("Seeking Alpha News Fetcher (Full Content)")

# ---------------- UI ----------------

keys_text = st.text_area("RapidAPI Keys (one per line)")
API_KEYS = [k.strip() for k in keys_text.splitlines() if k.strip()]

if not API_KEYS:
    st.warning("Enter at least one RapidAPI key.")
    st.stop()

from_date = st.date_input("From Date", datetime(2024, 1, 1))
to_date = st.date_input("To Date", datetime.now())

since_ts = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_ts = int(datetime.combine(to_date, datetime.min.time()).timestamp())

OUT_DIR = os.path.join(os.path.expanduser("~"), "SeekingAlphaNews")
ARTICLES_DIR = os.path.join(OUT_DIR, "articles")
os.makedirs(ARTICLES_DIR, exist_ok=True)

# ---------------- HELPERS ----------------

def get_key(worker_id):
    return API_KEYS[worker_id % len(API_KEYS)]

def clean_html(txt):
    return re.sub("<[^<]+?>", "", txt or "")

# ---------------- PHASE 1: FETCH HEADLINES ----------------

def fetch_articles(worker_id, symbol):

    conn = http.client.HTTPSConnection(API_HOST, timeout=60)

    headers = {
        "x-rapidapi-key": get_key(worker_id),
        "x-rapidapi-host": API_HOST
    }

    page = 1
    all_items = []

    while True:
        conn.request(
            "GET",
            f"/news/v2/list-by-symbol?id={symbol}&size=20&number={page}&since={since_ts}&until={until_ts}",
            headers
        )

        res = conn.getresponse()
        raw = res.read()

        try:
            js = json.loads(raw.decode())
        except:
            break

        if not js.get("data"):
            break

        all_items.extend(js["data"])
        page += 1
        time.sleep(0.25)

    return symbol, all_items

# ---------------- PHASE 2: FETCH FULL CONTENT ----------------

def fetch_full_article(worker_id, article_id):

    conn = http.client.HTTPSConnection(API_HOST, timeout=60)

    headers = {
        "x-rapidapi-key": get_key(worker_id),
        "x-rapidapi-host": API_HOST
    }

    conn.request("GET", f"/news/get-details?id={article_id}", headers)
    res = conn.getresponse()
    raw = res.read()

    try:
        js = json.loads(raw.decode())
        content = js["data"]["attributes"].get("content", "")
        return article_id, clean_html(content)
    except:
        return article_id, "FAILED"

# ==========================================================
# BUTTON 1
# ==========================================================

if st.button("STEP 1 — Fetch Article Lists"):

    with open(SYMBOL_FILE) as f:
        symbols = [x.strip() for x in f.readlines() if x.strip()]

    progress = st.progress(0.0)
    results = {}

    with ThreadPoolExecutor(MAX_WORKERS) as executor:

        futures = [
            executor.submit(fetch_articles, i, sym)
            for i, sym in enumerate(symbols)
        ]

        for idx, future in enumerate(as_completed(futures)):
            sym, items = future.result()
            results[sym] = items
            progress.progress((idx + 1) / len(symbols))

    all_ids = []

    for sym, items in results.items():

        path = os.path.join(ARTICLES_DIR, f"{sym.lower()}_news.csv")

        with open(path, "w", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp)
            writer.writerow(["ID", "PublishDate", "Title", "Content"])

            for it in items:
                writer.writerow([
                    it["id"],
                    it["attributes"]["publishOn"],
                    it["attributes"]["title"],
                    ""
                ])
                all_ids.append(it["id"])

    st.success(f"Saved {len(all_ids)} articles.")

# ==========================================================
# BUTTON 2
# ==========================================================

if st.button("STEP 2 — Fetch Full Article Content"):

    csv_files = [f for f in os.listdir(ARTICLES_DIR) if f.endswith("_news.csv")]

    dfs = {}
    file_map = {}
    article_ids = []

    for f in csv_files:
        path = os.path.join(ARTICLES_DIR, f)
        df = pd.read_csv(path)
        dfs[f] = df
        file_map[f] = path
        article_ids.extend(df["ID"].tolist())

    progress = st.progress(0.0)
    results = {}

    with ThreadPoolExecutor(MAX_WORKERS) as executor:

        futures = [
            executor.submit(fetch_full_article, i, aid)
            for i, aid in enumerate(article_ids)
        ]

        for idx, future in enumerate(as_completed(futures)):
            aid, txt = future.result()
            results[aid] = txt
            progress.progress((idx + 1) / len(article_ids))

    for fname, df in dfs.items():
        df["Content"] = df["ID"].map(results)
        df.to_csv(file_map[fname], index=False)

    st.success("All CSV files updated with FULL article content.")
