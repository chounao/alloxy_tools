from common.simple_request import HttpRequest
from common import read_and_save_tool
from transfer_out_fee import TransferOutFee
import random

class TransferOutOperation:
    def __init__(self, user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
        self.config = read_and_save_tool.ConfigTools()
        self.authority = self.config.get_url_data()
        self.county = self.config.get_pay_out_county()
        self.transfer_out_fee = TransferOutFee()

    #获取对应的链
    def get_chain(self,chain_name):
        """
        获取对应的链
        :return: 链
        """
        chain_id = self.http_request.send_request(api_name='钱包-获取支持的链列表', jsonpath_expr=f'$.data.data[?(@.chain_name=="{chain_name}")].chain_id')

        return chain_id

    def chain(self):
        """
        获取对应的链
        :return: 链
        """
        chain = self.http_request.send_request(api_name='钱包-获取支持的链列表'
                                               )
        print(chain.text)


    #获取转出账户id
    def get_payee_id(self, currency,chain_id):
        """
        获取转出账户id
        :param currency: 币种
        :return: 转出账户id
        """

        data = {
            'page': 1,
            'take': 100,
            'currency': currency,
            'chain_id': chain_id,

        }
        payee_id = self.http_request.send_request(api_name='钱包-获取加密收款地址列表', dict_data=data,jsonpath_expr=f'$.data.list[?(@.status=="active")].id')

        return payee_id
    #转出

    def transfer_out(self, amount,currency,chain_name):
        """
        转出
        :param currency: 币种
        :param amount: 金额
        :param address: 地址
        :param chain_id: 链id
        :return: 交易id
        """
        wallet_before = self.transfer_out_fee.get_wallets_data(currency)['amount']
        wallet_id = self.transfer_out_fee.get_wallets_data(currency)['id']
        chain_id = self.get_chain(chain_name)
        print(chain_id)
        payee_id = self.get_payee_id(currency,chain_id)
        body= {"wallet_id": wallet_id,
                "chain_id": chain_id,
                "payee_id": random.choice(payee_id),
                "amount": amount,
                "attachments": [
                    # {"file_name": "寻汇渠道接入需求文档",
                    # "file_suffix": "pdf",
                    # "file_type": "application/pdf",
                    # "file_url": "https://sandbox-hangzhou-web.s3.ap-southeast-2.amazonaws.com/929ff175-e26b-43ad-ba02-467756bff867/2026-09-08/202609081413222164920.pdf"
                    # }
        ],
                "check_method": "email",
                "access_code": "123456"}
        response = self.http_request.send_request(api_name='钱包-加密资产转出', data=body)
        if response.status_code == 201:
            print('转出成功')
            # 获取手续费
            # 没有手续费
            # 验证余额
            self.transfer_out_fee.assert_wallets_data(currency,amount,wallet_before=wallet_before)
        else:
            print('转出失败')


if __name__ == '__main__':
    amount = 13
    currency = 'USDT'
    chain_name = 'Arbitrum'
    transfer_out_operation = TransferOutOperation()
    #chain_id = transfer_out_operation.get_chain(chain_name)
    #transfer_out_operation.get_payee_id(currency,chain_id)
    transfer_out_operation.transfer_out(amount,currency,chain_name)
