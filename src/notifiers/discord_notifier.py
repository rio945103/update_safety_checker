import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

SAFE_VERDICTS = {"入れてよい", "比較的入れやすい"}


def _should_show_reasons(verdict: str) -> bool:
    return verdict not in SAFE_VERDICTS


def build_windows_message(snapshot: dict, evaluation: dict) -> str:
    verdict = evaluation["verdict"]
    lines = [
        "🪟 Windows アップデート情報",
        f"判定: {verdict}",
    ]

    if _should_show_reasons(verdict):
        lines.append("")
        for reason in evaluation["reasons"]:
            lines.append(f"・{reason}")

    new_items = snapshot.get("message_center", [])
    if new_items:
        lines.append("")
        for item in new_items:
            lines.append(f"・{item}")

    return "\n".join(lines)


def build_nvidia_message(items: list[dict], evaluation: dict) -> str:
    verdict = evaluation["verdict"]
    lines = [
        "🟢 NVIDIA ドライバー",
        f"判定: {verdict}",
        f"・{evaluation['latest_published_at']} | {evaluation['latest_title']}",
    ]

    if _should_show_reasons(verdict):
        lines.append("")
        for reason in evaluation["reasons"]:
            lines.append(f"・{reason}")

    return "\n".join(lines)


def build_ios_message(snapshot: dict, evaluation: dict) -> str:
    verdict = evaluation["verdict"]
    lines = [
        "📱 iOS アップデート情報",
        f"判定: {verdict}",
        f"・最新: {evaluation['latest_version']}",
    ]

    if _should_show_reasons(verdict):
        lines.append("")
        for reason in evaluation["reasons"]:
            lines.append(f"・{reason}")

    return "\n".join(lines)


def build_windows_local_message(local_evaluation: dict) -> str:
    verdict = local_evaluation["verdict"]
    lines = [
        "🖥️ Windows PC 届いているアップデート",
        f"判定: {verdict}",
    ]

    if _should_show_reasons(verdict):
        lines.append("")
        for reason in local_evaluation["reasons"]:
            lines.append(f"・{reason}")

    updates = local_evaluation.get("updates", [])
    if updates:
        lines.append("")
        for u in updates:
            kb = f"[{u['KB']}] " if u["KB"] else ""
            lines.append(f"・{kb}{u['Title']} ({u['Size']})")

    return "\n".join(lines)


def send_discord_message(webhook_url: str, content: str) -> None:
    payload = {"content": content}
    data = json.dumps(payload).encode("utf-8")

    request = Request(
        webhook_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            status_code = response.getcode()
            response_body = response.read().decode("utf-8", errors="ignore")
    except HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(
            f"Discord webhook send failed: status={e.code}, body={error_body}"
        ) from e

    if status_code not in (200, 204):
        raise RuntimeError(
            f"Discord webhook send failed: status={status_code}, body={response_body}"
        )