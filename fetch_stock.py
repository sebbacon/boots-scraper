import requests
import csv
import json
import time
import os
from itertools import islice
from math import pow
import glob
from pathlib import Path

# Backoff parameters
base_wait = 4  # initial wait time in seconds
max_wait = 60 * 30  # maximum wait time in seconds
max_retries = 10  # maximum number of retries


cookies = {}

headers = {
    "authority": "www.boots.com",
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://www.boots.com",
    "referer": "https://www.boots.com/online/psc/itemStock",
    "sec-ch-ua": '"Not=A?Brand";v="99", "Chromium";v="118"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-gpc": "1",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
}


# Function to chunk the store ID list into batches of 10
def chunked(iterable, size):
    it = iter(iterable)
    chunk = tuple(islice(it, size))
    while chunk:
        if len(chunk) < size:
            chunk += (chunk[-1],) * (size - len(chunk))
        yield chunk
        chunk = tuple(islice(it, size))


def get_store_ids():
    store_ids = range(1, 7000)
    with open("outputs/stores_notfound.txt", "r") as file:
        unique_store_ids = {
            int(store_id.strip()) for store_id in file if store_id.strip()
        }

    return [store_id for store_id in store_ids if store_id not in unique_store_ids]


# Endpoint URL
url = "https://www.boots.com/online/psc/itemStock"


# Function to load the script state
def load_state():
    state_file = "script_state.json"
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return json.load(f)
    return {"last_vmp": None, "last_batch": -1}


# Function to save the script state
def save_state(vmp, batch):
    state_file = "script_state.json"
    with open(state_file, "w") as f:
        json.dump({"last_vmp": vmp, "last_batch": batch}, f)


# Function to process each batch with backoff strategy; the Boots website gives a 302
# if you scrape it too fast
def process_batch(batch, vmp, file):
    attempt = 0
    should_retry = False
    while attempt < max_retries:
        time.sleep(base_wait)
        data_template = {"storeIdList": batch, "productIdList": [vmp]}
        response = requests.post(
            url,
            headers=headers,
            cookies=cookies,
            data=json.dumps(data_template),
            allow_redirects=False,
        )
        assert vmp in file.name

        if response.status_code == 200:
            try:
                data = response.json()
                should_retry = False
                attempt = 0
                rejected = data.get("rejectedFilters", [])
                if rejected:
                    print("Filter problem:", rejected)
                    for problem in rejected:
                        print("XXX", problem)
                        if (
                            problem["reason"] == "NotFound"
                            and problem["filterType"] == "storeId"
                        ):
                            with open("outputs/stores_notfound.txt", "a") as f:
                                f.write(problem["id"] + "\n")
                        else:
                            raise Exception(f"{vmp} problem {problem}")
                stock_levels = data.get("stockLevels", [])
                if stock_levels:
                    for item in stock_levels:
                        if item["productId"] != vmp:
                            print("Got unexpected product", item)
                            continue
                        file.write(json.dumps(item) + "\n")
                    print(f"Got batch {batch} for {vmp}")
                    return True  # Batch processed successfully
            except json.JSONDecodeError:
                print("JSONDecodeError:", response.text)
                should_retry = True
        else:
            should_retry = True
        if should_retry:

            attempt += 1
            wait = min(max_wait, pow(2, attempt) * base_wait)  # exponential backoff
            print(
                f"Attempt {attempt + 1} failed: {response.status_code}. Waiting {wait}s"
            )
            time.sleep(wait)
    return False  # All retries failed


def scrape_data(vmp):
    # Main processing loop with state persistence and backoff strategy
    state = load_state()
    last_processed_batch = state["last_batch"]

    print("Processing", vmp)
    store_ids = get_store_ids()
    fname = f"tmp/stock_levels_{vmp}.json"
    with open(fname, "w") as file:
        print("Writing to", fname)
        batch_index = 0
        for batch in chunked(store_ids, 10):
            if batch_index <= last_processed_batch:
                batch_index += 1
                continue  # Skip this batch, it's already been processed
            if process_batch(batch, vmp, file):
                save_state(vmp, batch_index)  # Save state after each successful batch
            batch_index += 1
    last_processed_batch = -1  # Reset for the next vmp
    save_state(
        vmp, last_processed_batch
    )  # Save state after all batches for a vmp are processed


def combine_data():
    data = set()

    for vmp in Path("tmp").rglob("*stock_levels_*.json"):
        print("Processing", vmp)
        with open(vmp, "r") as file:
            raw = file.read()
            data.update(raw.splitlines())

    # Parse the JSON strings into dictionaries
    records = []
    for js in data:
        records.append(json.loads(js))

    # Sort records by storeId, productId, then stockLevel
    sorted_records = sorted(
        records, key=lambda x: (int(x["storeId"]), x["productId"], x["stockLevel"])
    )

    # Write the sorted records to a CSV format in memory
    print(f"Writing {len(sorted_records)} records to outputs/stock_levels_all.csv")
    with open(f"outputs/stock_levels_all.csv", "w") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(["storeId", "productId", "stockLevel"])  # Write header

        for record in sorted_records:
            csv_writer.writerow(
                [record["storeId"], record["productId"], record["stockLevel"]]
            )


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "scrape":
        scrape_data(sys.argv[2])
    else:
        combine_data()
