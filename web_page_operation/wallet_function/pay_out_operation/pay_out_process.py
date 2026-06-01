from common.simple_request import HttpRequest
from common import read_and_save_tool
from pay_out_fee import PayOutFee


class PayOutProcess:
    def __init__(self, http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()
        self.config = read_and_save_tool.ConfigTools()
        self.config = read_and_save_tool.ConfigTools()
        self.authority = self.config.get_url_data()
        self.county = self.config.get_pay_out_county()
        self.pay_out_fee = PayOutFee()
    def get_Wallet(self,currency):
        """
        通过钱包接口获取usdc/usdt的ID
        :return: usdc/usdt的ID
        """
        #url  = self.authority+'/web/crypto/wallets'
        currency_id = self.http_request.send_request(api_name='钱包-获取钱包列表', jsonpath_expr=f'$.data.list[?(@.currency == "{currency}")].id')
        print(f'获取到的{currency}钱包ID为：{currency_id}')
        return currency_id

    def get_payee_fee(self, country):
        # 获取收款
        path = '/web/crypto/payee/fiat?currency={}&payee_name=&page=1&take=100&status=active'.format(country)
        url = self.authority + path
        dict_data = {
            'currency': country,
            'payee_name': '',
            'page': 1,
            'take': 100,
            'status': 'active'
        }
        payee_id = self.http_request.send_request(api_name='钱包-获取法币收款地址列表', dict_data=dict_data,
                                                  nested_keys=['data', 'list', 0, 'id'])
        print(f'获取到的{country}收款地址ID为：{payee_id}')
        return payee_id
    def fiat_transfer_out(self,send_amount,country,currency, memo):
        """
        Fiat transfer out /pay_put
        :param send_amount: 页面输入的金额
        :param country: 收款国家
        :param currency: 收款币种
        :param memo: 备注
        :return:
        """
        to_currency_rate = self.pay_out_fee.for_currency_get_fei(currency, country)

        payee_id = self.get_payee_fee(country)
        wallet_id = self.get_Wallet(currency)
        to_currency_amount = send_amount * to_currency_rate

        data = {
            "to_currency_rate": to_currency_rate,
            "to_currency_amount": to_currency_amount,
            "access_code": "123456",
            "amount": send_amount,
            "check_method": "email",
            "payee_id": payee_id,
            "wallet_id": wallet_id,
            "memo": memo,
            "attachments": []
        }
        path = '/web/crypto/fiat-transfer-out'
        # url = self.authority + pathget_pay_out_county

        id_no = self.http_request.send_request(api_name='钱包-法币转出', data=data,jsonpath_expr='$..id_no')
        self.pay_out_fee.get_pay_out_fee(send_amount,currency,country)
        print(f'获取到的id_no为：{id_no}')
        return id_no

if __name__ == '__main__':
    pay_out_process = PayOutProcess()
    pay_out_process.fiat_transfer_out(100,'USD','USDC','test')
    #pay_out_process.get_Wallet('USDC')
    #pay_out_process.get_payee_fee('ZAR')
