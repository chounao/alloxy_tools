from common.simple_request import HttpRequest
from common import read_and_save_tool


class WalletOperation:
    def __init__(self, http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()
        self.config = read_and_save_tool.ConfigTools()


    def get_wallet_data(self,currency):
        """
        获取钱包数据
        :return:
        """
        method, url = self.config.get_data_from_name('钱包-获取钱包列表')
        # wallet_url = self.authority + value[1]
        wallet_data = self.http_request.send_request(method,url, jsonpath_expr=f'$.data.list[?(@.currency=="{currency}")]')
        print(wallet_data)
        wallet_price = float(wallet_data['price'])
        wallet_id = wallet_data['id']
        return wallet_price,wallet_id
    def get_fee(self):
        """
        获取账户费率
        :return:
        """
        dict_data ={
            "type": "crypto_withdraw_fee",
        }
        # method, url = self.config.get_data_from_name('账户费率',dict_data=dict_data)
        # fee_url = url+"?feeType=crypto_withdraw_fee"
        fee_data = self.http_request.send_request('账户费率',dict_data=dict_data, jsonpath_expr='$.data.number')
        print(fee_data)
        return fee_data
    def get_chain_data(self,chain):
        """
        获取链数据
        :param chain_name: 链名称
        :return: 链id
        """
        # chain_url = self.authority + "/web/crypto/chain"
        # method, url = self.config.get_data_from_name('钱包-获取支持的链列表')
        chain_id = self.http_request.send_request(api_name='钱包-获取支持的链列表',jsonpath_expr=f'$.data.data[?(@.chain_name =="{chain}")].chain_id')
        # print(chain_id)
        return chain_id
    def get_payee_id(self,chain,currency):
        """
        获取收款人id
        :param chain_name: 链名称
        :param currency: 加密货币名称
        :return: 收款人id
        """
        chain_id = int(self.get_chain_data(chain))
        # method, url = self.config.get_data_from_name('钱包-获取加密收款地址列表')
        # payee_url = url + f"?chain_id={chain_id}&currency={currency}"
        dict_data ={
            "chain_id": chain_id,
            "currency": currency
        }

        payee_id = self.http_request.send_request(api_name='钱包-获取加密收款地址列表',dict_data=dict_data,nested_keys=['data','list',0,'id'])
        print(payee_id)
        return payee_id
    #充值
    def get_wallet_address(self,currency,chain):
        """
        链上充值和法币充值
        钱包充值
        :param currency: 加密货币名称
        :return:
        """
        chain_id = int(self.get_chain_data(chain))
        # method, url = self.config.get_data_from_name('钱包-获取币种/链对应的钱包地址')
        # url = url + f"?currency={currency}&chain_ids={chain_id}"
        dict_data ={
            "currency": currency,
            "chain_ids": chain_id
        }
        wallet_address = self.http_request.send_request(api_name='钱包-获取币种/链对应的钱包地址',dict_data=dict_data,nested_keys=['data','adress'])
        print(wallet_address)
        return wallet_address
    #pay_in操作
    #钱包汇率操纵
    def get_exchange_rate(self,from_currency,to_currency):
        """
        获取汇率
        :param from_currency: 加密货币名称
        :param to_currency: 法币名称
        :return:
        """
        # method, url = self.config.get_data_from_name('钱包-获取汇率')
        # url = url + f"?from_currency={from_currency}&to_currency={to_currency}"

        dict_data ={
            "from_currency": from_currency,
            "to_currency": to_currency
        }
        exchange_data = self.http_request.send_request(api_name='钱包-获取汇率',dict_data=dict_data, nested_keys=['data','data'])
        buy = exchange_data['buy']
        locale = exchange_data['locale']
        print(exchange_data)
        return buy,locale
    def pay_in(self,amount,from_currency,currency,chain):
        """
        钱包充值
        :param amount: 充值金额
        :param from_currency: 付币名称
        :param currency: 充值币名称
        :param chain: 链名称
        :return:
        """

        # method, url = self.config.get_data_from_name('钱包-提交payin请求')


        chain_id = self.get_chain_data(chain)
        buy, locale = self.get_exchange_rate(from_currency, currency)
        data = {"type":"fiat","country":locale,"from_currency":from_currency,"to_currency":currency,"chain":chain_id,"amount":amount}
        pay_in_data = self.http_request.send_request(api_name='钱包-提交payin请求',data=data)
        print(pay_in_data)
        return pay_in_data
    #转出
    def wallet_transfer(self,chain,currency,amount):
        """
        钱包转出
        :param wallet_id: 钱包id
        :param amount: 转出金额
        :return:
        """
        wallet_price,wallet_id = self.get_wallet_data(currency)
        print("转出前的钱包余额为：",wallet_price)
        payee_id = self.get_payee_id(chain, currency)
        chain_id = self.get_chain_data(chain)
        data ={"wallet_id":wallet_id,"chain_id":chain_id,"payee_id":payee_id,"amount":amount,"attachments":[],"check_method":"email","access_code":"123456"}

        # method, url = self.config.get_data_from_name('钱包-加密资产转出')
        self.http_request.send_request(api_name='钱包-加密资产转出',data= data)

        new_wallet_price = wallet_price+amount
        print("钱包余额为：",new_wallet_price)
        wallet_price, wallet_id = self.get_wallet_data(currency)
        if wallet_price == new_wallet_price:
            print("转出的额度正常")
        else:
            print("转出的额度异常")
        return new_wallet_price




if __name__ == '__main__':
    chain = "arbitrum"
    currency = "USDC"
    from_currency = "XAF"
    amount = 100
    wallet_operation = WalletOperation()

    # wallet_operation.get_chain_data(chain)
    # wallet_operation.get_fee()
    # wallet_operation.get_wallet_data(currency)
    # wallet_operation.get_payee_id(chain,currency)
    # wallet_operation.wallet_transfer(chain,currency,0.01)
    # wallet_operation.get_wallet_address(currency,chain)
    wallet_operation.pay_in(amount,from_currency,currency,chain)





























