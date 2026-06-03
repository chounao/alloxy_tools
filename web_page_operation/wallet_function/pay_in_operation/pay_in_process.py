
from common.simple_request import HttpRequest
from common import read_and_save_tool
from web_page_operation.wallet_function.pay_in_operation.pay_in_fee import PayInFee
class PayInProcess:
    def __init__(self, user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
        self.authority = self.config.get_url_data()
        self.county = self.config.get_pay_in_county()
        self.pay_in_fee = PayInFee()


    def pay_in_process(self, send_amount,currency,country):
        buy, locale = self.pay_in_fee.get_exchange_rate(currency,country)
        data = {
            "type": "fiat",
            "country": locale,
            "from_currency": country,
            "to_currency": currency,
            "amount": send_amount
        }
        savePayinOrder = self.http_request.send_request(api_name='钱包-提交payin请求', data=data,
                                                        nested_keys=['data', 'savePayinOrder'])
        source_order_id = savePayinOrder['source_order_id']
        transaction_id = savePayinOrder['transaction_id']
        #计算相关费用
        self.pay_in_fee.get_pay_in_fee(send_amount,currency,country)

        return source_order_id, transaction_id