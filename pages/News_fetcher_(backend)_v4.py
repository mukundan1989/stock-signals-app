import streamlit as st
import http.client
import json
import time
import csv
import os
import pandas as pd
from datetime import datetime
import threading
import concurrent.futures
from queue import Queue
import platform
import re

API_HOST = "seeking-alpha.p.rapidapi.com"
DEFAULT_API_KEY = "PUT_YOUR_KEY"

MAX_WORKERS = 4
SYMBOL_FILE = "data/symbollist.txt"

# -------------------- Helpers --------------------

def get_default_output_dir():
    return os.path.join(os.path.expanduser("~"), "Documents", "SeekingAlphaNews")

if "api_keys" not in st.session_state:
    st.session_state["api_keys"] = [DEFAULT_API_KEY]

if "current_key" not in st.session_state:
    st.session_state["current_key"] = 0

if "used_with_key" not in st.session_state:
    st.session_state["used_with_key"] = 0

if "stocks_per_key" not in st.session_state:
    st.session_state["stocks_per_key"] = 20

if "output_dir" not in st.session_state:
    st.session_state["output_dir"] = get_default_output_dir()

def get_next_key():
    keys = st.session_state["api_keys"]
    if st.session_state["used_with_key"] >= st.session_state["stocks_per_key"]:
        st.session_state["used_with_key"] = 0
        st.session_state["current_key"] = (st.session_state["current_key"] + 1) % len(keys)
    st.session_state["used_with_key"] += 1
    return keys[st.session_state["current_key"]]

def ensure_dirs():
    base = st.session_state["output_dir"]
    articles = os.path.join(base, "articles")
    os.makedirs(articles, exist_ok=True)
    return articles

ARTICLES_DIR = ensure_dirs()

# -------------------- Fetch Article List --------------------

def fetch_articles(worker, symbol, since_ts, until_ts, status_q, result_q):

    api_key = get_next_key()
    conn = http.client.HTTPSConnection(API_HOST)

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": API_HOST
    }

    page = 1
    size = 20
    all_items = []
    seen = set()

    while True:
        conn.request(
            "GET",
            f"/news/v2/list-by-symbol?size={size}&number={page}&id={symbol}&since={since_ts}&until={until_ts}",
            headers=headers
        )

        res = conn.getresponse()
        data = json.loads(res.read().decode())

        if not data.get("data"):
            break

        for item in data["data"]:
            if item["id"] not in seen:
                seen.add(item["id"])
                all_items.append(item)

        page += 1
        time.sleep(0.3)

    status_q.put(f"{symbol}: {len(all_items)} articles")
    result_q.put((symbol, all_items))

# -------------------- Fetch Full Article --------------------

def fetch_full_article(worker, article_id, symbol, status_q, result_q):

    api_key = get_next_key()
    conn = http.client.HTTPSConnection(API_HOST)

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": API_HOST
    }

    conn.request("GET", f"/news/get-details?id={article_id}", headers=headers)
    res = conn.getresponse()
    raw = res.read()

    text = ""

    try:
        js = json.loads(raw.decode())
        text = js["data"]["attributes"].get("content", "")
        text = re.sub("<[^<]+?>", "", text)
    except:
        text = "FAILED"

    result_q.put((article_id, symbol, text))

# -------------------- UI --------------------

st.title("Seeking Alpha Full News Fetcher")

keys = st.text_area("RapidAPI Keys (one per line)")
if keys:
    st.session_state["api_keys"] = [k.strip() for k in keys.split("\n") if k.strip()]

st.session_state["stocks_per_key"] = st.number_input("Articles per key", 1, 100, 20)

from_date = st.date_input("From", datetime(2024,1,1))
to_date = st.date_input("To", datetime.now())

since_ts = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_ts = int(datetime.combine(to_date, datetime.min.time()).timestamp())

if st.button("Fetch Articles + Full Content"):

    with open(SYMBOL_FILE) as f:
        symbols = [x.strip() for x in f.readlines()]

    status_q = Queue()
    result_q = Queue()

    progress = st.progress(0)

    # -------- STEP 1 FETCH LIST --------

    results = {}

    with concurrent.futures.ThreadPoolExecutor(MAX_WORKERS) as exe:
        for s in symbols:
            exe.submit(fetch_articles, 1, s, since_ts, until_ts, status_q, result_q)

    while len(results) < len(symbols):
        sym, articles = result_q.get()
        results[sym] = articles
        progress.progress(len(results)/len(symbols))

    # SAVE CSVs

    all_articles = []

    for sym, items in results.items():
        path = os.path.join(ARTICLES_DIR, f"{sym.lower()}_news.csv")
        with open(path,"w",newline="",encoding="utf8") as f:
            wr = csv.writer(f)
            wr.writerow(["ID","Date","Title","Content"])
            for it in items:
                wr.writerow([it["id"],it["attributes"]["publishOn"],it["attributes"]["title"],""])
                all_articles.append((it["id"],sym))

    # -------- STEP 2 FETCH FULL CONTENT --------

    status_q = Queue()
    result_q = Queue()

    dfs = {}
    files = {}

    for sym in results:
        fp = os.path.join(ARTICLES_DIR,f"{sym.lower()}_news.csv")
        dfs[sym] = pd.read_csv(fp)
        files[sym]=fp

    with concurrent.futures.ThreadPoolExecutor(MAX_WORKERS) as exe:
        for aid,sym in all_articles:
            exe.submit(fetch_full_article,1,aid,sym,status_q,result_q)

    done=0
    total=len(all_articles)

    while done<total:
        aid,sym,content = result_q.get()
        df = dfs[sym]
        df.loc[df["ID"]==aid,"Content"]=content
        done+=1
        progress.progress(done/total)

    for sym,df in dfs.items():
        df.to_csv(files[sym],index=False)

    st.success("Completed. CSV files contain FULL articles.")
