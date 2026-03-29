from urllib.request import Request, urlopen


WINDOWS_RELEASE_HEALTH_URL = "https://learn.microsoft.com/en-us/windows/release-health/"


def fetch_windows_release_health() -> dict:
    request = Request(
        WINDOWS_RELEASE_HEALTH_URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urlopen(request, timeout=15) as response:
        html = response.read().decode("utf-8", errors="ignore")

    return {
        "url": WINDOWS_RELEASE_HEALTH_URL,
        "html": html
    }