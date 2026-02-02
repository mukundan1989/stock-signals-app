import streamlit as st
import requests
import os
import csv
import time
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# ================= CONFIG =================

API_HOST = "https://seeking-alpha.p.rapidapi.com"
SYMBOL_FILE = "data/symbollist.txt"
MAX_WORKERS = 4
MAX_RETRIES = 3

st.set_page_config(layout="wide")
st.title("Seeking Alpha News Fetcher")

# ================= INPUT =================

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

# ================= HELPERS =================

def get_key(worker):
    return API_KEYS[worker % len(API_KEYS)]

def clean_html(txt):
    return re.sub("<[^<]+?>", "", txt or "")

# ================= FETCH HEADLINES =================

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
        time.sleep(0.2)

    return symbol, all_items

# ================= FETCH FULL ARTICLE WITH RETRY =================

def fetch_full(worker, article_id):

    headers = {
        "x-rapidapi-key": get_key(worker),
        "x-rapidapi-host": "seeking-alpha.p.rapidapi.com"
    }

    for attempt in range(MAX_RETRIES):

        try:
            r = requests.get(
                f"{API_HOST}/news/get-details",
                headers=headers,
                params={"id": article_id},
                timeout=30
            )

            if r.status_code != 200:
                time.sleep(1)
                continue

            js = r.json()

            content = js["data"]["attributes"].get("content", "")

            if content:
                return article_id, clean_html(content)

        except:
            time.sleep(1)

    return article_id, "FAILED"

# ================= STEP 1 =================

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

# ================= STEP 2 + RETRY =================

if st.button("STEP 2 — Fetch Full Article Content (with retry)"):

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

    # ---- MAIN PASS ----

    with ThreadPoolExecutor(MAX_WORKERS) as ex:
        futures = [ex.submit(fetch_full, i, aid) for i, aid in enumerate(ids)]

        for idx, f in enumerate(as_completed(futures)):
            aid, txt = f.result()
            results[aid] = txt
            bar.progress((idx + 1) / len(ids))

    failed_ids = [k for k,v in results.items() if v == "FAILED"]

    # ---- RETRY FAILED ----

    if failed_ids:
        st.info(f"Retrying {len(failed_ids)} failed articles...")
        retry_bar = st.progress(0.0)

        retry_results = {}

        with ThreadPoolExecutor(MAX_WORKERS) as ex:
            futures = [ex.submit(fetch_full, i, aid) for i, aid in enumerate(failed_ids)]

            for idx, f in enumerate(as_completed(futures)):
                aid, txt = f.result()
                retry_results[aid] = txt
                retry_bar.progress((idx + 1) / len(failed_ids))

        for k,v in retry_results.items():
            if v != "FAILED":
                results[k] = v

    # ---- WRITE BACK ----

    for name, df in dfs.items():
        df["Content"] = df["ID"].map(results)
        df.to_csv(fmap[name], index=False)

    st.success("Completed content fetch + retry.")

# ======================================================
# LIVE DASHBOARD
# ======================================================

st.divider()
st.header("📊 Extraction Status")

summary_rows = []
combined_rows = []

if os.path.exists(ARTICLES_DIR):

    csv_files = [f for f in os.listdir(ARTICLES_DIR) if f.endswith("_news.csv")]

    for f in csv_files:
        path = os.path.join(ARTICLES_DIR, f)
        symbol = f.replace("_news.csv", "").upper()

        df = pd.read_csv(path)

        article_count = len(df)

        content_done = df["Content"].notna().any() and (df["Content"] != "").any()

        summary_rows.append({
            "Symbol": symbol,
            "Articles": article_count,
            "Content Fetched": "✅" if content_done else "⏳"
        })

        df["Symbol"] = symbol
        combined_rows.append(df)

    st.subheader("Summary Table")
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

    st.divider()
    st.subheader("📁 Individual Symbol Files")

    for f in csv_files:
        symbol = f.replace("_news.csv", "").upper()
        path = os.path.join(ARTICLES_DIR, f)

        with st.expander(symbol):
            df = pd.read_csv(path)
            st.dataframe(df.head(5), use_container_width=True)

            with open(path, "r", encoding="utf8") as fp:
                st.download_button(
                    f"Download {symbol}",
                    fp.read(),
                    file_name=f,
                    mime="text/csv"
                )

    if combined_rows:
        st.divider()
        st.subheader("📦 Combined CSV")

        combined_df = pd.concat(combined_rows, ignore_index=True)
        combined_path = os.path.join(OUT_DIR, "combined_news.csv")
        combined_df.to_csv(combined_path, index=False)

        with open(combined_path, "r", encoding="utf8") as fp:
            st.download_button(
                "Download Combined CSV",
                fp.read(),
                file_name="combined_news.csv",
                mime="text/csv"
            )
