import json
import os

from common.simple_request import HttpRequest
from common import read_and_save_tool
from common.get_time import GetTime
from common import logger
logger = logger.logger
"""
转出交易明细
"""

class AdminWithdrawPage:
    def __init__(self, admin_http=None):
        self.http_request = admin_http or HttpRequest(user_type='admin')

        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.get_time = GetTime()
    # 获取提现订单信息
    def get_withdraw_order_info(self,status,date):
        """
        获取提现订单信息
        :param status: 订单状态
        :param date: 日期
        :return: 提现订单信息
        """

        all_transaction_data = []
        page = 1
        while True:
            start_time, end_time = self.get_time.get_time_range(date)

            url = self.config_url + f'/admin/crypto/withdrawals?page={page}&take=100&business_type=chain_withdraw&transaction_status={status}&transaction_start_time={start_time}&transaction_end_time={end_time}'
            transaction_data = self.http_request.gets(url,nested_keys=['data','data'])
            if not transaction_data or len(transaction_data) == 0:  # 检查交易数据是否为空或长度为0，如果是则跳出循环
                break
            all_transaction_data.extend(transaction_data)
            # 检查是否有更多数据
            total_count = self.http_request.gets(url, nested_keys=['data', 'count'])
            if total_count and len(all_transaction_data) >= total_count:
                break

            page += 1

        logger.info(f"总共获取到{len(all_transaction_data)}条记录")
        # print(all_transaction_data)

        with open(f'chain_withdraw_{date}.json', 'w', encoding='utf-8') as f:
            json.dump(all_transaction_data, f, ensure_ascii=False, indent=4)
        #返回保存的路径
        if not hasattr(self, 'save_path'):
            self.save_path = os.getcwd()
        save_path = os.path.join(self.save_path, f'chain_withdraw_{date}.json')
        print(save_path)
        return save_path,all_transaction_data

    def get_withdraw_order_info_02(self,business_type,status,date):
        """
        获取提现订单信息
        :param status: 订单状态
        :param date: 日期
        :return: 提现订单信息
        """

        all_transaction_data = []
        page = 1
        while True:
            start_time, end_time = self.get_time.get_time_range(date)

            url = self.config_url + f'/admin/crypto/withdrawals?page={page}&take=100&business_type={business_type}&transaction_status={status}&transaction_start_time={start_time}&transaction_end_time={end_time}'
            transaction_data = self.http_request.gets(url,nested_keys=['data','data'])
            if not transaction_data or len(transaction_data) == 0:  # 检查交易数据是否为空或长度为0，如果是则跳出循环
                break
            all_transaction_data.extend(transaction_data)
            # 检查是否有更多数据
            total_count = self.http_request.gets(url, nested_keys=['data', 'count'])
            if total_count and len(all_transaction_data) >= total_count:
                break

            page += 1

        logger.info(f"总共获取到{len(all_transaction_data)}条记录")
        # print(all_transaction_data)

        with open(f'{business_type}{date}.json', 'w', encoding='utf-8') as f:
            json.dump(all_transaction_data, f, ensure_ascii=False, indent=4)
        #返回保存的路径
        if not hasattr(self, 'save_path'):
            self.save_path = os.getcwd()
        save_path = os.path.join(self.save_path, f'{business_type}{date}.json')
        print(save_path)
        return save_path,all_transaction_data
  #获取台账部分信息：amount,fee ,count
    def get_chain_withdraw_account_info(self,date):
        """
        获取充值订单信息
        :param status: 订单状态
        :param date: 日期
        :return: 提现订单信息
        """

        """
               获取充值订单信息
               :param date: 日期
               :return: 提现订单信息
               """
        currency_list = ['USDC', 'USDT']
        save_path, all_transaction_data = self.get_withdraw_order_info_02(business_type='chain_withdraw',status='completed', date=date)

        # 提取amount,fee,count
        amount = 0
        fee = 0
        count = 0
        for currency in currency_list:
            for transaction in all_transaction_data:
                print(transaction)
                if transaction['from_currency'] == currency:
                    if transaction['process_status'] =='completed':


                        amount += abs(float(transaction['amount']))
                        fee += abs(float(transaction['fee']))
                        count += 1

            logger.info(f"币种,{currency}总金额: {amount}总手续费: {fee}总数量: {count}")

        return amount, fee, count

    def get_vcc_in_account_info(self, date):
        """
        获取充值订单信息
        :param status: 订单状态
        :param date: 日期
        :return: 提现订单信息
        """

        """
               获取充值订单信息
               :param date: 日期
               :return: 提现订单信息
               """
        currency_list = ['USDC', 'USDT']
        save_path, all_transaction_data = self.get_withdraw_order_info_02(business_type='card_account_recharge',
                                                                          status='completed', date=date)

        # 提取amount,fee,count
        amount = 0
        fee = 0
        count = 0
        for currency in currency_list:
            for transaction in all_transaction_data:
                if transaction['from_currency'] == currency:
                    if transaction['process_status'] =='completed':

                        print( transaction)
                        amount += abs(float(transaction['to_currency_amount']))
                        fee += abs(float(transaction['fee']))
                        count += 1

            logger.info(f"币种,{currency}总金额: {amount}总手续费: {fee}总数量: {count}")

        return amount, fee, count


if __name__ == '__main__':
    withdraw = AdminWithdrawPage()
    # withdraw.get_withdraw_order_info(status='completed',date='202509')
    # withdraw.get_chain_withdraw_account_info(date='20251205')
    # data_list = ['20251201','20251202','20251203','20251204','20251205','20251206','20251207','20251208','20251209','20251210','20251211']
    # for date in data_list:
    #     # withdraw.get_chain_withdraw_account_info(date)
    #     withdraw.get_vcc_in_account_info(date)
    # withdraw.get_vcc_in_account_info('20251211')
    withdraw.get_chain_withdraw_account_info('202511')