

"""
不同流程的查询费的接口 通过fee计算对应的费用，并获取对应的余额
"""
from decimal import Decimal
from common.simple_request import HttpRequest
from common import read_and_save_tool
class Balance_Calculate():
    def __init__(self,http_request= None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()
        self.config = read_and_save_tool.ConfigTools()
        self.url = self.config.get_url_data()
    def get_wallet_data(self, currency):
        """
        获取钱包数据
        钱包-获取钱包列表
        :param currency: 钱包类型
        :return:
        """
        # wallet_url = self.authority + "/web/crypto/wallets"
        wallet_data = self.http_request.send_request(api_name='钱包-获取钱包列表', jsonpath_expr=f'$.data.list[?(@.currency=="{currency}")]')
        wallet_price = float(wallet_data['price'])
        wallet_id = wallet_data['id']
        wallet_amount = float(wallet_data['amount'])
        # print(wallet_price, wallet_id,wallet_amount)
        return wallet_price, wallet_id,wallet_amount


    def get_wallet_id(self,currency):
        """获取钱包ID"""
        wallet_price, wallet_id,wallet_amount = self.get_wallet_data(currency)
        return wallet_id
    def get_wallet_price(self, currency):
        """
        获取钱包汇率
        :param currency: 钱包类型
        :return:
        """
        wallet_price, wallet_id,wallet_amount = self.get_wallet_data(currency)
        return float(wallet_price)
    def get_wallet_amount(self, currency):
        """
        获取钱包余额
        :param currency: 钱包类型
        :return:
        """
        wallet_price, wallet_id,wallet_amount = self.get_wallet_data(currency)
        return wallet_amount
    def get_card_balance(self):
        """
        获取卡余额
        获取虚拟卡总余额和卡账户总余额
        :return:
        """
        # URL = self.authority + "/web/virtual-card/card-balance"
        balance = self.http_request.send_request(api_name='获取虚拟卡总余额和卡账户总余额', nested_keys=['data'])
        card_AccountBalance = balance['cardAccountBalance']  # 账户余额
        card_Balance = balance['cardBalance']  # 卡内余额
        befer_data = [card_AccountBalance, card_Balance]

        return befer_data

    # # 钱包到卡账户充值的费率
    # def get_wallet_to_card_fee(self):
    #
    #     url_data = {
    #         'feeType': 'card_account_recharge_fee'
    #     }
    #     # fee_url = self.authority + "/web/account/fees-v1?feeType=card_account_recharge_fee"
    #     fee = self.http_request.send_request(api_name='获取手续费列表', dict_data=url_data, nested_keys=['data'])
    #     per_count = fee['per_count']  # 固定
    #     prorate = fee['prorate']  # 百分比
    #     return per_count, prorate

    #消耗前后查看卡账户余额
    def get_card_balance_before_and_after(self, currency  ,send_amount,fee, type,before_data):
        """
        获取卡账户余额并在操作前后进行验证
        :param send_amount: 操作金额
        :param type: 操作类型
        :return:
        """
        # 获取操作前余额
        # card_account_balance_before, card_balance_before = self.get_card_balance()
        # print(f'操作前：卡账户余额{card_account_balance_before}，卡内余额{card_balance_before}')

        # 定义不同类型操作的预期结果
        """
               类型有：
               wallet_to_card：钱包到卡账户充值
               card_to_wallet：卡到钱包充值
               create_card：创建卡
               card_recharge：卡充值
               card_transfer_out：卡转出
               create_physical_card：创建实体卡



               """
        amount = 0.0
        #不同的金额有不同的费率
        if currency == 'USDT':
            # amount = self.get_wallet_price('USDT') * send_amount
            amount = Decimal(str(self.get_wallet_price('USDT'))) * Decimal(str(send_amount))
        if currency == 'USDC':
            # amount = self.get_wallet_price('USDC') * send_amount
            amount = Decimal(str(self.get_wallet_price('USDC'))) * Decimal(str(send_amount))
        if currency == 'USD':
            # amount = self.get_wallet_price('BUSD') * send_amount
            amount = send_amount
        print(f'{currency}金额{amount}')
        # 定义不同类型操作的预期结果
        operation_effects = {
            'wallet_to_card': {
                'account_change': float(amount) - float(fee),  # 卡账户余额增加
                'card_change': 0  # 卡内余额不变化
            },
            'card_to_wallet': {
                'account_change': -send_amount,  # 卡账户余额减少
                'card_change': 0  # 卡内余额不变化
            },
            'create_card': {
                'account_change': -float(amount) - float(fee),  # 卡账户余额增加
                'card_change': + amount  # 卡内余额增加
            },
            'create_physical_card': {
                'account_change': -float(amount) - float(fee),  # 卡账户余额增加
                'card_change': + amount  # 卡内余额增加
            },
            'card_recharge': {
                'account_change': -float(amount),  # 卡账户余额增加
                'card_change': +float(amount) -float(fee) # 卡内余额增加
            },
            'card_transfer_out': {
                'account_change':  +amount,  # 卡账户余额减少
                'card_change': - amount  # 卡内余额减少
            },

        }

        if type not in operation_effects:
            print(f'不支持的操作类型: {type}')
            return

        # 计算预期结果
        print(f'实际到账金额:{operation_effects[type]['account_change']}')
        expected_account_balance = before_data[0] + operation_effects[type]['account_change']
        expected_card_balance = before_data[1] + operation_effects[type]['card_change']
        print(f'操作后：卡账户余额{expected_account_balance}，卡内余额{expected_card_balance}')

        # 执行操作（这里需要根据实际业务逻辑补充）
        # ...

        # 获取操作后余额
        now_data = self.get_card_balance()
        print(f'实际页面显示结果：卡账户余额{now_data[0]}，卡内余额{now_data[1]}')

        # # 验证余额是否符合预期
        if (abs(now_data[0] - expected_account_balance) < 1e-6 and
                abs(now_data[1] - expected_card_balance) < 1e-6):
            print('卡账户余额和卡内余额一致')
            # 根据操作类型输出特定的成功信息
            success_messages = {
                'wallet_to_card': '钱包到卡账户充值成功',
                'card_to_wallet': '卡到钱包充值成功',
                'create_physical_card': '创建实体卡成功',
                'create_card': '创建卡成功',
                'card_recharge': '卡充值成功',
                'card_transfer_out': '卡转出成功',

            }
            if type in success_messages:
                print(success_messages[type])
        else:
            print('卡账户余额和卡内余额不一致')
            #根据操作类型输出特定的失败信息
            failure_messages = {
                'wallet_to_card': '钱包到卡账户充值失败',
                'card_to_wallet': '卡到钱包充值失败',
                'create_card': '创建虚拟卡失败',
                'card_recharge': '卡充值失败',
                'card_transfer_out': '卡转出失败',
                'create_physical_card': '创建实体卡失败'
            }
            if type in failure_messages:
                print(failure_messages[type])

    #获取钱包消耗或充值后前后的变化
    def get_wallet_to_card_balance_before_and_after(self,currency, send_amount, type, wallet_amount_before):
        """获取钱包到卡账户充值前后的余额变化"""

        """
        定义哪些情况是和钱包相关的操作：
        wallet_to_card：钱包到卡账户充值
        card_to_wallet：卡到钱包充值
        """
        amount = None
        # 不同的金额有不同的费率
        if currency == 'USDT':
            amount = (2-self.get_wallet_price('USDT')) * send_amount
        if currency == 'USDC':
            amount = (2-self.get_wallet_price('USDC')) * send_amount
        print(f'{currency}金额{amount}')
        #定义不同类型操作的预期结果
        operation_effects = {
            'wallet_to_card': {
                'wallet_change': -send_amount,  # 钱包余额减少
            },
            'card_to_wallet': {
                'wallet_change': + amount,  # 钱包余额增加
            },
        }
        if type not in operation_effects:
            print(f'不支持的操作类型: {type}')
            return
        #计算操作后余额
        wallet_balance_after = wallet_amount_before + operation_effects[type]['wallet_change']
        print(f'钱包充值后：钱包余额{wallet_balance_after}')

        now_wallet_balance = self.get_wallet_amount(currency)
        print(f'当前钱包余额：{now_wallet_balance}')
        #验证余额是否符合预期
        if abs(wallet_balance_after - now_wallet_balance) < 1e-6:
            print('钱包余额一致')
        else:
            print('钱包余额不一致')

    def get_wallet_to_card_fee_amount(self, currency, send_amount):
        """获取钱包到卡账户充值手续费"""
        url_data = {
            'feeType': 'card_account_recharge_fee'
        }
        fee_url = self.url + "/web/account/fees-v1?feeType=card_account_recharge_fee"
        #fee = self.http_request.send_request(api_name='获取手续费列表', dict_data=url_data, nested_keys=['data'])
        fee = self.http_request.gets(fee_url, nested_keys=['data'])
        per_count = fee['per_count']  # 固定
        prorate = fee['prorate']  # 百分比
        #计算手续费
        price = self.get_wallet_price(currency)
        fee_amount = price * send_amount * prorate + per_count

        print(f'钱包到卡账户充值手续费：{fee_amount}')
        return fee_amount

    def card_recharge_fee(self):
        """获取卡账户充值手续费"""
        """
                计算充值手续费
                :param send_amount: 充值金额
                :return:
                """
        url_body = {
            'feeType': 'card_recharge_fee'
        }
        data = self.http_request.send_request(api_name='获取手续费列表', dict_data=url_body,
                                              nested_keys=['data'])
        per_count = data['per_count']  # 固定
        prorate = data['prorate']  # 百分比
        return per_count, prorate
    # def get_card_create_fee(self):
    #     """获取创建手续费"""
    #
    #     url_data={
    #         'feeType' : 'card_recharge_fee'
    #     }
    #     #path = '/web/account/fees-v1?feeType=card_create_fee'
    #     # url = self.authority + path
    #     data = self.http_request.send_request(api_name='获取手续费列表',dict_data=url_data, nested_keys=['data'])
    #     per_count = data['per_count']# 固定
    #     prorate = data['prorate']#百分比
    #     return per_count, prorate

    def get_card_recharge_fee(self, send_amount):

        """
        计算充值手续费
        :param send_amount: 充值金额
        :return:
        """
        per_count, prorate = self.card_recharge_fee()
        recharge_amount = send_amount * prorate + per_count
        print(f'卡账户充值手续费：{recharge_amount}')
        return recharge_amount
    def get_open_card_fee(self):
        """获取开卡手续费
        """
        url_body = {
            'feeType': 'card_create_fee'
        }
        # url = self.authority + "/web/account/fees-v1?feeType=card_create_fee"
        open_card_fee = self.http_request.send_request(api_name='获取手续费列表', dict_data=url_body,
                                                       nested_keys=['data', 'per_count'])
        return open_card_fee
    #计算开卡手续费
    def get_card_create_fee_amount(self, send_amount):
        """
        计算开卡手续费
        :param send_amount: 开卡金额
        :return:
        """
        url_body = {
            'feeType': 'card_create_fee'
        }
        # url = self.authority + "/web/account/fees-v1?feeType=card_create_fee"
        open_card_fee = self.http_request.send_request(api_name='获取手续费列表', dict_data=url_body,
                                                       nested_keys=['data', 'per_count'])
        per_count, prorate = self.card_recharge_fee()
        open_card_fee_amount = open_card_fee + send_amount * prorate + per_count
        return open_card_fee_amount
    #获取创建实体卡的开卡费
    def get_entity_card_create_fee(self):
        """获取创建实体卡的开卡费
        获取创建实体卡的开卡费
        """
        url_body = {
            'feeType': 'card_physical_create_fee'
        }
        open_card_fee_amount = self.http_request.send_request(api_name='获取手续费列表', dict_data=url_body,
                                                       nested_keys=['data', 'per_count'])
        return open_card_fee_amount

    # 国家获取对应的快递费
    def get_express_fee(self, country):
        """获取国家对应的快递费
        获取国家对应的快递费
        """
        url = self.url + f'/web/account/get-virtual-card-logistics-fee?country={country}'
        express_fee = float(self.http_request.gets(url=url, nested_keys=['data', 'fee']))
        print(express_fee)
        return express_fee
    #计算开实体卡的开卡费
    def get_entity_card_create_fee_amount(self,send_amount,country):
        """
        计算开实体卡的开卡费
        """
        open_card_fee_amount=self.get_entity_card_create_fee()
        per_count, prorate = self.card_recharge_fee()
        express_fee = self.get_express_fee(country)
        open_card_fee_amount = open_card_fee_amount + send_amount * prorate + per_count + express_fee
        print(f'开实体卡的开卡费：{open_card_fee_amount}')
        return open_card_fee_amount
if __name__ == '__main__':
    card_wallet_fee = Balance_Calculate()
    # card_wallet_fee.get_wallet_to_card_fee_amount('USDT',10)
    # card_wallet_fee.get_express_fee('AX')
    # card_wallet_fee.get_entity_card_create_fee_amount(1,'HK')
    card_wallet_fee.get_wallet_to_card_fee_amount('USDT',10)
