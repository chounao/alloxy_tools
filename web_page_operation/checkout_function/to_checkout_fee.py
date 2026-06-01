from common.simple_request import HttpRequest
from common import read_and_save_tool


class ToCheckoutFee:
    def __init__(self, http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()
        self.config = read_and_save_tool.ConfigTools()
        self.authority = self.config.get_url_data()
    def fees(self,currency):
        """

        获取手续费
        获取概览
        :param currency: 币种
        :return:
        """
        # method, url = self.config.get_data_from_name()
        data = self.http_request.send_request(api_name='获取概览', nested_keys=['data'])

        usd_rate = float(data['total_assets'][currency]['usd_rate'])
        fee_rate = float(data['feeSettings']['fee_rate'])#百分比
        fixed_fee = float(data['feeSettings']['fixed_fee'])#固定
        withdrawable_assets = float(data['total_assets'][currency]['withdrawable_assets'])
        # print(usd_rate, fee_rate, fixed_fee,withdrawable_assets)
        return usd_rate,fee_rate,fixed_fee,withdrawable_assets
    def all_fees(self,currency,amount):
        """
        计算手续费
        :param amount:
        :param currency:
        :return:
        """
        usd_rate, fee_rate, fixed_fee,withdrawable_assets = self.fees(currency)
        fee = float(amount) * fee_rate/100 +fixed_fee*usd_rate + float(amount)
        print('当前的{}手续费{}'.format(currency,fee))
        # print(type(fee))
        return fee,withdrawable_assets

    def get_wallet(self, currency, amount):
        """
        获取钱包余额
        :param currency:
        :return:
        """
        # usd_rate, fee_rate, fixed_fee, withdrawable_assets = self.fees(currency)
        fee, withdrawable_assets = self.all_fees(currency, amount)
        self.send_amount(currency, amount)
        wallet = withdrawable_assets - fee
        print('当前钱包剩余{}'.format(wallet))