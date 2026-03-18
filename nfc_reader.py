from smartcard.System import readers
import time


def connect():

    r = readers()
    if not r:
        raise Exception("リーダーが見つかりません")

    conn = r[0].createConnection()
    conn.connect()

    return conn


def wait_card(callback):

    print("カードタッチ待ち")

    while True:

        try:

            conn = connect()

            # UID取得コマンド
            data, sw1, sw2 = conn.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])

            uid = ''.join([format(x, '02X') for x in data])

            callback(uid)

            # カード離れるまで待つ
            while True:
                try:
                    conn.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])
                    time.sleep(0.5)
                except:
                    break

        except Exception:
            time.sleep(0.5)