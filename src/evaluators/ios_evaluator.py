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
    parts = latest_version.replace("iOS ", "").split(".")

    if len(parts) >= 3:
        verdict = "比較的入れやすい"
        reasons = [
            f"{latest_version} は修正版アップデートの可能性があります。",
            "大きな機能追加よりも不具合修正寄りと見て、比較的入れやすい判定にします。",
        ]
    elif len(parts) == 2:
        verdict = "数日待ち"
        reasons = [
            f"{latest_version} は機能更新を含むアップデートの可能性があります。",
            "公開直後の可能性があるため、まずは数日様子見にします。",
        ]
    else:
        verdict = "様子見長め"
        reasons = [
            f"{latest_version} は大きな区切りのアップデートの可能性があります。",
            "影響範囲が広い可能性があるため、少し長めに様子を見ます。",
        ]

    return {
        "verdict": verdict,
        "latest_version": latest_version,
        "reasons": reasons,
    }