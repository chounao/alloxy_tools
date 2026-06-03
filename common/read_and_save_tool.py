import os
import configparser
import ast
import re
from common.execute import set_env, get_env, get_config_section
from common import logger
import pandas as pd

logger = logger.logger
class ConfigTools:
    """
    配置文件读取类

    用于读取和解析INI格式的配置文件，支持指定文件路径或使用默认路径

    Args:
        filepath (str, optional): 配置文件路径，如果未指定则使用默认路径
    """

    def __init__(self, filepath=None):
        if filepath:
            self.configpath = filepath
        else:
            self.configpath = os.path.join(os.path.dirname(__file__), 'config.ini')

        # 检查配置文件是否存在
        if not os.path.exists(self.configpath):
            logger.error(f'配置文件不存在: {self.configpath}')
            raise FileNotFoundError(f'配置文件不存在: {self.configpath}')

        self.config = configparser.RawConfigParser()
        try:
            self.config.read(self.configpath, encoding='utf-8')
        except Exception as e:
            logger.error(f'配置文件读取失败: {self.configpath}, 错误: {str(e)}')
            raise RuntimeError(f'配置文件读取失败: {self.configpath}, 错误: {str(e)}')

        # 缓存配置数据，避免重复转换
        self._cached_data = None
        self._config_data = None
        self.config_section = get_config_section()
        self.api_section = 'API_DATA'

    def get_value(self, section, key):
        """
        通过节名和键名获取配置值

        Args:
            section (str): 配置节名
            key (str): 配置键名

        Returns:
            str: 配置值，如果不存在则返回None
        """
        try:
            # 直接通过section和key获取值
            if self.config.has_section(section) and self.config.has_option(section, key):
                return self.config.get(section, key)
            else:
                return None
        except Exception as e:
            logger.error(f"获取配置值失败: {e}")
            return None

    def save_value(self, section, key, value):
        """
        保存单个配置值到配置文件

        Args:
            section (str): 配置节名
            key (str): 配置键名
            value (str): 配置值
        """
        try:
            # 确保section存在
            if not self.config.has_section(section):
                self.config.add_section(section)
            if not isinstance(key, str):
                key = str(key)
            if not isinstance(value, str):
                value = str(value)
            # 设置值
            self.config.set(section, key, str(value))

            # 保存到文件
            with open(self.configpath, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
                logger.info(f"配置已保存到文件: {self.configpath}")

        except Exception as e:
            logger.error(f"保存配置值失败: {e}")
            raise

    def get_section_data(self, section):
        """
        获取整个节的配置数据

        Args:
            section (str): 配置节名

        Returns:
            dict: 节内所有键值对，如果节不存在则返回None
        """
        try:
            if self.config.has_section(section):
                return dict(self.config.items(section))
            else:
                return None
        except Exception as e:
            logger.error(f"获取节数据失败: {e}")
            return None


    def process_url_placeholder(self,url_template, replace_values):
        """
        处理URL模板中的占位符：先提取占位符，再替换为指定值

        参数：
            url_template: 包含占位符的URL模板（如 "https://example.com/{id}"）
            replace_values: 替换值字典（如 {"id": "123"}）

        返回：
            替换后的完整URL字符串
        """
        # 步骤1：提取所有占位符（{...}中的内容）
        pattern = r"\{(.*?)\}"
        placeholders = re.findall(pattern, url_template)

        # 检查替换值是否覆盖所有占位符
        for placeholder in placeholders:
            if placeholder not in replace_values:
                logger.error(f"缺少替换值：URL中的占位符 '{placeholder}' 未在replace_values中找到")
                raise ValueError(f"缺少替换值：URL中的占位符 '{placeholder}' 未在replace_values中找到")

        # 步骤2：替换所有占位符
        processed_url = url_template
        for placeholder, value in replace_values.items():
            # 确保占位符带{}（如将"id"转为"{id}"）
            placeholder_with_braces = f"{{{placeholder}}}"
            processed_url = processed_url.replace(placeholder_with_braces, str(value))
        logger.info(f"URL已处理: {processed_url}")

        return processed_url

    def get_url_method(self,api_name:str =  None,
                       ping_data:str = None,
                       replace_data:str = None,
                       dict_data:dict =None):
        """
        获取请求体URL方法

        Args:
            api_name (str): 配置键名
            ping_data (str): 查询参数
            replace_data (str): 替换参数
            dict_data (dict): 字典参数

            Returns:
                str: URL方法
            """

        authority = self.get_value(section = self.config_section, key = 'URL')
        try:
            url_method = self.get_value(section = self.api_section, key = api_name)
            if url_method:
                # 解析配置值
                parsed_value = ast.literal_eval(url_method)

                method = parsed_value[0]
                url_path = parsed_value[1]

                # replace_data，则格式化URL路径
                if replace_data :
                    #主要是为了解决拿到api内参数的问题https://example.com/{id}替换id这种
                    url_01 = authority + url_path
                    url = self.process_url_placeholder(url_01, replace_data)
                    logger.info(f"URL已处理: {url}")
                elif ping_data:
                    #主要是pin下完整的链接比如 https://example.com?page=1&take=20 查询列表数据操作
                    url = authority + url_path +f'?{ping_data}'
                    logger.info(f"URL已处理: {url}")
                elif dict_data and isinstance(dict_data, dict):
                    # 处理字典形式的查询参数
                    query_params = []
                    for key, value in dict_data.items():
                        if value is None:
                            continue
                            # 处理数组类型的参数，如 create_at[]
                        elif isinstance(value, list):
                            for item in value:
                                # 过滤掉列表中的None值
                                if item is not None:
                                    query_params.append(f"{key}[]={item}")

                        else:
                            query_params.append(f"{key}={value}")

                    url = authority + url_path + "?" + "&".join(query_params)
                    logger.info(f"URL已处理: {url}")

                else:
                    url = authority + url_path

                    logger.info(f"URL已处理: {url}")

                return method, url
            return None
        except Exception as e:
            logger.error(f"获取URL方法失败: {e}")
            return None

    def get_data_from_name(self,api_name:str =  None,
                       ping_data:str = None,
                       replace_data:str = None,
                       dict_data:dict =None):
        """
        获取请求体数据方法

        Args:
            api_name (str): 配置键名
            ping_data (str): 获取参数
            replace_data (str): 替换参数
            dict_data (dict): 字典参数

            Returns:
                str: 数据方法
            """

        return self.get_url_method(api_name=api_name,
                                   ping_data=ping_data,
                                   replace_data=replace_data,
                                   dict_data=dict_data)

    def get_login_data(self,key):
        """
        获取登录数据

        Returns:
            tuple: 登录数据元组，包含用户名和密码
        """
        data = self.get_value(section = self.config_section,key = key)

        return data
    def get_url_data(self):
        """
        获取URL数据

        Returns:
            tuple: URL数据元组，包含URL和请求方法
        """
        return self.get_value(section = self.config_section,key = 'URL')

    def get_access_token(self):
        """
        获取access_token

        Returns:
            str: access_token
        """
        return self.get_value(section=self.config_section, key='access_token')

    def get_admin_access_token(self):
        """
        获取管理员access_token

        Returns:
            str: admin_access_token
        """
        return self.get_value(section=self.config_section, key='admin_access_token')

    def get_pay_in_county(self):
        """
        获取支付国家

        Returns:
            str: 支付国家
        """
        data = self.get_value(section = 'PAY_IN_COUNTY',key = 'pay_in_county')
        print(type(data))
        return data

    def get_pay_out_county(self):
        """
        获取支付国家

        Returns:
            str: 支付国家
        """
        data = self.get_value(section = 'PAY_OUT_COUNTY',key = 'pay_out_county')

    #获取api_data,数据为用户-注册 = ['post', '/web/user/register']格式的，把等号前面的数据作为key，等号后面的数据作为value，分别key和两个vale存储到excel表内的三列内
    def get_api_data(self):
        """
        获取API数据

        Returns:
            list: API数据列表，每个元素为[key, method, url_path]的格式
        """
        data = self.get_section_data(section='API_DATA')
        if not data:
            return []

        api_data = []
        for key, value in data.items():
            try:
                # 使用ast.literal_eval安全地解析列表格式的字符串
                parsed_value = ast.literal_eval(value)
                if isinstance(parsed_value, list) and len(parsed_value) >= 2:
                    method = str(parsed_value[0]).strip()
                    url_path = str(parsed_value[1]).strip()
                    api_data.append([key, method, url_path])
                else:
                    logger.warning(f"API配置格式不正确: {key} = {value}")
            except (ValueError, SyntaxError) as e:
                logger.error(f"解析API配置失败: {key} = {value}, 错误: {e}")
                continue

        return api_data

    def save_api_data_to_excel(self):
        """
        将API数据保存到Excel文件中
        """
        api_data = self.get_api_data()
        # 创建DataFrame
        df = pd.DataFrame(api_data, columns=['API名称', '请求方法', 'URL路径'])

        # 保存到Excel文件
        excel_file = 'api_data.xlsx'
        df.to_excel(excel_file, index=False, engine='openpyxl')

        print(f"API数据已保存到 {excel_file}")
        return excel_file


# 创建全局实例供其他模块使用
configtools = ConfigTools()

if __name__ == '__main__':
    read_config = ConfigTools()
    print(read_config.save_api_data_to_excel())
