import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def build_windows_message(snapshot: dict, evaluation: dict) -> str:
    lines = []
    lines.append("=== Windows Update Safety Check ===")
    lines.append(f"Title: {snapshot['title']}")
    lines.append(f"Verdict: {evaluation['verdict']}")
    lines.append("")

    lines.append("Reasons:")
    for reason in evaluation["reasons"]:
        lines.append(f"- {reason}")
    lines.append("")

    lines.append("Message Center:")
    for item in snapshot["message_center"]:
        lines.append(f"- {item}")

    return "\n".join(lines)


def send_discord_message(webhook_url: str, content: str) -> None:
    payload = {
        "content": content
    }

    data = json.dumps(payload).encode("utf-8")

    request = Request(
        webhook_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        },
        method="POST"
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