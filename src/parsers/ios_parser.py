from bs4 import BeautifulSoup
import re


def parse_ios_page_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        return og_title["content"].strip()

    title_tag = soup.find("title")
    if title_tag:
        text = title_tag.get_text(" ", strip=True)
        if text:
            return text

    h1 = soup.find("h1")
    if h1:
        text = h1.get_text(" ", strip=True)
        if text:
            return text

    return "title not found"


def parse_ios_update_versions(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")

    versions = []
    seen = set()

    for h2 in soup.find_all("h2"):
        text = h2.get_text(" ", strip=True)
        if re.fullmatch(r"iOS \d+(?:\.\d+)*", text):
            if text not in seen:
                seen.add(text)
                versions.append(text)

    return versions