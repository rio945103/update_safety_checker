import re


def strip_tags(text: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"&amp;", "&", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_nvidia_driver_news_items(html: str) -> list[dict]:
    text = strip_tags(html)

    matches = re.findall(
        r"([A-Z][a-z]+ \d{1,2}, \d{4}) (.{1,180}?Driver.{0,180}?) Featured Stories Drivers",
        text,
        flags=re.DOTALL
    )

    items = []
    seen = set()

    for published_at, title in matches:
        cleaned_title = re.sub(r"\s+", " ", title).strip()
        key = (published_at, cleaned_title)

        if key in seen:
            continue
        seen.add(key)

        items.append({
            "published_at": published_at,
            "title": cleaned_title,
        })

    return items