# wallet_function/wallet_transaction_record.py

from common.simple_request import HttpRequest
from common.get_time import GetTime
from common import read_and_save_tool
from common import logger
from jsonpath_ng import parse
import jsonpath_ng.ext as jsonpath
logger = logger.logger


class WalletTransactionRecord():
    def __init__(self, user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
        self.time = GetTime()
        self.from_currencies = ['USDC', 'USDT']
        self.to_currencies = ['USDC', 'USDT']

        # 定义每种交易类型的币种使用规则
        self.transaction_type_config = {
            #pay_in
            '法币充值': {
                'code': 'crypto_payin',
                'use': 'to_currency',  # 关注目标币种
                'currencies': self.to_currencies
            },
            #钱包充值
            '链上充值': {
                'code': 'chain_deposit',
                'use': 'to_currency',  # 关注目标币种
                'currencies': self.to_currencies
            },
            # 收单提现
            '商户提现': {
                'code': 'checkout_withdraw',
                'use': 'to_currency',  # 关注目标币种
                'currencies': self.to_currencies
            },
            # 失败退款
            '失败退款': {
                'code': 'failed_refund',
                'use': 'to_currency',  # 关注目标币种
                'currencies': self.to_currencies
            },
            # 赎回——ryt
            '赎回': {
                'code': 'crypto_contract_out',
                'use': 'to_currency',  # 关注目标币种
                'currencies': self.to_currencies
            },

            # 卡账户转入
            '卡账户转入': {
                'code': 'card_account_to_wallet',
                'use': 'to_currency',  # 关注目标币种
                'currencies': self.to_currencies
            },
            # 钱包转出
            '链上提现': {
                'code': 'chain_withdraw',
                'use': 'from_currency',  # 关注源币种
                'currencies': self.from_currencies
            },
            #pay_out
            '加密付款': {
                'code': 'crypto_payout',
                'use': 'from_currency',  # 关注源币种
                'currencies': self.from_currencies
            },

            #申购——ryt
            '申购': {
                'code': 'crypto_contract_in',
                'use': 'from_currency',  # 关注源币种
                'currencies': self.from_currencies
            },

            #卡账户充值
            '卡账户充值': {
                'code': 'card_account_recharge',
                'use': 'from_currency',  # 关注源币种
                'currencies': self.from_currencies
            }
            ,
            #系统充值
            '系统充值':{
                'code': 'system_recharge',
                'use': 'to_currency',  # 关注源币种
                'currencies': self.from_currencies
            },
            #系统扣款
            '系统扣款':{
                'code': 'system_deduction',
                'use': 'from_currency',  # 关注源币种
                'currencies': self.from_currencies
            }
        }

        # 状态映射：中文显示名 -> 英文API值
        self.transaction_statuses = {
            "进行中": "pending",
            "成功": "completed",
            "失败": "failed"
        }

        # 反向映射：英文API值 -> 中文显示名
        self.status_display_names = {v: k for k, v in self.transaction_statuses.items()}
    #根据输入的内容判断获取的时间是哪个方法
    def get_time_range(self, date):
        #如果输入的string类型为数字，判断是否为月份
        if date.isdigit() and len(date) == 6:
            return self.time.get_month_range(date)
        #如果输入的string类型为日期，判断是否为日期
        elif date.isdigit() and len(date) == 8:
            return self.time.get_day_range(date)
        else:
            raise ValueError("时间格式错误")

    def get_wallet_transaction_record(self, from_currency=None, to_currency=None,
                                      transaction_type=None, transaction_status=None, id_no=None,data=None):
        """
        获取对账数据
        钱包-交易记录
        """
        page = 1
        all_transaction_data = []
        while True:
            start_time, end_time = self.get_time_range(data)
            # 确保传入的是英文状态值而不是中文
            if transaction_status and transaction_status in self.status_display_names:
                # 已经是正确的英文值
                api_status = transaction_status
            elif transaction_status and transaction_status in self.transaction_statuses:
                # 是中文值，转换为英文值
                api_status = self.transaction_statuses[transaction_status]
            else:
                # 未知状态值，保持原样（可能为None）
                api_status = transaction_status

            dict_data = {
                'page': page,
                'take': 100,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'transaction_type': transaction_type,
                'transaction_status': api_status,  # 使用转换后的英文值
                'id_no': id_no,
                'create_at': [start_time, end_time],
            }

            logger.info(f"发送请求: transaction_type={transaction_type}, transaction_status={api_status}")
            reconciliation_data = self.http_request.send_request(
                api_name='钱包-交易记录',
                dict_data=dict_data,
                nested_keys=['data', 'list']
            )
            if not reconciliation_data or len(reconciliation_data) == 0:
                return
            all_transaction_data.extend(reconciliation_data)
            total_count = self.http_request.send_request(api_name='钱包-交易记录', dict_data=dict_data,
                                                         nested_keys=['data', 'total'])
            if total_count and len(all_transaction_data) >= total_count:
                break
            page += 1
        return all_transaction_data

    def get_wallet_transaction_count(self, transaction_data, amount_field):
        """
        获取钱包交易记录统计
        :param transaction_data: 交易数据列表
        :param amount_field: 金额字段名，默认为'amount'
        """
        if not transaction_data:
            return 0.0, 0.0

        total_amount = 0.0
        total_fee = 0.0

        for data in transaction_data:
            try:
                amount_str = data.get(amount_field)  # 使用动态字段名
                fee_str = data.get('fee')

                amount = float(amount_str) if amount_str and str(amount_str).strip() else 0.0
                fee = float(fee_str) if fee_str and str(fee_str).strip() else 0.0

                total_amount += amount
                total_fee += fee
            except (ValueError, TypeError) as e:
                logger.error(f"数据转换错误 {data}, 错误: {e}")
                continue
        return total_amount, total_fee

    # def get_wallet_transaction_data(self, from_currency=None, to_currency=None,
    #                                 transaction_type=None, transaction_status=None):
    #     """
    #     获取钱包交易数据并计算总金额和手续费
    #     """
    #     data = self.get_wallet_transaction_record(
    #         from_currency=from_currency,
    #         to_currency=to_currency,
    #         transaction_type=transaction_type,
    #         transaction_status=transaction_status
    #     )
    #     total_amount, total_fee = self.get_wallet_transaction_count(data)
    #     return total_amount, total_fee

    def get_transaction_summary_data(self, transaction_type_name=None, currency=None,
                                     status=None, currencies=None, statuses=None,date=None):
        """
        按交易类型和状态获取交易数据及汇总信息
        :param transaction_type_name: 交易类型名称（如不指定则获取所有类型）
        :param currency: 币种（如不指定则使用默认币种列表）
        :param status: 状态（中文或英文，如不指定则使用默认状态列表）
        :param currencies: 自定义币种列表
        :param statuses: 自定义状态列表（支持中文或英文）
        :return: 包含原始数据和汇总信息的字典
        """
        result_data = {}
        summary_data = {}

        # 确定要处理的交易类型
        transaction_types_to_process = {}
        if transaction_type_name:
            if transaction_type_name in self.transaction_type_config:
                transaction_types_to_process[transaction_type_name] = self.transaction_type_config[
                    transaction_type_name]
            else:
                raise ValueError(f"不支持的交易类型: {transaction_type_name}")
        else:
            transaction_types_to_process = self.transaction_type_config

        # 确定币种列表
        if currencies:
            currency_list = currencies
        elif currency:
            currency_list = [currency]
        else:
            # 使用默认币种列表
            currency_list = self.from_currencies + self.to_currencies
            # 去重
            currency_list = list(set(currency_list))

        # 确定状态列表
        if statuses:
            status_list = statuses
        elif status:
            status_list = [status]
        else:
            # 使用默认状态列表（包括中英文）
            status_list = list(self.transaction_statuses.keys()) + list(self.transaction_statuses.values())

        # 初始化结果数据结构
        for type_name in transaction_types_to_process.keys():
            result_data[type_name] = {}
            summary_data[type_name] = {}

            # 根据交易类型确定使用的币种
            type_config = transaction_types_to_process[type_name]
            if type_config['use'] == 'from_currency':
                type_currencies = [c for c in currency_list if c in self.from_currencies]
            else:  # to_currency
                type_currencies = [c for c in currency_list if c in self.to_currencies]

            for curr in type_currencies:
                result_data[type_name][curr] = {}
                summary_data[type_name][curr] = {}

                for stat in status_list:
                    result_data[type_name][curr][stat] = []
                    summary_data[type_name][curr][stat] = {
                        'total_amount': 0.0,
                        'total_fee': 0.0
                    }

        # 遍历交易类型、币种和状态获取数据
        for type_name, type_config in transaction_types_to_process.items():
            # 确定金额字段
            amount_field = 'to_currency_amount' if type_name == '法币充值' else 'amount'
            #print(f"处理交易类型: {type_name}, 币种: {type_currencies}, 状态: {status_list}, 金额字段: {amount_field}")
            # 根据交易类型确定使用的币种
            if type_config['use'] == 'from_currency':
                type_currencies = [c for c in currency_list if c in self.from_currencies]
            else:  # to_currency
                type_currencies = [c for c in currency_list if c in self.to_currencies]

            for curr in type_currencies:
                for stat in status_list:
                    # 获取数据
                    if type_config['use'] == 'from_currency':
                        data = self.get_wallet_transaction_record(
                            from_currency=curr,
                            transaction_type=type_config['code'],
                            transaction_status=stat,
                            data=date
                        )
                    else:  # to_currency
                        data = self.get_wallet_transaction_record(
                            to_currency=curr,
                            transaction_type=type_config['code'],
                            transaction_status=stat,
                            data=date
                        )

                    # 计算总金额和手续费
                    total_amount, total_fee = self.get_wallet_transaction_count(data,amount_field)

                    result_data[type_name][curr][stat] = data
                    summary_data[type_name][curr][stat] = {
                        'total_amount': total_amount,
                        'total_fee': total_fee
                    }

        return result_data, summary_data

    def get_all_transaction_summary(self, currency=None, status=None,date=None):
        """
        获取所有交易类型的汇总数据（仅返回total_amount和total_fee）
        :param currency: 币种（如不指定则使用默认币种列表）
        :param status: 状态（中文或英文，如不指定则使用默认状态列表）
        :return: 包含所有交易类型汇总信息的字典
        """
        _, summary_data = self.get_transaction_summary_data(currency=currency, status=status,date=date)
        return summary_data


    def get_cim_transaction_summary(self, currency=None, transaction_type_name=None,date= None):
        _, summary_data = self.get_transaction_summary_data(currency=currency, status = 'completed', transaction_type_name=transaction_type_name,date=date)
        if not summary_data or not isinstance(summary_data, dict):
            return None

        try:
            for key, value in summary_data.items():
                if not isinstance(value, dict):
                    continue
                for record_key, record_value in value.items():
                    if not isinstance(record_value, dict):
                        continue
                    for k, n in record_value.items():
                        if k == 'completed':
                            total_amount = abs(float(n['total_amount']))
                            total_fee = abs(float(n['total_fee']))
                            return total_amount, total_fee
        except (KeyError, TypeError):
            # 处理键不存在或类型错误的情况
            return None

        # 如果未找到匹配项，返回None
        return None






if __name__ == '__main__':
    wallet_record = WalletTransactionRecord()

    # 示例1: 获取特定交易类型和币种的数据
    a = ['USDT','USDC']
    for i in a:
        result_data, summary_data = wallet_record.get_transaction_summary_data(
            currency=i,
            status='pending'
        )
        #从summary_data中提取total_amount和total_fee 并打印
        jsonpath_expr = parse(f'$..{i}.pending.total_amount')
        matches = jsonpath_expr.find(summary_data)
        total_amount = matches[0].value if matches else None
        total_amount+=total_amount
        # total_fee = jsonpath.jsonpath(summary_data, f'$.法币充值.{i}.pending.total_fee')[0]
        print(f"币种: {i}, 状态: pending, 总金额: {total_amount}")

    for currency in ['USDT', 'USDC']:
        reconciliation_data = wallet_record.get_wallet_transaction_record(
            transaction_status = 'pending'
        )
    # wallet_record.get_price_data('USDT',10000)
