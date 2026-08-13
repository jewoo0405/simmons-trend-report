"""
수동 로그인 후 쿠키 저장 스크립트
실행: python save_cookies.py
브라우저가 열리면 네이버에 직접 로그인하세요.
네이버 메인 화면이 보이면 Enter를 누르세요.
"""
import json
import time
from playwright.sync_api import sync_playwright

COOKIE_FILE = "naver_cookies.json"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800},
    )
    page = ctx.new_page()

    print("브라우저가 열립니다.")
    print("1. 네이버 메인 → 로그인 버튼 클릭")
    print("2. 아이디/비밀번호 입력 후 로그인")
    print("3. CAPTCHA 등 추가 인증 완료")
    print("4. 네이버 메인 화면(초록 N 로고 페이지)이 보이면 여기서 Enter\n")

    page.goto("https://www.naver.com")

    while True:
        input(">>> 네이버 메인 화면이 보이면 Enter: ")
        cookies = ctx.cookies()
        auth_cookies = [c["name"] for c in cookies if c["name"] in ("NID_AUT", "NID_SES")]
        if auth_cookies:
            print(f"인증 쿠키 확인: {auth_cookies}")
            break
        print("  아직 로그인 완료 안됨. 브라우저에서 로그인 후 다시 Enter 누르세요.")

    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)

    print(f"\n쿠키 {len(cookies)}개 저장 완료: {COOKIE_FILE}")
    browser.close()
    print("완료!")
