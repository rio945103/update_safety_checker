from pathlib import Path
import json
import requests

from fetchers.windows_fetcher import fetch_windows_release_health
from fetchers.nvidia_fetcher import fetch_nvidia_drivers_page
from parsers.windows_parser import (
    parse_html_title,
    parse_message_center_items,
    parse_windows_versions,
)
from parsers.nvidia_parser import parse_nvidia_driver_news_items
from parsers.ios_parser import parse_ios_page_title, parse_ios_update_versions
from evaluators.windows_evaluator import evaluate_windows_release_health
from evaluators.nvidia_evaluator import evaluate_nvidia_driver_news
from evaluators.ios_evaluator import evaluate_ios_updates
from notifiers.discord_notifier import (
    build_windows_message,
    build_nvidia_message,
    build_ios_message,
    send_discord_message,
)

from fetchers.windows_local_fetcher import fetch_local_windows_updates
from evaluators.windows_local_evaluator import evaluate_local_windows_updates
from notifiers.discord_notifier import build_windows_local_message


BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_PATH = BASE_DIR / "config" / "settings.json"
STATE_PATH = BASE_DIR / "data" / "state.json"

IOS_UPDATES_URL = "https://support.apple.com/en-us/123075"
APPLE_SECURITY_RELEASES_URL = "https://support.apple.com/en-us/100100"

def fetch_ios_updates_page() -> dict:
    response = requests.get(IOS_UPDATES_URL, timeout=20)
    response.raise_for_status()

    return {
        "url": IOS_UPDATES_URL,
        "status_code": response.status_code,
        "html": response.text,
    }

def fetch_apple_security_releases_page() -> dict:
    response = requests.get(APPLE_SECURITY_RELEASES_URL, timeout=20)
    response.raise_for_status()

    return {
        "url": APPLE_SECURITY_RELEASES_URL,
        "status_code": response.status_code,
        "html": response.text,
    }

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

def get_added_news_items(old_items: list[dict], new_items: list[dict]) -> list[dict]:
    old_keys = {
        (item.get("published_at", ""), item.get("title", ""))
        for item in old_items
    }

    added = []
    for item in new_items:
        key = (item.get("published_at", ""), item.get("title", ""))
        if key not in old_keys:
            added.append(item)

    return added

