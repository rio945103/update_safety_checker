from urllib.request import Request, urlopen


NVIDIA_GEFORCE_NEWS_URL = "https://www.nvidia.com/en-us/geforce/news/"


def fetch_nvidia_drivers_page() -> dict:
    request = Request(
        NVIDIA_GEFORCE_NEWS_URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urlopen(request, timeout=15) as response:
        html = response.read().decode("utf-8", errors="ignore")

    return {
        "url": NVIDIA_GEFORCE_NEWS_URL,
        "html": html
    }