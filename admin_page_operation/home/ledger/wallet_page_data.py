import json
from calendar import month

from common.Sql import DatabaseConnection
from common.get_time import GetTime
from common.simple_request import HttpRequest
from common import read_and_save_tool
from common import logger
from admin_page_operation.wallet_page.pay_in_page.pay_in import AdminPayInPage
from admin_page_operation.wallet_page.pay_out_page.pay_out import AdminPayOutPage
from admin_page_operation.checkout_page.checkout import AdminCheckout
from admin_page_operation.RYT_page.RYT import AdminRYTPage
from admin_page_operation.wallet_page.chain_deposit_page.chain_deposit import AdminDepositPage
from admin_page_operation.wallet_page.chain_withdraw_page.chain_withdraw import AdminWithdrawPage
import os
import json


logger = logger.logger

"""
交易趋势图：
on-ramp：法币充值的到账数量，包含手续费，换算为USD
off-ramp：加密付款的支付数量，包含手续费，换算为USD
AX-Card：卡消费 + 清算扣款 + 手续费 + 交易授权费，所有值为增量，遇到退款为 -xx 。
AX-Wallet：加密付款、链上充值、法币充值、链上提现、收单提现、RYT申购和赎回，包含手续费，换算为USD。
"""
class WalletPageData:
    """
    页面接口数据
    """
    def __init__(self, admin_http=None):
        self.http_request = admin_http or HttpRequest(user_type='admin')
        self.config = read_and_save_tool.ConfigTools()
        self.admin_url = self.config.get_url_data()
        self.currency = ['USDT','USDC']
        self.pay_in = AdminPayInPage()
        self.pay_out = AdminPayOutPage()
        self.checkout = AdminCheckout()
        self.ryt_operation = AdminRYTPage()
        self.deposit = AdminDepositPage()
        self.withdraw = AdminWithdrawPage()
        self.sql=DatabaseConnection

    def get_sql_data(self,currency):
        self.sql = DatabaseConnection()
        if self.sql.connect():
            result = self.sql.execute_sql("SELECT current_database();")
            if result:
                print(f"当前数据库: {result[0][0]}")
            self.sql.disconnect()

        with DatabaseConnection() as self.sql:
            # 执行查询
            result = self.sql.execute_sql(f"select rate from currency_rate c where c.from_currency = '{currency}' and c.to_currency = 'USD';")



            print(f'当前币种是{currency},汇率是{result[0][0]}')
            # print(result_usdc[0][0])
            # print(result_usdt[0][0])
            return result[0][0]

    def get_wallet_transaction_detail(self,file_name,date,transaction_data):
        """
        获取当前路径下以card_transaction_detail_{date}.json 文件的内容
        :param date: 日期字符串，格式如 '202510'
        :return: JSON文件内容解析后的数据
        """
        save_path = os.getcwd()
        path = os.path.join(save_path, f'{file_name+date}.json')

        # 先判断文件是否存在
        if os.path.exists(path):
            print(f'文件{path}已存在，直接读取')
            try:
                # 读取并解析JSON文件
                with open(path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                print(f"文件{path}已存在，直接读取成功读取文件 ")
                print(f"数据类型: {type(data)}, 数据条数: {len(data) if hasattr(data, '__len__') else 'N/A'}")
                return data
            except Exception as e:
                logger.error(f"读取文件 {path} 时出错: {e}")
                return None
        else:
            print(f'文件{path}不存在，尝试从接口获取数据')
            try:
                # 从接口获取数据并保存到文件
                # path ,all_transaction_data= self.card_detail.get_all_card_detail_info(
                #     status='completed',
                #     date=date
                # )
                if transaction_data :

                    # 读取刚刚获取并保存的文件
                    with open(path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                    print(f"成功读取文件 {path}")
                    # print(f"数据类型: {type(data)}, 数据条数: {len(data) if hasattr(data, '__len__') else 'N/A'}")
                    return data
            except Exception as e:
                logger.error(f"获取或读取文件 {path} 时出错: {e}")
                return None

    def get_wallet_transaction_count(self, type_key, type_value, transaction_data, get_body):
        """
        获取钱包交易记录统计
        :param type_key: 类型键名
        :param type_value: 类型值
        :param transaction_data: 交易数据列表
        :param get_body: 获取交易记录的字段名列表 [amount_field, fee_field]
        :return: 总金额, 总手续费
        """
        [amount_field, fee_field] = get_body
        total_amount = 0.0
        total_fee = 0.0
        data_list = []
        id_no = []
        # 筛选符合条件的数据
        for data in transaction_data:
            if isinstance(data, dict) and data.get(type_key) == type_value:
                data_list.append(data)

        print(f'获取{type_value}钱包交易记录数 {len(data_list)}')

        # 统计总金额和总手续费
        for item in data_list:
            id_num = item.get('id_no')
            id_no.append(id_num)
            # print(f"id_no:{id_num}")
            # 处理金额
            try:
                amount_value = item.get(amount_field)
                amount_float = float(amount_value) if amount_value is not None else 0.0
                # print(f"金额:{amount_value}")
            except (ValueError, TypeError):
                amount_float = 0.0
            total_amount += amount_float
            # print(f'amount_str:{amount_float}, 累计总额:{total_amount}')


            # 处理手续费
            try:
                fee_value = item.get(fee_field)
                fee_float = float(fee_value) if fee_value is not None else 0.0
                # print(f"手续费:{fee_float}")
            except (ValueError, TypeError):
                fee_float = 0.0
            total_fee += fee_float
            # print(f'fee_str:{fee_float}, 累计手续费:{total_fee}')

        print(f"币种: {type_value}, 总金额: {total_amount}, 总手续费: {f'{total_fee:.10f}'}")

        return total_amount, total_fee


    def get_wallet_transaction_count_for_id(self, type_key, type_value, transaction_data, get_body,account_id):
        """
        根据企业id获取
        获取钱包交易记录统计
        :param type_key: 类型键名
        :param type_value: 类型值
        :param transaction_data: 交易数据列表
        :param get_body: 获取交易记录的字段名列表 [amount_field, fee_field]
        :return: 总金额, 总手续费
        """
        [amount_field, fee_field] = get_body
        total_amount = 0.0
        total_fee = 0.0
        data_list = []
        id_no = []
        # 筛选符合条件的数据
        for data in transaction_data:
            if isinstance(data, dict) and data.get(type_key) == type_value :
                if account_id == data['account_id']:
                    data_list.append(data)

        print(f'获取{type_value}钱包交易记录数 {len(data_list)}')

        # 统计总金额和总手续费
        for item in data_list:
            id_num = item.get('id_no')
            id_no.append(id_num)
            # print(f"id_no:{id_num}")
            # 处理金额
            try:
                amount_value = item.get(amount_field)
                amount_float = float(amount_value) if amount_value is not None else 0.0
                print(f"金额:{amount_value}")
            except (ValueError, TypeError):
                amount_float = 0.0
            total_amount += amount_float
            # print(f'amount_str:{amount_float}, 累计总额:{total_amount}')


            # 处理手续费
            try:
                fee_value = item.get(fee_field)
                fee_float = float(fee_value) if fee_value is not None else 0.0
                # print(f"手续费:{fee_float}")
            except (ValueError, TypeError):
                fee_float = 0.0
            total_fee += fee_float
            # print(f'fee_str:{fee_float}, 累计手续费:{total_fee}')

        print(f"币种: {type_value}, 总金额: {total_amount}, 总手续费: {f'{total_fee:.10f}'}")

        return total_amount, total_fee

    def get_usd_data(self, currency, amount):
        """
        获取转成USD的汇率并转成usd金额
        :param currency: 币种
        :param amount: 金额
        :return: 转成USD的金额
        """
        rate = self.get_sql_data(currency)
        try:
            # 获取价格数据
            # price_data = self.http_request.send_request(
            #     api_name='钱包-获取钱包列表',nested_keys=['data']
            #
            # )
            # print(currency,price_data)
            if currency == 'USDC':
                price_data =rate
            elif currency == 'USDT':
                price_data = rate
            # 安全地转换数据类型
            if price_data is not None:
                price = float(price_data)
            else:
                logger.warning(f"未能获取到 {currency} 的价格数据，使用默认值 0.0")
                price = 0.0

            amount_val = float(amount or 0.0)

            # 计算USD金额
            # print(amount_val)
            usd_amount = price * amount_val
            print(f'{amount_val} {currency} 转换为USD为 {usd_amount}')
            return usd_amount

        except (ValueError, TypeError) as e:
            logger.error(f"货币转换失败: currency={currency}, amount={amount}, error={e}")
            return 0.0

        # 把获取数据和转化usd 合并到一个方法

    def get_USD_value_of_transaction_record(self, currency, amount):
        """
        获取交易记录的USD值
        :param currency: 币种
        :param amount: 金额
        :return: 转成USD的金额
        """

        usd_amount = self.get_usd_data(currency, amount)
        return usd_amount

    """
    ==================================================================================================================================================
    这部分是钱包=转入明细
    
    """

    # 获取上充值的到账数量，包含手续费，换算为USD
    def get_wallet_in_completed_transaction_record(self, business_type,date):
        chain_deposit_usda_data =0.0
        amount = 0.0
        fee = 0.0
        data = self.deposit.get_deposit_order_info_02(
            business_type,
            status='completed',
            date=date
        )
        transaction_data = self.get_wallet_transaction_detail(business_type, date, data)
        for currency in self.currency:
            try:

                total_amount, total_fee = self.get_wallet_transaction_count(
                    'to_currency',
                    currency,
                    transaction_data,
                    ['amount', 'fee']
                )
                data = self.get_USD_value_of_transaction_record(currency, total_amount)
                chain_deposit_usda_data += data
                amount += total_amount
                fee += total_fee

                logger.info(f"{currency} 充值完成订单金额: {total_amount}, 手续费: {total_fee}, 转换为USD: {data}")
            except Exception as e:
                logger.error(f"处理币种 {currency} 的充值数据时出错: {e}")
                continue



    # 获取pay_in包含手续费，换算为USD
    def get_pay_in_transaction_record(self,date):
        self.get_wallet_in_completed_transaction_record('crypto_payin',date)


    #获取链上充值数据包含手续费，换成usd
    def get_chain_deposit_transaction_record(self, date):
        self.get_wallet_in_completed_transaction_record('chain_deposit',date)




    """

    这部分是钱包====>>>>>转出交易明细

    """

    def get_wallet_out_completed_transaction_record(self, business_type,date):
        chain_withdraw_usda_data = 0.0
        all_usdt = 0.0
        amount = 0.0
        fee = 0.0
        status_list = ['completed', 'pending']
        for i in status_list:
            data = self.withdraw.get_withdraw_order_info_02(
                business_type,
                status=i,
                date=date
            )
            transaction_data = self.get_wallet_transaction_detail(business_type, date, data)
            for currency in self.currency:
                try:

                    total_amount, total_fee = self.get_wallet_transaction_count(
                        'from_currency',
                        currency,
                        transaction_data,
                        ['amount', 'fee']
                    )
                    data = self.get_USD_value_of_transaction_record(currency, total_amount)
                    chain_withdraw_usda_data += data
                    amount += total_amount
                    fee += total_fee
                    logger.info(f"{currency} 充值完成订单金额: {total_amount}, 手续费: {total_fee}, 转换为USD: {data}")

                except Exception as e:
                    logger.error(f"处理币种 {currency} 的提现数据时出错: {e}")
                    continue

        print(f"完成订单USD总值: {chain_withdraw_usda_data}")
        all_usdt += chain_withdraw_usda_data
        print(f"订单USD总值: {all_usdt}")
        return amount, fee
    def get_pay_out_transaction_record(self,date):
        self.get_wallet_out_completed_transaction_record('crypto_payout',date)

    def get_chain_withdraw_transaction_record(self,date):
        self.get_wallet_out_completed_transaction_record('chain_withdraw',date)

    def get_card_account_recharge_transaction_record(self,date):
        amount, fee = self.get_wallet_out_completed_transaction_record('card_account_recharge',date)
        return amount, fee


    """
    ==================================================================================================================================================

    """
    """
    根据某个企业查询充值提现
    """
    def get_wallet_in_completed_transaction_record_for_account_id(self,date,account_id):
        business_type = 'chain_deposit'
        chain_deposit_usda_data = 0.0
        amount = 0.0
        fee = 0.0
        data = self.deposit.get_deposit_order_info_02(
            business_type,
            status='completed',
            date=date
        )
        transaction_data = self.get_wallet_transaction_detail(business_type, date, data)

        try:
            for currency in self.currency:
                total_amount, total_fee = self.get_wallet_transaction_count_for_id(
                    'to_currency',
                    currency,
                    transaction_data,
                    ['amount', 'fee'],
                    account_id
                )
                data = self.get_USD_value_of_transaction_record(currency, total_amount)
                chain_deposit_usda_data += data
                amount += total_amount
                fee += total_fee

                logger.info(f"{currency} 充值完成订单金额: {total_amount}, 手续费: {total_fee}, 转换为USD: {data}")
                return amount,fee
        except Exception as e:
            logger.error(f"处理币种 {currency} 的充值数据时出错: {e}")


    def get_wallet_out_completed_transaction_record_for_account_id(self, date,account_id):

        chain_withdraw_usda_data = 0.0
        all_usdt = 0.0
        amount = 0.0
        fee = 0.0
        business_type = 'chain_withdraw'
        status_list = ['completed', 'pending']
        for i in status_list:
            data = self.withdraw.get_withdraw_order_info_02(
                business_type,
                status=i,
                date=date
            )
            transaction_data = self.get_wallet_transaction_detail(business_type, date, data)
            for currency in self.currency:
                try:

                    total_amount, total_fee = self.get_wallet_transaction_count_for_id(
                        'from_currency',
                        currency,
                        transaction_data,
                        ['amount', 'fee'],
                        account_id
                    )
                    data = self.get_USD_value_of_transaction_record(currency, total_amount)
                    chain_withdraw_usda_data += data
                    amount += total_amount
                    fee += total_fee

                    logger.info(f"{currency} 充值完成订单金额: {total_amount}, 手续费: {total_fee}, 转换为USD: {data}")
                    return amount, fee
                except Exception as e:
                    logger.error(f"处理币种 {currency} 的提现数据时出错: {e}")
                    continue


if __name__ == '__main__':
    times = GetTime()
    month_list = times.get_month_for_year(2025)
    # day_list = times.get_day_for_month(2025, 12)
    wallet_transaction_count = WalletPageData()


    account_id = 'cb828d40-674c-4f6a-b42d-8a0a4bbf6fac'
    date = '202512'





    #钱包入账。pay_in chain_deposit
    # wallet_transaction_count.get_pay_in_transaction_record(date)
    # wallet_transaction_count.get_chain_deposit_transaction_record(date)

    #钱包出账。pay_out chain_withdraw
    # wallet_transaction_count.get_pay_out_transaction_record(date)
    # wallet_transaction_count.get_chain_withdraw_transaction_record(date)



    #根据id获取充值和提现并便利每个月的
    in_num = 0
    out_num = 0
    for i in month_list:
        in_amount,_ = wallet_transaction_count.get_wallet_in_completed_transaction_record_for_account_id(i,account_id)
        in_num += in_amount

        out_amount,_ = wallet_transaction_count.get_wallet_out_completed_transaction_record_for_account_id(i,account_id)
        out_num += out_amount

    print('充值金额:',in_num)
    print('提现金额:',out_num)




    #根据id获取充值和转出
    # in_amount, _ = wallet_transaction_count.get_wallet_in_completed_transaction_record_for_account_id(date, account_id)
    #
    # out_amount, _ = wallet_transaction_count.get_wallet_out_completed_transaction_record_for_account_id(date, account_id)



    #卡账户充值
    # wallet_transaction_count.get_card_account_recharge_transaction_record(date)
    #一年卡账户充值的总额
    # all_amount = 0.0
    # for  date in month_list:
    #     amount,_ = wallet_transaction_count.get_card_account_recharge_transaction_record(date)
    #     all_amount += amount
    #
    # print('卡账户充值总额:',all_amount)
