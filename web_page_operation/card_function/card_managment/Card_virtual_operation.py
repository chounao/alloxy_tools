from web_page_operation.card_function.card_managment import card_wallet_fee
from common.simple_request import HttpRequest
from common import read_and_save_tool
""""

创建虚拟卡的流程 并包括：转入转出冻结解冻删除流程

"""
class CardOperation():
    def __init__(self,http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()
        self.config = read_and_save_tool.ConfigTools()
        self.url = self.config.get_url_data()
        self.card_wallet_balance = card_wallet_fee.Balance_Calculate(self.http_request)
        self.before_data  = self.card_wallet_balance.get_card_balance()



    #创建虚拟卡

    def get_cardBin(self):
        """获取所有卡BIN：ID和名字
        获取所有虚拟卡通道
        """
        # url = self.authority + '/web/virtual-card/all-channels'
        data = self.http_request.send_request(api_name='获取所有虚拟卡通道', nested_keys=['data'])
        peron_bin_id = data[0]['id']
        firm_bin_id = data[1]['id']
        peron_bin_name = data[0]['bin']
        firm_bin_name = data[1]['bin']
        # print(peron_bin_id, peron_bin_name)
        # print(firm_bin_id, firm_bin_name)
        return peron_bin_id, peron_bin_name, firm_bin_id, firm_bin_name

    def get_all_holders(self):
        """获取所有持卡人
        根据用户获取所有虚拟卡持有人
        """
        # url = self.authority + '/web/virtual-card/get-all-holders'
        create_card_people_id = self.http_request.send_request(api_name='根据用户获取所有虚拟卡持有人',
                                                               # jsonpath_expr=f'$.data.list[?(@.rbac_department_name=="测试部门")].id')
                                                               nested_keys=['data', 0, 'id'])
        # print(create_card_people_id)
        return create_card_people_id
    def create_card(self, send_amount):
        """创建卡
        创建虚拟卡
        """
        self.before_data = self.card_wallet_balance.get_card_balance()
        print(f'操作前：卡账户余额{self.before_data[0]}，卡内余额{self.before_data[1]}')
        peron_bin_id, peron_bin_name, firm_bin_id, firm_bin_name= self.get_cardBin()
        create_card_people_id = self.get_all_holders()
        # path = '/web/virtual-card/create-card'


        body = {
                "cardType": "Virtual",
                "bin_id": peron_bin_id,
                "virtualCardHolderId": 'abd5564f-c9c7-4610-9463-68594ad06282',
                "label": "test_data",
                "available": send_amount,
                "limit": [
                    {
                        "transactionLimit": 10
                    }
                ],
                "receiveEmail": True,
                "check_method": "email",
                "access_code": "123456"
            }

        # 提取卡片ID
        # card_id = self.http_request.post(url, data, ['data', 'id'])
        data = self.http_request.send_request(api_name='创建虚拟卡', data=body, nested_keys=['data'])
        self.card_id = data['id']
        self.bank_card_id = data['bank_card_id']
        print(f"Created card ID: {self.card_id}")
        if self.card_id:
            print('创建虚拟卡成功')
            # 获取手续费
            fee_amount = self.card_wallet_balance.get_card_create_fee_amount(send_amount)
            # 验证余额
            self.card_wallet_balance.get_card_balance_before_and_after('USD',send_amount, fee_amount, 'create_card',self.before_data)
        return self.card_id, self.bank_card_id


        #卡充值
    def card_recharge(self,card_id,send_amount):
        """
        卡充值
        从卡账户充值到卡
        :param send_amount: 转账金额
        :return:
        """

        print(f'操作前：卡账户余额{self.before_data[0]}，卡内余额{self.before_data[1]}')

        body = {"card_id":card_id,"amount":send_amount,"check_method":"email","access_code":"123456"}

        response = self.http_request.send_request(api_name='卡账户充值到卡')
        if response.status_code == 201:
            print('充值成功')
            # 获取手续费
            fee_amount = self.card_wallet_balance.get_card_recharge_fee(send_amount)
            # 验证余额
            self.card_wallet_balance.get_card_balance_before_and_after('USD',send_amount, fee_amount, 'card_recharge',self.before_data)
        else:
            print('充值失败')



        #卡转出

    def card_transfer_out(self,card_id,send_amount):
        """
        卡转出
        从卡转出到卡账户
        :param send_amount: 转账金额
        :return:
        """
        print(f'操作前：卡账户余额{self.before_data[0]}，卡内余额{self.before_data[1]}')
        body = {"card_id":card_id,"amount":send_amount,"memo":"1"}
        response = self.http_request.send_request(api_name='卡到卡账户', data=body)
        if response.status_code == 201:
            print('转出成功')
            # 获取手续费
            # 没有手续费
            # 验证余额
            self.card_wallet_balance.get_card_balance_before_and_after('USD',send_amount, 0, 'card_transfer_out',self.before_data)
        else:
            print('转出失败')


    #卡详情
    def get_card_detail(self,card_id):
        """获取卡详情
        获取虚拟卡详情
        """

        response = self.http_request.send_request(api_name='获取虚拟卡详情', replace_data={'id': card_id})
        if response:
            print('获取卡详情成功')
            print(response.json())
        else:
            print('获取卡详情失败')



    #冻结
    def freeze_card(self,bank_card_id):
        """冻结卡
        冻结虚拟卡
        """

        response = self.http_request.send_request(api_name='冻结卡', replace_data={'id':bank_card_id})
        if response:
            print('冻结卡成功')
        else:
            print('冻结卡失败')


    #解冻
    def unfreeze_card(self,bank_card_id):
        """解冻卡
        解冻虚拟卡
        """


        response = self.http_request.send_request(api_name='解冻卡', replace_data={'id': bank_card_id})
        if response:
            print('解冻卡成功')
        else:
            print('解冻卡失败')


    #删除
    def delete_card(self,card_id):
        """删除卡
        删除虚拟卡
        """

        response = self.http_request.send_request(api_name='删除卡', replace_data={'id': card_id})
        if response:
            print('删除卡成功')
        else:
            print('删除卡失败')


    #卡交易明细
    def get_card_transaction_detail(self,card_id):
        """获取卡交易明细
        获取虚拟卡交易明细
        """


        data = {
            "page": 1,
            "take": 20,
            "virtual_card_id": card_id,
            "transaction_sub_type": "card",
        }
        response = self.http_request.send_request(api_name='获取交易列表', dict_data=data)
        if response:
            print('获取卡交易明细成功')
            print(response.json())
        else:
            print('获取卡交易明细失败')



if __name__ == '__main__':
    bank_card_id = 'c9a7c326-a173-4915-8d8e-ea76e650b92c'
    card_id = '1a8f6501-90e3-42a2-bc32-ebca0599ad02'
    card_transaction = CardOperation ()
    # card_transaction.card_recharge(card_id,1)
    # card_transaction.get_entity_card_activation_code(bank_card_id)
    # card_transaction.get_default_address()
    # card_transaction.get_express_fee('US')
    # card_transaction.get_country_city_info()
    # card_transaction.freeze_card(bank_card_id)
    # card_transaction.unfreeze_card(bank_card_id)
    card_transaction.create_card(1)
