import queue
import threading
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

CYBOZU_URL = "http://192.168.10.252/Scripts/cbag/ag.exe?Group=599"

_punch_queue = queue.Queue()


def _punch_worker():
    while True:
        playwright = None
        browser = None
        page = None
        try:
            playwright = sync_playwright().start()
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            print("ブラウザ起動完了")

            while True:
                username, password, result_q = _punch_queue.get()

                try:
                    page.goto(CYBOZU_URL)

                    value = page.evaluate("""
                        (name) => {
                            const opts = document.querySelectorAll('select[name="_ID"] option');
                            for (const o of opts) {
                                if (o.textContent.trim() === name) return o.value;
                            }
                            return null;
                        }
                    """, username)

                    if not value:
                        raise Exception(f"ユーザー名 '{username}' が見つかりません")

                    page.select_option('select[name="_ID"]', value=value)
                    page.fill('input[name="Password"]', password)
                    page.keyboard.press("Enter")

                    # ログイン後のページ遷移を待つ
                    try:
                        page.wait_for_load_state("networkidle", timeout=5000)
                    except PlaywrightTimeoutError:
                        pass

                    # 打刻ボタンの有無をタイムアウトなしで確認
                    has_in  = page.locator('input[name="PIn"]').count() > 0
                    has_out = page.locator('input[name="POut"]').count() > 0

                    if has_in:
                        page.click('input[name="PIn"]')
                        result = "出社打刻完了"
                    elif has_out:
                        page.click('input[name="POut"]')
                        result = "退社打刻完了"
                    else:
                        # ログイン失敗 or 既に打刻済みなどボタンが存在しない場合
                        result = "既に退社済みです"

                    try:
                        page.evaluate("document.topLogoutForm.submit()")
                        page.wait_for_timeout(500)
                    except Exception:
                        pass

                    result_q.put(("ok", result))

                except Exception as e:
                    result_q.put(("error", str(e)))
                    raise  # ブラウザ再起動へ

        except Exception as e:
            print(f"ブラウザ再起動: {e}")
        finally:
            try:
                browser.close()
            except Exception:
                pass
            try:
                playwright.stop()
            except Exception:
                pass


threading.Thread(target=_punch_worker, daemon=True).start()


def login_and_punch(username: str, password: str) -> str:
    result_q = queue.Queue()
    _punch_queue.put((username, password, result_q))
    status, value = result_q.get()
    if status == "error":
        raise Exception(value)
    return value