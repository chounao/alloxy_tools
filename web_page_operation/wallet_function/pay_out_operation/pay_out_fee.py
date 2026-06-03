from common.simple_request import HttpRequest
from common import read_and_save_tool
import math



class PayOutFee:
    def __init__(self,user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
        self.config = read_and_save_tool.ConfigTools()
        self.authority = self.config.get_url_data()
        self.county = self.config.get_pay_in_county()

    def get_fiat_in_fee(self, currency):
        url = self.authority + '/web/crypto/get-fiat-fee'
        rate_fee = self.http_request.gets(url, nested_keys=['data'])
        fee = rate_fee['rate'][currency]
        per_count = rate_fee['per_count']
        prorate = rate_fee['prorate']
        # print(USDT_fee,USDC_fee)
        print(f'{currency}手续费:{fee},每笔固定手续费:{per_count},每笔手续费比例:{prorate}')
        return fee, per_count, prorate

    def for_currency_get_fei(self, currency, country):
        # path = '/web/crypto/get-fiat-rate?from_currency={}&to_currency={}'.format(from_currency,to_currency)
        # url = self.authority + path
        dict_data = {
            'from_currency': currency,
            'to_currency': country
        }
        fei = self.http_request.send_request(api_name='获取pay_out汇率', dict_data=dict_data, nested_keys=['data'])
        print('汇率为：', fei, type(fei))
        return fei

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
    def get_pay_out_fee(self, send_amount, currency, country):
        to_currency_rate = self.for_currency_get_fei(currency, country)
        to_currency_amount = send_amount * to_currency_rate
        print(to_currency_amount)
        fee, per_count, prorate = self.get_fiat_in_fee(currency)
        pay_out_fee = self.custom_round(float(per_count) * float(fee) + float(prorate) * float(send_amount))
        print(pay_out_fee)
        return pay_out_fee



if __name__ == '__main__':
    pay_out_fee = PayOutFee()
    pay_out_fee.get_pay_out_fee(10000, 'USDC', 'ZAR')
