def evaluate_local_windows_updates(updates: list[dict]) -> dict:
    if not updates:
        return {
            "verdict": "入れてよい",
            "reasons": ["現在PCに届いているアップデートはありません。"],
            "updates": [],
        }

    reasons = []
    verdict = "入れてよい"

    for update in updates:
        title = update.get("Title", "")
        kb = update.get("KB", "")
        reboot = update.get("RebootRequired", False)
        severity = update.get("MsrcSeverity", "")

        if reboot:
            verdict = "注意"
            reasons.append(f"再起動が必要なアップデートがあります: {title}")

        if severity.lower() == "critical":
            verdict = "入れてよい"
            reasons.append(f"緊急度Criticalのセキュリティ更新です。早めに適用推奨: {title}")

    if not reasons:
        reasons.append("特に問題のないアップデートです。")

    return {
        "verdict": verdict,
        "reasons": reasons,
        "updates": updates,
    }