import json
from collections import defaultdict
import os
from common.simple_request import HttpRequest
from common import read_and_save_tool
from common.get_time import GetTime
from common import logger
logger = logger.logger

"""
卡账户明细
"""
class AdminCardAccountDetailPage:

    def __init__(self, http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()

        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.time = GetTime()
    def get_card_holders_info(self,date):

        """
        获取所有持卡人信息
        :param date: 日期
        :return: 所有持卡人信息
        """
        all_transaction_data = []
        page = 1
        while True:
            start_time, end_time = self.time.get_day_range(date)
            url = self.config_url + f'/admin/virtual-card/get-all-transactions?page={page}&take=50&status=completed&transaction_sub_type=card_account&created_at[]={start_time}&created_at[]={end_time}'
            transaction_data = self.http_request.gets(url, nested_keys=['data', 'list'])
            if not transaction_data or len(transaction_data) == 0:  # 检查交易数据是否为空或长度为0，如果是则跳出循环
                break
            all_transaction_data.extend(transaction_data)
            # 检查是否有更多数据
            total_count = self.http_request.gets(url, nested_keys=['data', 'total'])
            if total_count and len(all_transaction_data) >= total_count:
                break

            page += 1

        logger.info(f"总共获取到{len(all_transaction_data)}条记录")
        # print(all_transaction_data)

        with open(f'card_detail_{date}.json', 'w', encoding='utf-8') as f:
            json.dump(all_transaction_data, f, ensure_ascii=False, indent=4)
        # 返回保存的路径
        if not hasattr(self, 'save_path'):
            self.save_path = os.getcwd()
        path = os.path.join(self.save_path, f'card_detail_{date}.json')
        # print(path)
        return path, all_transaction_data

    # 处理台账记录： 卡账户充值，卡账户转出 次数
    def process_transaction_data(self):
        transaction_type = ['vcc_out', 'vcc_in']
        path, all_transaction_data = self.get_card_holders_info('20251204')

        # 使用字典存储不同类型交易的统计信息
        stats = {}
        for type in transaction_type:
            stats[type] = {'count': 0, 'amount': 0.0, 'fee': 0.0}

        # 一次遍历完成所有统计
        for transaction in all_transaction_data:
            trans_type = transaction['transaction_type']
            if trans_type in transaction_type:
                try:
                    stats[trans_type]['count'] += 1
                    stats[trans_type]['amount'] += abs(float(transaction['amount']))
                    stats[trans_type]['fee'] += abs(float(transaction['fee']))
                except (ValueError, KeyError) as e:
                    logger.warning(f"处理交易数据时出现错误: {e}, 数据: {transaction}")
                    continue

        # 输出统计结果
        for type in transaction_type:
            count = stats[type]['count']
            amount = stats[type]['amount']
            fee = stats[type]['fee']
            logger.info(f'{type}充值次数为：{count}个,充值金额：{amount},手续费为：{fee}')


if __name__ == '__main__':
    CardHolders = AdminCardAccountDetailPage()
    CardHolders.process_transaction_data()