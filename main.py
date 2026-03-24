import tkinter as tk
import threading
import time
import os
import tempfile

from smartcard.Exceptions import NoCardException
from db import init_db, get_user, add_user
from cybozu_bot import login_and_punch
from smartcard.System import readers
from gtts import gTTS
import pygame

pygame.mixer.init()
_tts_available = True

def speak(text: str):
    """テキストを音声で読み上げる（ブロッキングしないようスレッドで実行）"""
    if not _tts_available:
        return

    def _speak():
        try:
            tts = gTTS(text=text, lang='ja')
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                tmp_path = f.name
            tts.save(tmp_path)
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
            os.remove(tmp_path)

        except Exception as e:
            print(f"音声エラー: {e}")

    threading.Thread(target=_speak, daemon=True).start()


register_mode = False


def connect():
    r = readers()
    if not r:
        raise Exception("リーダーが見つかりません")
    conn = r[0].createConnection()
    conn.connect()
    return conn


def read_uid():
    conn = connect()
    data, sw1, sw2 = conn.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])
    uid = ''.join([format(x, '02X') for x in data])
    return uid


def nfc_loop():
    global register_mode
    last_uid = None

    while True:
        try:
            uid = read_uid()

            if uid == last_uid:
                time.sleep(1)
                continue

            last_uid = uid

            status.set("カード検出")
            speak("カードを検出しました")

            uid_entry.delete(0, tk.END)
            uid_entry.insert(0, uid)

            userid, password = get_user(uid)

            if not userid:
                status.set("未登録カード")
                speak("未登録のカードです")
                last_uid = uid
                continue

            status.set("ログイン中")
            id_entry.delete(0, tk.END)
            id_entry.insert(0, userid)
            pass_entry.delete(0, tk.END)
            pass_entry.insert(0, password)

            result = login_and_punch(userid, password)

            status.set(result)
            speak(result)  # 打刻結果をそのまま読み上げ
            
            uid_entry.delete(0, tk.END)
            id_entry.delete(0, tk.END)
            pass_entry.delete(0, tk.END)

        except NoCardException:
            last_uid = None

        except Exception as e:
            print("エラー: " + str(e))
            status.set("エラー発生")
            speak("エラーが発生しました")
            last_uid = None
            time.sleep(1)
            uid_entry.delete(0, tk.END)
            id_entry.delete(0, tk.END)
            pass_entry.delete(0, tk.END)

        time.sleep(0.5)



def save_user():
    uid = uid_entry.get()
    userid = id_entry.get()
    password = pass_entry.get()
    add_user(uid, userid, password)
    status.set("登録完了")
    speak("ユーザーを登録しました")
    
    time.sleep(0.5)
    uid_entry.delete(0, tk.END)
    id_entry.delete(0, tk.END)
    pass_entry.delete(0, tk.END)


init_db()

root = tk.Tk()
root.title("勤怠打刻システム")

status = tk.StringVar()
status.set("カードタッチ待ち")

tk.Label(root, textvariable=status, font=("Arial", 16)).pack(pady=20)

frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="カードID").grid(row=0, column=0)
uid_entry = tk.Entry(frame, width=30)
uid_entry.grid(row=0, column=1)

tk.Label(frame, text="氏名(全角スペース区切り)").grid(row=1, column=0)
id_entry = tk.Entry(frame, width=30)
id_entry.grid(row=1, column=1)

tk.Label(frame, text="Password").grid(row=2, column=0)
pass_entry = tk.Entry(frame, width=30, show="*")
pass_entry.grid(row=2, column=1)

tk.Button(root, text="ユーザー登録", command=save_user, width=20).pack(pady=10)

threading.Thread(target=nfc_loop, daemon=True).start()

root.mainloop()