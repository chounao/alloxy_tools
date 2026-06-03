from web_page_operation.card_function.card_managment import card_wallet_fee
from common.simple_request import HttpRequest
from common import read_and_save_tool
import time



""""

创建实体卡的流程 并包括：获取激活码，激活，设置pin流程

"""
class CardPhysicalOperation():
    def __init__(self,card_id = None,user_http=None):
        self.user_http = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
        self.url = self.config.get_url_data()
        self.card_wallet_balance = card_wallet_fee.Balance_Calculate(self.user_http)
        self.card_id = card_id

    def get_cardBin(self):
        """获取所有卡BIN：ID和名字
        获取所有虚拟卡通道
        """
        # url = self.authority + '/web/virtual-card/all-channels'
        data = self.user_http.send_request(api_name='获取所有虚拟卡通道', nested_keys=['data'])
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
        create_card_people_id = self.user_http.send_request(api_name='根据用户获取所有虚拟卡持有人',
              #                                                 jsonpath_expr=f'$.data.list[?(@.rbac_department_name=="测试部门")].id')
                                                               nested_keys=['data',0,'id'])
        print(create_card_people_id)
        return create_card_people_id

    # 获取默认地址
    def get_default_address(self):
        """获取默认地址
        获取默认地址
        """
        url = self.url + f'/web/virtual-card/card-shipping-address?address_source=default'
        data = self.user_http.gets(url=url, nested_keys=['data'])
        print(data)
        return data

    # 获取城市信息
    def get_country_city_info(self):
        """获取国家对应的城市信息
        获取国家对应的城市信息
        """
        url = self.url + '/web/country/country-info'
        data = {
            'business_type': 'reap_physical_cards_shipment',
            'physical_card': True
        }
        data = self.user_http.send_request(api_name='获取国家信息', dict_data=data, nested_keys=['data'])
        print(data)
        return data

    # 创建实体卡
    def create_entity_card(self, send_amount):
        self.before_data = self.card_wallet_balance.get_card_balance()
        print(f'操作前：卡账户余额{self.before_data[0]}，卡内余额{self.before_data[1]}')
        peron_bin_id, peron_bin_name, firm_bin_id, firm_bin_name = self.get_cardBin()
        create_card_people_id = self.get_all_holders()
        consignee = self.get_default_address()
        # path = '/web/virtual-card/create-card'

        body = {
            "cardType": "Physical",
            "bin_id": peron_bin_id,
            "virtualCardHolderId": 'abd5564f-c9c7-4610-9463-68594ad06282',
            "label": "test_data",
            "available": send_amount,
            "limit": [
                {
                    "transactionLimit": 1000000
                }
            ],
            "receiveEmail": True,
            "check_method": "email",
            "access_code": "123456",
            "cardShipInput": {
                "recipientFirstName": consignee['recipient_first_name'],
                "recipientLastName": consignee['recipient_last_name'],
                "recipientDialCode": consignee['recipient_phone_dial_code'],
                "recipientPhoneNumber": consignee['recipient_phone'],
                "recipientEmail": consignee['recipient_email'],
                "shippingAddress": {
                    "country": consignee['country_code'],
                    "zone": consignee['state_province'],
                    "city": consignee['city'],
                    "line1": consignee['line1'],
                    "postalCode": consignee['postal_code']
                }
            },
            "isDefaultAddress": True
        }
        data = self.user_http.send_request(api_name='创建虚拟卡', data=body, nested_keys=['data'])
        self.card_id = data['id']
        self.bank_card_id = data['bank_card_id']
        print(f"Created card ID: {self.card_id}")
        if self.card_id:

            # 获取手续费
            fee_amount = self.card_wallet_balance.get_entity_card_create_fee_amount(send_amount,consignee['country_code'])
            # 验证余额
            self.card_wallet_balance.get_card_balance_before_and_after('USD',send_amount, fee_amount, 'create_physical_card',self.before_data)

        return self.card_id, self.bank_card_id
    # 获取实体卡激活码
    def get_entity_card_activation_code(self, bank_card_id):
        """获取实体卡激活码
        获取实体卡激活码
        """
        url = self.url + f'/web/virtual-card/get-activate-code/{bank_card_id}'
        code = self.user_http.gets(url=url, nested_keys=['data', 'activationCode'])
        print(code)
        return code

    # 激活实体卡
    def activate_entity_card(self, bank_card_id, activation_code):
        """激活实体卡
        激活实体卡
        """
        url = self.url + '/web/virtual-card/activate-physical-card'
        body = {
            "code": activation_code,
            "bank_card_id": bank_card_id
        }
        response = self.user_http.posts(url=url, data=body)
        print(response)
        # return response.status_code

    # 设置pin
    def set_pin(self, bank_card_id, pin):
        """设置pin
        设置实体卡pin
        """
        url = self.url + '/web/virtual-card/update-physical-card-pin'
        body = {
            "cardId": bank_card_id,
            "pin": pin
        }
        response = self.user_http.posts(url=url, data=body)
        print( response)


if __name__ == '__main__':
    card_physical_operation = CardPhysicalOperation()
    # card_physical_operation.get_all_holders()
    # card_id, bank_card_id = card_physical_operation.create_entity_card(1)
    # card_id ='76ed6c87-791f-4250-849a-ce765dc09b5b'
    bank_card_id = '7016e98a-dc4e-46a1-b615-39b568a2115b'
    time.sleep(1)
    activation_code = card_physical_operation.get_entity_card_activation_code(bank_card_id)
    # time.sleep(1)
    # card_physical_operation.activate_entity_card(bank_card_id, activation_code)
    # time.sleep(1)
    # card_physical_operation.set_pin(bank_card_id, '028988')