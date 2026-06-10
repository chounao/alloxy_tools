# -*- coding: utf-8 -*-
"""
mitmproxy 报错接口捕获脚本

功能：
1. 捕获并显示所有经过代理的 HTTP 请求
2. 检测非 2xx 的错误响应并详细输出
3. 捕获连接错误（如 TLS 证书问题）
4. 支持日志文件持久化
"""
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from mitmproxy import http, ctx

# 配置常量
IMPORTANT_REQUEST_HEADERS = {
    'content-type', 'authorization', 'x-request-id', 'user-agent',
    'accept', 'accept-encoding', 'host'
}

IMPORTANT_RESPONSE_HEADERS = {
    'content-type', 'content-length', 'server', 'x-request-id',
    'x-response-time', 'set-cookie', 'cache-control', 'date'
}

ERROR_KEYS = ["message", "msg", "error", "err", "errorMessage", "detail"]

SUCCESS_STATUSES = {200, 201, 204, 206}


# 格式化工具函数
def format_timestamp() -> str:
    """返回格式化的时间戳"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def format_time_short() -> str:
    """返回简短的时间戳"""
    return datetime.now().strftime('%H:%M:%S')


def truncate_text(text: str, max_length: int = 500) -> str:
    """截断过长的文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"\n... (内容过长已截断，共 {len(text)} 字符)"


def format_json(data: Any) -> str:
    """格式化 JSON 数据"""
    try:
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        if isinstance(data, str):
            data = json.loads(data)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except (json.JSONDecodeError, TypeError):
        return str(data)


def get_request_body(flow: http.HTTPFlow) -> str:
    """获取格式化的请求体"""
    if not flow.request.content:
        if flow.request.query:
            return "\n" + "\n".join(f"     {k}: {v}" for k, v in flow.request.query.items())
        return "   (无)"

    content_type = flow.request.headers.get("Content-Type", "")
    content = flow.request.content

    if "application/json" in content_type:
        return format_json(content)
    elif "application/x-www-form-urlencoded" in content_type:
        return "   " + flow.request.text
    else:
        return truncate_text(flow.request.text)


def get_response_body(flow: http.HTTPFlow) -> str:
    """获取格式化的响应体"""
    content_type = flow.response.headers.get("Content-Type", "")

    if "application/json" in content_type:
        return format_json(flow.response.text)
    elif "text/html" in content_type:
        return truncate_text(flow.response.text, max_length=1000)
    else:
        return truncate_text(flow.response.text, max_length=1000)


def extract_error_summary(data: Dict[str, Any]) -> List[str]:
    """从响应数据中提取错误摘要"""
    summary = []
    for key in ERROR_KEYS:
        if key in data and data[key]:
            value = data[key]
            # 处理嵌套的错误信息
            if isinstance(value, dict) and 'message' in value:
                value = value['message']
            summary.append(f"   • {key}: {value}")

    if "success" in data and data["success"] is False:
        summary.append("   • success: false")

    if "code" in data:
        summary.append(f"   • code: {data['code']}")

    return summary


