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
    def get_card_balance(self):
        """
        获取卡余额
        获取虚拟卡总余额和卡账户总余额
        :param date: 时间范围
        :return: 商务卡账户余额和商务卡卡内余额
        """
        balance = self.user_http.send_request(api_name='获取虚拟卡总余额和卡账户总余额', nested_keys=['data'])
        card_AccountBalance = balance['cardAccountBalance']  # 账户余额
        card_Balance = balance['cardBalance']  # 卡内余额
        print(f'商务卡账户余额为：', card_AccountBalance)
        print(f'商务卡卡内余额为：', card_Balance)
        return card_AccountBalance, card_Balance

    def get_card_reconciliation_data(self, transaction_type=None, status=None, transaction_sub_type=None,date=None):
        """
        获取商务卡对账数据
        获取交易列表
        :param transaction_type: 交易类型:
                                    账户：
                                        vcc_in 充值
                                        vcc_out 转出
                                        card_transaction_authorization_fee 卡授权费
                                    商务卡：
                                        card_consume 消费
                                        card_clearing 清算
                                        card_reversal 退回
                                        card_refund 退款
                                        card_deposit 卡转入
                                        card_to_card_account 卡转出
                                        card_clearing_deduction 卡清算扣款
                                        card_clearing_refund 卡清算退款
                                        system_deduction 系统扣款
                                        system_recharge 系统充值
        :param status: 交易状态:completed/failed/pending
        :param transaction_sub_type: 交易子类型:card /card_account
        :return:
        """
        #如果输入的时间为None，默认获取当前月的时间范围

        #根据输入的时间获取时间范围
        page = 1
        all_transaction_data = []
        while True:
            start_time, end_time = self.get_time_range(date)
            params_data = {
                'page': page,
                'take': 100,
                "created_at[]": ["2025-11-01 00:00", "2025-11-30 23:59"]
            }
            if transaction_sub_type:
                params_data['transaction_sub_type'] = transaction_sub_type
            if transaction_type:
                params_data['transaction_type'] = transaction_type
            if status:
                params_data['status'] = status

            reconciliation_data = self.user_http.send_request(api_name='获取交易列表', dict_data=params_data,
                                                                 nested_keys=['data', 'list'])
            if not reconciliation_data or len(reconciliation_data) == 0:
                return
            all_transaction_data.extend(reconciliation_data)
            total_count = self.user_http.send_request(api_name='获取交易列表', dict_data=params_data,
                                                         nested_keys=['data', 'total'])
            if total_count and len(all_transaction_data) >= total_count:
                break

            page += 1

        return all_transaction_data
    def calculate_transaction_totals(self, transaction_data):
        """
        计算交易总额和手续费
        :param transaction_data: 交易数据列表
        :return: 交易总额和手续费元组
        """
        if not transaction_data:
            return 0.0, 0.0

        total_amount = 0.0
        total_fee = 0.0

        for data in transaction_data:
            try:
                # 获取并转换金额，处理各种边界情况
                amount_str = data.get('amount')
                fee_str = data.get('fee')

                amount = float(amount_str) if amount_str and str(amount_str).strip() else 0.0
                fee = float(fee_str) if fee_str and str(fee_str).strip() else 0.0

                total_amount += amount
                total_fee += fee
                # print(f"交易金额: {amount}, 手续费: {fee}")
            except (ValueError, TypeError) as e:
                # 处理转换异常，记录日志或跳过异常数据
                print(f"警告: 数据转换错误 {data}, 错误: {e}")
                continue

        return total_amount, total_fee

    def get_card_data(self, transaction_type, status,transaction_sub_type,date=None):
        """
        获取商务卡账户交易数据
        :param transaction_type: 交易类型:
                                    账户：
                                        vcc_in 充值
                                        vcc_out 转出
                                        card_transaction_authorization_fee 卡授权费
                                    商务卡：
                                        card_consume 消费
                                        card_clearing 清算
                                        card_reversal 退回
                                        card_refund 退款
                                        card_deposit 卡转入
                                        card_to_card_account 卡转出
                                        card_clearing_deduction 卡清算扣款
                                        card_clearing_refund 卡清算退款
        :param status: 交易状态:completed/failed/pending
        :param transaction_sub_type: 交易子类型:card /card_account
        :return:
        """
        data = self.get_card_reconciliation_data(transaction_type=transaction_type, status=status,
                                                 transaction_sub_type=transaction_sub_type,date=date)
        total_amount, total_fee = self.calculate_transaction_totals(data)
        return total_amount, total_fee

    def get_card_account_count(self, transaction_type,date=None):
        """
        获取商务卡账户交易数据
        :param transaction_type: 交易类型:vcc_in 充值
                                        vcc_out 转出
                                        card_transaction_authorization_fee 卡授权费
        :return:
        """
        status_list = ['completed']
        total_amount = 0
        total_fee = 0
        for status in status_list:

            amount, fee = self.get_card_data(transaction_type=transaction_type, status=status, transaction_sub_type='card_account',date=date)
            total_amount += amount
            total_fee += fee
        return total_amount, total_fee

    def get_card_count(self, transaction_type, date= None):
        """
        获取商务卡账户交易数据
        :param transaction_type: 交易类型:
                                商务卡：
                                        card_consume 消费
                                        card_clearing 清算
                                        card_reversal 退回
                                        card_refund 退款
                                        card_deposit 卡转入
                                        card_to_card_account 卡转出
                                        card_clearing_deduction 卡清算扣款
                                        card_clearing_refund 卡清算退款
        :return:
        """
        status_list = ['completed']
        total_amount = 0
        total_fee = 0
        for status in status_list:
            amount, fee = self.get_card_data(transaction_type=transaction_type, status=status,
                                             transaction_sub_type='card',date=date)
            total_amount += amount
            total_fee += fee
        return total_amount, total_fee
























if __name__ == '__main__':
    transaction_sub_type = ['card', 'card_account']
    transaction_type = {'充值': 'vcc_in', '转出': 'vcc_out', '卡授权费': 'card_transaction_authorization_fee'}
    status = ['completed', 'failed', 'pending']
    card_transaction_type = {'充值': 'card_deposit',
                             '消费': 'card_consume',
                             '清算': 'card_clearing',
                             '退回': 'card_reversal',
                             '退款': 'card_refund'}

    card_transaction_record = CardTransactionRecord()

    for i in transaction_sub_type:
        if i == 'card':
            for j in status:
                for k, v in card_transaction_type.items():
                    print(i, k, j)
                    card_transaction_record.get_card_data(transaction_type=v, status=j,date='202511')

                    print(i, k, j)
        # if i == 'card_account':
        #     for j in status:
        #         for k, v in transaction_type.items():
        #             print(i, k, j)
        #             card_transaction_record.get_card_account_data(transaction_type=v, status=j)

