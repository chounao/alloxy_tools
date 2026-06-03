from common.get_time import GetTime
from faker import Faker
import random
import requests
from web_page_operation.checkout_function import to_checkout, merchant_management
from common.simple_request import HttpRequest
from common import read_and_save_tool
import json
import os
from common import logger
logger = logger.logger

class AdminCheckout:
    def __init__(self, admin_http=None):
        self.http_request = admin_http or HttpRequest(user_type='admin')
        self.config = read_and_save_tool.ConfigTools()

        self.config_url = self.config.get_url_data()
        self.to_checkout = to_checkout.ToCheckout()
        self.merchant = merchant_management.MerchantManagement()
        self.time = GetTime()



        headers = {
            "content-type": "application/json",
            "x-gatepay-signature": "test6666666666test"
        }
        # url = self.url+'/web/checkout_page/gatepay/callback'
        self.session = requests.Session()
        self.session.headers.update(headers)

        self.url = 'https://ax-api.pertest.tech/web/checkout/gatepay/callback'

    def get_checkout_order_info(self, status, date):
        """
        获取充值订单信息
        :param status: 订单状态
        :param date: 日期
        :return: 充值订单信息
        """
        all_transaction_data = []
        page = 1

        while True:
            start_time, end_time =self.time.get_time_range(date)

            url = self.config_url + f'/admin/checkout/order?page={page}&take=100&order_type=withdraw&status={status}&created_at[]={start_time}&created_at[]={end_time}'
            transaction_data = self.http_request.gets(url, nested_keys=['data', 'list'])

            if not transaction_data or len(transaction_data) == 0:  # 检查交易数据是否为空或长度为0，如果是则跳出循环
                break
            all_transaction_data.extend(transaction_data)
            # 检查是否有更多数据
            total_count = self.http_request.gets(url, nested_keys=['data', 'total'])
            if total_count and len(all_transaction_data) >= total_count:
                break

            page += 1

        logger.info(f"总共获取到{len(all_transaction_data)}条记录")
        # print(all_transaction_data)

        with open(f'checkout_{date}.json', 'w', encoding='utf-8') as f:
            json.dump(all_transaction_data, f, ensure_ascii=False, indent=4)
        # 返回保存的路径
        if not hasattr(self, 'save_path'):
            self.save_path = os.getcwd()
        save_path = os.path.join(self.save_path, f'checkout_{date}.json')
        print(save_path)
        return save_path, all_transaction_data
    def Recorded(self,address_data,name,currency,amount):
        """
        三方回掉
        :return:
        """
        bizId = random.randint(10000000000000000, 99999999999999999)

        for key,value in address_data.items():
            if key == currency:
                address = value['address']
                chain = value['chain']

                data = {
                        "bizType": "PAY_FIXED_ADDRESS",
                        "bizId": str(bizId), #与下方的transactionId保持一致，随机number
                        "bizStatus": "PAY_SUCCESS",
                        "data": {
                                    "address": address, # 商户的链 - 币种的地址
                        "amount": amount, # 充值数量
                        "chain": chain, # 链
                        "channel_id": name, # 商户名
                        "createTime": 1757036760688,
                        "currency": currency, # 币种
                        "orderAmount": amount,
                        "transactionId":str(bizId),
                        "transactionTime": 1757036850408,
                        "txHash": "0x303e5941409a40f37a62e6068e76668d6c2f49e86ccc825e458e322058c5d084"
                    }
                    }
                print(data)
                data = json.dumps(data)
                response = self.session.post(self.url,data)
                # return response.status_code

                print(response.status_code)


    def up_status(self,id_no,status):
        """
        更新订单状态 进行审核
        :param id_no: 订单id
        :param status: 拒绝/通过
        :return: 订单状态更新结果withdraw_completed/withdraw_rejected
        """

        if status == '拒绝':
            set_status = 'withdraw_rejected'
        else:
            set_status = 'withdraw_completed'

        url = self.config_url + '/admin/checkout_page/order/withdraw/approve'
        data ={
            "order_id":id_no,
            'approve_remark':'123',
            "status":set_status,

        }
        self.http_request.post(url, data)

    #创建商户
    def create_merchant(self):
        """
        创建子商户
        :return:
        """
        # 创建子商户并操作三方回调
        """
        固定内容
        """
        # address_data = {'USDT': {'address':'THnymPLodBJwP4THCogAoLHMgpMcRNeezb','chain': 'TRX'},
        #         'USDC': {'address':'0xC4069Aa887B43AFd89B585Ed0e6163585fca8f59', 'chain':'ETH'},
        #         }
        # name = 'Madeline'
        # self.Recorded(address_data,name,'USDT',0.5)
        # self.Recorded(address_data,name,'USDC',5.3)

        """
        传参
        """
        fake = Faker('en_US')
        name = fake.first_name()
        address_data = self.merchant .get_merchant_address_data(name=name)
        if name:
            self.Recorded(address_data, name, 'USDT', 32.5)
            self.Recorded(address_data, name, 'USDC', 12.8)

    #提现的所有流程
    def withdraw_all(self,currency,amount,memo):
        """
        提现的所有流程
        :param currency: 币种
        :param amount: 金额
        :param memo: 备注
        :return:
        """
        #第一步创建订单

        self.to_checkout.create_order(currency, amount, memo)
        id_no = self.to_checkout.get_order_id(memo)
        return id_no

if __name__ == '__main__':

    checkout = AdminCheckout ()
    # currency = 'USDT'
    # amount = "0.01"
    # memo = 'zhou.test'
    # #创建订单
    # id_no = checkout.withdraw_all(currency,amount,memo)
    #
    #
    # # 创建子商户并调用三方接口回掉
    # checkout.create_merchant()
    #
    #
    #
    # # 订单状态更新
    #
    # checkout.up_status(id_no,"拒绝")

    checkout.get_checkout_order_info('withdraw_completed','202510')
