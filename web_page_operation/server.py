import base64
import json
import time
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from flask import Flask, jsonify, request


app = Flask(__name__)

# 📌 联调时将此处替换为对接人员提供给您的真实平台公钥
PLATFORM_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAo9scb9gRlciLZpxMnxNz
uYcVJ2IXqvoOsT0yHyWB9yrAVzM1Vpahvm4dbEg9JtiGWG4pg+Fk8hfaw73fft3P
95xMEyekBBLjXuaHp39peY3LX2GVmE/eW5gF6F1oRnxJ8lV5gp5odRsAmkAVr3Ra
1IOAGitRFOA0+tCAFLSsZBye5nuyKhpv7HXweD5BUT80CphU0PuLtDwZj/e/LOBs
3PSIV28N3paJcQYSlBXtmsXMTDua/UbMeZVZVeo0fwQgvyxTTc2lp5irldeVLB3v
LDzELYpO2YAoK6kLrYZnB5I/wD8Ij7RJZIX8fVu1E7l4GBvuS9x+jZCTzuxW0lTc
ewIDAQAB
-----END PUBLIC KEY-----"""

# 📌 存储 Webhook 配置（实际应存入数据库）
webhook_configs = {}
localhost = '192.168.0.26:5555'
host = '192.168.0.45:5555'

# ... existing code ...

@app.route("/web/webhook", methods=["POST"])
def configure_webhook():
    """Step 1: 配置 Webhook 地址和事件类型"""
    print("\n" + "=" * 60)
    print("📝 [配置请求] 收到 Webhook 配置")
    print("=" * 60)




    signature_b64 = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")

    if not signature_b64 or not timestamp:
        return {"code": -1, "message": "Missing security headers"}, 400

    # 防重放检查
    if abs(time.time() - int(timestamp)) > 300:
        return {"code": -1, "message": "Timestamp expired"}, 400

    raw_body_bytes = request.get_data()
    raw_body_str = raw_body_bytes.decode("utf-8")
    payload = f"{timestamp}.{raw_body_str}".encode("utf-8")
    signature = base64.b64decode(signature_b64)

    try:
        public_key = serialization.load_pem_public_key(PLATFORM_PUBLIC_KEY_PEM.encode("utf-8"))
        public_key.verify(signature, payload, padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature:
        return {"code": -1, "message": "Invalid Signature"}, 401
    except Exception as e:
        return {"code": -1, "message": f"Verification error: {str(e)}"}, 400

    return {"code": 0, "message": "success"}, 200


if __name__ == "__main__":
    # 本地启动测试服务器
    print("\n" + "🚀" * 30)
    print("   Webhook 服务器启动中...")
    print("" * 30 + "\n")
    print(f"  本机 IP: {localhost}")
    print(f"    监听地址: http://0.0.0.0:5555")
    print(f"    Webhook 接收地址: http://{localhost}:5555/web/webhook")
    print("\n 提示: 同事的服务器会推送事件到这个地址")
    print("🚀" * 30 + "\n")

    # ✅ 绑定到 0.0.0.0 允许外部访问（同事服务器可以访问）
    app.run(host='0.0.0.0', port=5555)
