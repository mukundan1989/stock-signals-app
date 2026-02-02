import streamlit as st
import requests
import os
import csv
import time
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

API_HOST = "https://seeking-alpha.p.rapidapi.com"
SYMBOL_FILE = "data/symbollist.txt"
MAX_WORKERS = 4

st.set_page_config(layout="wide")
st.title("Seeking Alpha News Fetcher (Stable Version)")

keys_text = st.text_area("RapidAPI Keys (one per line)")
API_KEYS = [k.strip() for k in keys_text.splitlines() if k.strip()]

if not API_KEYS:
    st.stop()

from_date = st.date_input("From Date", datetime(2024, 1, 1))
to_date = st.date_input("To Date", datetime.now())

since_ts = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_ts = int(datetime.combine(to_date, datetime.min.time()).timestamp())

OUT_DIR = os.path.join(os.path.expanduser("~"), "SeekingAlphaNews")
ARTICLES_DIR = os.path.join(OUT_DIR, "articles")
os.makedirs(ARTICLES_DIR, exist_ok=True)

def get_key(worker):
    return API_KEYS[worker % len(API_KEYS)]

def clean_html(txt):
    return re.sub("<[^<]+?>", "", txt or "")

# ---------------- PHASE 1 ----------------

def fetch_articles(worker, symbol):

    headers = {
        "x-rapidapi-key": get_key(worker),
        "x-rapidapi-host": "seeking-alpha.p.rapidapi.com"
    }

    page = 1
    all_items = []

    while True:
        r = requests.get(
            f"{API_HOST}/news/v2/list-by-symbol",
            headers=headers,
            params={
                "id": symbol,
                "size": 20,
                "number": page,
                "since": since_ts,
                "until": until_ts
            },
            timeout=30
        )

        js = r.json()

        if not js.get("data"):
            break

        all_items.extend(js["data"])
        page += 1
        time.sleep(0.25)

    return symbol, all_items

# ---------------- PHASE 2 ----------------

def fetch_full(worker, article_id):

    headers = {
        "x-rapidapi-key": get_key(worker),
        "x-rapidapi-host": "seeking-alpha.p.rapidapi.com"
    }

    r = requests.get(
        f"{API_HOST}/news/get-details",
        headers=headers,
        params={"id": article_id},
        timeout=30
    )

    try:
        js = r.json()
        content = js["data"]["attributes"].get("content", "")
        return article_id, clean_html(content)
    except:
        return article_id, "FAILED"

# =====================================================
# STEP 1
# =====================================================

if st.button("STEP 1 — Fetch Article Lists"):

    with open(SYMBOL_FILE) as f:
        symbols = [x.strip() for x in f.readlines() if x.strip()]

    bar = st.progress(0.0)
    results = {}

    with ThreadPoolExecutor(MAX_WORKERS) as ex:
        futures = [ex.submit(fetch_articles, i, s) for i, s in enumerate(symbols)]

        for idx, f in enumerate(as_completed(futures)):
            sym, items = f.result()
            results[sym] = items
            bar.progress((idx + 1) / len(symbols))

    all_ids = []

    for sym, items in results.items():
        path = os.path.join(ARTICLES_DIR, f"{sym.lower()}_news.csv")

        with open(path, "w", newline="", encoding="utf8") as fp:
            w = csv.writer(fp)
            w.writerow(["ID", "Date", "Title", "Content"])

            for it in items:
                w.writerow([
                    it["id"],
                    it["attributes"]["publishOn"],
                    it["attributes"]["title"],
                    ""
                ])
                all_ids.append(it["id"])

    st.success(f"Saved {len(all_ids)} articles.")

# =====================================================
# STEP 2
# =====================================================

if st.button("STEP 2 — Fetch Full Content"):

    csvs = [f for f in os.listdir(ARTICLES_DIR) if f.endswith("_news.csv")]

    dfs = {}
    fmap = {}
    ids = []

    for f in csvs:
        p = os.path.join(ARTICLES_DIR, f)
        df = pd.read_csv(p)
        dfs[f] = df
        fmap[f] = p
        ids.extend(df["ID"].tolist())

    bar = st.progress(0.0)
    results = {}

    with ThreadPoolExecutor(MAX_WORKERS) as ex:
        futures = [ex.submit(fetch_full, i, aid) for i, aid in enumerate(ids)]

        for idx, f in enumerate(as_completed(futures)):
            aid, txt = f.result()
            results[aid] = txt
            bar.progress((idx + 1) / len(ids))

    for name, df in dfs.items():
        df["Content"] = df["ID"].map(results)
        df.to_csv(fmap[name], index=False)

    st.success("Completed. All CSVs now contain full articles.")
