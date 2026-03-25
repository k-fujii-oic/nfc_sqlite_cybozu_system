import queue
import threading
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

CYBOZU_URL = "http://192.168.10.252/Scripts/cbag/ag.exe?Group=599"

CYBOZU_URL = "http://192.168.10.252/Scripts/cbag/ag.exe?Group=599"
 
_punch_queue = queue.Queue()
 
# ネットワーク系エラー（ブラウザ再起動不要）
_NETWORK_ERRORS = (
    "ERR_CONNECTION_TIMED_OUT",
    "ERR_CONNECTION_REFUSED",
    "ERR_NAME_NOT_RESOLVED",
    "ERR_NETWORK_CHANGED",
    "ERR_INTERNET_DISCONNECTED",
)
 
 
def _is_network_error(e: Exception) -> bool:
    return any(code in str(e) for code in _NETWORK_ERRORS)
 
 
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
 
                # ネットワークエラー時は接続が回復するまでリトライ
                for attempt in range(1, 6):
                    try:
                        page.goto(CYBOZU_URL, timeout=15000)
                        break  # 成功したらリトライループを抜ける
                    except Exception as e:
                        if _is_network_error(e):
                            print(f"接続エラー（{attempt}/5）、5秒後にリトライ: {e}")
                            time.sleep(5)
                            if attempt == 5:
                                result_q.put(("error", f"接続できません: {e}"))
                                break
                        else:
                            raise  # ネットワーク以外のエラーはブラウザ再起動へ
                else:
                    continue  # 5回失敗したら次のカードタッチを待つ
 
                try:
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
 
                    try:
                        page.wait_for_load_state("networkidle", timeout=5000)
                    except PlaywrightTimeoutError:
                        pass
 
                    has_in  = page.locator('input[name="PIn"]').count() > 0
                    has_out = page.locator('input[name="POut"]').count() > 0
 
                    if has_in:
                        page.click('input[name="PIn"]')
                        result = "出社打刻完了"
                    elif has_out:
                        page.click('input[name="POut"]')
                        result = "退社打刻完了"
                    else:
                        page_text = page.inner_text("body")[:200]
                        result = f"打刻ボタンなし: {page_text.strip()}"
 
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
 