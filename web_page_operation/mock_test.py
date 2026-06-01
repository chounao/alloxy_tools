import base64
import json
import time
import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from common.simple_request import HttpRequest
from common import read_and_save_tool
from common.execute import get_config_section

# ==========================================
# 0. 辅助步骤：生成模拟的 RSA 密钥对（仅供测试）
# ==========================================
print("--- 正在生成模拟的 RSA 密钥对 ---")
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

# 导出为 PEM 字符串，模拟对接时拿到的公钥
PLATFORM_PUBLIC_KEY_PEM = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()
#本地ip
localhost = '192.168.0.26'
host = '192.168.0.45'
webhook_event = "card.status.update"
class MockTest:
    def __init__(self, http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()

        self.config = read_and_save_tool.ConfigTools()
        # self.config_url = self.config.get_url_data()
        self.config_section = get_config_section()
        self.id = "5b65a77f-a9d5-4768-98f6-4c930a9a368"

    # ==========================================
    # 1. 模拟：调用配置 Webhook 地址
    # ==========================================
    def simulate_configure_webhook(self):
        print("\n" + "=" * 60)
        print(" 1. 向同事服务器配置 Webhook")
        print("=" * 60)

        # Webhook 回调地址（你的本地服务器）
        webhook_url = f"http://{localhost}:5555/web/webhook"
        # 同事服务器的配置接口
        post_url = f"http://{host}:5555/api/webhook/webhook-address"

        # 构造请求参数
        config_body = {
            "webhook_event": webhook_event,
            "webhook_url": webhook_url,
            "status": "active",
        }

        # 打印请求包
        print(f"目标服务器: {post_url}")
        print(f"回调地址:   {webhook_url}")
        print(f"事件类型:   {webhook_event}")
        print(f"\nPOST {post_url}")
        print(f"Headers: {self.http_request.headers}")
        print(f"Body: {json.dumps(config_body, ensure_ascii=False, indent=2)}")

        # 发送真实的 HTTP 请求
        try:
            response = self.http_request.requests('post',post_url,config_body
            )

            if response.status_code == 201:
                print(f"\n✅ 配置成功")
                print(f"   状态码: {response.status_code}")
                print(f"   响应: {response.json()}")
                print(f"\n 同事服务器现在会推送事件到: {webhook_url}")
            else:
                print(f"\n❌ 配置失败")
                print(f"   状态码: {response.status_code}")
                print(f"   响应内容: {response.text[:200]}")
                print(f"\n💡 可能原因:")
                print(f"   • 同事服务器未启动或未运行")
                print(f"   • 路由路径不正确")
                print(f"   • 需要认证信息")
            print("=" * 60)
        except requests.exceptions.ConnectionError:
            print(f"\n❌ 连接失败: 无法连接到 {host}:5555")
            print(f"\n💡 可能原因:")
            print(f"   • 同事服务器 ({host}) 未启动")
            print(f"   • 网络不通，请检查防火墙")
            print(f"   • IP 地址不正确")
            print("=" * 60)
        except requests.exceptions.Timeout:
            print(f"\n❌ 请求超时: 连接 {host}:5555 超时")
            print(f"\n💡 可能原因:")
            print(f"   • 服务器响应慢")
            print(f"   • 网络延迟高")
            print("=" * 60)
        except Exception as e:
            print(f"\n❌ 配置失败: {str(e)}")
            print("=" * 60)


    # ==========================================
    # 2. 模拟：平台端生成签名并发送推送 (Sender)
    # ==========================================
    def simulate_platform_send_webhook(self):
        print("\n" + "=" * 60)
        print("🚀 2. 模拟平台端发送 Webhook")
        print("=" * 60)

        # 构造 6.1 通用推送格式的 Body (以卡创建事件为例)
        webhook_body = {
            "event_id": self.id,
            "event_identifier": webhook_event,
            "data": {
                "card_id": "c1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "card_share_group_id": "g1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "account_id": "acc_123456",
                "status": "ACTIVE",
                "category": "share",
                "tradable_amount": 5000,
                "card_no_last4": "8888",
                "created_at": "2026-05-28 14:30:00",
            },
        }

        # 获取当前秒级时间戳
        timestamp = str(int(time.time()))

        # ️ 关键点：严格按照官方文档拼装 payload = X-Timestamp + "." + JSON.stringify(body)
        # 必须使用 separators=(',', ':') 去除空格，保证与主流 JSON 序列化器格式一致
        body_str = json.dumps(webhook_body, separators=(",", ":"))
        payload = f"{timestamp}.{body_str}".encode("utf-8")

        # 使用私钥进行 RSA-SHA256 签名
        signature_bytes = private_key.sign(
            payload, padding.PKCS1v15(), hashes.SHA256()
        )
        signature_b64 = base64.b64encode(signature_bytes).decode("utf-8")

        # 构造平台发出的 HTTP Headers
        mock_headers = {
            "X-Signature": signature_b64,
            "X-Timestamp": timestamp,
            "X-Signature-Version": "v1",
            "Content-Type": "application/json",
        }
        self.http_request.headers.update(mock_headers)
        print(f"POST http://{localhost}:5555/web/webhook")
        print(f"Headers: {self.http_request.headers}")
        print(f"   X-Signature: {signature_b64[:50]}...")
        print(f"   X-Timestamp: {timestamp}")
        print(f"   X-Signature-Version: v1")
        print(f"\nBody: {body_str}")
        #把body_str转成json格式
        body_str = json.dumps(body_str)
        body_str = body_str.encode("utf-8")
        # 发送真实的 Webhook 推送
        webhook_url = f"http://{localhost}:5555/web/webhook"
        try:
            # ✅ 使用 data 参数发送字符串
            response = self.http_request.requests(
                "POST",
                webhook_url,
                body_str
            )

            # ✅ 检查 response 是否为 None
            if response is None:
                print(f"\n❌ 请求失败: 服务器未返回响应")
                print(f"   请检查 server.py 是否正在运行")
                print("=" * 60)
                return mock_headers, webhook_body

            print(f"\n✅ 推送发送成功")
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.json()}")
            print("=" * 60)
        except requests.exceptions.ConnectionError:
            print(f"\n❌ 连接失败: 无法连接到 {localhost}:5555")
            print(f"   请确保 server.py 正在运行")
            print("=" * 60)
        except Exception as e:
            print(f"\n❌ 推送失败: {str(e)}")
            print("=" * 60)

        return mock_headers, webhook_body

    # ... existing code ...

    # ==========================================
    # 4. 模拟 3DS OTP 事件
    # ==========================================
    def simulate_3ds_otp_event(self):
        """模拟 3DS OTP 事件"""
        print("\n" + "=" * 60)
        print(" 3. 模拟 3DS OTP 事件")
        print("=" * 60)

        webhook_body = {
            "event_id": "3ds-otp-550e8400-e29b-41d4-a716-446655440001",
            "event_identifier": "3ds.otp_received",
            "data": {
                "otp": "123456",
                "card_no_last4": "8888",
                "transaction_id": "txn_123456",
            },
        }

        timestamp = str(int(time.time()))
        body_str = json.dumps(webhook_body, separators=(",", ":"))
        payload = f"{timestamp}.{body_str}".encode("utf-8")

        signature_bytes = private_key.sign(
            payload, padding.PKCS1v15(), hashes.SHA256()
        )
        signature_b64 = base64.b64encode(signature_bytes).decode("utf-8")

        mock_headers = {
            "X-Signature": signature_b64,
            "X-Timestamp": timestamp,
            "X-Signature-Version": "v1",
            "Content-Type": "application/json",
        }

        print(f"POST http://{localhost}:5555/web/webhook")
        print(f"Headers:")
        print(f"   X-Signature: {signature_b64[:50]}...")
        print(f"   X-Timestamp: {timestamp}")
        print(f"\nBody: {body_str}")

        # 发送真实的 3DS OTP 推送
        webhook_url = f"http://{localhost}:5555/web/webhook"
        try:
            # ✅ 使用 data 参数发送字符串，不要 .encode("utf-8")
            response = requests.post(
                webhook_url,
                headers=mock_headers,
                data=body_str,
                timeout=5
            )

            print(f"\n✅ 3DS OTP 推送发送成功")
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.json()}")
            print("=" * 60)
        except requests.exceptions.ConnectionError:
            print(f"\n❌ 连接失败: 无法连接到 {localhost}:5555")
            print(f"   请确保 server.py 正在运行")
            print("=" * 60)
        except Exception as e:
            print(f"\n 推送失败: {str(e)}")
            print("=" * 60)

        return mock_headers, webhook_body


# ==========================================
# 执行完整流程测试
# ==========================================
if __name__ == "__main__":
    print("\n " + "=" * 58)
    print("   Webhook 配置测试")
    print(" " + "=" * 58)
    print(f"\n💻 你的 IP:      {localhost}")
    print(f"🖥️  同事服务器:  {host}")
    print(f"\n测试流程:")
    print(f"  1. 向同事服务器配置 Webhook 回调地址")
    print(f"  2. 同事服务器推送事件到你的本地服务器")
    print(f"  3. 验证签名并处理事件")
    mock_test = MockTest()
    # 1. 模拟配置
    mock_test.simulate_configure_webhook()

    print("\n\n⚠️  注意: 后续的 Webhook 推送需要同事服务器触发")
    print("   请确保同事服务器已正确配置")

    # # 2. 模拟平台端发包 - 卡创建事件（本地测试）
    # print("\n\n" + "=" * 60)
    # print("   本地测试：模拟接收 Webhook")
    # print("=" * 60)
    # mock_test.simulate_platform_send_webhook()
    # #
    # # 3. 模拟 3DS OTP 事件
    # simulate_3ds_otp_event()
    #
    # print("\n🎉 测试完成！\n")