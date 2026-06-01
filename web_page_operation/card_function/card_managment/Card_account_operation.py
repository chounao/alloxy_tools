
"""

卡账户转入转出的操作

"""
from web_page_operation.card_function.card_managment import card_wallet_fee
from common.simple_request import HttpRequest
from common import read_and_save_tool


class CardAccountOperation():
    def __init__(self,card_id = None,http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()
        self.config = read_and_save_tool.ConfigTools()
        self.url = self.config.get_url_data()
        self.card_wallet_balance = card_wallet_fee.Balance_Calculate(self.http_request)
        self.before_data  = self.card_wallet_balance.get_card_balance()
        self.card_id = card_id

    # 卡账户充值
    def wallet_to_card(self, currency, send_amount):
        """
        钱包转卡
        获取手续费列表
        :param currency: 钱包类型
        :param send_amount: 转账金额
        :return:
        """

        print(f'操作前：卡账户余额{self.before_data[0]}，卡内余额{self.before_data[1]}')
        wallet_id = self.card_wallet_balance.get_wallet_id(currency)
        wallet_amount = self.card_wallet_balance.get_wallet_amount(currency)

        # 发生充值请求
        body = {"wallet_id": wallet_id, "from_currency": currency, "amount": send_amount, "memo": "123",
                "to_currency": "USD"}
        # wallet_to_card_url = self.authority + "/web/virtual-card/wallet-to-card-account"
        response = self.http_request.send_request(api_name='钱包转到卡账户', data=body)

        #验证钱包，卡账户余额，卡余额
        if response.status_code == 201:

            # 获取手续费
            fee_amount = self.card_wallet_balance.get_wallet_to_card_fee_amount(currency, send_amount)
            # 验证余额
            self.card_wallet_balance.get_card_balance_before_and_after(currency,send_amount ,fee_amount, 'wallet_to_card',self.before_data)

            # 验证余额

            self.card_wallet_balance.get_wallet_to_card_balance_before_and_after(currency, send_amount, 'wallet_to_card',wallet_amount)
        else:
            print('钱包转卡失败')



    #卡账户转出
    def card_transfer_out_to_wallet(self, currency, send_amount):
        """
        卡转出
        从卡转出到卡账户
        :param currency: 钱包类型
        :param send_amount: 转账金额
        :return:
        """

        print(f'操作前：卡账户余额{self.before_data[0]}，卡内余额{self.before_data[1]}')
        wallet_id = self.card_wallet_balance.get_wallet_id(currency)
        wallet_amount = self.card_wallet_balance.get_wallet_amount(currency)
        body = {"wallet_id": wallet_id,
                "from_currency": "USD",
                "amount": send_amount,
                "memo": "123",
                "to_currency": currency}

        response = self.http_request.send_request(api_name='卡账户转出到钱包', data=body)
        if response.status_code == 201:
            print('转出成功')
            # 获取手续费
            #没有手续费
            # 验证余额
            self.card_wallet_balance.get_card_balance_before_and_after(currency,send_amount ,0, 'card_to_wallet',self.before_data)
            # 验证余额
            self.card_wallet_balance.get_wallet_to_card_balance_before_and_after(currency, send_amount, 'card_to_wallet',wallet_amount)
        else:
            print('转出失败')




if __name__ == '__main__':

    card_transaction = CardAccountOperation()
    card_transaction.wallet_to_card(currency='USDC', send_amount=10)
    # card_transaction.card_transfer_out_to_wallet(currency='USDC', send_amount=10)
