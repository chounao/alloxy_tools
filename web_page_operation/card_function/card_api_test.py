# -*- coding: utf-8 -*-
# @Time    : 2020/12/23 10:05
import base64
import time
import json
import requests
from dotenv import load_dotenv
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from common.simple_request import HttpRequest
from common import read_and_save_tool
from common.execute import get_config_section
import random


class CardApi:
    def __init__(self, http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()

        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.config_section = get_config_section()
        # self.base_url = self.config.get_url_data()
        self.base_url = 'http://192.168.0.45:5555'
        # 模拟交易接口
        self.card_base_url = f'{self.base_url}/web/virtual-card/simulate-transaction'

    # ==================== 共享卡组管理 ====================
    def create_card_group(self, name, label, amount):
        """创建卡组"""
        url = f"{self.base_url}/api/virtual-card/create-card-group"
        data = {
            "name": name,
            "label": label,
            "amount": amount
        }
        resp = self.http_request.requests('post',url,data)
        return resp.json()

    def get_card_group_list(self,name):
        """卡组列表"""

        url = f"{self.base_url}/api/virtual-card/card-group-list?page=1&take=10"
        resp = self.http_request.requests('get', url,jsonpath_expr = f'$.data[?(@.name == "{name}")].id')
        return resp

    def query_card_group_list(self,
                              name=None,
                              last4=None,
                              binID=None,
                              bin=None,
                              virtualCardHolderId=None,
                              virtualCardHolderName=None,
                              status=None,
                              label=None,
                              email=None,
                              type=None):
        """查询所有卡组"""
        optional_params = {
            "name": name,
            "last4": last4,
            "bindID": binID,
            "bin": bin,
            "virtualCardHolderId": virtualCardHolderId,
            "virtualCardHolderName": virtualCardHolderName,
            "status": status,
            "label": label,
            "email": email,
            "type": type,
        }
        params = {"page": 1, "take": 10}
        for key, value in optional_params.items():
            if value:
                params[key] = value
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.base_url}/api/virtual-card/card-group-list?{query_string}"
        resp = self.http_request.requests('get', url)
        return resp.json()

    def get_card_group_card_list(self):
        """查询卡组下的所有卡"""

        url = f"{self.base_url}/api/virtual-card/card-group-card-list"
        resp = self.http_request.requests('get', url)
        return resp.json()

    def get_card_group_balance(self, group_id):
        """查询卡组余额"""

        url = f"{self.base_url}/api/virtual-card/card-group-balance/{group_id}"
        resp = self.http_request.requests('get', url)
        return resp.json()

    def card_account_to_group(self, group_id, amount, memo="", verify=False):
        """卡账户充值到卡组"""

        url = f"{self.base_url}/api/virtual-card/card-account-to-card-group"
        data = {
            "card_share_group_id": group_id,
            "amount": amount,
            "memo": memo,
            "verify": verify
        }
        resp = self.http_request.requests('post', url, data)
        return resp.json()

    def card_group_to_account(self, group_id, amount, memo=""):
        """卡组转出到卡账户"""

        url = f"{self.base_url}/api/virtual-card/card-group-to-card-account"
        data = {
            "card_share_group_id": group_id,
            "amount": amount,
            "memo": memo
        }
        resp = self.http_request.requests('post', url, data)
        return resp.json()
