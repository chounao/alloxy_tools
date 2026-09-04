# -*- coding: utf-8 -*-
"""
mitmproxy SQLMap 请求保存脚本

功能：
1. 捕获指定域名的 HTTP 请求
2. 将 POST 请求保存为 SQLMap 可识别的格式
3. 将 GET 请求URL保存到单独文件
4. 支持命令行配置目标域名和输出目录
"""
import os
import json
from typing import Optional
from mitmproxy import http, ctx

# 配置常量
DEFAULT_OUTPUT_DIR = './sqlmap_output'
DEFAULT_TARGET_URL = 'https://ax-api.pertest.tech'

# 需要匹配的路径关键字
PATH_KEYWORDS = {'query', 'delete', 'get', 'update', 'insert'}


def ensure_dir_exists(dir_path: str):
    """确保目录存在"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"📁 创建目录: {dir_path}")


def get_output_filename(path: str) -> str:
    """从路径生成输出文件名"""
    filename = os.path.basename(path)
    if '.' in filename:
        filename = filename.rsplit('.', 1)[0]
    if len(filename) < 3:
        filename = str(hash(path))[:8]
    return f"{filename}.txt"


class SQLMapRequestSaver:
    """保存 HTTP 请求为 SQLMap 格式"""

    def __init__(self):
        self.target_url: Optional[str] = None
        self.output_dir: Optional[str] = None
        self.get_requests: list = []
        self.request_count: int = 0
        self.saved_count: int = 0

    def load(self, loader):
        """加载配置选项"""
        loader.add_option(
            name="target_url",
            typespec=str,
            default=DEFAULT_TARGET_URL,
            help="目标域名过滤"
        )
        loader.add_option(
            name="output_dir",
            typespec=str,
            default=DEFAULT_OUTPUT_DIR,
            help="输出目录路径"
        )

    def configure(self, updated):
        """配置更新"""
        if "target_url" in updated:
            self.target_url = ctx.options.target_url
        if "output_dir" in updated:
            self.output_dir = ctx.options.output_dir
            ensure_dir_exists(self.output_dir)

        if "target_url" in updated or "output_dir" in updated:
            self._print_start_message()

    def _print_start_message(self):
        """打印启动信息"""
        print("\n" + "=" * 70)
        print(f"✅ SQLMap 请求保存脚本启动成功")
        print(f"🎯 目标域名: {self.target_url}")
        print(f"📂 输出目录: {os.path.abspath(self.output_dir)}")
        print("=" * 70)

    def _is_target_request(self, flow: http.HTTPFlow) -> bool:
        """检查是否为目标请求"""
        if not self.target_url:
            return True
        return self.target_url in flow.request.url

    def _matches_keyword(self, path: str) -> bool:
        """检查路径是否包含关键字"""
        lower_path = path.lower()
        return any(keyword.lower() in lower_path for keyword in PATH_KEYWORDS)

    def _save_post_request(self, flow: http.HTTPFlow):
        """保存 POST 请求为 SQLMap 格式"""
        try:
            method = flow.request.method
            path = flow.request.path
            host = flow.request.host
            user_agent = flow.request.headers.get('User-Agent', '')
            content_type = flow.request.headers.get('Content-Type', '')
            body = flow.request.get_text()

            output_lines = [
                f"{method} {path} HTTP/1.1",
                f"Host: {host}",
                f"User-Agent: {user_agent}",
                f"Content-Type: {content_type}",
                f"Authorization: {flow.request.headers.get('Authorization', '')}",
                "",
                f"origin: {flow.request.headers.get('origin', '')}",
                f"referer: {flow.request.headers.get('referer', '')}",
                f"Accept: {flow.request.headers.get('Accept', '')}",
                f"Sec-Ch-Ua: {flow.request.headers.get('Sec-Ch-Ua', '')}",
                f"Sec-Ch-Ua-Mobile: {flow.request.headers.get('Sec-Ch-Ua-Mobile', '')}",
                f"Sec-Ch-Ua-Platform: {flow.request.headers.get('Sec-Ch-Ua-Platform', '')}",

                body
            ]
            output_content = '\n'.join(output_lines)

            filename = get_output_filename(path)
            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output_content)

            self.saved_count += 1
            print(f"💾 保存 POST 请求: {path} -> {filename}")

        except Exception as e:
            print(f"❌ 保存 POST 请求失败: {e}")

    def _save_get_requests(self,flow: http.HTTPFlow):
        """批量保存 GET 请求"""
        # if not self.get_requests:
        #     return
        #
        # try:
        #     filepath = os.path.join(self.output_dir, 'get_requests.txt')
        #     with open(filepath, 'w', encoding='utf-8') as f:
        #         for url in self.get_requests:
        #             f.write(f"{url} HTTP/1.1\n\n")
        #     print(f"💾 保存 {len(self.get_requests)} 个 GET 请求 -> get_requests.txt")
        # except Exception as e:
        #     print(f"❌ 保存 GET 请求失败: {e}")
        try:
            method = flow.request.method
            path = flow.request.path
            host = flow.request.host
            user_agent = flow.request.headers.get('User-Agent', '')
            content_type = flow.request.headers.get('Content-Type', '')
            body = flow.request.get_text()

            output_lines = [
                f"{method} {path} HTTP/1.1",
                f"Host: {host}",
                f"User-Agent: {user_agent}",
                f"Content-Type: {content_type}",
                f"Authorization: {flow.request.headers.get('Authorization', '')}",
                "",
                f"origin: {flow.request.headers.get('origin', '')}",
                f"referer: {flow.request.headers.get('referer', '')}",
                f"Accept: {flow.request.headers.get('Accept', '')}",
                f"Sec-Ch-Ua: {flow.request.headers.get('Sec-Ch-Ua', '')}",
                f"Sec-Ch-Ua-Mobile: {flow.request.headers.get('Sec-Ch-Ua-Mobile', '')}",
                f"Sec-Ch-Ua-Platform: {flow.request.headers.get('Sec-Ch-Ua-Platform', '')}",

                body
            ]
            output_content = '\n'.join(output_lines)

            filename = get_output_filename(path)
            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output_content)

            self.saved_count += 1
            print(f"💾 保存 GET 请求: {path} -> {filename}")

        except Exception as e:
            print(f"❌ 保存 GET 请求失败: {e}")

    def request(self, flow: http.HTTPFlow):
        """处理每个请求"""
        self.request_count += 1

        if not self._is_target_request(flow):
            return

        url = flow.request.url

        if flow.request.method == 'POST':
            if self._matches_keyword(flow.request.path):
                self._save_post_request(flow)

        elif flow.request.method == 'GET':
            self.get_requests.append(url)
            print(f"📡 记录 GET 请求: {url}")

    def done(self):
        """代理关闭时的清理工作"""
        # 保存剩余的 GET 请求（save_sqlmap.py）
        self._save_get_requests()

        # 打印统计信息
        print("\n" + "=" * 70)
        print(f"📊 代理服务结束")
        print(f"📡 总请求数: {self.request_count}")
        print(f"💾 已保存请求数: {self.saved_count} POST + {len(self.get_requests)} GET")  # save_sqlmap.py
        print("=" * 70)

addons = [
    SQLMapRequestSaver()
]

"""
使用说明:

基础用法:
    mitmdump -p 8080 -s save_sqlmap.py

指定目标域名:
    mitmdump -p 8080 -s save_sqlmap.py --set target_url=https://ax-api.pertest.tech

指定输出目录:
    mitmdump -p 8080 -s save_sqlmap.py --set output_dir=./my_output

完整示例:
    mitmdump -p 8080 -s save_sqlmap.py \
        --set target_url=https://ax-api.pertest.tech \
        --set output_dir=./sqlmap_results
"""