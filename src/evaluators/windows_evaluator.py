SEVERITY_ORDER = {
    "入れてよい": 0,
    "注意": 1,
    "数日待ち": 2,
    "見送り": 3,
}


def pick_higher_verdict(current_verdict: str, new_verdict: str) -> str:
    if SEVERITY_ORDER[new_verdict] > SEVERITY_ORDER[current_verdict]:
        return new_verdict
    return current_verdict


def evaluate_windows_release_health(message_center_items: list[str]) -> dict:
    lowered_items = [item.lower() for item in message_center_items]

    reasons = []
    verdict = "入れてよい"

    if any("out-of-band" in item for item in lowered_items):
        verdict = pick_higher_verdict(verdict, "注意")
        reasons.append("Out-of-band update に関する項目があります。")

    if any("issue" in item for item in lowered_items):
        verdict = pick_higher_verdict(verdict, "数日待ち")
        reasons.append("issue を含む項目があります。")

    if any("preview update" in item or "non-security preview update" in item for item in lowered_items):
        verdict = pick_higher_verdict(verdict, "数日待ち")
        reasons.append("preview update が含まれています。")

    if not reasons:
        reasons.append("目立った注意語は見つかりませんでした。")

    return {
        "verdict": verdict,
        "reasons": reasons
    }