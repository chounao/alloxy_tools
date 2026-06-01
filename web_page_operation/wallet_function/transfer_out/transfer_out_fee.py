from common.simple_request import HttpRequest
from common import read_and_save_tool

class TransferOutFee:
    def __init__(self,http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()
        self.config = read_and_save_tool.ConfigTools()
        self.authority = self.config.get_url_data()
        self.list = []
        self.county = self.config.get_pay_out_county()
    def get_wallets_data(self,currency):
        """
        获取钱包数据
        :return: 钱包数据
        """

        wallets_data = self.http_request.send_request(api_name='钱包-获取钱包列表', jsonpath_expr=f'$.data.list[?(@.currency == "{currency}")]')

        return wallets_data

    def assert_wallets_data(self,currency,send_amount,wallet_before):
        """
        断言钱包数据
        :param currency: 币种
        :return: None
        """
        wallet_afeter = float(wallet_before) - float(send_amount)

        now_wallet_data = float(self.get_wallets_data(currency)['amount'])
        if abs(now_wallet_data - wallet_afeter) < 1e-6:
            print(f'{currency}钱包数据断言成功')
        else:
            print(f'{currency}钱包数据断言失败')



if __name__ == '__main__':
    transfer_out_fee = TransferOutFee()
    transfer_out_fee.get_wallets_data('USDT')
