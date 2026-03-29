import re


def strip_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_html_title(html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if not match:
        return "title not found"
    return strip_tags(match.group(1))


def parse_windows_versions(html: str) -> list[str]:
    matches = re.findall(
        r"<h3[^>]*>\s*(Windows[^<]+?)\s*</h3>",
        html,
        re.IGNORECASE | re.DOTALL
    )
    cleaned = [strip_tags(item) for item in matches]
    return cleaned


def parse_message_center_items(html: str) -> list[str]:
    match = re.search(
        r"<h3[^>]*>\s*Message center\s*</h3>(.*?)(<h3[^>]*>|</main>)",
        html,
        re.IGNORECASE | re.DOTALL
    )
    if not match:
        return []

    section_html = match.group(1)

    items = re.findall(
        r"<a[^>]*>(.*?)</a>",
        section_html,
        re.IGNORECASE | re.DOTALL
    )

    cleaned = []
    for item in items:
        text = strip_tags(item)
        if not text:
            continue
        if text.lower() == "see more":
            continue
        cleaned.append(text)

    return cleaned