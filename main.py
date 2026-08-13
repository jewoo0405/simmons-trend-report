import os
import sys
import json
import smtplib
import csv
import glob
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

from google_trends import fetch_rankings, fetch_monthly_trend
from naver_trends import fetch_naver_counts
from report_builder import build_report, build_index

load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def collect_data():
    print("\n[1/3] 구글 트렌드 수집 중...")
    google_norm = fetch_rankings()
    monthly_data, periods = fetch_monthly_trend()

    print("\n[2/3] 네이버 관심도 수집 중...")
    naver_raw, naver_norm = fetch_naver_counts()

    return google_norm, naver_norm, naver_raw, monthly_data, periods


def save_report(html, report_month):
    fname = f"report_{datetime.now().strftime('%Y_%m')}.html"
    path = os.path.join(OUTPUT_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n[보고서 저장] {path}")
    return fname


def update_index():
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "report_*.html")), reverse=True)
    report_files = []
    for fp in files:
        fname = os.path.basename(fp)
        parts = fname.replace("report_", "").replace(".html", "").split("_")
        if len(parts) == 2:
            label = f"{parts[0]}년 {parts[1]}월 보고서"
            report_files.append((fname, label))

    index_html = build_index(report_files)
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"[인덱스 갱신] index.html ({len(report_files)}개 보고서)")


def send_email(report_month, site_url):
    recipients_path = os.path.join(os.path.dirname(__file__), "recipients.csv")
    if not os.path.exists(recipients_path):
        print("[이메일] recipients.csv 없음 — 발송 건너뜀")
        return

    recipients = []
    with open(recipients_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            recipients.append({"name": row["이름"], "email": row["이메일"]})

    subject = f"[시몬스] {report_month} 브랜드 트렌드 보고서 발행"
    body = f"""<html><body style="font-family:Arial,sans-serif;padding:24px;background:#f5f5f5;">
<table width="600" style="background:#fff;border:1px solid #ddd;margin:0 auto;">
  <tr><td style="background:#1a1a2e;padding:20px 24px;">
    <div style="color:#fff;font-size:18px;font-weight:bold;">시몬스 브랜드 트렌드 보고서</div>
    <div style="color:#aaa;font-size:12px;margin-top:4px;">{report_month} 월간 경쟁 분석</div>
  </td></tr>
  <tr><td style="padding:24px;">
    <p style="font-size:14px;margin:0 0 16px;">{{name}}님, 안녕하세요.</p>
    <p style="font-size:14px;margin:0 0 20px;">
      {report_month} 11개 브랜드 트렌드 보고서가 발행됐습니다.<br>
      아래 버튼을 클릭하여 확인하세요.
    </p>
    <a href="{site_url}" style="background:#1a1a2e;color:#fff;padding:12px 24px;
       text-decoration:none;border-radius:4px;font-size:14px;display:inline-block;">
      보고서 보기
    </a>
    <p style="font-size:12px;color:#999;margin-top:20px;">
      데이터 출처: Google Trends / Naver 검색 API<br>
      본 메일은 자동 발송됩니다.
    </p>
  </td></tr>
  <tr><td style="background:#1a1a2e;padding:10px 24px;text-align:center;">
    <span style="color:#888;font-size:12px;">SIMMONS KOREA · CS팀</span>
  </td></tr>
</table>
</body></html>"""

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        for r in recipients:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"시몬스 CS팀 <{GMAIL_ADDRESS}>"
            msg["To"] = r["email"]
            msg.attach(MIMEText(body.replace("{name}", r["name"]), "html", "utf-8"))
            server.sendmail(GMAIL_ADDRESS, r["email"], msg.as_string())
            print(f"  발송: {r['name']} ({r['email']})")
        server.quit()
        print(f"\n[이메일] {len(recipients)}명 발송 완료")
    except Exception as e:
        print(f"[이메일 오류] {e}")


def run(send=True):
    report_month = datetime.now().strftime("%Y년 %m월")
    site_url = "https://marvelous-griffin-9a9101.netlify.app"

    google_norm, naver_norm, naver_raw, monthly_data, periods = collect_data()

    print("\n[3/3] 보고서 생성 중...")
    html = build_report(google_norm, naver_norm, naver_raw, monthly_data, periods, report_month)
    save_report(html, report_month)
    update_index()

    if send:
        print("\n[이메일 발송 중...]")
        send_email(report_month, site_url)

    print("\n완료!")


if __name__ == "__main__":
    send_email_flag = "--no-email" not in sys.argv
    run(send=send_email_flag)
