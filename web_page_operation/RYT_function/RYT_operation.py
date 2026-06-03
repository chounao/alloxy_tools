from common.simple_request import HttpRequest
from common import read_and_save_tool
from web_page_operation.RYT_function.RYT_fee import RYTFee


class RYT_Operation:
    def __init__(self, user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
        self.authority = self.config.get_url_data()
        self.ryt_fee = RYTFee()


    def buy_RYT(self, amount):
        """
        购买RYT
        :param amount: 金额
        :param currency: 币种
        :param chain: 链
        :return:
        """
        parmars = {
        "amount": amount,
        "check_method": "email",
        "access_code": "123456",
        "know_terms": True,
        }
        usdcAmount = self.ryt_fee.get_wallets_data()
        print("当前USDC余额为：", usdcAmount)
        data = self.http_request.send_request(api_name='ryt购买', data=parmars)
        self.ryt_fee.buying_expenses_RYT(amount,usdcAmount)
        id_no = data.json()['data']['contractTransaction']['id_no']
        return id_no



    def sell_RYT(self, amount):
        """
        RYT 赎回
        :param amount: 金额
        :return:
        """
        ryt_num = self.ryt_fee.get_ryt_data()
        parmars = {
            "amount": amount,
            "check_method": "email",
            "access_code": "123456"
        }
        self.ryt_fee.get_wallets_data()
        data = self.http_request.send_request(api_name='ryt赎回', data=parmars)
        self.ryt_fee.selling_expenses_RYT(amount,ryt_num)
        id_no = data.json()['data']['contractTransaction']['id_no']
        return id_no





if __name__ == '__main__':
    ryt = RYT_Operation()
    # ryt.buy_RYT(1)
    ryt.sell_RYT(1)

