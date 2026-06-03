import json
from collections import defaultdict
import os
from common.simple_request import HttpRequest
from common import read_and_save_tool
from common.get_time import GetTime
from common import logger
logger = logger.logger

"""


数字商务卡明细
"""
class AdminCardDetailPage:
    def __init__(self, admin_http=None):
        self.http_request = admin_http or HttpRequest(user_type='admin')

        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.time = GetTime()

    def get_all_card_detail_info(self, status, date):

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
            start_time, end_time = self.time.get_time_range(date)
            url = self.config_url + f'/admin/virtual-card/get-all-transactions?page={page}&take=20&transaction_sub_type=card&status={status}&created_at[]={start_time}&created_at[]={end_time}'
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
        #返回保存的路径
        if not hasattr(self, 'save_path'):
            self.save_path = os.getcwd()
        path = os.path.join(self.save_path, f'card_detail_{date}.json')
        # print(path)
        return path,all_transaction_data
    def get_all_card_detail_info_02(self, transaction_sub_type,status, date):

        """
        自动获取所有卡交易详情信息card
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
            start_time, end_time = self.time.get_time_range(date)
            url = self.config_url + f'/admin/virtual-card/get-all-transactions?page={page}&take=100transaction_sub_type={transaction_sub_type}&status={status}&created_at[]={start_time}&created_at[]={end_time}'
            transaction_data = self.http_request.gets(url, nested_keys=['data', 'list'])

            if not transaction_data or len(transaction_data) == 0:  # 检查交易数据是否为空或长度为0，如果是则跳出循环
                break
            all_transaction_data.extend(transaction_data)
            # print(len(transaction_data))
            # 检查是否有更多数据
            total_count = self.http_request.gets(url, nested_keys=['data', 'total'])
            if total_count and len(all_transaction_data) >= total_count:
                break

            page += 1

        logger.info(f"总共获取到{len(all_transaction_data)}条记录")
        # print(all_transaction_data)

        with open(f'card_detail{date}.json', 'w', encoding='utf-8') as f:
            json.dump(all_transaction_data, f, ensure_ascii=False, indent=4)
        #返回保存的路径
        if not hasattr(self, 'save_path'):
            self.save_path = os.getcwd()
        path = os.path.join(self.save_path, f'card_detail_{date}.json')
        # print(path)
        return path,all_transaction_data

    def process_transaction_data(self,date):

        target_date = '202601'
        path, all_transaction_data = self.get_all_card_detail_info_02('card','completed', date)
        # print(all_transaction_data)
        # 初始化计数器
        consume_count = 0
        local_consume_count = 0
        local_amount = 0.0
        local_fee = 0.0
        no_local_count = 0
        no_local_amount = 0.0
        no_local_fee = 0.0
        atm_count = 0
        atm_amount = 0.0
        atm_fee = 0.0
        return_count = 0
        return_amount = 0.0
        return_fee = 0.0
        clearing_refund_count = 0
        clearing_refund_amount = 0.0
        clearing_refund_fee = 0.0
        clearing_deduction_count = 0
        clearing_deduction_amount = 0.0
        clearing_deduction_fee = 0.0
        reversal_count = 0
        reversal_amount = 0.0
        reversal_fee = 0.0
        advice_count =0
        advice_amount = 0.0
        advice_fee = 0.0
        consume_amount = 0.0
        consume_fee = 0.0
        card_transaction_authorization_fee_count = 0
        card_transaction_authorization_fees = 0.0

        amount_1 = 0.0
        try:
            for transaction in all_transaction_data:
                if transaction['transaction_type'] == 'card_consume': #消费（本地和跨境）
                    consume_count += 1
                    consume_amount += abs(float(transaction['amount']))
                    consume_fee = abs(float(transaction['fee']))
                    if transaction['merchant_country'] == 'HK':#本地消费
                        local_consume_count += 1
                        local_amount += abs(float(transaction['amount']))
                        local_fee += abs(float(transaction['fee']))
                    else:
                        no_local_count += 1
                        no_local_amount += abs(float(transaction['amount']))
                        no_local_fee += abs(float(transaction['fee']))
                    amount_1 += abs(float(transaction['amount']))
                if transaction['transaction_type'] == 'card_transaction_authorization_fee':
                    card_transaction_authorization_fee_count += 1
                    card_transaction_authorization_fees += abs(float(transaction['fee']))

                    print(card_transaction_authorization_fees)
                if transaction['transaction_type'] == 'card_atm': #atm取现
                    atm_count += 1
                    atm_amount += abs(float(transaction['amount']))
                    atm_fee += abs(float(transaction['fee']))
                if transaction['transaction_type'] == 'card_refund': #退款
                    return_count += 1
                    return_amount += abs(float(transaction['amount']))
                    return_fee += abs(float(transaction['fee']))
                    amount_1 += abs(float(transaction['amount']))
                if transaction['transaction_type'] == 'card_clearing_refund': #卡清算退款
                    clearing_refund_count += 1
                    clearing_refund_amount += abs(float(transaction['amount']))
                    clearing_refund_fee += abs(float(transaction['fee']))
                    amount_1 += abs(float(transaction['amount']))
                if transaction['transaction_type'] == 'card_clearing_deduction': #卡清算扣款
                    clearing_deduction_count += 1
                    clearing_deduction_amount += abs(float(transaction['amount']))
                    clearing_deduction_fee += abs(float(transaction['fee']))

                    amount_1 += abs(float(transaction['amount']))
                if transaction['transaction_type'] == 'card_reversal': #退回
                    reversal_count += 1
                    # a = abs(float(transaction['amount']))
                    # if 65.0>a>70.0:

                    reversal_amount += abs(float(transaction['amount']))


                    reversal_fee += abs(float(transaction['fee']))
                    amount_1 += abs(float(transaction['amount']))
                    # print(transaction['id'])
                if transaction['transaction_type'] == 'card_advice':  # 拒绝
                    advice_count += 1
                    advice_amount += abs(float(transaction['amount']))
                    advice_fee += abs(float(transaction['fee']))
                    amount_1 += abs(float(transaction['amount']))




            logger.info(f'**********{date}消费次数为：{consume_count}个,金额：{consume_amount},手续费为：{consume_fee}**********')
            logger.info(f'本地消费次数为：{local_consume_count}个,金额：{local_amount},手续费为：{local_fee}')
            logger.info(f'跨境消费次数为：{no_local_count}个,金额：{no_local_amount},手续费为：{no_local_fee}')
            logger.info(f'授权次数为：{card_transaction_authorization_fee_count}个,金额：{card_transaction_authorization_fees}')
            logger.info(f'ATM取现次数为：{atm_count}个,金额：{atm_amount},手续费为：{atm_fee}')
            logger.info(f'退款次数为：{return_count}个,金额：{return_amount},手续费为：{return_fee}')
            logger.info(f'卡清算退款次数为：{clearing_refund_count}个,金额：{clearing_refund_amount},手续费为：{clearing_refund_fee}')
            logger.info(f'卡清算扣款次数为：{clearing_deduction_count}个,金额：{clearing_deduction_amount},手续费为：{clearing_deduction_fee}')
            logger.info(f'退回次数为：{reversal_count}个,金额：{reversal_amount},手续费为：{reversal_fee}')
            logger.info(f'拒绝次数为：{advice_count}个,金额：{advice_amount},手续费为：{advice_fee}')
            all_amount = (consume_amount
                          # + card_transaction_authorization_fees
                          # + atm_amount
                          + return_amount
                          + clearing_refund_amount
                          + clearing_deduction_amount
                          + reversal_amount
                          + advice_amount)
            print(all_amount)
            return all_amount
        except KeyError as e:
            logger.warning(f"数据字段缺失: {e}")
        except Exception as e:
            logger.warning(f"处理交易数据时发生错误: {e}")

    def get_all_card_detail_info_03(self,  status, date):

        """
        自动获取所有卡交易详情信息card
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
            start_time, end_time = self.time.get_time_range(date)
            url = self.config_url + f'/admin/virtual-card/get-all-transactions?page={page}&take=100&status={status}&created_at[]={start_time}&created_at[]={end_time}'
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
    def get_vcc_in_transaction_count(self,date):
        path, all_transaction_data = self.get_all_card_detail_info_02( 'card_account','completed', date)
        amount = 0
        fee = 0
        count = 0
        for transaction in all_transaction_data:
            if transaction['transaction_type'] =='vcc_in':
                # print( transaction)
                amount += abs(float(transaction['amount']))
                fee += abs(float(transaction['fee']))
                count += 1
        logger.info(f"{date}卡账户充值总金额: {amount}总手续费: {fee}总数量: {count}")
        return amount, fee, count

    def get_vcc_in_transaction_count_for_id(self, date,account_id):
        path, all_transaction_data = self.get_all_card_detail_info_02('card_account', 'completed', date)
        amount = 0
        fee = 0
        count = 0
        for transaction in all_transaction_data:
            if transaction['account_id'] == account_id:
                if transaction['transaction_type'] == 'vcc_in':
                    # print( transaction)
                    amount += abs(float(transaction['amount']))
                    fee += abs(float(transaction['fee']))
                    count += 1
        logger.info(f"{date}卡账户充值总金额: {amount}总手续费: {fee}总数量: {count}")

        return amount, fee, count


    def process_transaction_data_for_id(self, date,account_id):

        target_date = '202601'
        path, all_transaction_data = self.get_all_card_detail_info_02('card', 'completed', date)
        # print(all_transaction_data)
        # 初始化计数器
        consume_count = 0
        local_consume_count = 0
        local_amount = 0.0
        local_fee = 0.0
        no_local_count = 0
        no_local_amount = 0.0
        no_local_fee = 0.0
        atm_count = 0
        atm_amount = 0.0
        atm_fee = 0.0
        return_count = 0
        return_amount = 0.0
        return_fee = 0.0
        clearing_refund_count = 0
        clearing_refund_amount = 0.0
        clearing_refund_fee = 0.0
        clearing_deduction_count = 0
        clearing_deduction_amount = 0.0
        clearing_deduction_fee = 0.0
        reversal_count = 0
        reversal_amount = 0.0
        reversal_fee = 0.0
        advice_count = 0
        advice_amount = 0.0
        advice_fee = 0.0
        card_transaction_authorization_fee_count = 0
        card_transaction_authorization_fees = 0.0
        try:
            for transaction in all_transaction_data:
                if transaction['account_id'] == account_id:

                    if transaction['transaction_type'] == 'card_consume':  # 消费（本地和跨境）
                        consume_count += 1
                        if transaction['merchant_country'] == 'HK':  # 本地消费
                            local_consume_count += 1
                            local_amount += abs(float(transaction['amount']))
                            local_fee += abs(float(transaction['fee']))
                        else:
                            no_local_count += 1
                            no_local_amount += abs(float(transaction['amount']))
                            no_local_fee += abs(float(transaction['fee']))
                    if transaction['transaction_type'] == 'card_transaction_authorization_fee':
                        card_transaction_authorization_fee_count += 1
                        card_transaction_authorization_fees += abs(float(transaction['fee']))

                        print(card_transaction_authorization_fees)
                    if transaction['transaction_type'] == 'card_atm':  # atm取现
                        atm_count += 1
                        atm_amount += abs(float(transaction['amount']))
                        atm_fee += abs(float(transaction['fee']))
                    if transaction['transaction_type'] == 'card_refund':  # 退款
                        return_count += 1
                        return_amount += abs(float(transaction['amount']))
                        return_fee += abs(float(transaction['fee']))
                    if transaction['transaction_type'] == 'card_clearing_refund':  # 卡清算退款
                        clearing_refund_count += 1
                        clearing_refund_amount += abs(float(transaction['amount']))
                        clearing_refund_fee += abs(float(transaction['fee']))
                    if transaction['transaction_type'] == 'card_clearing_deduction':  # 卡清算扣款
                        clearing_deduction_count += 1
                        clearing_deduction_amount += abs(float(transaction['amount']))
                        clearing_deduction_fee += abs(float(transaction['fee']))
                    if transaction['transaction_type'] == 'card_reversal':  # 退回
                        reversal_count += 1
                        reversal_amount += abs(float(transaction['amount']))

                        reversal_fee += abs(float(transaction['fee']))
                    if transaction['transaction_type'] == 'card_advice':  # 拒绝
                        advice_count += 1
                        advice_amount += abs(float(transaction['amount']))
                        advice_fee += abs(float(transaction['fee']))

            print(f'当前操作的时间是{date}')
            logger.info(f'本地消费次数为：{local_consume_count}个,金额：{local_amount},手续费为：{local_fee}')
            logger.info(f'跨境消费次数为：{no_local_count}个,金额：{no_local_amount},手续费为：{no_local_fee}')
            logger.info(
                f'授权次数为：{card_transaction_authorization_fee_count}个,金额：{card_transaction_authorization_fees}')
            logger.info(f'ATM取现次数为：{atm_count}个,金额：{atm_amount},手续费为：{atm_fee}')
            logger.info(f'退款次数为：{return_count}个,金额：{return_amount},手续费为：{return_fee}')
            logger.info(
                f'卡清算退款次数为：{clearing_refund_count}个,金额：{clearing_refund_amount},手续费为：{clearing_refund_fee}')
            logger.info(
                f'卡清算扣款次数为：{clearing_deduction_count}个,金额：{clearing_deduction_amount},手续费为：{clearing_deduction_fee}')
            logger.info(f'退回次数为：{reversal_count}个,金额：{reversal_amount},手续费为：{reversal_fee}')
            logger.info(f'拒绝次数为：{advice_count}个,金额：{advice_amount},手续费为：{advice_fee}')
            all_amount = (local_amount
                          + no_local_amount
                          # + card_transaction_authorization_fees + atm_amount
                          + return_amount + clearing_refund_amount
                          + clearing_deduction_amount
                          + reversal_amount
                          + advice_amount)
            print(all_amount)
            return all_amount
        except KeyError as e:
            logger.warning(f"数据字段缺失: {e}")
        except Exception as e:
            logger.warning(f"处理交易数据时发生错误: {e}")




    #计算开卡费用
    def get_create_fee(self,date):
        path,all_transaction_data = self.get_all_card_detail_info_02(transaction_sub_type = 'card_account',status = 'completed', date = date)
        create_physical_count = 0
        create_physical_amount = 0.0
        create_virtual_count = 0
        create_virtual_amount = 0.0
        for i in all_transaction_data:
            if i['transaction_type'] == 'card_create_physical':
                create_physical_amount += abs(float(i['fee']))
                create_physical_count += 1
            if i['transaction_type'] == 'card_create_virtual':
                create_virtual_amount += abs(float(i['fee']))
                create_virtual_count += 1
        logger.info(f'创建实体卡次数为：{create_physical_count}个,金额：{create_physical_amount}')
        logger.info(f'创建虚拟卡次数为：{create_virtual_count}个,金额：{create_virtual_amount}')







