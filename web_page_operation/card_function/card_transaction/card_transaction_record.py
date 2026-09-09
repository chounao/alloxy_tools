# card_function/card_transaction_record.py
from common.simple_request import HttpRequest
from common.get_time import GetTime
from common import read_and_save_tool


class CardTransactionRecord:
    def __init__(self, user_http=None):
        self.user_http = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.time = GetTime()

    def get_time_range(self, date: str):
        """根据6位月份/8位日期字符串，获取起止时间"""
        if date.isdigit() and len(date) == 6:
            return self.time.get_month_range(date)
        elif date.isdigit() and len(date) == 8:
            return self.time.get_day_range(date)
        raise ValueError("时间格式错误，仅支持6位年月或8位年月日")

    def get_card_balance(self):
        """获取虚拟卡总余额和卡账户总余额"""
        balance = self.user_http.send_request(api_name='获取虚拟卡总余额和卡账户总余额', nested_keys=['data'])
        card_account_balance = balance['cardAccountBalance']
        card_balance = balance['cardBalance']
        print(f'商务卡账户余额为：{card_account_balance}')
        print(f'商务卡卡内余额为：{card_balance}')
        return card_account_balance, card_balance

    def get_card_reconciliation_data(self, transaction_type=None, status=None, transaction_sub_type=None, date=None):
        """分页获取交易列表"""
        start_time, end_time = self.get_time_range(date)
        page = 1
        all_transaction_data = []
        while True:
            params_data = {
                'page': page,
                'take': 100,
                "created_at[]": [start_time, end_time]
            }
            if transaction_sub_type:
                params_data['transaction_sub_type'] = transaction_sub_type
            if transaction_type:
                params_data['transaction_type'] = transaction_type
            if status:
                params_data['status'] = status

            reconciliation_data = self.user_http.send_request(
                api_name='获取交易列表',
                dict_data=params_data,
                nested_keys=['data', 'list']
            )
            if not reconciliation_data:
                break
            all_transaction_data.extend(reconciliation_data)

            total_count = self.user_http.send_request(
                api_name='获取交易列表',
                dict_data=params_data,
                nested_keys=['data', 'total']
            )
            if total_count and len(all_transaction_data) >= total_count:
                break
            page += 1
        return all_transaction_data

    def calculate_transaction_totals(self, transaction_data: list):
        """汇总交易总额amount、手续费fee"""
        if not transaction_data:
            return 0.0, 0.0
        total_amount = 0.0
        total_fee = 0.0
        for data in transaction_data:
            try:
                amount = float(data.get('amount', 0) or 0)
                fee = float(data.get('fee', 0) or 0)
                total_amount += amount
                total_fee += fee
            except (ValueError, TypeError) as e:
                print(f"警告: 数据转换错误 {data}, 错误: {e}")
                continue
        return total_amount, total_fee

    def get_card_data(self, transaction_type, status, transaction_sub_type, date=None):
        """获取单状态下指定子类型、交易类型的汇总金额"""
        data = self.get_card_reconciliation_data(
            transaction_type=transaction_type,
            status=status,
            transaction_sub_type=transaction_sub_type,
            date=date
        )
        return self.calculate_transaction_totals(data)

    def _get_completed_total(self, transaction_type: str, transaction_sub_type: str, date=None):
        """【内部通用方法】查询completed状态汇总金额，消除重复代码"""
        total_amount = 0.0
        total_fee = 0.0
        for status in ['completed']:
            amount, fee = self.get_card_data(transaction_type, status, transaction_sub_type, date)
            total_amount += amount
            total_fee += fee
        print(f"【{transaction_sub_type}】{transaction_type} 交易总额: {total_amount}, 手续费: {total_fee}")
        return total_amount, total_fee

    def get_card_account_count(self, transaction_type: str, date=None):
        """card_account 账户交易统计，仅completed"""
        return self._get_completed_total(transaction_type, "card_account", date)

    def get_card_count(self, transaction_type: str, date=None):
        """card 商务卡交易统计，仅completed"""
        return self._get_completed_total(transaction_type, "card", date)

    def get_shared_card_count(self, transaction_type: str, date=None):
        """card_share_group 共享卡组交易统计，仅completed"""
        return self._get_completed_total(transaction_type, "card_share_group", date)


if __name__ == '__main__':
    card_transaction_record = CardTransactionRecord()
    res = card_transaction_record.get_card_account_count(transaction_type='vcc_in', date='202608')
    print(res)
