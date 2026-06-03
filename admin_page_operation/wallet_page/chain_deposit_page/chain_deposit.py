from common.simple_request import HttpRequest
from common import read_and_save_tool
from common.get_time import GetTime
from common import logger
import json
import os
logger = logger.logger

""""

充值交易明细
"""
class AdminDepositPage:
    def __init__(self, admin_http=None):
        self.http_request = admin_http or HttpRequest(user_type='admin')

        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.get_time = GetTime()
    # 获取充值订单信息
    def get_deposit_order_info(self,status,date):
        """
               获取充值订单信息
               :param status: 订单状态
               :param date: 日期
               :return: 提现订单信息
               """

        all_transaction_data = []
        page = 1
        while True:
            start_time, end_time = self.get_time.get_time_range(date)
            url = self.config_url + f'/admin/crypto/deposits?page={page}&take=100&business_type=chain_deposit&transaction_status={status}&transaction_start_time={start_time}&transaction_end_time={end_time}'
            transaction_data = self.http_request.gets(url, nested_keys=['data', 'data'])
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

        with open(f'chain_deposit{date}.json', 'w', encoding='utf-8') as f:
            json.dump(all_transaction_data, f, ensure_ascii=False, indent=4)
        # 返回保存的路径
        if not hasattr(self, 'save_path'):
            self.save_path = os.getcwd()
        save_path = os.path.join(self.save_path, f'chain_deposit_{date}.json')
        print(save_path)
        return save_path,all_transaction_data
        # 获取充值订单信息

    def get_deposit_order_info_02(self, business_type,status, date):
        """
               获取充值订单信息chain_deposit
               :param status: 订单状态
               :param date: 日期
               :return: 提现订单信息
               """

        all_transaction_data = []
        page = 1
        while True:
            start_time, end_time = self.get_time.get_time_range(date)
            url = self.config_url + f'/admin/crypto/deposits?page={page}&take=100&business_type={business_type}&transaction_status={status}&transaction_start_time={start_time}&transaction_end_time={end_time}'
            transaction_data = self.http_request.gets(url, nested_keys=['data', 'data'])
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
        # 返回保存的路径
        if not hasattr(self, 'save_path'):
            self.save_path = os.getcwd()
        save_path = os.path.join(self.save_path, f'{business_type}{date}.json')
        print(save_path)
        return save_path, all_transaction_data





    #获取台账部分信息：amount,fee ,count
    def get_deposit_account_info(self,date):
        """
        获取充值订单信息
        :param date: 日期
        :return: 提现订单信息
        """
        currency_list= ['USDC','USDT']
        save_path, all_transaction_data = self.get_deposit_order_info_02(business_type = 'chain_deposit',status='completed',date=date)

        # 提取amount,fee,count
        amount = 0
        fee = 0
        count = 0
        for currency in currency_list:
            for transaction in all_transaction_data:
                if transaction['to_currency'] == currency:
                    amount += abs(float(transaction['amount']))
                    fee += abs(float(transaction['fee']))
                    count += 1

            logger.info(f"币种,{currency}总金额: {amount}总手续费: {fee}总数量: {count}")

        return amount,fee,count


    def get_card_vcc_out_info(self,date):
        """
           获取充值订单信息
           :param date: 日期
           :return: 提现订单信息
         """
        business_type = ['card_account_recharge','card_account_to_wallet']
        currency_list = ['USDC', 'USDT']
        save_path, all_transaction_data = self.get_deposit_order_info_02(business_type='card_account_to_wallet',
                                                                        status='completed', date=date)

        # 提取amount,fee,count
        amount = 0
        fee = 0
        count = 0
        for currency in currency_list:
           for transaction in all_transaction_data:
               if transaction['to_currency'] == currency:
                   amount += abs(float(transaction['usd_amount']))
                   fee += abs(float(transaction['fee']))
                   count += 1

           logger.info(f"币种,{currency}总金额: {amount}总手续费: {fee}总数量: {count}")

        return amount, fee, count







if __name__ == '__main__':
    Deposit = AdminDepositPage()
    # Deposit.get_deposit_order_info(status='completed',date='202512')
    # Deposit.get_deposit_account_info(date='20251210')
    data_list = ['202511', '202512']
    for date in data_list:
        Deposit.get_deposit_account_info(date)
        # Deposit.get_card_vcc_out_info(date)

