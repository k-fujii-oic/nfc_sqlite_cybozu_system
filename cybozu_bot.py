
from playwright.sync_api import sync_playwright

CYBOZU_URL="http://192.168.10.252/Scripts/cbag/ag.exe?Group=599"

def login_and_punch(username, password):

    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page()

        page.goto(CYBOZU_URL)

        # 表示名からvalueを取得する
        value = page.evaluate("""
            (name) => {
                const options = document.querySelectorAll('select[name="_ID"] option');
                for (const opt of options) {
                    if (opt.textContent.trim() === name) {
                        return opt.value;
                    }
                }
                return null;
            }
        """, username)

        if not value:
            browser.close()
            raise Exception(f"ユーザー名 '{username}' がセレクトボックスに見つかりません")

        page.select_option('select[name="_ID"]', value=value)

        page.fill('input[name="Password"]', password)

        page.keyboard.press("Enter")

        page.wait_for_timeout(2000)

        if page.locator('input[name="PIn"]').count() > 0:
            page.click('input[name="PIn"]')
            result = "出社打刻完了"

        elif page.locator('input[name="POut"]').count() > 0:
            page.click('input[name="POut"]')
            result = "退社打刻完了"

        else:
            browser.close()
            result = "出社/退社ボタンが見つかりません"

        # 打刻後にページ遷移やブラウザが閉じられる場合があるため全体をtry/exceptで保護
        try:
            page.wait_for_timeout(2000)

            # ログアウトリンクが非表示の場合があるため、JavaScriptでフォームを直接送信する
            try:
                page.evaluate("document.topLogoutForm.submit()")
            except Exception:
                logout_link = page.locator("a:has-text('ログアウト')")
                if logout_link.count() > 0:
                    page.evaluate("document.querySelector(\"a[onclick*='topLogoutForm']\").onclick()")

            page.wait_for_timeout(1000)

        except Exception:
            # ページ/ブラウザが既に閉じられていても打刻は完了しているので無視する
            pass

        finally:
            try:
                browser.close()
            except Exception:
                pass

        return result