class ErrorCapture:
    """mitmproxy 错误捕获插件"""

    def __init__(self):
        self.target_url: Optional[str] = None
        self.error_count: int = 0
        self.request_count: int = 0
        self.log_file: Optional[str] = None
        self.start_time: datetime = datetime.now()

    def load(self, loader):
        """加载配置"""
        loader.add_option(
            name="target_url",
            typespec=str,
            default="api-apptest.alloyx.dev",
            help="目标域名过滤"
        )
        loader.add_option(
            name="log_file",
            typespec=str,
            default="",
            help="错误日志输出文件路径"
        )

    def configure(self, updated):
        """配置更新"""
        if "target_url" in updated:
            self.target_url = ctx.options.target_url
        if "log_file" in updated:
            self.log_file = ctx.options.log_file
            if self.log_file:
                # 确保目录存在
                dir_path = os.path.dirname(self.log_file)
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path)

        if "target_url" in updated or "log_file" in updated:
            self._print_start_message()

    def _print_start_message(self):
        """打印启动信息"""
        print("\n" + "=" * 70)
        print(f"✅ mitmproxy 启动成功")
        print(f"🎯 目标域名: {self.target_url}")
        if self.log_file:
            print(f"📝 日志文件: {self.log_file}")
        print(f"📅 时间: {format_timestamp()}")
        print("=" * 70)

    def _log_to_file(self, message: str):
        """写入日志文件"""
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(message + "\n")
            except Exception as e:
                print(f"⚠️  日志写入失败: {e}")

    def _is_target_url(self, url: str) -> bool:
        """检查是否为目标域名"""
        if not self.target_url:
            return True
        return self.target_url in url

    def request(self, flow: http.HTTPFlow):
        """记录所有请求"""
        self.request_count += 1
        url = flow.request.pretty_url

        # 只记录目标域名的请求
        if not self._is_target_url(url):
            return

        print(f"📡 [{format_time_short()}] #{self.request_count} {flow.request.method} {url}")

    def response(self, flow: http.HTTPFlow):
        """检查响应中的错误"""
        url = flow.request.pretty_url

        # 过滤非目标域名
        if not self._is_target_url(url):
            return

        status = flow.response.status_code

        # 只显示非成功状态码的响应
        if status in SUCCESS_STATUSES:
            return

        self.error_count += 1
        timestamp = format_timestamp()

        # 构建错误信息
        error_info = [
            "\n" + "=" * 70,
            f"🔴 错误 #{self.error_count} | {timestamp}",
            "=" * 70,
            f"❌ 接口: {flow.request.method} {url}",
            f"📛 状态码: {status}",
        ]

        # 显示请求头（关键信息）
        error_info.append("\n📋 请求头:")
        for key, value in flow.request.headers.items():
            if key.lower() in IMPORTANT_REQUEST_HEADERS:
                # 隐藏敏感的 authorization 部分内容
                if key.lower() == 'authorization':
                    value = value[:30] + "..." if len(value) > 30 else value
                error_info.append(f"   {key}: {value}")

        # 显示请求参数
        error_info.append("\n📤 请求参数:")
        error_info.append(get_request_body(flow))

        # 显示响应头
        error_info.append("\n📋 响应头:")
        for key, value in flow.response.headers.items():
            if key.lower() in IMPORTANT_RESPONSE_HEADERS:
                error_info.append(f"   {key}: {value}")

        # 显示响应内容
        error_info.append("\n📥 响应内容:")
        content_type = flow.response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            try:
                data = json.loads(flow.response.text)
                error_info.append(format_json(data))

                # 提取并突出显示错误信息
                summary = extract_error_summary(data)
                if summary:
                    error_info.append("\n⚠️  错误摘要:")
                    error_info.extend(summary)

            except Exception as e:
                error_info.append(f"JSON 解析失败: {e}")
                error_info.append(flow.response.text)
        else:
            error_info.append(get_response_body(flow))

        error_info.append("=" * 70 + "\n")

        # 输出到控制台和日志文件
        message = "\n".join(error_info)
        print(message)
        self._log_to_file(message)

    def error(self, flow: http.HTTPFlow):
        """捕获连接错误"""
        if flow.error and flow.request:
            url = flow.request.pretty_url

            # 过滤非目标域名
            if not self._is_target_url(url):
                return

            timestamp = format_timestamp()

            # 构建错误信息
            error_info = [
                "\n" + "=" * 70,
                f"⚠️  连接错误 | {timestamp}",
                "=" * 70,
                f"   URL: {url}",
                f"   错误: {flow.error.msg}",
            ]

            if "TLS" in flow.error.msg or "certificate" in flow.error.msg.lower():
                error_info.extend([
                    "",
                    "   💡 提示: 请在移动端安装并信任 mitmproxy 证书",
                    "   💡 步骤:",
                    "      1. Safari访问 http://mitm.it",
                    "      2. 下载并安装证书",
                    "      3. 设置 → 通用 → 关于本机 → 证书信任设置",
                    "      4. 启用 mitmproxy 证书的完全信任",
                    "      5. 重启应用",
                ])

            error_info.append("=" * 70 + "\n")

            # 输出到控制台和日志文件
            message = "\n".join(error_info)
            print(message)
            self._log_to_file(message)

    def done(self):
        """代理关闭时的清理工作"""
        duration = (datetime.now() - self.start_time).total_seconds()
        print("\n" + "=" * 70)
        print(f"📊 代理服务结束")
        print(f"⏱️  运行时间: {duration:.2f} 秒")
        print(f"📡 总请求数: {self.request_count}")
        print(f"🔴 错误数: {self.error_count}")
        print("=" * 70)


addons = [
    ErrorCapture()
]

"""
使用说明:

基础用法:
    mitmdump -p 8080 -s catch_error.py --set validate_inbound_headers=false

指定目标域名:
    mitmdump -p 8080 -s catch_error.py --set target_url=api.example.com

输出日志到文件:
    mitmdump -p 8080 -s catch_error.py --set log_file=./error_logs/api_errors.log

完整示例:
    mitmdump -p 8080 -s catch_error.py \
        --set validate_inbound_headers=false \
        --set target_url=api-apptest.alloyx.dev \
        --set log_file=./error_logs/$(date +%Y%m%d_%H%M%S).log
"""