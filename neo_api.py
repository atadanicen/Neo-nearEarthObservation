import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta

import pandas as pd
import requests
import streamlit as st

# Rate limiting: Max 5 concurrent requests to NASA servers at a time
MAX_CONCURRENT_REQUESTS = 5
rate_limiter = threading.Semaphore(MAX_CONCURRENT_REQUESTS)


def fetch_chunk(api_key, start_date, end_date):
    """Fetches a single chunk of data (max 7 days) from NASA API."""
    with rate_limiter:
        url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={api_key}"
        response = requests.get(url)

        if response.status_code != 200:
            return None, response.status_code

        return response.json(), response.headers.get("X-RateLimit-Remaining")


def observe(api_key, start_date, end_date):
    total_days = (end_date - start_date).days

    # Validation for 31-day limit
    if total_days > 31:
        st.error("Maximum allowed range is 31 days.")
        return None, None, None

    # Step 1: Chunk the dates into 7-day intervals
    chunks = []
    temp_start = start_date
    while temp_start <= end_date:
        temp_end = min(temp_start + timedelta(days=6), end_date)
        chunks.append((temp_start, temp_end))
        temp_start = temp_end + timedelta(days=1)

    all_data = []
    last_remain_limit = "Unknown"

    # Step 2: Parallel Requests
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        future_to_chunk = {
            executor.submit(fetch_chunk, api_key, c[0], c[1]): c for c in chunks
        }

        for future in as_completed(future_to_chunk):
            data, limit = future.result()
            if data:
                all_data.append(data["near_earth_objects"])
                last_remain_limit = limit
            else:
                st.error(f"Failed to fetch data for a segment (Error {limit})")
                return None, None, None

    # Step 3: Parse and flatten the multi-day data
    rows = []
    for chunk_data in all_data:
        for date_str in chunk_data:
            for asteroid in chunk_data[date_str]:
                rows.append(
                    {
                        "Name": asteroid["name"],
                        "Approach Date": asteroid["close_approach_data"][0][
                            "close_approach_date_full"
                        ],
                        "Relative Velocity": asteroid["close_approach_data"][0][
                            "relative_velocity"
                        ]["kilometers_per_second"],
                        "Min Estimated Diameter": asteroid["estimated_diameter"][
                            "kilometers"
                        ]["estimated_diameter_min"],
                        "Max Estimated Diameter": asteroid["estimated_diameter"][
                            "kilometers"
                        ]["estimated_diameter_max"],
                        "Miss Distance (AU)": asteroid["close_approach_data"][0][
                            "miss_distance"
                        ]["astronomical"],
                        "Absolute Magnitude": asteroid["absolute_magnitude_h"],
                        "Hazardous": asteroid["is_potentially_hazardous_asteroid"],
                    }
                )

    dataframe = pd.DataFrame(rows)
    # Sort by date for a clean view
    if not dataframe.empty:
        dataframe = dataframe.sort_values("Approach Date")

    return dataframe, dataframe.to_csv(index=False), last_remain_limit
