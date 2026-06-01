import json
from collections import defaultdict
import os
from common.simple_request import HttpRequest
from common import read_and_save_tool
from common.get_time import GetTime
from common import logger
logger = logger.logger

"""
持卡人管理
"""
class AdminCardHoldersPage:

    def __init__(self, http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()

        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.time = GetTime()
    def get_card_holders_info(self):

        """
        获取所有持卡人信息
        :param date: 日期
        :return: 所有持卡人信息
        """
        all_transaction_data = []
        page = 1
        while True:
            # start_time, end_time = self.time.get_day_range(date)
            url = self.config_url + f'/admin/virtual-card/get-all-holders?page={page}&take=100'
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

        with open(f'card_detail_all.json', 'w', encoding='utf-8') as f:
            json.dump(all_transaction_data, f, ensure_ascii=False, indent=4)
        # 返回保存的路径
        if not hasattr(self, 'save_path'):
            self.save_path = os.getcwd()
        path = os.path.join(self.save_path, f'card_detail_all.json')
        # print(path)
        return path, all_transaction_data
    def get_count_of_card_holders(self,created_at):
        count_num = 0
        path, all_transaction_data = self.get_card_holders_info()
        for data in all_transaction_data:
            if data['status'] == 'ACTIVE':
                if created_at in data['created_at']:
                    count_num += 1
        print(count_num)



if __name__ == '__main__':
    CardHolders = AdminCardHoldersPage()
    CardHolders.get_count_of_card_holders('2026-01')