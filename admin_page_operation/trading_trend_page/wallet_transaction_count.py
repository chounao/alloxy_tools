import json
from common.Sql import DatabaseConnection
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
class PageInterfaceData:
    """
    页面接口数据
    """
    def __init__(self, http_request=None):
        self.date = ['20251204']
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()
        self.config = read_and_save_tool.ConfigTools()
        self.admin_url = self.config.get_url_data()
        self.currency = [ 'USDC','USDT']
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





    def get_pay_in_completed_transaction_record(self,date):
        """
        获取充值完成交易记录的USD总值
        :return: 所有币种充值完成订单转换为USD后的总金额
        """
        pay_in_usd_data = 0.0
        amount = 0.0
        fee = 0.0
        data = self.pay_in.get_pay_in_order_info(

            status='completed',
            date=date
        )
        transaction_data = self.get_wallet_transaction_detail('pay_in_' ,date ,data)
        for currency in self.currency:
            try:

                total_amount, total_fee = self.get_wallet_transaction_count(
                    'to_currency',
                    currency,
                    transaction_data,
                    ['amount','fee']
                )
                data = self.get_USD_value_of_transaction_record(currency, total_amount)
                pay_in_usd_data += float(data)
                total_amount += float(total_amount)
                fee += float(total_fee)
                logger.info(f"{currency} 充值完成订单金额: {total_amount}, 手续费: {total_fee}, 转换为USD: {data}")
            except Exception as e:
                logger.error(f"处理币种 {currency} 的充值数据时出错: {e}")
                continue

        print(f"pay_in完成订单USD总值: {pay_in_usd_data}")
        return pay_in_usd_data,amount,fee

    #获取加密付款的支付数量，包含手续费，换算为USD
    def get_pay_out_completed_transaction_record(self,date):
        all_usdt =0.0
        amount=0.0
        fee = 0.0
        status_list = ['admin_completed', 'pending_withdraw']
        print(f"开始处理支付出账单: {date}")
        pay_out_usd_data = 0.0

        for i in status_list:
            data = self.pay_out.get_pay_out_order_info(
                status=i,
                date=date
            )
            transaction_data = self.get_wallet_transaction_detail('pay_out_',date,data)
            for currency in self.currency:

                total_amount, total_fee = self.get_wallet_transaction_count(
                    'from_currency',
                    currency,
                    transaction_data,
                    ['amount','fee']
                )
                data = self.get_USD_value_of_transaction_record(currency, total_amount+total_fee)
                print(data)
                pay_out_usd_data += data
                amount += total_amount
                fee += total_fee
                logger.info(f"pay_out{currency} 充值完成订单金额: {total_amount}, 手续费: {total_fee}, 转换为USD: {data}")

        all_usdt += pay_out_usd_data
        print(f"pay_out完成订单USD总值: {all_usdt}")
        return all_usdt,amount,fee
    # 获取上充值的到账数量，包含手续费，换算为USD
    def get_chain_deposit_completed_transaction_record(self, date):
        chain_deposit_usda_data =0.0
        amount = 0.0
        fee = 0.0
        data = self.deposit.get_deposit_order_info(
            status='completed',
            date=date
        )
        transaction_data = self.get_wallet_transaction_detail('chain_deposit_', date, data)
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

        print(f"链上充值订单USD总值: {chain_deposit_usda_data}")
        return chain_deposit_usda_data,amount,fee
    #链上提现的到账数量，包含手续费，换算为USD
    def get_chain_withdraw_completed_transaction_record(self,date):
        chain_withdraw_usda_data =0.0
        all_usdt = 0.0
        amount = 0.0
        fee = 0.0
        status_list = ['completed', 'pending']
        for  i in status_list:
            data = self.withdraw.get_withdraw_order_info(

                status= i,
                date=date
            )
            transaction_data = self.get_wallet_transaction_detail('chain_withdraw_', date, data)
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

        print(f"链上提现完成订单USD总值: {chain_withdraw_usda_data}")
        all_usdt += chain_withdraw_usda_data
        print(f"所有链上提现完成订单USD总值: {all_usdt}")
        return all_usdt,amount,fee
    #收单提现的到账数量，包含手续费，换算为USD
    def get_checkout_withdraw_completed_transaction_record(self,date):
        checkout_withdraw_usda_data =0.0
        amount = 0.0
        fee = 0.0
        data = self.checkout.get_checkout_order_info('withdraw_completed', date=date)
        transaction_data = self.get_wallet_transaction_detail('checkout_', date, data)
        for currency in self.currency:
            try:

                total_amount, total_fee = self.get_wallet_transaction_count(
                    'currency',
                    currency,
                    transaction_data,
                    ['order_amount', 'fee_amount']
                )
                data = self.get_USD_value_of_transaction_record(currency, total_amount)
                checkout_withdraw_usda_data += data #两种币种相加
                amount += total_amount
                fee += total_fee
            except Exception as e:
                logger.error(f"处理币种 {currency} 的收单提现数据时出错: {e}")
                continue
        print(f'收单提现金额 {checkout_withdraw_usda_data}')
        return checkout_withdraw_usda_data,amount,fee
    #RYT申购的到账数量，包含手续费，换算为USD
    def get_ryt_crypto_contract_in_transaction_record(self,date):
        ryt_crypto_contract_in_usda_data =0.0
        amount = 0.0
        fee = 0.0
        data = self.ryt_operation.get_RYT_order_info(status='completed', date=date,
                                                                   business_type='crypto_contract_in')  # 获取数据

        transaction_data = self.get_wallet_transaction_detail('RYT_crypto_contract_in_', date, data)
        total_amount, total_fee = self.get_wallet_transaction_count(
            'from_currency',
            'USDC',
            transaction_data,
            ['usdc_amount', 'usdc_fee'])
        data = self.get_USD_value_of_transaction_record('USDC', total_amount+total_fee)
        ryt_crypto_contract_in_usda_data += data #两种币种相加
        amount += total_amount
        fee += total_fee
        print(f'RYT申购金额 {ryt_crypto_contract_in_usda_data}')
        return ryt_crypto_contract_in_usda_data,amount,fee
    # 获取 RYT赎回金额，包含手续费，换算为USD
    def get_ryt_crypto_contract_out_transaction_record(self,date):
        amount = 0.0
        fee = 0.0
        yt_crypto_contract_out_usda_data =0.0
        data = self.ryt_operation.get_RYT_order_info(status='completed', date=date,
                                                     business_type='crypto_contract_out')  # 获取数据

        transaction_data = self.get_wallet_transaction_detail('RYT_crypto_contract_out_', date, data)
        for currency in self.currency:
            try:

                total_amount, total_fee = self.get_wallet_transaction_count(
                    'to_currency',
                    currency,
                    transaction_data,
                    ['usdc_amount', 'usdc_fee'])
                data = self.get_USD_value_of_transaction_record(currency, total_amount)
                yt_crypto_contract_out_usda_data += data  # 两种币种相加
                amount += total_amount
                fee += total_fee
            except Exception as e:
                logger.error(f"处理币种 {currency} 的RYT赎回数据时出错: {e}")
            continue

        print(f'RYT赎回金额 {yt_crypto_contract_out_usda_data}')
        return yt_crypto_contract_out_usda_data,amount,fee
        # 执行所有的数据
    #获取消费记录的到账数量，包含手续费，换算为USD

    def get_all_wallet_data(self):
        """
        获取所有钱包数据并保存到文件
        """
        # 使用 'w' 模式先清空文件，或创建新文件
        with open('wallet_transaction_count.txt', 'w') as f:
            f.write("钱包交易记录汇总\n")
            f.write("=" * 50 + "\n")

        total_pay_in = 0.0
        total_pay_out = 0.0
        total_chain_deposit = 0.0
        total_checkout_withdraw = 0.0
        total_ryt_in = 0.0
        total_ryt_out = 0.0
        tatal_crypto_withdrawals = 0.0
        # 使用 'a' 模式追加写入每个月的数据
        for date in self.date:
            try:
                pay_in_usda_data,in_ampunt,in_fee = self.get_pay_in_completed_transaction_record(date)
                pay_out_usda_data,out_amount,out_fee = self.get_pay_out_completed_transaction_record(date)
                chain_deposit_usda_data,chain_depost_amount,chain_deposit_fee= self.get_chain_deposit_completed_transaction_record(date)
                checkout_withdraw_usda_data ,chackout_amount,chackout_fee= self.get_checkout_withdraw_completed_transaction_record(date)
                ryt_crypto_contract_in_usda_data ,ryt_in_amount,ryt_in_fee= self.get_ryt_crypto_contract_in_transaction_record(date)
                ryt_crypto_contract_out_usda_data ,ryt_out_amount,ryt_out_fee= self.get_ryt_crypto_contract_out_transaction_record(date)
                crypto_withdrawals ,crypto_withdrawals_amount,crypto_withdrawals_fee= self.get_chain_withdraw_completed_transaction_record(date)
                # 累计总金额
                total_pay_in += pay_in_usda_data
                total_pay_out += pay_out_usda_data
                total_chain_deposit += chain_deposit_usda_data
                total_checkout_withdraw += checkout_withdraw_usda_data
                total_ryt_in += ryt_crypto_contract_in_usda_data
                total_ryt_out += ryt_crypto_contract_out_usda_data
                tatal_crypto_withdrawals += crypto_withdrawals
                # 追加写入每个月的数据
                with open('wallet_transaction_count.txt', 'a') as f:
                    f.write(f'\n{date}月钱包交易记录:\n')
                    f.write(f'  pay_in金额: {pay_in_usda_data}, in_amount: {in_ampunt}, in_fee: {in_fee}\n')
                    f.write(f'  pay_out金额: {pay_out_usda_data}, out_amount: {out_amount}, out_fee: {out_fee}\n')
                    f.write(f'  链上充值金额: {chain_deposit_usda_data}, chain_depost_amount: {chain_depost_amount}, chain_deposit_fee: {chain_deposit_fee}\n')
                    f.write(f'  收单体现金额: {checkout_withdraw_usda_data}, chackout_amount: {chackout_amount}, chackout_fee: {chackout_fee}\n')
                    f.write(f'  RYT合约入金金额: {ryt_crypto_contract_in_usda_data}, ryt_in_amount: {ryt_in_amount}, ryt_in_fee: {ryt_in_fee}\n')
                    f.write(f'  RYT合约出金金额: {ryt_crypto_contract_out_usda_data}, ryt_out_amount: {ryt_out_amount}, ryt_out_fee: {ryt_out_fee}\n')
                    f.write(f'  链上提现金额: {crypto_withdrawals}, crypto_withdrawals_amount: {crypto_withdrawals_amount}, crypto_withdrawals_fee: {crypto_withdrawals_fee}\n')

            except Exception as e:
                logger.error(f"处理 {date} 月份数据时出错: {e}")
                continue

        # 写入总计数据
        with open('wallet_transaction_count.txt', 'a') as f:
            f.write("\n" + "=" * 50 + "\n")
            f.write("总计:\n")
            f.write(f'  pay_in总金额: {total_pay_in}\n')
            f.write(f'  pay_out总金额: {total_pay_out}\n')
            f.write(f'  链上充值总金额: {total_chain_deposit}\n')
            f.write(f'  收单体现总金额: {total_checkout_withdraw}\n')
            f.write(f'  RYT合约入金总金额: {total_ryt_in}\n')
            f.write(f'  RYT合约出金总金额: {total_ryt_out}\n')
            f.write(f'  链上提现总金额: {tatal_crypto_withdrawals}\n')

        logger.info("所有钱包数据已保存到 wallet_transaction_count.txt 文件")

# 加密付款 脸上充值 提现
if __name__ == '__main__':
     date = '202512'
     page_interface_data = PageInterfaceData()
     # page_interface_data.get_all_wallet_data()



    #加密付款
     pay_out_usda_data =  page_interface_data.get_pay_out_completed_transaction_record(date)


    #链上提现
     chain_withdraw_usda_data =  page_interface_data.get_chain_withdraw_completed_transaction_record(date)

    #商户提现
     checkout_withdraw_usda_data =  page_interface_data.get_checkout_withdraw_completed_transaction_record(date)
     #
     # all_money = pay_out_usda_data + chain_withdraw_usda_data + checkout_withdraw_usda_data
     # print(all_money)

    #链上充值
     chain_deposit_usda_data =  page_interface_data.get_chain_deposit_completed_transaction_record(date)

     # #ryt合约入金
     ryt_crypto_contract_in_usda_data =  page_interface_data.get_ryt_crypto_contract_in_transaction_record(date)
     # #ryt合约出金
     ryt_crypto_contract_out_usda_data =  page_interface_data.get_ryt_crypto_contract_out_transaction_record(date)

