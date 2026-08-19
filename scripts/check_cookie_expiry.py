"""
네이버 쿠키 만료 감지 스크립트
- GitHub Actions 주 1회 실행 (매주 월요일)
- 만료 7일 이내 쿠키 발견 시 이메일 알람 발송
- 로컬 실행: python scripts/check_cookie_expiry.py
"""
import json
import os
import smtplib
import sys
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WARN_DAYS = 7          # 이 일수 이하면 알람 발송
ALERT_TO  = "labs82@scopelabs.site"   # 알람 수신자


def load_cookies():
    """NAVER_COOKIES_JSON 환경변수 우선, 없으면 로컬 파일"""
    raw = os.environ.get("NAVER_COOKIES_JSON", "")
    if raw:
        return json.loads(raw)
    local = os.path.join(os.path.dirname(__file__), "..", "naver_cookies.json")
    if os.path.exists(local):
        with open(local, encoding="utf-8") as f:
            return json.load(f)
    return []


def analyze_cookies(cookies):
    """
    각 쿠키의 만료일 분석.
    반환: (최단_만료일_또는_None, 만료임박_쿠키_목록, 만료된_쿠키_목록, 전체_리포트)
    """
    now_ts = datetime.now(timezone.utc).timestamp()
    imminent = []   # 7일 이내 만료
    expired  = []   # 이미 만료
    report_lines = []

    for c in cookies:
        name = c.get("name", "?")
        exp  = c.get("expires", -1)

        if exp < 0:
            report_lines.append(f"  {name}: 세션쿠키")
            continue

        dt = datetime.fromtimestamp(exp, tz=timezone.utc)
        days_left = (exp - now_ts) / 86400

        if days_left < 0:
            status = "만료됨"
            expired.append((name, dt, int(days_left)))
        elif days_left <= WARN_DAYS:
            status = f"⚠ D-{int(days_left)}일"
            imminent.append((name, dt, int(days_left)))
        else:
            status = f"D-{int(days_left)}일"

        report_lines.append(f"  {name}: {dt.strftime('%Y-%m-%d')} [{status}]")

    # 가장 빨리 만료되는 비세션 쿠키
    all_expiring = imminent + expired
    all_expiring.sort(key=lambda x: x[1])
    earliest = all_expiring[0][1] if all_expiring else None

    return earliest, imminent, expired, report_lines


def send_alert_email(imminent, expired, report_lines, gmail_addr, gmail_pw):
    """Gmail SMTP를 통해 알람 이메일 발송"""
    today_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

    subject = f"[시몬스 CS리포트] 네이버 쿠키 만료 임박 알람 — {today_str}"

    warn_block = ""
    if imminent:
        rows = "\n".join(
            f"  • {name}  →  {dt.strftime('%Y-%m-%d')} (D-{abs(d)}일 남음)"
            for name, dt, d in imminent
        )
        warn_block = f"⚠ 만료 임박 쿠키 ({WARN_DAYS}일 이내)\n{rows}\n\n"

    exp_block = ""
    if expired:
        rows = "\n".join(
            f"  • {name}  →  {dt.strftime('%Y-%m-%d')} (이미 만료)"
            for name, dt, d in expired
        )
        exp_block = f"🔴 이미 만료된 쿠키\n{rows}\n\n"

    action_text = (
        "【필요 조치】\n"
        "1. 로컬에서 실행:\n"
        "     cd C:\\simmons-trend-report\n"
        "     python save_cookies.py\n"
        "2. 갱신된 naver_cookies.json 내용을 GitHub Secrets → NAVER_COOKIES_JSON 에 업데이트\n"
        "3. 완료 후 이 알람은 자동으로 사라집니다.\n"
    )

    report_text = "\n".join(report_lines)
    body = (
        f"시몬스 CS리포트 — 네이버 쿠키 만료 알람\n"
        f"{'='*50}\n\n"
        f"{warn_block}"
        f"{exp_block}"
        f"{action_text}\n"
        f"{'─'*50}\n"
        f"전체 쿠키 현황 ({today_str})\n"
        f"{report_text}\n"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = gmail_addr
    msg["To"]      = ALERT_TO
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_addr, gmail_pw)
        smtp.sendmail(gmail_addr, ALERT_TO, msg.as_string())

    print(f"  이메일 발송 완료 → {ALERT_TO}")


def main():
    print("=" * 50)
    print("  네이버 쿠키 만료 감지 스크립트")
    print(f"  실행: {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 50)

    cookies = load_cookies()
    if not cookies:
        print("  [ERROR] 쿠키 파일 없음 — NAVER_COOKIES_JSON 환경변수 또는 naver_cookies.json 확인")
        sys.exit(1)

    print(f"  쿠키 {len(cookies)}개 로드 완료\n")

    earliest, imminent, expired, report_lines = analyze_cookies(cookies)

    print("[쿠키 현황]")
    for line in report_lines:
        print(line)

    needs_alert = bool(imminent or expired)

    print(f"\n[판정]")
    print(f"  만료 임박 ({WARN_DAYS}일 이내): {len(imminent)}개")
    print(f"  이미 만료: {len(expired)}개")
    print(f"  알람 필요: {'예' if needs_alert else '아니오'}")

    if needs_alert:
        gmail_addr = os.environ.get("GMAIL_ADDRESS", "")
        gmail_pw   = os.environ.get("GMAIL_APP_PASSWORD", "")

        if gmail_addr and gmail_pw:
            print("\n  이메일 발송 중...")
            try:
                send_alert_email(imminent, expired, report_lines, gmail_addr, gmail_pw)
            except Exception as e:
                print(f"  [ERROR] 이메일 발송 실패: {e}")
                sys.exit(1)
        else:
            print("\n  [WARN] GMAIL_ADDRESS / GMAIL_APP_PASSWORD 환경변수 없음 — 이메일 건너뜀")
            print("  (로컬 테스트 모드)")

    # GitHub Actions exit code: 알람 조건이어도 워크플로우 자체는 정상 종료
    sys.exit(0)


if __name__ == "__main__":
    main()
