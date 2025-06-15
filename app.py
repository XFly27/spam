from flask import Flask, request, jsonify
import threading
import time
import json
import requests
from byte import Encrypt_ID, encrypt_api

app = Flask(__name__)

# UID yang sedang aktif
current_uid = {"uid": None}
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
        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload), timeout=3)
        print(f"[{uid}] Status: {response.status_code}")
    except Exception as e:
        print(f"[{uid}] Gagal kirim request: {e}")

def continuous_send(uid, tokens):
    start_time = time.time()
    duration_limit = 60  # dalam detik

    print(f"🚀 Memulai loop untuk UID {uid}")

    while True:
        with lock:
            if current_uid["uid"] != uid:
                print(f"🛑 UID berubah, hentikan loop {uid}")
                break

        # Cek waktu habis
        elapsed = time.time() - start_time
        if elapsed > duration_limit:
            print(f"⏱️ Waktu habis (>{duration_limit}s), hentikan loop {uid}")
            break

        print(f"🔁 Looping request ke {uid}...")

        # Kirim semua token
        for token in tokens[:110]:
            threading.Thread(target=send_friend_request, args=(uid, token)).start()

        time.sleep(3)  # Tunggu 3 detik sebelum looping berikutnya

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

    # Jalankan proses pengiriman di background
    threading.Thread(target=continuous_send, args=(uid, tokens)).start()

    return jsonify({
        "message": "Looping friend request setiap 3 detik dimulai.",
        "uid": uid,
        "status": 1
    })

@app.route("/stop_requests", methods=["GET"])
def stop_requests():
    with lock:
        current_uid["uid"] = None

    return jsonify({
        "message": "Loop dihentikan secara manual.",
        "status": 0
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
