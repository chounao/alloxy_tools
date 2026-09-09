# wallet_function/wallet_transaction_record.py
from common.simple_request import HttpRequest
from common.get_time import GetTime
from common import read_and_save_tool
from common import logger
from jsonpath_ng import parse
import jsonpath_ng.ext as jsonpath

logger = logger.logger


class WalletTransactionRecord:
    def __init__(self, user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
        self.time = GetTime()
        self.from_currencies = ['USDC', 'USDT']
        self.to_currencies = ['USDC', 'USDT']

        # 交易类型配置
        self.transaction_type_config = {
            '链上充值': {'code': 'chain_deposit', 'use': 'to_currency', 'currencies': self.to_currencies},
            '法币充值': {'code': 'crypto_payin', 'use': 'to_currency', 'currencies': self.to_currencies},
            '加密付款': {'code': 'crypto_payout', 'use': 'from_currency', 'currencies': self.from_currencies},
            '链上提现': {'code': 'chain_withdraw', 'use': 'from_currency', 'currencies': self.from_currencies},
            '失败退款': {'code': 'failed_refund', 'use': 'to_currency', 'currencies': self.to_currencies},
            '商户提现': {'code': 'checkout_withdraw', 'use': 'to_currency', 'currencies': self.to_currencies},
            '申购': {'code': 'crypto_contract_in', 'use': 'from_currency', 'currencies': self.from_currencies},
            '赎回': {'code': 'crypto_contract_out', 'use': 'to_currency', 'currencies': self.to_currencies},
            '卡账户充值': {'code': 'card_account_recharge', 'use': 'from_currency', 'currencies': self.from_currencies},
            '卡账户转入': {'code': 'card_account_to_wallet', 'use': 'to_currency', 'currencies': self.to_currencies},
            '系统扣款': {'code': 'system_deduction', 'use': 'from_currency', 'currencies': self.from_currencies},
            '系统充值': {'code': 'system_recharge', 'use': 'to_currency', 'currencies': self.from_currencies},
        }

        # 状态映射
        self.transaction_statuses = {"进行中": "pending", "成功": "completed", "失败": "failed"}
        self.status_display_names = {v: k for k, v in self.transaction_statuses.items()}


    def _convert_status(self, status):
        """内部工具：中文状态转API英文状态，兼容中英文入参"""
        if not status:
            return None
        if status in self.transaction_statuses:
            return self.transaction_statuses[status]
        return status

    def get_wallet_transaction_record(self, from_currency=None, to_currency=None,
                                      transaction_type=None, transaction_status=None, id_no=None, date=None):
        """分页获取钱包交易记录原始列表"""
        page = 1
        all_transaction_data = []
        start_time, end_time = self.time.get_time_range(date)
        api_status = self._convert_status(transaction_status)

        while True:
            dict_data = {
                'page': page,
                'take': 100,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'transaction_type': transaction_type,
                'transaction_status': api_status,
                'id_no': id_no,
                'create_at': [start_time, end_time],
            }
            logger.info(f"发送请求: transaction_type={transaction_type}, transaction_status={api_status}")
            reconciliation_data = self.http_request.send_request(
                api_name='钱包-交易记录',
                dict_data=dict_data,
                nested_keys=['data', 'list']
            )
            if not reconciliation_data:
                break
            all_transaction_data.extend(reconciliation_data)

            total_count = self.http_request.send_request(
                api_name='钱包-交易记录',
                dict_data=dict_data,
                nested_keys=['data', 'total']
            )
            if total_count and len(all_transaction_data) >= total_count:
                break
            page += 1
        return all_transaction_data

    def get_wallet_transaction_count(self, transaction_data: list, amount_field: str = 'amount'):
        """汇总交易amount与fee"""
        if not transaction_data:
            return 0.0, 0.0
        total_amount = 0.0
        total_fee = 0.0
        for item in transaction_data:
            try:
                amount = float(item.get(amount_field, 0) or 0)
                fee = float(item.get('fee', 0) or 0)
                total_amount += amount
                total_fee += fee
            except (ValueError, TypeError) as e:
                logger.error(f"数据转换错误 {item}, 错误: {e}")
                continue
        return total_amount, total_fee

    def _filter_currency_list(self, raw_currency_list, use_rule):
        """内部工具：根据from/to规则过滤币种列表"""
        if use_rule == "from_currency":
            return [c for c in raw_currency_list if c in self.from_currencies]
        else:
            return [c for c in raw_currency_list if c in self.to_currencies]

    def get_transaction_summary_data(self, transaction_type_name=None, currency=None,
                                     status=None, currencies=None, statuses=None, date=None):
        """按交易类型/币种/状态获取原始数据+汇总金额"""
        # 交易类型筛选
        if transaction_type_name:
            if transaction_type_name not in self.transaction_type_config:
                raise ValueError(f"不支持的交易类型: {transaction_type_name}")
            type_map = {transaction_type_name: self.transaction_type_config[transaction_type_name]}
        else:
            type_map = self.transaction_type_config

        # 币种列表
        if currencies:
            currency_list = currencies
        elif currency:
            currency_list = [currency]
        else:
            currency_list = list(set(self.from_currencies + self.to_currencies))

        # 状态列表
        if statuses:
            status_list = statuses
        elif status:
            status_list = [status]
        else:
            status_list = list(self.transaction_statuses.keys()) + list(self.transaction_statuses.values())

        result_data = {}
        summary_data = {}
        # 初始化数据结构
        for type_name in type_map:
            result_data[type_name] = {}
            summary_data[type_name] = {}
            cfg = type_map[type_name]
            curr_list = self._filter_currency_list(currency_list, cfg['use'])
            for curr in curr_list:
                result_data[type_name][curr] = {}
                summary_data[type_name][curr] = {}
                for stat in status_list:
                    result_data[type_name][curr][stat] = []
                    summary_data[type_name][curr][stat] = {"total_amount": 0.0, "total_fee": 0.0}

        # 循环拉取并汇总
        for type_name, cfg in type_map.items():
            amount_field = "to_currency_amount" if type_name == "法币充值" else "amount"
            curr_list = self._filter_currency_list(currency_list, cfg['use'])

            for curr in curr_list:
                for stat in status_list:
                    if cfg['use'] == 'from_currency':
                        records = self.get_wallet_transaction_record(
                            from_currency=curr,
                            transaction_type=cfg['code'],
                            transaction_status=stat,
                            date=date
                        )
                    else:
                        records = self.get_wallet_transaction_record(
                            to_currency=curr,
                            transaction_type=cfg['code'],
                            transaction_status=stat,
                            date=date
                        )
                    amt, fee = self.get_wallet_transaction_count(records, amount_field)
                    result_data[type_name][curr][stat] = records
                    summary_data[type_name][curr][stat]["total_amount"] = amt
                    summary_data[type_name][curr][stat]["total_fee"] = fee
        return result_data, summary_data

    def get_all_transaction_summary(self, currency=None, status=None, date=None):
        """获取全部交易类型汇总，只返回summary"""
        _, summary_data = self.get_transaction_summary_data(currency=currency, status=status, date=date)
        return summary_data

    def get_cim_transaction_summary(self, currency=None, transaction_type_name=None, date=None):
        """获取指定交易类型 completed状态 汇总，返回绝对值总额"""
        _, summary_data = self.get_transaction_summary_data(
            currency=currency,
            status="completed",
            transaction_type_name=transaction_type_name,
            date=date
        )
        if not isinstance(summary_data, dict):
            return None

        total_amount = 0.0
        total_fee = 0.0
        try:
            for type_info in summary_data.values():
                for curr_info in type_info.values():
                    completed_info = curr_info.get("completed")
                    if completed_info:
                        total_amount += abs(float(completed_info["total_amount"]))
                        total_fee += abs(float(completed_info["total_fee"]))
            return total_amount, total_fee
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"解析汇总数据异常: {e}")
            return None


if __name__ == '__main__':
    wallet_record = WalletTransactionRecord()
    a = ['USDT', 'USDC']
    for i in a:
        result_data, summary_data = wallet_record.get_transaction_summary_data(
            currency=i,
            status='pending',
            date="202609"
        )
        jsonpath_expr = parse(f'$..{i}.pending.total_amount')
        matches = jsonpath_expr.find(summary_data)
        total_amount = sum(m.value for m in matches) if matches else 0
        print(f"币种: {i}, 状态: pending, 总金额: {total_amount}")

    for currency in ['USDT', 'USDC']:
        wallet_record.get_wallet_transaction_record(transaction_status='pending', date='202609')
