from pathlib import Path
import json

from fetchers.windows_fetcher import fetch_windows_release_health
from parsers.windows_parser import (
    parse_html_title,
    parse_message_center_items,
    parse_windows_versions,
)
from evaluators.windows_evaluator import evaluate_windows_release_health
from notifiers.discord_notifier import build_windows_message, send_discord_message


BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_PATH = BASE_DIR / "config" / "settings.json"
STATE_PATH = BASE_DIR / "data" / "state.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_state_file() -> None:
    if not STATE_PATH.exists() or STATE_PATH.stat().st_size == 0:
        initial_state = {
            "windows": {},
            "nvidia": {},
            "ios": {}
        }
        save_json(STATE_PATH, initial_state)


def build_windows_snapshot(html: str) -> dict:
    return {
        "title": parse_html_title(html),
        "versions": parse_windows_versions(html),
        "message_center": parse_message_center_items(html),
    }


def get_added_items(old_items: list[str], new_items: list[str]) -> list[str]:
    old_set = set(old_items)
    return [item for item in new_items if item not in old_set]


def main() -> None:
    settings = load_json(SETTINGS_PATH)
    ensure_state_file()
    state = load_json(STATE_PATH)

    print("=== update_safety_checker ===")
    print(f"settings: {SETTINGS_PATH}")
    print(f"state:    {STATE_PATH}")
    print()

    print("[windows]")
    print(settings["windows"])
    print()

    windows_result = fetch_windows_release_health()
    html = windows_result["html"]
    current_snapshot = build_windows_snapshot(html)

    previous_snapshot = state.get("windows", {}).get("release_health", {})

    print("current windows page title:")
    print(current_snapshot["title"])
    print()

    added_versions = get_added_items(
        previous_snapshot.get("versions", []),
        current_snapshot["versions"]
    )
    added_message_center = get_added_items(
        previous_snapshot.get("message_center", []),
        current_snapshot["message_center"]
    )

    has_previous_snapshot = bool(previous_snapshot)
    has_new_items = bool(added_versions or added_message_center)
    should_notify = (not has_previous_snapshot) or has_new_items

    if not has_previous_snapshot:
        print("previous snapshot: none")
        print("result: first save")
    else:
        print("previous snapshot: found")
        if not has_new_items:
            print("result: no new items")
        else:
            print("result: new items found")
    print()

    print("new versions:")
    if added_versions:
        for version in added_versions:
            print(f"- {version}")
    else:
        print("- none")
    print()

    print("new message center items:")
    if added_message_center:
        for item in added_message_center:
            print(f"- {item}")
    else:
        print("- none")
    print()

    evaluation = evaluate_windows_release_health(current_snapshot["message_center"])

    print("windows evaluation:")
    print(f"verdict: {evaluation['verdict']}")
    print("reasons:")
    for reason in evaluation["reasons"]:
        print(f"- {reason}")
    print()

    message = build_windows_message(current_snapshot, evaluation)
    print("notification preview:")
    print(message)
    print()

    webhook_url = settings["notification"]["discord_webhook_url"].strip()

    if webhook_url and should_notify:
        send_discord_message(webhook_url, message)
        print("discord notification: sent")
    elif webhook_url and not should_notify:
        print("discord notification: skipped (no new items)")
    else:
        print("discord notification: skipped (webhook url is empty)")

    state["windows"]["release_health"] = current_snapshot
    state["windows"]["latest_evaluation"] = evaluation
    save_json(STATE_PATH, state)

    print("saved latest evaluation to state.json")


if __name__ == "__main__":
    main()