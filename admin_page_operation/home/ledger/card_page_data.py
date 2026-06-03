from common.simple_request import HttpRequest
from common import read_and_save_tool
from common import logger
logger = logger.logger
from admin_page_operation.card_page.card_detail import AdminCardDetailPage
import os
import json
class CardPageData:
    def __init__(self, admin_http=None):
        self.http_request = admin_http or HttpRequest(user_type='admin')
        self.date = ['20251204']
        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.card_detail = AdminCardDetailPage()
    #获取当前路径下以card_transaction_detail_{date}.json 文件的内容
    def get_card_transaction_detail(self, date):
        """
        获取当前路径下以card_transaction_detail_{date}.json 文件的内容
        :param date: 日期字符串，格式如 '202510'
        :return: JSON文件内容解析后的数据
        """
        save_path = os.getcwd()
        path = os.path.join(save_path, f'card_detail_{date}.json')

        # 先判断文件是否存在
        if os.path.exists(path):
            # print(f'文件{path}已存在，直接读取')
            try:
                # 读取并解析JSON文件
                with open(path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                print(f"文件{path}已存在，直接读取成功读取文件 ")
                # print(f"数据类型: {type(data)}, 数据条数: {len(data) if hasattr(data, '__len__') else 'N/A'}")
                return data
            except Exception as e:
                logger.error(f"读取文件 {path} 时出错: {e}")
                return None
        else:
            print(f'文件{path}不存在，尝试从接口获取数据')
            try:
                # 从接口获取数据并保存到文件
                path ,all_transaction_data= self.card_detail.get_all_card_detail_info(
                    status='completed',
                    date=date
                )

                # 读取刚刚获取并保存的文件
                with open(path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                print(f"成功读取文件 {path}")
                # print(f"数据类型: {type(data)}, 数据条数: {len(data) if hasattr(data, '__len__') else 'N/A'}")
                return data
            except Exception as e:
                logger.error(f"获取或读取文件 {path} 时出错: {e}")
                return None

    def get_card_transaction_count(self,  type_value, transaction_data,
                                   get_body):
        """
        获取卡交易记录统计
        :param type_key: 交易类型键名
        :param type_value: 交易类型值
        :param transaction_data: 交易数据列表
        :param get_body: 获取交易记录的字段名列表 [金额字段名, 手续费字段名]
        :return: 总金额, 总手续费
        """

        [amount, fee] = get_body
        data_list = []
        for data in transaction_data:
            if isinstance(data, dict):
                if data.get('transaction_type') == type_value:
                    data_list.append(data)
        total_amount_list = []
        total_fee_list = []
        for i in data_list:
            amount_str = float(i.get(amount))  # 使用动态字段名
            fee_str = float(i.get(fee))
            total_fee_list.append(fee_str)
            total_amount_list.append(amount_str)
        total_amount = sum(total_amount_list)
        total_fee = sum(total_fee_list)

        print(f"币种: {type_value}, 总金额: {total_amount}, 总手续费: {total_fee}")
        return total_amount, total_fee

    def get_card_completed_transaction_record(self, type_value, date):
        """
        获取卡交易完成记录的金额和手续费统计
        :param type_key: 交易类型键名
        :param type_value: 交易类型值
        :return: 总金额, 总手续费
        """
        card_usda_amount = 0.0
        card_usda_fee = 0.0

        try:
            # 只获取一次数据，避免重复请求
            transaction_data = self.get_card_transaction_detail(
                date=date
            )

            total_amount, total_fee = self.get_card_transaction_count(
                type_value,
                transaction_data =transaction_data,
                get_body =['amount', 'fee']
            )

            card_usda_amount += total_amount
            card_usda_fee += total_fee

        except Exception as e:
            logger.error(f"处理USD卡交易数据时出错: {e}")

        # 更清晰地显示两个值
        print(f'卡交易完成记录({type_value}) - 金额: {card_usda_amount}, 手续费: {card_usda_fee}')
        data = [card_usda_amount, card_usda_fee]
        return data