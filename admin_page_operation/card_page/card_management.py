import json
from collections import defaultdict
import os
from common.simple_request import HttpRequest
from common import read_and_save_tool
from common.get_time import GetTime
from common import logger
logger = logger.logger

"""


数字商务卡管理
"""
class AdminCardManagement:
    def __init__(self, http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()

        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.time = GetTime()

    def get_all_card_people_detail_info(self):

        """
        自动获取所有卡交易详情信息
        :param status: 订单状态
        :param date: 日期
        :param take: 每页数量，默认为100
        :return: 所有卡交易详情信息
         transaction_type :card_transaction_authorization_fee
                             card_deposit
                             card_consume
                             card_to_card_account
                             card_refund
                             card_reversal
                            card_atm
        """
        all_transaction_data = []
        page = 1

        while True:
            # start_time, end_time = self.time.get_day_range(date)
            url = self.config_url + f'/admin/virtual-card/get-all-cards?page={page}&take=100'
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

        with open(f'card_people_detail.json', 'w', encoding='utf-8') as f:
            json.dump(all_transaction_data, f, ensure_ascii=False, indent=4)
        #返回保存的路径
        if not hasattr(self, 'save_path'):
            self.save_path = os.getcwd()
        path = os.path.join(self.save_path, f'card_people_detail.json')
        # print(path)
        return path,all_transaction_data




    def process_transaction_data(self,date):
        path, all_transaction_data = self.get_all_card_people_detail_info()
        user_list = []
        card_holder_list = []
        Enterprise_count = 0
        card_count = 0
        Valid_card_count = 0
        Physical_card_count = 0
        Virtual_card_count = 0
        Cardholder_count = 0
        for i in all_transaction_data:
            if date in i['b_created_at']: #"b_created_at": "2025-12-11T07:34:04.009Z",
                card_count+=1
                user_id= i['b_account_id']
                card_holder_id = i['vch_account_id']
                card_holder_list.append(card_holder_id)
                user_list.append(user_id)
                if i['status'] == 'ACTIVE':
                    Valid_card_count += 1
                    if i['type'] == 'Physical':
                        Physical_card_count += 1
                    elif i['type'] == 'Virtual':
                        Virtual_card_count += 1

            Enterprise_count = len(set(user_list))
            Cardholder_count = len(set(card_holder_list))
        logger.info(f"{date} 总共获取到{Enterprise_count}家企业，{card_count}张卡,{Valid_card_count}个有效卡,{Physical_card_count}张实体卡,{Virtual_card_count}张虚拟卡,{Cardholder_count}位持卡人")
        return Enterprise_count,card_count,Valid_card_count,Physical_card_count,Virtual_card_count,Cardholder_count
    def get_new_enterprise_statistics(self):
        """
        优化后的函数：遍历时间列表，统计每天新增企业数量
        """
        list_date = ['2025-12-01', '2025-12-02', '2025-12-03', '2025-12-04', '2025-12-05', '2025-12-06', '2025-12-07',
                     '2025-12-08', '2025-12-09', '2025-12-10', '2025-12-11', '2025-12-12', '2025-12-13', '2025-12-14',
                     '2025-12-15', '2025-12-16', '2025-12-17', '2025-12-18', '2025-12-19', '2025-12-20', '2025-12-21',
                     '2025-12-22', '2025-12-23', '2025-12-24', '2025-12-25', '2025-12-26', '2025-12-27', '2025-12-28', '2025-12-29','2025-12-30','2025-12-31']

        all_date_data = []
        cumulative_user_set = set()  # 累积的企业ID集合，用于去重

        for date in list_date:
            path, all_transaction_data = self.get_all_card_people_detail_info()
            user_list = []

            # 收集当前日期创建的所有企业ID
            for item in all_transaction_data:
                if date in item['b_created_at']:
                    user_id = item['b_account_id']
                    user_list.append(user_id)

            # 当天企业的集合
            current_day_users = set(user_list)

            # 计算新增企业数量（不在之前累积集合中的企业）
            new_users = current_day_users - cumulative_user_set
            new_user_count = len(new_users)

            # 更新累积集合
            cumulative_user_set.update(current_day_users)

            # 添加到结果列表
            all_date_data.append({
                'date': date,
                'Enterprise_count': len(current_day_users),
                'new_Enterprise_count': new_user_count,
                'user_list': list(current_day_users)
            })

            logger.info(f"{date} 新增企业数量: {new_user_count}")

        return all_date_data

    def get_card_count(self,date,account_id):
        path, all_transaction_data = self.get_all_card_people_detail_info()
        card_count = 0

        for i in all_transaction_data:
            if date in i['b_created_at']:

                if i['account_id'] == account_id:
                    card_count += 1
        print(card_count)
        return card_count







if __name__ == '__main__':
    times = GetTime()
    month_list = times.get_month_for_year(2025)
    day_list = times.get_day_for_month(2025, 12)
    CardManagement = AdminCardManagement()
    account_id = 'cb828d40-674c-4f6a-b42d-8a0a4bbf6fac'
    # for i in list_date:
    #     CardManagement.process_transaction_data(i)
    #获取卡数量



    # # list_date = ['2025-12-01','2025-12-02', '2025-12-03', '2025-12-04', '2025-12-05', '2025-12-06', '2025-12-07', '2025-12-08', '2025-12-09', '2025-12-10','2025-12-11']
    # # all_date_data = []
    # #
    # result_data = CardManagement.get_new_enterprise_statistics()
    #
    # # 直接打印结果
    # all_num = 0
    # print("\n每日新增企业详细数据:")
    # for item in result_data:
    #     print(f"日期: {item['date']}, 当天企业数: {item['Enterprise_count']}, 新增企业: {item['new_Enterprise_count']}")
    #     all_num += item['new_Enterprise_count']
    # print(f"总新增企业数: {all_num}")


    #获取本月发卡量
    CardManagement.get_card_count('2025-06',account_id)
    #获取本年发卡量
    # card_all = 0.0
    # for i in month_list:
    #     card_count = CardManagement.get_card_count(i,account_id)
    #     card_count = card_count or 0  # 如果 card_count 为 None，则使用 0
    #     card_all += card_count
    # print(card_all)


    # list_months = ['2025-12', '2025-11', '2025-10', '2025-09', '2025-08', '2025-07', '2025-06', '2025-05', '2025-04',
    #                '2025-03', '2025-02', '2025-01']
    # card_num = 0
    # for month in list_months:
    #     _, card_count, _, _, _, _ = CardManagement.process_transaction_data(month)
    #     card_num += card_count
    # print(card_num)
