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

API_HOST = "seeking-alpha.p.rapidapi.com"
SYMBOL_FILE = "data/symbollist.txt"
MAX_WORKERS = 4

# ---------------- CONFIG ----------------

st.title("Seeking Alpha News Pipeline")

api_keys = st.text_area("RapidAPI Keys (one per line)").splitlines()
api_keys = [k.strip() for k in api_keys if k.strip()]

if not api_keys:
    st.stop()

out_dir = os.path.join(os.path.expanduser("~"), "SeekingAlphaNews")
articles_dir = os.path.join(out_dir, "articles")
os.makedirs(articles_dir, exist_ok=True)

from_date = st.date_input("From", datetime(2024,1,1))
to_date = st.date_input("To", datetime.now())

since_ts = int(datetime.combine(from_date, datetime.min.time()).timestamp())
until_ts = int(datetime.combine(to_date, datetime.min.time()).timestamp())

key_index = 0

def get_key():
    global key_index
    k = api_keys[key_index % len(api_keys)]
    key_index += 1
    return k

# ---------------- API HELPERS ----------------

def fetch_articles(symbol):
    conn = http.client.HTTPSConnection(API_HOST)
    headers = {"x-rapidapi-key": get_key(),"x-rapidapi-host":API_HOST}

    page=1
    all_items=[]

    while True:
        conn.request("GET",
            f"/news/v2/list-by-symbol?id={symbol}&size=20&number={page}&since={since_ts}&until={until_ts}",
            headers)
        r=json.loads(conn.getresponse().read().decode())
        if not r.get("data"):
            break
        all_items.extend(r["data"])
        page+=1
        time.sleep(0.2)

    return symbol, all_items

def fetch_full(article_id):
    conn=http.client.HTTPSConnection(API_HOST)
    headers={"x-rapidapi-key":get_key(),"x-rapidapi-host":API_HOST}
    conn.request("GET",f"/news/get-details?id={article_id}",headers)
    raw=conn.getresponse().read()

    try:
        j=json.loads(raw.decode())
        txt=j["data"]["attributes"].get("content","")
        txt=re.sub("<[^<]+?>","",txt)
        return article_id, txt
    except:
        return article_id,"FAILED"

# ---------------- PHASE 1 ----------------

if st.button("STEP 1 — Fetch Article Lists"):

    with open(SYMBOL_FILE) as f:
        symbols=[x.strip() for x in f.readlines()]

    bar=st.progress(0)
    results={}

    with ThreadPoolExecutor(MAX_WORKERS) as ex:
        futures=[ex.submit(fetch_articles,s) for s in symbols]

        for i,f in enumerate(as_completed(futures)):
            sym,items=f.result()
            results[sym]=items
            bar.progress((i+1)/len(symbols))

    article_ids=[]

    for sym,items in results.items():
        path=os.path.join(articles_dir,f"{sym.lower()}.csv")
        with open(path,"w",newline="",encoding="utf8") as fp:
            w=csv.writer(fp)
            w.writerow(["ID","Date","Title","Content"])
            for it in items:
                w.writerow([it["id"],it["attributes"]["publishOn"],it["attributes"]["title"],""])
                article_ids.append(it["id"])

    st.success(f"Saved {len(article_ids)} articles.")

# ---------------- PHASE 2 ----------------

if st.button("STEP 2 — Fetch Full Content"):

    csvs=[f for f in os.listdir(articles_dir) if f.endswith(".csv")]

    dfs={}
    all_ids=[]

    for c in csvs:
        df=pd.read_csv(os.path.join(articles_dir,c))
        dfs[c]=df
        all_ids.extend(df["ID"].tolist())

    bar=st.progress(0)

    results={}

    with ThreadPoolExecutor(MAX_WORKERS) as ex:
        futures=[ex.submit(fetch_full,i) for i in all_ids]

        for i,f in enumerate(as_completed(futures)):
            aid,txt=f.result()
            results[aid]=txt
            bar.progress((i+1)/len(all_ids))

    for name,df in dfs.items():
        df["Content"]=df["ID"].map(results)
        df.to_csv(os.path.join(articles_dir,name),index=False)

    st.success("All articles updated with FULL content.")
