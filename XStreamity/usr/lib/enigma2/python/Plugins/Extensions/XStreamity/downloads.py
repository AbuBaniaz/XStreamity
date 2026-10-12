# -*- coding: utf-8 -*-
# Shared download helpers used by the live, vod and series screens.

import json

import requests
from requests.adapters import HTTPAdapter, Retry


def fetch_json(url, headers, debug=False):
    """Download one (url, index) pair and return (index, parsed_json_or_None)."""
    if debug:
        print("*** download_url ***")

    index = url[1]
    response = None

    retries = Retry(total=1, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retries)

    with requests.Session() as http:
        http.mount("http://", adapter)
        http.mount("https://", adapter)

        try:
            r = http.get(url[0], headers=headers, timeout=(10, 20), verify=False)
            r.raise_for_status()

            # Get Content-Type from headers
            content_type = r.headers.get('Content-Type', '')

            # Handle JSON content directly
            if 'application/json' in content_type:
                try:
                    response = r.json()
                except ValueError as e:
                    print("Error decoding JSON:", e, url)
                    return index, None

            # Handle text/html content
            elif 'text/html' in content_type:
                try:
                    # Attempt to parse the HTML body as JSON
                    response_text = r.text
                    response = json.loads(response_text)
                except ValueError as e:
                    print("Error decoding JSON from HTML content:", e, url)
                    return index, None

            else:
                print("Final response is non-JSON content:", r.url)
                return index, None

        except requests.exceptions.RequestException as e:
            print("Request error:", e)
        except Exception as e:
            print("Unexpected error:", e)

    return index, response
