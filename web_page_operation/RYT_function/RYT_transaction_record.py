from common.simple_request import HttpRequest
from common import  read_and_save_tool
from common.get_time import GetTime
class TransactionProcessor:
    def __init__(self, http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()
        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.time = GetTime()

        # 根据输入的内容判断获取的时间是哪个方法
    def get_time_range(self, date):
        # 如果输入的string类型为数字，判断是否为月份
        if date.isdigit() and len(date) == 6:
            return self.time.get_month_range(date)
        # 如果输入的string类型为日期，判断是否为日期
        elif date.isdigit() and len(date) == 8:
            return self.time.get_day_range(date)
        else:
            raise ValueError("时间格式错误")
    def get_ryt_data(self):
        """
        获取 ryt 余额
        :return:
        """
        base_url = self.config_url + "/web/contract/getContractAccountInfo"
        ryt_Balance = self.http_request.get(base_url, nested_keys=['data', 'num'])  # ryt 余额
        print(f'ryt 余额为：', ryt_Balance)

    def get_ryt_reconciliation_data(self, business_type=None,status=None,date=None):
        """
        获取 ryt 对账数据
        :param business_type: 业务类型:
                                1 购入crypto_contract_in
                                2 赎回crypto_contract_out
                                3 赎回失败failed_refund

        :return:
        """
        page = 1
        all_transaction_data = []
        while True:
            time_range = self.get_time_range(date=date)
            time= ["2025-11-01+00:00", "2025-11-30+23:59" ]

            base_url = self.config_url + "/web/contract/getRytTransactionList?page={}&take=100&business_type={}&created_at%5B%5D={}&created_at%5B%5D={}".format(page,business_type,time[0],time[1])

            ryt_reconciliation_data = self.http_request.gets(base_url, jsonpath_expr='$.data.list[?(@.process_status == "{}")]'.format(status))
            # print(f'获取RYT对账数据: {ryt_reconciliation_data}')
            if not ryt_reconciliation_data or len(ryt_reconciliation_data) == 0:
                break
            all_transaction_data.extend(ryt_reconciliation_data)
            total_count = self.http_request.gets(base_url, jsonpath_expr='$.data.total')
            # print(f'总条数: {total_count}')
            if total_count and len(all_transaction_data) >= total_count:
                break
            page += 1
        # print(f'RYT对账数据: {all_transaction_data}')
        return all_transaction_data

    def _process_ryt_data(self, data, amount_field='usdc_amount', fee_field='usdc_fee', operation='add'):
        """
        统一处理RYT数据的通用方法
        :param data: 数据列表
        :param amount_field: 金额字段名
        :param fee_field: 手续费字段名
        :param operation: 运算操作 ('add' 或 'subtract')
        :return: (ryt_amount, wallet_amount)
        """
        if not isinstance(data, list):
            data = [data]

        amount = 0
        fee = 0
        ryt_amount = 0

        for item in data:
            if isinstance(item, dict):
                if 'amount' in item:
                    ryt_amount += float(item['amount'])
                    print(f'RYT充值金额: {ryt_amount}')
                amount += float(item.get(amount_field, 0.0)) if item.get(amount_field) is not None else 0.0
                fee += float(item.get(fee_field, 0.0)) if item.get(fee_field) is not None else 0.0

        wallet_amount = amount + fee if operation == 'add' else amount - fee
        return ryt_amount, wallet_amount

    def get_RYT_failed_refund_data(self, wallet_currency, status=None, date=None):
        """
        获取 RYT 失败退款数据
        :param wallet_currency: 钱包币种 (如 USDT, USDC)
        :return: (ryt_amount, wallet_amount)
        """
        data = self.get_ryt_reconciliation_data(
            business_type='failed_refund',
            status=status,
            date=date
        )

        if not isinstance(data, list):
            data = [data]

        amount = 0
        fee = 0
        ryt_amount = 0

        if isinstance(data, list):
            failed_data = [
                item for item in data
                if isinstance(item, dict) and
                   (item.get('from_currency') == wallet_currency and
                    item.get('to_currency') == wallet_currency)
            ]

            for item in failed_data:
                if isinstance(item, dict) and 'amount' in item:
                    ryt_amount += float(item['amount'])
                amount += float(item.get('usdc_amount', 0.0))
                fee += float(item.get('usdc_fee', 0.0))

        wallet_amount = amount + fee
        print(f'失败退款RYT数量: {ryt_amount}')
        print(f'钱包余额: {wallet_amount}')
        print(f'Ryt 充值金额: {amount}')
        return ryt_amount, wallet_amount

    def get_RYT_crypto_contract_out(self, status=None, date=None):
        """获取RYT赎回数据"""
        data = self.get_ryt_reconciliation_data(
            business_type='crypto_contract_out',
            status=status,
            date=date
        )
        ryt_amount, wallet_amount = self._process_ryt_data(data, operation='subtract')
        print('赎回RYT数据')
        print(f'钱包余额: {wallet_amount}')
        print(f'Ryt 充值金额: {ryt_amount}')
        return ryt_amount, wallet_amount

    def get_RYT_crypto_contract_in(self, status=None, date=None):
        """获取RYT申购数据"""
        data = self.get_ryt_reconciliation_data(
            business_type='crypto_contract_in',
            status=status,
            date=date
        )
        ryt_amount, wallet_amount = self._process_ryt_data(data, operation='add')
        print("申购RYT数据")
        print(f'钱包余额: {wallet_amount}')
        print(f'Ryt 充值金额: {ryt_amount}')
        return ryt_amount, wallet_amount


if __name__ == '__main__':
    ryt= TransactionProcessor()
    ryt_amount,wallet_amount = ryt.get_RYT_crypto_contract_in(status='completed',date='202611')
    ryt_amount,wallet_amount = ryt.get_RYT_crypto_contract_out(status='completed',date='202611')
