from traceback import print_tb

from common.simple_request import HttpRequest
from common import read_and_save_tool
import requests

class PayMentOut:
    def __init__(self,user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
        self.authority = self.config.get_value('TEST_CONFIG', 'URL')
        self.chain = 'MATIC'
        self.wallet = 'AXCNH'
        self.from_currency = 'USDC'
        # self.authority  = 'https://ax-api.pertest.tech/web/'
        self.fei_currency = ['BWP','KES','MWK','NGN','RWF','ZAR','TZS','UGX','ZMW']
        self.currency = {
            'BWP':[150,1000000],#博茨瓦纳
            'KES':[500,999999],#肯尼亚
            'MWK':[5000,20000000],#马拉维
            'NGN':[1800,30000000],#尼日利亚
            'RWF':[1500,10000000],#卢旺达
            'ZAR':[200,500000],#南非
            'TZS':[2500,40000000],#坦桑尼亚
            'UGX':[15000,36000000],#乌干达
            'ZMW':[100,15000000]#赞比亚
        }

    def get_Wallet(self,from_currency):
        """
        通过钱包接口获取usdc/usdt的ID
        :return: usdc/usdt的ID
        """
        #url  = self.authority+'/web/crypto/wallets'
        wallet_list = self.http_request.send_request(api_name='钱包-获取钱包列表', nested_keys=['data', 'list'])
        for i in wallet_list:
            if i['currency'] == from_currency:
                from_currency_id = i['id']

                print(from_currency_id)
                return from_currency_id

    def for_currency_get_fei(self,from_currency,to_currency):
        #path = '/web/crypto/get-fiat-rate?from_currency={}&to_currency={}'.format(from_currency,to_currency)
        #url = self.authority + path
        dict_data ={
            'from_currency':from_currency,
            'to_currency':to_currency
        }
        fei = self.http_request.send_request(api_name='获取pay_out汇率', dict_data=dict_data, nested_keys=['data'])
        print('汇率为：',fei,type(fei))
        return fei
    def get_payee_fee(self,to_currency):
        # 获取收款
        path = '/web/crypto/payee/fiat?currency={}&payee_name=&page=1&take=100&status=active'.format(to_currency)
        url = self.authority + path
        dict_data ={
            'currency':to_currency,
            'payee_name':'',
            'page':1,
            'take':100,
            'status':'active'
        }
        payee_id = self.http_request.send_request(api_name='钱包-获取法币收款地址列表', dict_data=dict_data, nested_keys=['data','list',0,'id'])

        return payee_id


    def fiat_transfer_out(self,amount,from_currency,to_currency, memo):
        """
        Fiat transfer out /pay_put
        :param amount: 页面输入的金额
        :param from_currency: 付款币种
        :param to_currency: 收款币种
        :param memo: 备注
        :return:
        """
        to_currency_rate = self.for_currency_get_fei(from_currency,to_currency)

        payee_id = self.get_payee_fee(to_currency)
        wallet_id = self.get_Wallet(from_currency)
        to_currency_amount = amount * to_currency_rate

        data = {
            "to_currency_rate": to_currency_rate,
            "to_currency_amount": to_currency_amount,
            "access_code": "123456",
            "amount": amount,
            "check_method": "email",
            "payee_id": payee_id,
            "wallet_id": wallet_id,
            "memo": memo,
            "attachments": []
        }
        path = '/web/crypto/fiat-transfer-out'
        url = self.authority + path

        response = self.http_request.send_request(api_name='钱包-法币转出', data=data)
        print(response.text)




if __name__ == '__main__':
    memo = 'housing'
    from_currency = 'USDT'
    to_currency = 'KES'
    count = {
        'BWP': [150, 1000000],
        # 'KES': [500, 999999],
        # 'MWK': [5000, 20000000],
        # 'NGN': [1800, 30000000],
        # 'RWF': [1500, 10000000],
        # 'ZAR': [200, 500000],
        #'TZS': [2500, 40000000],
        # 'UGX': [15000, 36000000],
        # 'ZMW': [100, 15000000]

    }
    pay_out = PayMentOut()
    # for to_currency, value in count.items() :
    #
    #     print('---------------------------------------------------------------------------------')
    #     print('执行的是小于最小值的情况')
    #     pay_out.fiat_transfer_out(value[0]-1,from_currency, to_currency, memo)
    #     print('执行的是大于最大值的情况')
    #     pay_out.fiat_transfer_out(value[1]+1, from_currency, to_currency, memo)
    #     print('执行边界最小值')
    #     pay_out.fiat_transfer_out(value[0], from_currency, to_currency, memo)
    #     print('执行正常最大值')
    #     pay_out.fiat_transfer_out(value[1], from_currency, to_currency, memo)
    pay_out.for_currency_get_fei(from_currency,to_currency)
    pay_out.get_Wallet(from_currency)