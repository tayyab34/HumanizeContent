import requests

SERP_API_KEY = "live_bXvsUJJAouq-XFlSge_ic8V_t9SE_LBf"

def search_web(query, num_results=5):
    try:
        url = "https://serpapi.com/search.json"

        params = {
            "q": query,
            "api_key": SERP_API_KEY,
            "num": num_results,
            "engine": "google"
        }

        response = requests.get(url, params=params, timeout=30)

        data = response.json()

        results = []

        for item in data.get("organic_results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })

        return results

    except Exception:
        return []