if __name__ == '__main__':
    times = GetTime()
    month_list = times.get_month_for_year(2025)
    day_list = times.get_day_for_month(2025, 12)


    CardDetail = AdminCardDetailPage()
    account_id = 'cb828d40-674c-4f6a-b42d-8a0a4bbf6fac'






    #卡账户充值
    # CardDetail.get_vcc_in_transaction_count('202512')
    #获取每天卡账户充值明细
    # for i in day_list:
    #     CardDetail.get_vcc_in_transaction_count(i)
    #获取某企业某月的充值
    # CardDetail.get_vcc_in_transaction_count_for_id('202512',account_id)

    #获取一年的商务卡明细
    # all_num = 0.0
    # for i in month_list:
    #     amount = CardDetail.process_transaction_data(i)
    #     all_num += amount
    #获取商务卡当月明细
    # for i in day_list:
    #
    #     amount = CardDetail.process_transaction_data(i)
    #获取某月的商务卡明细
    # CardDetail.process_transaction_data('202512')

    #获取某月某家的商务卡明细
    # CardDetail.process_transaction_data_for_id('202512',account_id)

    #获取当年商务卡明细
    # all_num = 0.0
    # for i  in month_list:
    #     num = CardDetail.process_transaction_data_for_id(i,account_id)
    #     print(f'{i}的交易金额为：{num}')
    #     all_num += num
    # print(all_num)




    #计算开卡费
    CardDetail.get_create_fee('20260128')