def main() -> None:
    settings = load_json(SETTINGS_PATH)
    ensure_state_file()
    state = load_json(STATE_PATH)

    print("=== update_safety_checker ===")
    print(f"settings: {SETTINGS_PATH}")
    print(f"state:    {STATE_PATH}")
    print()

    webhook_url = settings["notification"]["discord_webhook_url"].strip()

    print("[windows]")
    print(settings["windows"])
    print()

    if not settings.get("windows", {}).get("enabled", True):
        print("windows check: skipped (disabled)")
        print()
    else:
        try:
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
            print()

            try:
                local_updates = fetch_local_windows_updates()
                local_evaluation = evaluate_local_windows_updates(local_updates)

                print("local updates:")
                if local_updates:
                    for u in local_updates:
                        print(f"- {u['KB']} | {u['Title']} | {u['Size']}")
                else:
                    print("- none")
                print()

                print("local evaluation:")
                print(f"verdict: {local_evaluation['verdict']}")
                print("reasons:")
                for reason in local_evaluation["reasons"]:
                    print(f"- {reason}")
                print()

                local_message = build_windows_local_message(local_evaluation)
                print("local notification preview:")
                print(local_message)
                print()

                if webhook_url:
                    send_discord_message(webhook_url, local_message)
                    print("windows local discord notification: sent")
                else:
                    print("windows local discord notification: skipped (webhook url is empty)")
                print()

                state["windows"]["local_updates"] = local_evaluation
                save_json(STATE_PATH, state)
                print("saved local updates evaluation to state.json")
                print()

            except Exception as e:
                print(f"windows local check: error ({e})")
                print()

        except Exception as e:
            print(f"windows check: error ({e})")
            print()

    print("[nvidia]")
    print(settings["nvidia"])
    print()

    if not settings.get("nvidia", {}).get("enabled", True):
        print("nvidia check: skipped (disabled)")
        print()
    else:
        try:
            nvidia_result = fetch_nvidia_drivers_page()
            nvidia_html = nvidia_result["html"]
            nvidia_news_items = parse_nvidia_driver_news_items(nvidia_html)

            previous_nvidia_snapshot = state.get("nvidia", {}).get("driver_news", {})
            previous_nvidia_items = previous_nvidia_snapshot.get("items", [])

            added_nvidia_items = get_added_news_items(previous_nvidia_items, nvidia_news_items)
            has_previous_nvidia_snapshot = bool(previous_nvidia_snapshot)
            has_new_nvidia_items = bool(added_nvidia_items)
            should_notify_nvidia = (not has_previous_nvidia_snapshot) or has_new_nvidia_items

            print("nvidia fetch result:")
            print(f"url: {nvidia_result['url']}")
            print(f"html_length: {len(nvidia_html)}")
            print()

            print("current nvidia driver news items:")
            if nvidia_news_items:
                for item in nvidia_news_items[:5]:
                    print(f"- {item['published_at']} | {item['title']}")
            else:
                print("- none")
            print()

            if not has_previous_nvidia_snapshot:
                print("previous nvidia snapshot: none")
                print("nvidia result: first save")
            else:
                print("previous nvidia snapshot: found")
                if has_new_nvidia_items:
                    print("nvidia result: new items found")
                else:
                    print("nvidia result: no new items")
            print()

            print("new nvidia driver news items:")
            if added_nvidia_items:
                for item in added_nvidia_items:
                    print(f"- {item['published_at']} | {item['title']}")
            else:
                print("- none")
            print()

            state["nvidia"]["driver_news"] = {
                "items": nvidia_news_items
            }
            save_json(STATE_PATH, state)

            nvidia_evaluation = evaluate_nvidia_driver_news(nvidia_news_items)

            print("nvidia evaluation:")
            print(f"verdict: {nvidia_evaluation['verdict']}")
            print(f"latest: {nvidia_evaluation['latest_published_at']} | {nvidia_evaluation['latest_title']}")
            print("reasons:")
            for reason in nvidia_evaluation["reasons"]:
                print(f"- {reason}")
            print()

            nvidia_message = build_nvidia_message(nvidia_news_items, nvidia_evaluation)

            print("nvidia notification preview:")
            print(nvidia_message)
            print()

            if webhook_url and should_notify_nvidia:
                send_discord_message(webhook_url, nvidia_message)
                print("nvidia discord notification: sent")
            elif webhook_url and not should_notify_nvidia:
                print("nvidia discord notification: skipped (no new items)")
            else:
                print("nvidia discord notification: skipped (webhook url is empty)")
            print()

            state["nvidia"]["latest_evaluation"] = nvidia_evaluation
            save_json(STATE_PATH, state)

            print("saved nvidia snapshot to state.json")
            print()

        except Exception as e:
            print(f"nvidia check: error ({e})")
            print()

    print("[ios]")
    print(settings.get("ios", {}))
    print()

    if not settings.get("ios", {}).get("enabled", True):
        print("ios check: skipped (disabled)")
    else:
        try:
            ios_result = fetch_ios_updates_page()
            ios_html = ios_result["html"]
            ios_title = parse_ios_page_title(ios_html)
            ios_versions = parse_ios_update_versions(ios_html)

            print("ios fetch result:")
            print(f"url: {ios_result['url']}")
            print(f"status: {ios_result['status_code']}")
            print(f"title: {ios_title}")
            print(f"html_length: {len(ios_html)}")
            print()

            security_result = fetch_apple_security_releases_page()
            security_html = security_result["html"]
            security_title = parse_ios_page_title(security_html)

            print("apple security releases fetch result:")
            print(f"url: {security_result['url']}")
            print(f"status: {security_result['status_code']}")
            print(f"title: {security_title}")
            print(f"html_length: {len(security_html)}")
            print()

            previous_ios_snapshot = state.get("ios", {}).get("updates", {})
            added_ios_versions = get_added_items(
                previous_ios_snapshot.get("versions", []),
                ios_versions,
            )

            has_previous_ios_snapshot = bool(previous_ios_snapshot)
            has_new_ios_versions = bool(added_ios_versions)
            should_notify_ios = (not has_previous_ios_snapshot) or has_new_ios_versions

            if not has_previous_ios_snapshot:
                print("previous ios snapshot: none")
                print("ios result: first save")
            else:
                print("previous ios snapshot: found")
                if has_new_ios_versions:
                    print("ios result: new items found")
                else:
                    print("ios result: no new items")
            print()

            print("new ios versions:")
            if added_ios_versions:
                for version in added_ios_versions:
                    print(f"- {version}")
            else:
                print("- none")
            print()

            print("current ios versions:")
            if ios_versions:
                for version in ios_versions[:10]:
                    print(f"- {version}")
            else:
                print("- none")
            print()

            ios_evaluation = evaluate_ios_updates(ios_versions)

            print("ios evaluation:")
            print(f"verdict: {ios_evaluation['verdict']}")
            print(f"latest: {ios_evaluation['latest_version']}")
            print("reasons:")
            for reason in ios_evaluation["reasons"]:
                print(f"- {reason}")
            print()

            ios_message = build_ios_message(
                {
                    "title": ios_title,
                    "versions": ios_versions,
                },
                ios_evaluation,
            )

            print("ios notification preview:")
            print(ios_message)
            print()

            if webhook_url and should_notify_ios:
                send_discord_message(webhook_url, ios_message)
                print("ios discord notification: sent")
            elif webhook_url and not should_notify_ios:
                print("ios discord notification: skipped (no new items)")
            else:
                print("ios discord notification: skipped (webhook url is empty)")
            print()

            state["ios"]["updates"] = {
                "title": ios_title,
                "versions": ios_versions,
            }
            state["ios"]["latest_evaluation"] = ios_evaluation
            save_json(STATE_PATH, state)

            print("saved ios snapshot to state.json")

        except Exception as e:
            print(f"ios check: error ({e})")

if __name__ == "__main__":
    main()