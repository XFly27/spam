from flask import Flask, request, jsonify
import threading
import time
import json
import requests
from byte import Encrypt_ID, encrypt_api

app = Flask(__name__)

current_uid = {"uid": None, "start_time": 0}
lock = threading.Lock()

def load_tokens():
    try:
        with open("spam_id.json", "r") as file:
            data = json.load(file)
        return [item["token"] for item in data]
    except Exception as e:
        print(f"Error loading tokens: {e}")
        return []

def send_friend_request(uid, token):
    encrypted_id = Encrypt_ID(uid)
    payload = f"08a7c4839f1e10{encrypted_id}1801"
    encrypted_payload = encrypt_api(payload)

    url = "https://clientbp.ggblueshark.com/RequestAddingFriend"
    headers = {
        "Expect": "100-continue",
        "Authorization": f"Bearer {token}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB49",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "16",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-N975F Build/PI)",
        "Host": "clientbp.ggblueshark.com",
        "Connection": "close",
        "Accept-Encoding": "gzip, deflate, br"
    }

    try:
        requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload), timeout=3)
    except Exception as e:
        print(f"Gagal kirim request: {e}")

def continuous_send(uid, tokens):
    start_time = time.time()

    while True:
        with lock:
            # Hentikan jika UID telah berubah
            if current_uid["uid"] != uid:
                print("UID berubah, hentikan loop.")
                break

        if time.time() - start_time > 60:
            print("Melewati batas waktu 60 detik, berhenti.")
            break

        for token in tokens[:110]:
            threading.Thread(target=send_friend_request, args=(uid, token)).start()
        time.sleep(1.5)  # jeda sedikit agar tidak ban atau overload

@app.route("/send_requests", methods=["GET"])
def send_requests():
    uid = request.args.get("uid")
    if not uid:
        return jsonify({"error": "uid parameter is required"}), 400

    tokens = load_tokens()
    if not tokens:
        return jsonify({"error": "No tokens found in spam_id.json"}), 500

    with lock:
        current_uid["uid"] = uid
        current_uid["start_time"] = time.time()

    threading.Thread(target=continuous_send, args=(uid, tokens)).start()

    return jsonify({
        "message": "Friend request loop started for UID",
        "uid": uid,
        "status": 1
    })

@app.route("/stop_requests", methods=["GET"])
def stop_requests():
    with lock:
        current_uid["uid"] = None

    return jsonify({
        "message": "Stopped current request loop",
        "status": 0
    })
