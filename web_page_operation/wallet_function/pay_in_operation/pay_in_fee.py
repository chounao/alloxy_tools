import math
from common.simple_request import HttpRequest
from common import read_and_save_tool
class PayInFee:
    def __init__(self,user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
        self.authority = self.config.get_url_data()
        self.list = []
        self.county = self.config.get_pay_in_county()

    def get_fiat_in_fee(self,currency):
        url = self.authority + '/web/crypto/get-fiat-in-fee'
        rate_fee = self.http_request.gets(url, nested_keys=['data'])
        fee = rate_fee['rate'][currency]
        per_count = rate_fee['per_count']
        prorate = rate_fee['prorate']
        # print(USDT_fee,USDC_fee)
        # print(f'{currency}手续费:{fee},每笔固定手续费:{per_count},每笔手续费比例:{prorate}')
        return fee, per_count, prorate

    #根据钱包获取汇率
    def get_exchange_rate(self,currency,country):
        url = self.authority + '/web/crypto/get-exchange-rate'
        params = {
            'from_currency': country,
            'to_currency': currency
        }
        data = self.http_request.send_request(api_name='钱包-获取汇率', dict_data=params, nested_keys=['data'])
        if data is None:
            # 处理数据为空的情况
            raise ValueError("Failed to fetch fee data")
        buy = data['data']['buy']
        locale = data['data']['locale']

        return buy, locale

    def custom_round(self, value):
        """
        自定义舍入规则：小数点后第三位不为0则进位，为0则舍去
        """
        # 将数值乘以100，获取前两位小数
        multiplied = value * 100
        # 获取第三位小数
        third_decimal = int((value * 1000) % 10)
        # 如果第三位小数不为0，则进位；否则舍去
        if third_decimal != 0:
            return math.ceil(multiplied) / 100
        else:
            return math.floor(multiplied) / 100
    def get_pay_in_fee(self,send_amount,currency,country):
        fee, per_count, prorate = self.get_fiat_in_fee(currency)
        # 计算手续费
        amount = float(send_amount) /float(fee)
        pay_in_fee = self.custom_round(amount * prorate + per_count*float(fee))
        # pay_in_fee = amount * prorate + per_count * float(fee)
        estimated_amount = send_amount - pay_in_fee
        print(f'{currency}支付手续费:{pay_in_fee}')
        print(f'{currency}预计到账金额:{estimated_amount}')
        return pay_in_fee, estimated_amount
if __name__ == '__main__':
    pay_in_fee = PayInFee()
    pay_in_fee.get_pay_in_fee(1000,'USDT','UGX')
