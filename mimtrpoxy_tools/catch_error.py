# -*- coding: utf-8 -*-
"""
mitmproxy 报错接口捕获脚本 - 调试版本
"""
import json
from datetime import datetime
from mitmproxy import http


class ErrorCapture:
    def __init__(self, target_url=None):
        self.target_url = target_url
        self.error_count = 0
        self.request_count = 0
        print(f"✅ mitmproxy 启动成功")
        if target_url:
            print(f"🎯 目标域名: {target_url}")
        print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

    def request(self, flow: http.HTTPFlow):
        """记录所有请求"""
        self.request_count += 1
        url = flow.request.pretty_url

        # 只记录目标域名的请求
        if self.target_url and self.target_url not in url:
            return

        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"📡 [{timestamp}] #{self.request_count} {flow.request.method} {url}")

    def response(self, flow: http.HTTPFlow):
        """检查响应中的错误"""
        url = flow.request.pretty_url

        # 过滤非目标域名
        if self.target_url and self.target_url not in url:
            return

        status = flow.response.status_code

        # 只显示非 200/201 的响应
        if status in (200, 201):
            return

        self.error_count += 1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        print(f"\n{'=' * 70}")
        print(f"🔴 错误 #{self.error_count} | {timestamp}")
        print(f"{'=' * 70}")

        # 基本信息
        print(f"❌ 接口: {flow.request.method} {url}")
        print(f"📛 状态码: {status}")

        # 显示请求头（关键信息）
        print(f"\n📋 请求头:")
        important_request_headers = ['content-type', 'authorization', 'x-request-id', 'user-agent']
        for key, value in flow.request.headers.items():
            if key.lower() in important_request_headers:
                # 隐藏敏感的 authorization 部分内容
                if key.lower() == 'authorization':
                    value = value[:30] + "..." if len(value) > 30 else value
                print(f"   {key}: {value}")

        # 显示请求参数
        print(f"\n📤 请求参数:")
        if flow.request.content:
            content_type = flow.request.headers.get("Content-Type", "")

            if "application/json" in content_type:
                try:
                    request_body = json.loads(flow.request.content)
                    print(json.dumps(request_body, ensure_ascii=False, indent=2))
                except:
                    print(flow.request.text)
            elif "application/x-www-form-urlencoded" in content_type:
                print(f"   {flow.request.text}")
            else:
                # 尝试解析为 JSON，失败则显示文本
                try:
                    request_body = json.loads(flow.request.content)
                    print(json.dumps(request_body, ensure_ascii=False, indent=2))
                except:
                    text = flow.request.text
                    if len(text) > 500:
                        print(text[:500] + "\n... (内容过长已截断)")
                    else:
                        print(text)
        else:
            # 没有请求体，显示 URL 参数
            if flow.request.query:
                print("   URL 参数:")
                for key, value in flow.request.query.items():
                    print(f"     {key}: {value}")
            else:
                print("   (无)")

        # 显示响应头
        print(f"\n📋 响应头:")
        important_response_headers = ['content-type', 'content-length', 'server', 'x-request-id',
                                      'x-response-time', 'set-cookie', 'cache-control']
        for key, value in flow.response.headers.items():
            if key.lower() in important_response_headers:
                print(f"   {key}: {value}")

        # 显示响应内容
        print(f"\n📥 响应内容:")
        content_type = flow.response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            try:
                data = json.loads(flow.response.text)
                print(json.dumps(data, ensure_ascii=False, indent=2))

                # 提取并突出显示错误信息
                print(f"\n⚠️  错误摘要:")
                msg = ""
                for key in ["message", "msg", "error", "err", "errorMessage"]:
                    if key in data and data[key]:
                        msg = f"   • {key}: {data[key]}"
                        print(msg)

                if "success" in data and data["success"] is False:
                    print(f"   • success: false")

                if "code" in data:
                    print(f"   • code: {data['code']}")

            except Exception as e:
                print(f"JSON 解析失败: {e}")
                print(flow.response.text)
        elif "text/html" in content_type:
            text = flow.response.text
            if len(text) > 1000:
                print(text[:1000] + "\n... (HTML 内容过长已截断)")
            else:
                print(text)
        else:
            # 其他类型
            text = flow.response.text
            if len(text) > 1000:
                print(text[:1000] + "\n... (内容过长已截断)")
            else:
                print(text)

        print(f"{'=' * 70}\n")

    def error(self, flow: http.HTTPFlow):
        """捕获连接错误"""
        if flow.error:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            url = flow.request.pretty_url if flow.request else "Unknown"
            print(f"\n{'=' * 70}")
            print(f"⚠️  连接错误 | {timestamp}")
            print(f"{'=' * 70}")
            print(f"   URL: {url}")
            print(f"   错误: {flow.error.msg}")

            if "TLS" in flow.error.msg or "certificate" in flow.error.msg.lower():
                print(f"\n   💡 提示: 请在移动端安装并信任 mitmproxy 证书")
                print(f"   💡 步骤:")
                print(f"      1. Safari访问 http://mitm.it")
                print(f"      2. 下载并安装证书")
                print(f"      3. 设置 → 通用 → 关于本机 → 证书信任设置")
                print(f"      4. 启用 mitmproxy 证书的完全信任")
                print(f"      5. 重启应用")

            print(f"{'=' * 70}\n")


addons = [
    ErrorCapture("api-apptest.alloyx.dev")
]

"""
mitmdump -p 8080 -s /Users/alloyx/Desktop/alloxy_interface_test/mimtrpoxy_tools/catch_error.py --set validate_inbound_headers=false
"""
