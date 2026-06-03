from common.simple_request import HttpRequest
from common.get_time import GetTime
from common import read_and_save_tool
from common import logger
logger = logger.logger
class ToCheckout:
    def __init__(self, user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
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
    def get_order_reconciliation_data(self, status=None,date=None):
        """
        获取订单列表
        :param status: 交易状态:
                            open 进行中
                            close 已过期
                            done 已完成
                            withdraw_pending 待审核
                            withdraw_rejected 已拒绝
                            withdraw_completed 已完成
        :return:
        """
        page = 1
        all_transaction_data = []
        while True:
            time_range = self.get_time_range(date)
            params_data = {
                'page': page,
                'take': 100,
                # 'created_at%5B%5D': [time_range[0], time_range[1]],
                'created_at': [time_range[0], time_range[1]],

            }

            if status:
                params_data['status'] = status

            reconciliation_data = self.http_request.send_request(api_name='获取订单列表', dict_data=params_data,
                                                                 nested_keys=['data', 'list'])
            if not reconciliation_data or len(reconciliation_data) == 0:
                break
            all_transaction_data.extend(reconciliation_data)
            total_count = self.http_request.send_request(api_name='获取订单列表', dict_data=params_data,
                                                         nested_keys=['data', 'total'])
            if total_count and len(all_transaction_data) >= total_count:
                break

            page += 1
        print(len(all_transaction_data))
        return all_transaction_data
            #


    def get_transaction_record(self, status,date,currency,order_type):
        """
        获取交易记录
        :param status: 交易状态
        :param date: 时间范围
        :param currency: 交易币种
        :param order_type: 订单类型
        :return:
        """
        reconciliation_data = self.get_order_reconciliation_data(status,date)
        total_amount = 0.0
        total_fee = 0.0
        try:
            for i in reconciliation_data:
                transaction_records = i.get('transaction_records')[0]
                print(transaction_records)
                # if transaction_records and isinstance(transaction_records, list):
                if transaction_records.get('currency') == currency and transaction_records.get('order_type') == order_type:
                    fee = float(transaction_records.get('fee')) if transaction_records.get('fee') else 0.0
                    print(f"Fee: {fee}")
                    amount = float(transaction_records.get('amount')) if transaction_records.get('amount') else 0.0
                    print(f"Amount: {amount}")
                    total_fee += fee
                    total_amount += amount

        except Exception as e:
            logger.error(f"获取交易记录失败: {e}")
        return total_fee, total_amount

    def withdraw_data(self,status,date,currency):
        all_amoubt = 0.0
        try:
            total_fee, total_amount = self.get_transaction_record(status, date, currency,'withdraw')

            if status == 'withdraw_pending':
                all_amoubt = -total_amount - total_fee
            if status == 'withdraw_rejected':
                all_amoubt = +total_amount +total_fee
            if status == 'done':
                all_amoubt = -total_amount - total_fee
            if status == 'open':
                all_amoubt = -total_amount - total_fee
            if status == 'withdraw_completed':
                all_amoubt = -total_amount - total_fee

            return all_amoubt, total_fee, total_amount
        except Exception as e:
            print(f"处理货币 {currency} 时出错: {e}")

    def pay_data(self,status,date,currency):
        all_amoubt = 0.0
        try:
            total_fee, total_amount = self.get_transaction_record(status, date, currency,'pay')

            if status == 'withdraw_pending':
                all_amoubt = -total_amount - total_fee
            if status == 'withdraw_rejected':
                all_amoubt = +total_amount + total_fee
            if status == 'open':
                all_amoubt = +total_amount + total_fee
            if status == 'withdraw_completed':
                all_amoubt = +total_amount + total_fee
            return all_amoubt, total_fee, total_amount
        except Exception as e:
            print(f"处理货币 {currency} 时出错: {e}")

    def refund_data(self,status,date,currency):
        all_amoubt = 0.0
        try:
            total_fee, total_amount = self.get_transaction_record(status, date, currency,'refund')

            if status == 'withdraw_pending':
                all_amoubt = -total_amount - total_fee
            if status == 'withdraw_rejected':
                all_amoubt = +total_amount + total_fee
            if status == 'done':
                all_amoubt = +total_amount + total_fee
            if status == 'open':
                all_amoubt = +total_amount + total_fee
            if status == 'withdraw_completed':
                all_amoubt = +total_amount + total_fee
            return all_amoubt, total_fee, total_amount
        except Exception as e:
            print(f"处理货币 {currency} 时出错: {e}")

