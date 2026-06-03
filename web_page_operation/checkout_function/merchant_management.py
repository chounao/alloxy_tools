from common.simple_request import HttpRequest
from common import read_and_save_tool
import random
class MerchantManagement:
    def __init__(self, user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
        self.authority = self.config.get_url_data()

    """
        下方的流程是创建子商户的流程
        """

    def create_merchant(self, name):
        """
        创建商户
        :param name: 商户名称
        :return: 地址数据字典
        """
        if not name:
            raise ValueError("商户名称不能为空")

        # 构建请求体

        currency_list = ['USDT', 'USDC']

        # 为每种币种获取支持的链并随机选择一个
        for currency in currency_list:
            # method, url = self.config.get_data_from_name(
            #     '获取支持的链',
            #     typename=f'currency={currency}'
            # )
            dict_data = {
                'currency': currency
            }
            chain_data = self.http_request.send_request(api_name='获取支持的链', dict_data=dict_data,
                                                        nested_keys=['data', 'data', 'chains'])

            if not chain_data or not isinstance(chain_data, list):
                raise ValueError(f"无法获取 {currency} 的链信息")

            # 随机选择一个链
            selected_chain = random.choice(chain_data)['chain']
            body = {
                "merchant_name": name,
                "withdraw_chain_currency": []
            }

            body['withdraw_chain_currency'].append({
                "currency": currency,
                "chain": selected_chain
            })

        # 创建商户
        # method, url = self.config.get_data_from_name('创建商户')
        merchant_data = self.http_request.send_request(api_name='创建商户', data=body, nested_keys=['data'])

        if not merchant_data:
            raise ValueError("创建商户失败")

        # 提取地址信息
        address_info = merchant_data.get('withdraw_chain_currency_address', [])
        if not address_info:
            raise ValueError("未返回商户地址信息")

        # 构建地址数据字典
        address_data = {}
        for item in address_info:
            currency = item.get('currency')
            if currency:
                address_data[currency] = {
                    'address': item.get('address'),
                    'chain': item.get('chain')
                }

        return address_data

    def get_merchant_address_data(self, name):
        """
        创建商户并获取地址数据的完整流程
        :param name: 商户名称
        :return: 地址数据字典
        """
        try:
            # 创建商户
            address_data = self.create_merchant(name)

            # 打印地址信息
            for currency, info in address_data.items():
                print(f"{currency} 地址: {info['address']}")
                print(f"{currency} 链: {info['chain']}")

            return address_data

        except Exception as e:
            print(f"创建商户失败: {e}")
            return None


if __name__ == '__main__':
    to_checkout = MerchantManagement()

    currency = ['USDC', 'USDT']
    amount = "0.001"
    for i in currency:
        print(
            '===================================================================================================充值币种为：',
            i)
        to_checkout.all_tocheckout(i, amount, '123456')

    # 创建子商户并操作收款流程
    """
    固定内容
    """
    # address_data = {'USDT': {'address':'THnymPLodBJwP4THCogAoLHMgpMcRNeezb','chain': 'TRX'},
    #         'USDC': {'address':'0xC4069Aa887B43AFd89B585Ed0e6163585fca8f59', 'chain':'ETH'},
    #         }
    # name = 'Madeline'
    # to_checkout.Recorded(address_data,name,'USDT',0.5)
    # to_checkout.Recorded(address_data,name,'USDC',5.3)

    """
    传参
    """
    # fake = Faker('en_US')
    # name = fake.first_name()
    # address_data = to_checkout.get_merchant_address_data(name=name)
    # if name :
    #     to_checkout.Recorded(address_data,name,'USDT',32.5)
    #     to_checkout.Recorded(address_data,name,'USDC',12.8)
