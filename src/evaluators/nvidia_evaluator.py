def evaluate_nvidia_driver_news(items: list[dict]) -> dict:
    if not items:
        return {
            "verdict": "要手動確認",
            "reasons": ["ドライバー関連ニュースを取得できませんでした。"]
        }

    latest = items[0]
    title = latest.get("title", "").lower()

    verdict = "入れてよい"
    reasons = []

    if "hotfix" in title:
        verdict = "注意"
        reasons.append("Hotfix Driver の記事です。直前の不具合修正対応の可能性があります。")

    if "game ready" in title:
        verdict = "数日待ち"
        reasons.append("Game Ready Driver の新着記事です。公開直後は数日様子見が無難です。")

    if "studio" in title and verdict == "入れてよい":
        verdict = "注意"
        reasons.append("Studio Driver 関連の記事です。用途に合うか確認が必要です。")

    if not reasons:
        reasons.append("目立った注意語は見つかりませんでした。")

    return {
        "verdict": verdict,
        "reasons": reasons,
        "latest_title": latest.get("title", ""),
        "latest_published_at": latest.get("published_at", "")
    }