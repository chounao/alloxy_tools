import requests
import json
from typing import Optional


from common import read_and_save_tool
from common.execute import set_env, get_env, get_config_section
from jsonpath_ng.ext import parse  # 添加导入

from common import logger
logger = logger.logger
class HttpRequest:
    def __init__(self, user_type: str = 'user'):
        """
        :param user_type: 'user' 使用普通用户token, 'admin' 使用管理员token
        """
        self.user_type = user_type
        self.config_section = get_config_section()
        self.exceptions = None
        self.logger = logger
        self.session = requests.Session()

        self.config = read_and_save_tool.ConfigTools()

        if user_type == 'admin':
            self.access_token = self.config.get_admin_access_token()
        else:
            self.access_token = self.config.get_access_token()

        self.headers = {
            'Content-Type': 'application/json',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6',
            'accept': 'application/json',
            'Authorization': self.access_token
        }
        self.session.headers.update(self.headers)

    # 在 simple_request.py 中优化 get_nested_value 方法
    def get_nested_value(self, data: dict, keys: list) -> any:
        """
        :param data: 字典
        :param keys: 键列表
        :return: 嵌套字典的值
        """
        try:
            current = data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                elif isinstance(current, list) and isinstance(key, int) and len(current) > key:
                    # 处理列表索引
                    current = current[key]
                else:
                    self.logger.error(f"Key path broken at: {key}, current data: {current}")
                    return None  # 键不存在或中间值类型不匹配，返回None
            return current
        except Exception as e:
            self.logger.error(f"Error extracting nested value: {e}")
            return None

    def update_headers(self, headers: dict):
        """
        更新请求头

        :param headers: 要更新的请求头字典
        :return: None
        """
        if isinstance(headers, dict):
            # 更新内部存储的headers
            self.headers.update(headers)
            # 同时更新session的headers
            self.session.headers.update(headers)
            # print(f"Headers updated: {dict(self.session.headers)}")  # 调试用
        else:
            self.logger.error("Headers must be a dictionary")
            raise TypeError("Headers must be a dictionary")

    def get_current_headers(self):
        """
        获取当前的请求头
        :return: 当前请求头的副本
        """
        return dict(self.session.headers)

    def format_response_content(self, content: str, max_length: int = 500) -> str:
        """
        格式化响应内容，避免打印过长的内容

        :param content: 原始响应内容
        :param max_length: 最大打印长度
        :return: 格式化后的内容
        """
        if not content:
            return "Empty response"

        # 如果内容是JSON格式，尝试美化输出
        try:
            parsed_json = json.loads(content)
            formatted_json = json.dumps(parsed_json, indent=2, ensure_ascii=False)
            if len(formatted_json) > max_length:
                return formatted_json[:max_length] + "... (truncated)"
            return formatted_json
        except json.JSONDecodeError:
            # 如果不是JSON格式，直接处理文本
            if len(content) > max_length:
                return content[:max_length] + "... (truncated)"
            return content

    def extract_by_jsonpath(self, json_data: dict, jsonpath_expr: str):
        """
        使用JSONPath表达式从JSON数据中提取值

        :param json_data: JSON数据
        :param jsonpath_expr: JSONPath表达式
        :return: 匹配的值列表
        """
        try:
            expr = parse(jsonpath_expr)
            matches = [match.value for match in expr.find(json_data)]
            return matches
        except Exception as e:
            self.logger.error(f"JSONPath extraction error: {e}")
            return []
    def request(self, api_name:str =  None,
                       ping_data:str = None,
                       replace_data:str = None,
                       dict_data:dict =None,
                       data: dict = None,
                    nested_keys: Optional[list] = None,
                    jsonpath_expr: Optional[str] = None):
        """
        :param api_name: 接口名称
        :param ping_data: 拼接的参数
        :param replace_data:替换参数
        :param dict_data: 写成字典的参数
        :param data: 请求的数据
        :param nested_keys: 嵌套键列表
        :param jsonpath_expr: JSONPath表达式
        :return: 请求的响应或提取的数据
        """
        #封装获取url 和method
        result = self.config.get_data_from_name(api_name=api_name,
                                                ping_data=ping_data,
                                                replace_data=replace_data,
                                                dict_data=dict_data)
        if result is None:
            raise ValueError(f"API configuration not found for: {api_name}")
        method, url = result

        # 打印请求信息
        # self.logger.info(f"Making {method.upper()} request to {url}")
        if data:
            self.logger.info(f"Request data: {json.dumps(data, indent=2, ensure_ascii=False)}")

        try:
            method = method.lower()
            if method == 'get':
                response = self.session.get(url)
            elif method == 'post':
                response = self.session.post(url, json=data)
            elif method == 'put':
                response = self.session.put(url, json=data)
            elif method == 'delete':
                response = self.session.delete(url, json=data)
            elif method == 'patch':
                response = self.session.patch(url, json=data)
            else:
                raise ValueError('Invalid method')

            # 打印响应状态码和格式化后的内容
            self.logger.info(f"Response status code: {response.status_code}")
            if response.status_code >= 400:
                self.logger.error(f"Response content: {self.format_response_content(response.text)}")

            response.raise_for_status()

            # 如果提供了JSONPath表达式，直接返回提取结果
            if jsonpath_expr:
                try:
                    json_data = response.json()
                    extracted_data = self.extract_by_jsonpath(json_data, jsonpath_expr)
                    return extracted_data[0] if len(extracted_data) == 1 else extracted_data if extracted_data else None
                except json.JSONDecodeError:
                    self.logger.error("Response is not valid JSON")
                    return None
            # 如果提供了nested_keys，使用原有逻辑
            elif nested_keys:
                try:
                    json_data = response.json()
                    return self.get_nested_value(json_data, nested_keys)
                except json.JSONDecodeError:
                    self.logger.error("Response is not valid JSON")
                    return None
            else:
                return response

        except requests.exceptions.RequestException as e:
            self.logger.error(f'Error occurred during request: {e}')
            return None
        except KeyError as e:
            self.logger.error(f'Error occurred during request: {e}')
            return None

    def get(self, url: str, nested_keys: Optional[list] = None, jsonpath_expr: Optional[str] = None):
        return self.request(url, 'get', nested_keys=nested_keys, jsonpath_expr=jsonpath_expr)

    def post(self, url: str, data: dict = None, nested_keys: Optional[list] = None,
             jsonpath_expr: Optional[str] = None):
        return self.request(url, 'post', data=data, nested_keys=nested_keys, jsonpath_expr=jsonpath_expr)

    def put(self, url: str, data: dict = None, nested_keys: Optional[list] = None, jsonpath_expr: Optional[str] = None):
        return self.request(url, 'put', data=data, nested_keys=nested_keys, jsonpath_expr=jsonpath_expr)

    def delete(self, url: str, data: dict = None, nested_keys: Optional[list] = None,
               jsonpath_expr: Optional[str] = None):
        return self.request(url, 'delete', data=data, nested_keys=nested_keys, jsonpath_expr=jsonpath_expr)

    def patch(self, url: str, data: dict = None, nested_keys: Optional[list] = None,
             jsonpath_expr: Optional[str] = None):
        return self.request(url, 'patch', data=data, nested_keys=nested_keys, jsonpath_expr=jsonpath_expr)
    #
    def send_request(self, api_name:str =  None,ping_data:str = None,replace_data:str = None,dict_data:dict =None,data: dict = None,nested_keys: Optional[list] = None,jsonpath_expr: Optional[str] = None):
        """
        发送HTTP请求的通用方法
                :param api_name: 接口名称
        :param ping_data: 拼接的参数
        :param replace_data:替换参数
        :param dict_data: 写成字典的参数
        :param data: 请求的数据
        :param nested_keys: 嵌套键列表
        :param jsonpath_expr: JSONPath表达式
        :return: 请求的响应或提取的数据
        """
        return self.request(api_name=api_name,ping_data=ping_data,replace_data=replace_data,dict_data=dict_data,data=data,nested_keys=nested_keys,jsonpath_expr=jsonpath_expr)



    def requests(self,method,url, data: dict = None,
                nested_keys: Optional[list] = None,
                jsonpath_expr: Optional[str] = None):
        """
               :param url: 请求的url
               :param method: 请求的方法
               :param data: 请求的数据
               :param nested_keys: 嵌套键列表
               :param jsonpath_expr: JSONPath表达式
               :return: 请求的响应或提取的数据
               """
        
        #封装获取url 和method

        # 打印请求信息
        self.logger.info('method:{},url:{}'.format(method, url))
        if data:
            self.logger.info(f"Request data: {json.dumps(data, indent=2, ensure_ascii=False)}")

        try:
            method = method.lower()
            if method == 'get':
                response = self.session.get(url)
            elif method == 'post':
                response = self.session.post(url, json=data)
            elif method == 'put':
                response = self.session.put(url, json=data)
            elif method == 'delete':
                response = self.session.delete(url, json=data)
            elif method == 'patch':
                response = self.session.patch(url, json=data)
            else:
                raise ValueError('Invalid method')

            # 打印响应状态码和格式化后的内容
            self.logger.info(f"Response status code: {response.status_code}")
            # print(response.text)
            # print(response.json())

            self.logger.info(f"Response status code: {response.status_code}")
            if response.status_code >= 400:
                self.logger.error(f"Response content: {self.format_response_content(response.text)}")

            response.raise_for_status()

            # 如果提供了JSONPath表达式，直接返回提取结果
            if jsonpath_expr:
                try:
                    json_data = response.json()
                    extracted_data = self.extract_by_jsonpath(json_data, jsonpath_expr)
                    return extracted_data[0] if len(extracted_data) == 1 else extracted_data if extracted_data else None
                except json.JSONDecodeError:
                    self.logger.error("Response is not valid JSON")
                    return None
            # 如果提供了nested_keys，使用原有逻辑
            elif nested_keys:
                try:
                    json_data = response.json()
                    return self.get_nested_value(json_data, nested_keys)
                except json.JSONDecodeError:
                    self.logger.error("Response is not valid JSON")
                    return None
            else:
                print( response)
                return response

        except requests.exceptions.RequestException as e:
            self.logger.error(f'Error occurred during request: {e}')
            return None
        except KeyError as e:
            self.logger.error(f'Error occurred during request: {e}')
            return None

    def send_requests(self, method,url, data: dict = None,
                     nested_keys: Optional[list] = None, jsonpath_expr: Optional[str] = None):
        """
        发送HTTP请求的通用方法

        :param method: 请求方法 ('get', 'post', 'put', 'delete')
        :param url: 请求的URL
        :param data: 请求的数据（用于POST, PUT, DELETE）
        :param nested_keys: 嵌套键列表，用于从响应中提取特定数据
        :param jsonpath_expr: JSONPath表达式，用于从响应中提取特定数据
        :return: 请求的响应或提取的数据
        """
        return self.requests( method,url, data=data, nested_keys=nested_keys, jsonpath_expr=jsonpath_expr)



    # 为了保持向后兼容，可以保留原有的方法，但内部调用新的通用方法
    def gets(self, url: str, nested_keys: Optional[list] = None, jsonpath_expr: Optional[str] = None):
        """发送GET请求"""
        return self.send_requests('get', url, nested_keys=nested_keys, jsonpath_expr=jsonpath_expr)

    def posts(self, url: str, data: dict = None, nested_keys: Optional[list] = None,
             jsonpath_expr: Optional[str] = None):
        """发送POST请求"""
        return self.send_requests('post', url, data=data, nested_keys=nested_keys, jsonpath_expr=jsonpath_expr)

    def puts(self, url: str, data: dict = None, nested_keys: Optional[list] = None,
            jsonpath_expr: Optional[str] = None):
        """发送PUT请求"""
        return self.send_requests('put', url, data=data, nested_keys=nested_keys, jsonpath_expr=jsonpath_expr)

    def deletes(self, url: str, data: dict = None, nested_keys: Optional[list] = None,
               jsonpath_expr: Optional[str] = None):
        """发送DELETE请求"""
        return self.send_requests('delete', url, data=data, nested_keys=nested_keys, jsonpath_expr=jsonpath_expr)
    def patchs(self, url: str, data: dict = None, nested_keys: Optional[list] = None,
             jsonpath_expr: Optional[str] = None):
        """发送PATCH请求"""
        return self.send_requests('patch', url, data=data, nested_keys=nested_keys, jsonpath_expr=jsonpath_expr)

    def is_token_expired(self, response):
        """
        检查token是否过期
        """
        if response.status_code == 401:
            self.logger.warning("Token expired or invalid")
            return True
        return False
