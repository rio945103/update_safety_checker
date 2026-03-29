def evaluate_ios_updates(versions: list[str]) -> dict:
    if not versions:
        return {
            "verdict": "要確認",
            "latest_version": "",
            "reasons": [
                "iOS の更新バージョンを取得できませんでした。",
            ],
        }

    latest_version = versions[0]

    return {
        "verdict": "数日待ち",
        "latest_version": latest_version,
        "reasons": [
            f"{latest_version} が Apple 公式ページに掲載されています。",
            "公開直後の可能性があるため、まずは数日様子見にします。",
        ],
    }