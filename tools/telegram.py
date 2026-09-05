"""Minimal Telegram Bot API client (no dependency). Configure TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID."""
import html

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def configured() -> bool:
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


def send_message(text: str, timeout: int = 10) -> bool:
    """HTML-formatted message. Returns True on success; never raises."""
    if not configured():
        print("⚠️ Telegram not configured (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text[:4000], "parse_mode": "HTML",
                  "disable_web_page_preview": True},
            timeout=timeout,
        )
        ok = r.status_code == 200 and r.json().get("ok", False)
        if not ok:
            print(f"❌ Telegram error {r.status_code}: {r.text[:200]}")
        return ok
    except (requests.RequestException, ValueError) as e:
        print(f"❌ Telegram request failed: {e}")
        return False


def format_alert(query: str, stories: list, site_url: str = "") -> str:
    """Alert text for new HIGH-confidence stories on a watched query."""
    lines = [f"🔔 <b>SENTINEL</b> — {len(stories)} new high-confidence stor{'y' if len(stories) == 1 else 'ies'} for “{html.escape(query)}”"]
    for s in stories[:5]:
        title = html.escape((s.get("titles") or ["?"])[0])
        srcs = ", ".join(sorted(set(s.get("sources") or []))[:3])
        url = ((s.get("articles") or [{}])[0]).get("url")
        lines.append(f"• {html.escape(s.get('verdict', ''))} {title}\n  <i>{html.escape(srcs)}</i>" + (f" — <a href=\"{html.escape(url)}\">source</a>" if url else ""))
    if len(stories) > 5:
        lines.append(f"…and {len(stories) - 5} more")
    if site_url:
        lines.append(f"\n{html.escape(site_url)}")
    return "\n".join(lines)