# ==================== 5.2 共享卡管理 ====================
    def create_card_api(self, group_id,holder_id, available=10):
        """API方式创建共享卡（个人模板）"""
        url = f"{self.base_url}/api/virtual-card/create-card"
        body = {
              "bin": "54502000",
              "virtualCardHolderId": holder_id,
              "cardType": "Virtual",
              "cardCategory": "share",
              "customerType": "CONSUMER",
              "entityType": "EMPLOYEE",
              "preferredCardName": "ZhangSan",
              "available": available,
              "label": "商务卡",
              "receiveEmail": True,
              "limit": [
                {
                  "transactionLimit": 1300,
                  "dailyLimit": 1500,
                  "weeklyLimit": 1700,
                  "monthlyLimit": 1800,
                  "yearlyLimit": 2000,
                  "allTimeLimit": 2100
                }
              ],
              "card_share_group_id": group_id,
              "tradable_amount": 0,
              "fingerprintId": "",
              "verify": False,
              "check_method": "email",
              "access_code": "123456"
            }

        resp = self.http_request.requests('post',url, body)
        return resp.json()

    def get_card_list(self):
        """获取卡列表"""
        url = f"{self.base_url}/api/virtual-card/get-card-list?page=1&take=10&category=share"
        resp = self.http_request.requests('get',url,jsonpath_expr = f'$.data.list[2].id')
        return resp
    def query_card_list(self,
                          last4=None,
                          binID=None,
                          bin=None,
                          virtualCardHolderId=None,
                          virtualCardHolderName=None,
                          status=None,
                          label=None,
                          email=None,
                          type=None,
                          category = None):
        """查询所有卡"""
        optional_params = {
            "last4": last4,
            "bindID": binID,
            "bin": bin,
            "virtualCardHolderId": virtualCardHolderId,
            "virtualCardHolderName": virtualCardHolderName,
            "status": status,
            "label": label,
            "email": email,
            "type": type,
            "category": category
        }
        params = {"page": 1, "take": 10}
        for key, value in optional_params.items():
            if value:
                params[key] = value
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.base_url}/api/virtual-card/get-card-list?{query_string}"
        resp = self.http_request.requests('get', url)
        return resp.json()

    def get_card_detail(self, card_id):
        """获取卡详情"""
        url = f"{self.base_url}/api/virtual-card/card/{card_id}"
        resp = self.http_request.requests('get',url)
        return resp

    def update_card(self, card_id):
        """更新卡信息"""
        url = f"{self.base_url}/api/virtual-card/update-card"
        data = {
              "id": card_id,
              "limit": [{ "transactionLimit": 1000 }, { "dailyLimit": 5000 }, { "monthlyLimit": 50000 }],
              "receiveEmail": True
            }
        resp = self.http_request.requests('put',url, data)
        return resp


    def update_tradable_amount(self, card_id, amount):
        """修改卡可交易额度"""
        url = f"{self.base_url}/api/virtual-card/update-tradable-amount"
        data = {
            "card_id": card_id,
            "amount": amount,
            "verify": True,
            'check_method': 'email',
            "access_code": "123456"
        }
        resp = self.http_request.requests('post',url, data)
        return resp.json()

    def freeze_card(self, card_id, reason="测试冻结"):
        """冻结卡"""
        url = f"{self.base_url}/api/virtual-card/freeze-card/{card_id}"
        data = {"reason": reason,"status":True}
        resp = self.http_request.requests('put',url, data=data)
        return resp.json()

    def unblock_card(self, card_id, reason="风控解除"):
        """解冻卡"""
        url = f"{self.base_url}/api/virtual-card/unblock-card/{card_id}"
        data = {"reason": reason}
        resp = self.http_request.requests('put',url, data=data)
        return resp.json()

    def delete_card(self, card_id, reason="测试注销"):
        """注销卡"""
        url = f"{self.base_url}/api/virtual-card/card/{card_id}"
        data = {"reason": reason}
        resp = self.http_request.requests('delete',url, data=data)
        return resp.json()

    # ==================== 5.3 持卡人管理 ====================
    def create_card_holder(self):
        """创建持卡人"""
        url = f"{self.base_url}/api/virtual-card/create-card-holders"
        data = {
            "first_name": "zhou",
            "last_name": "chaojie",
            "sex": "male",
            "nickname": "zhouchaojie",
            "email": f"holder{int(time.time())}@example.com",
            "phone": f"18{random.randint(0, 99999999)}",
            "area_code": "+852",
            "country": "CN",
            "province": "Guangdong",
            "city": "Shenzhen",
            "address": "No100ScienceParkNanShaDistrict",
            "address2": "",
            "postal_code": "518000",
            "iso_code": "CN",
            "birthday": "1990-01-01",
            "id_document_type": "Passport",
            "id_document_number": f"E{int(time.time())}",
            "portrait": "https://sandbox-hangzhou-web.s3.ap-southeast-2.amazonaws.com/929ff175-e26b-43ad-ba02-467756bff867/2026-05-25/202605251526322513545.jpg",
            "portrait_key": [
                            {
                                "file_key": "fme1iIxMwbd728",
                                "product_code": "photon-us"
                            },
                            {
                                "file_key": "Ifkb9dicjhU3pc",
                                "product_code": "photon-hk"
                            },
                            {
                                "file_key": "/INPUT/CI2038501586057805826/24e5490a-e481-409f-8f11-1798e6c1b7c7/ef355303-6885-475d-b4ab-f2f4f90f1b9f.jpg",
                                "product_code": "sunrate"
                            }
                        ],
            "reverseSide": "https://sandbox-hangzhou-web.s3.ap-southeast-2.amazonaws.com/929ff175-e26b-43ad-ba02-467756bff867/2026-05-25/202605251526331323628.jpg",
            "reverseSide_key": [
                            {
                                "file_key": "fmVVe1ixwxua68",
                                "product_code": "photon-us"
                            },
                            {
                                "file_key": "fkb9cBvjlcSglc",
                                "product_code": "photon-hk"
                            },
                            {
                                "file_key": "/INPUT/CI2038501586057805826/24e5490a-e481-409f-8f11-1798e6c1b7c7/3fcdc93a-0683-4cba-afbc-3a1a55f7dc73.jpg",
                                "product_code": "sunrate"
                            }
                        ],
                                "status": "active",
            "is_external": 0,
            "label": "VIP客户",
            "cardShipInput": "",
            "isSameAsPersonalAddress": True
        }
        resp = self.http_request.requests('post',url,data)
        return resp.json()

    def get_holder_list(self):
        """获取持卡人列表"""
        url = f"{self.base_url}/api/virtual-card/get-holders?page=1&take=100"
        holder_id = self.http_request.requests('get',url,jsonpath_expr=f'$.data.list[?(@.last_name == "chaojie")].id')
        return holder_id

    def query_holder_list(self,
                          nickname=None,
                          email=None,
                          rbac_department_id = None,
                          label=None,
                          status=None,
                          is_external=None):
        """查询持卡人列表"""
        """查询所有卡"""
        optional_params = {
            "nickname": nickname,
            "email": email,
            "rbac_department_id": rbac_department_id,
            "label": label,
            "status": status,
            "is_external": is_external
        }
        params = {"page": 1, "take": 10}
        for key, value in optional_params.items():
            if value:
                params[key] = value
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.base_url}/api/virtual-card/get-holders?{query_string}"
        resp = self.http_request.requests('get',url)
        return resp.json()
    def get_all_holder_list(self):
        """获取所有持卡人列表"""
        url = f"{self.base_url}/api/virtual-card/get-all-holders"
        resp = self.http_request.requests('get',url)
        return resp.json()
    #获取持卡人详情
    def get_holder_detail(self, holder_id):
        """获取持卡人详情"""
        url = f"{self.base_url}/api/virtual-card/holders/{holder_id}"
        resp = self.http_request.requests('get',url)
        return resp.json()
    # ==================== 5.4 余额查询 ====================
    def get_one_card_balance(self, card_id):
        """单卡余额"""
        url = f"{self.base_url}/api/virtual-card/one-card-balance/{card_id}"
        resp = self.http_request.requests('get',url)
        return resp.json()

    def get_total_balance(self):
        """账户总余额"""
        url = f"{self.base_url}/api/virtual-card/card-balance"
        resp = self.http_request.requests('get',url)
        return resp.json()

    # ==================== 5.5 交易查询 ====================
    def get_transaction_list(self):
        """交易列表"""
        url = f"{self.base_url}/api/virtual-card/transaction-list?page=1&take=100"

        resp = self.http_request.requests('get',url)
        return resp.json()

    def query_transaction_list(self,
                               id_no=None,
                               virtual_card_id=None,
                               transaction_type=None,
                               status=None,
                               create_at=None,
                               remarks=None,
                               vch_nickname=None):
        """查询交易列表"""
        from urllib.parse import urlencode
        optional_params = {
            "id_no": id_no,
            "virtual_card_id": virtual_card_id,
            "transaction_type": transaction_type,
            "status": status,
            "create_at": create_at,
            "remarks": remarks,
            "vch_nickname": vch_nickname
        }
        filtered_params = {k: v for k, v in optional_params.items() if v is not None}
        query_string = urlencode(filtered_params)
        url = f"{self.base_url}/api/virtual-card/transaction-list"
        if query_string:
            url = f"{url}?{query_string}"
        resp = self.http_request.requests('get', url)
        return resp.json()

    # ==================== 5.6 Webhook 配置 ====================
    def set_webhook(self, event, url, status="active"):
        """配置Webhook"""
        api_url = f"{self.base_url}/web/webhook-address"
        data = {
            "webhook_event": event,
            "webhook_url": url,
            "status": status
        }
        resp = self.http_request.requests('post',api_url, data)
        return resp.json()

    # ==================== Webhook 验签工具 ====================
    @staticmethod
    def verify_webhook(headers, body, public_key_pem):
        """
        验签Webhook请求
        :param headers: 请求头字典
        :param body: 请求体字典
        :param public_key_pem: 平台公钥字符串
        :return: True/False
        """
        try:
            signature = base64.b64decode(headers['X-Signature'])
            timestamp = headers['X-Timestamp']

            # 防重放：5分钟内有效
            if abs(time.time() - int(timestamp)) > 300:
                print("⚠️ 时间戳过期")
                return False

            # 构造签名原文
            payload = f"{timestamp}.{json.dumps(body, separators=(',', ':'))}".encode()

            # 加载公钥
            public_key = serialization.load_pem_public_key(public_key_pem.encode())

            # 验签
            public_key.verify(
                signature,
                payload,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            print(f"❌ 验签失败：{str(e)}")
            return False


# ==================== 测试主流程 ====================
if __name__ == "__main__":
    # 初始化API客户端
    group_name = "test_api"
    api = CardApi()


    # 2. 创建卡组
    # print("\n=== 创建卡组 ===")
    # group = api.create_card_group(group_name, "测试标签",100 )
    # print(json.dumps(group, indent=2, ensure_ascii=False))

    # 3. 查询卡组列表
    # print("\n=== 卡组列表 ===")
    # group_id = api.get_card_group_list(group_name)
    # print(group_id)
    # 3.1 查询卡组下的所有卡组
    # print("\n=== 卡组下的所有卡组 ===")
    # card_group_list = api.query_card_group_list(
    #                                             # name = 'test',
    #                                             # last4 = '0439',
    #                                             # binID="194a4600-9732-4d14-bbb6-9df0b5b05a45",
    #                                             # bin = '54502000',
    #                                             # virtualCardHolderId="c7da361c-6875-4915-b2e4-da18cf46ab02",
    #                                             # virtualCardHolderName='CHAOJIE ZHOU',
    #                                             label='测试标签',
    #                                             # status='active',
    #                                             # email= 'holder1779766280@example.com',
    #                                             # type='Physical'
    #                                             )
    # print(card_group_list)
    # # 3.2 查询卡组下的所有卡
    # print("\n=== 卡组下的所有卡 ===")
    # card_list = api.get_card_group_card_list()
    # print(json.dumps(card_list, indent=2, ensure_ascii=False))

    # # 4. 查询卡组余额
    # print("\n=== 卡组余额 ===")
    # balance = api.get_card_group_balance(group_id)
    # print(json.dumps(balance, indent=2, ensure_ascii=False))
    #
    # # 5. 卡组充值
    # print("\n=== 卡组充值 ===")
    # recharge = api.card_account_to_group(group_id, 100, "测试充值")
    # print(json.dumps(recharge, indent=2, ensure_ascii=False))
    # # # 5.1 查询卡组余额·
    # print("\n=== 卡组余额 ===")
    # balance = api.get_card_group_balance(group_id)
    # print(json.dumps(balance, indent=2, ensure_ascii=False))
    # # 5.2 卡组转出到卡账户
    # print("\n=== 卡组转出到卡账户 ===")
    # api.card_group_to_account(group_id, 100, "测试转出")




    # 13. 创建持卡人
    # print("\n=== 创建持卡人 ===")
    # holder = api.create_card_holder()
    # print(json.dumps(holder, indent=2, ensure_ascii=False))
    #
    # # 14. 持卡人列表
    # print("\n=== 持卡人列表 ===")
    # holder_id = api.get_holder_list()
    # 14.1 查询持卡人
    # print("\n=== 持卡人列表 ===")
    # holder= api.query_holder_list(
    #                               # nickname='CHAOJIE ZHOU',
    #                               # email='holder1779785311@example.com',
    #                               # rbac_department_id='6e4a207b-dbe7-4cae-bfb2-04ac8cd64867',
    #                               # label='VIP客户',
    #                               status='ACTIVE',
    #                               is_external=1
    #                                 )
    # print(holder)

    # 14.1 获取所有持卡人列表
    # print("\n=== 获取所有持卡人列表 ===")
    # holder_list = api.get_all_holder_list()
    # print(holder_list)
    # 15. 持卡人详情
    # print("\n=== 持卡人详情 ===")
    # holder_detail = api.get_holder_detail(holder_id)
    # print(json.dumps(holder_detail, indent=2, ensure_ascii=False))
    # #
    # # # 6. 创建共享卡
    # print("\n=== 创建共享卡 ===")
    # card = api.create_card_api(group_id, holder_id, 0)
    # print(json.dumps(card, indent=2, ensure_ascii=False))
    # 7. 卡列表
    print("\n=== 卡列表 ===")
    card_id = api.get_card_list()
    print(card_id)
    # 7.1 查询卡列表
    # print("\n=== 查询卡列表 ===")
    # card_list = api.query_card_list(
    #     # last4 = '0439',
    #     # binID="194a4600-9732-4d14-bbb6-9df0b5b05a45",
    #     # bin = '54502000',
    #     # virtualCardHolderId="c7da361c-6875-4915-b2e4-da18cf46ab02",
    #     # virtualCardHolderName='CHAOJIE ZHOU',
    #     # label='商务卡',
    #     # status='ACTIVE',
    #     # email= 'holder1779766280@example.com',
    #     # type='Virtual',
    #     # category='share'
    # )

    if card_id:
    #
    #
    #     # 8. 卡详情
    #     print("\n=== 卡详情 ===")
    #     card_detail = api.get_card_detail(card_id)
    #
    #     # 8.1更新卡信息
    #     print("\n=== 修改卡信息 ===")
    #     update_card = api.update_card(card_id)

        # # 9. 修改可交易额度
        # print("\n=== 修改卡额度 ===")
        # update_amount = api.update_tradable_amount(card_id, 10)
        # print(json.dumps(update_amount, indent=2, ensure_ascii=False))
        #
        #10. 冻结卡
        print("\n=== 冻结卡 ===")
        freeze = api.freeze_card(card_id)
        print(json.dumps(freeze, indent=2, ensure_ascii=False))

        # 11. 解冻卡
        print("\n=== 解冻卡 ===")
        time.sleep(15)
        unblock = api.unblock_card(card_id)
        print(json.dumps(unblock, indent=2, ensure_ascii=False))
        #
        # # # 12. 单卡余额
        # print("\n=== 单卡余额 ===")
        # card_balance = api.get_one_card_balance(card_id)
        # print(json.dumps(card_balance, indent=2, ensure_ascii=False))

        # 13 注销卡
        # print("\n=== 注销卡 ===")
        # cancel = api.delete_card(card_id)
        # print(json.dumps(cancel, indent=2, ensure_ascii=False))







    # 16. 总余额
    # print("\n=== 账户总余额 ===")
    # total_balance = api.get_total_balance()
    # print(json.dumps(total_balance, indent=2, ensure_ascii=False))

    # 17. 交易记录
    # print("\n=== 交易列表 ===")
    # tx_list = api.get_transaction_list()
    # print(json.dumps(tx_list, indent=2, ensure_ascii=False))
    # 17.1 查询交易记录
    # print("\n=== 查询交易列表 ===")
    # tx_list = api.query_transaction_list(
    #                     # id_no='2059947675224805378',
    #                     # virtual_card_id='7d2283ef-4ac9-46a4-bf06-cbf3a01b94d4',
    #                     # transaction_type= 'card_create_virtual',
    #                     # status='completed',
    #                     # create_at= '2026-05-25',
    #                     # remarks='测试转出',
    #                     vch_nickname= 'CHAOJIE ZHOU'
    # )
    # print(tx_list)

    # 18. 配置Webhook
    # print("\n=== 配置Webhook ===")
    # webhook = api.set_webhook("card.status.create", "shturl.cc/o7TjzP5dzl8k0DF3BXSuG")
    # print(json.dumps(webhook, indent=2, ensure_ascii=False))