from web_page_operation.card_function.card_managment import card_wallet_fee
from common.simple_request import HttpRequest
from common import read_and_save_tool
import time
import random
from typing import Optional, Union, List
"""
创建卡组 卡等流程

"""

class CardGroupOperation:
    # 业务常量抽离，方便修改维护
    DEFAULT_TRANSFER_IN_AMOUNT = 20
    DEFAULT_TRANSFER_OUT_AMOUNT = 1
    DEFAULT_CARD_LABEL = "1111"
    DEFAULT_CHANNEL = "Web"

    def __init__(self, user_http=None):
        self.user_http = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
        self.url = self.config.get_url_data()
        self.card_wallet_balance = card_wallet_fee.Balance_Calculate(self.user_http)
        self._card_group_cache = {}

    def create_card_shared_group(self, card_group_name: str, label: str, group_amount: Union[int, float]):
        """
        创建共享卡分组
        :param card_group_name: 分组名称
        :param label: 标签
        :param group_amount: 初始额度
        :return: jsonpath提取的分组id
        """
        payload = {
            "name": card_group_name,
            "label": label,
            "amount": group_amount
        }
        group_id = self.user_http.posts(
            url=f"{self.url}/web/virtual-card/create-card-group",
            data=payload,
            jsonpath_expr='$..id'
        )
        # 创建完成存入缓存
        self._card_group_cache[group_id] = None
        return group_id
    def get_card_group_info(self, card_group_id: str, use_cache: bool = True):
        """
        查询共享分组详情/余额接口，增加缓存避免重复请求
        :param card_group_id: 卡分组id
        :param use_cache: 是否开启缓存
        :return: jsonpath提取id
        """
        if use_cache and card_group_id in self._card_group_cache and self._card_group_cache[card_group_id]:
            return self._card_group_cache[card_group_id]

        shared_card_id = self.user_http.gets(
            url=f"{self.url}/web/virtual-card/card-group-balance/{card_group_id}",
            jsonpath_expr='$..id'
        )
        self._card_group_cache[card_group_id] = shared_card_id
        print(f"shared_card_id: {shared_card_id}")
        return shared_card_id

    def card_account_to_card_group(self, card_group_id: str, amount: Optional[int] = None, verify: bool = False):
        """
        主账户划转资金到共享卡分组
        :param card_group_id: 卡分组id
        :param amount: 转入金额，不传使用默认值20
        :param verify: verify标识
        :return: 接口返回
        """
        transfer_amount = amount or self.DEFAULT_TRANSFER_IN_AMOUNT
        # group_detail_id = self.get_card_group_info(card_group_id)
        payload = {
            "amount": transfer_amount,
            "verify": verify,
            "channel": self.DEFAULT_CHANNEL,
            "card_share_group_id": card_group_id
        }
        return self.user_http.posts(
            url=f"{self.url}/web/virtual-card/card-account-to-card-group",
            data=payload
        )

    def card_group_to_card_account(self, card_group_id: str, amount: Optional[int] = None):
        """
        共享卡分组资金划转回主账户
        :param card_group_id: 卡分组id
        :param amount: 转出金额，不传默认1
        :return: 接口返回
        """
        transfer_amount = amount or self.DEFAULT_TRANSFER_OUT_AMOUNT
        payload = {
            "amount": transfer_amount,
            "card_share_group_id": card_group_id
        }
        return self.user_http.posts(
            url=f"{self.url}/web/virtual-card/card-group-to-card-account",
            data=payload
        )

    def get_card_bin_id(self,category, product_code: str) -> Optional[str]:
        """
        根据产品编码获取共享卡bin id
        """
        bin_list = self.user_http.gets(
            url=f"{self.url}/web/virtual-card/all-channels?category={category}",
            jsonpath_expr=f"$.data[?(@.product_code=='{product_code}')].id"
        )

        return bin_list

    def get_holders_id(self, product_code: str) -> Optional[str]:
        """
        获取持卡人ID，增加空值保护，防止列表越界
        """
        holder_list = self.user_http.gets(
            url=f"{self.url}/web/virtual-card/get-all-holders?product_code={product_code}",
            jsonpath_expr='$..id'
        )
        if isinstance(holder_list, list) and len(holder_list) > 0:
            return holder_list[0]
        return ""

    def create_shared_card(self, card_group_id: str, product_code: str, label: str = None, tradable_amount: int = 20):
        """
        创建共享虚拟卡
        :param card_group_id: 共享分组id
        :param product_code: 产品编码
        :param label: 卡片标签，不传使用默认值
        :param tradable_amount: 可用额度
        :return: 创建卡片接口返回结果
        """
        bin_id = self.get_card_bin_id('share',product_code)
        holder_id = self.get_holders_id(product_code)

        create_shard_card_payload = {
            "cardType": "Virtual",
            "bin_id": bin_id,
            "virtualCardHolderId": holder_id or "",
            "label": label or self.DEFAULT_CARD_LABEL,
            "card_share_group_id": card_group_id,
            "tradable_amount": tradable_amount,
            "limit": [],
            "receiveEmail": True,
            "cardCategory": "share",
            "verify": False
        }
        return self.user_http.posts(
            url=f"{self.url}/web/virtual-card/create-card",
            data=create_shard_card_payload
        )
    def create_recharge_card(self, product_code: str, label: str = None, tradable_amount: int = 20):
        bin_id = self.get_card_bin_id('recharge',product_code)
        holder_id = self.get_holders_id(product_code)
        create_recharge_card_payload = {
                "cardType": "Virtual",
                "bin_id": bin_id,
                "virtualCardHolderId": holder_id,
                "label": label or self.DEFAULT_CARD_LABEL,
                "available": tradable_amount,
                "receiveEmail": True,
                "cardCategory": "recharge",
                "tradable_amount": None,
                "verify": False
            }
        return self.user_http.posts(
            url=f"{self.url}/web/virtual-card/create-card",
            data=create_recharge_card_payload
        )

    def card_group_to_shared_card(self, group_id, type,amount):
        """
        :param group_id: 共享卡组的id
        :param type: 提升/降价类型，可选值：increase/decrease
        :return:
        """
        shared_card_id = self.get_card_group_info(group_id)

        payload = {"card_id":random.choice(shared_card_id),"amount":amount,"type":type,"verify":False}
        return self.user_http.posts(
            url=f"{self.url}/web/virtual-card/update-tradable-amount-increment",
            data=payload
        )
    def clean_cache(self):
        """清空分组缓存，适合用在teardown清理"""
        self._card_group_cache.clear()







if __name__ == '__main__':
    op = CardGroupOperation()
    # 1. 创建分组
    # group_id = op.create_card_shared_group("测试分组002", "auto_test", 100)
    # print(group_id)
    group_id = 'b09a5cdb-1677-413c-8e06-2ca3c71d8ce1'
    # 2. 账户转入分组
    # op.card_account_to_card_group(group_id, amount=50)
    # # 3. 创建共享卡
    # op.create_shared_card(group_id, product_code="photon-us", tradable_amount=30)
    # # 4.卡提升/降价额度
    op.card_group_to_shared_card(group_id, type="decrease" ,amount =10)
    # # 4. 资金回收
    # op.card_group_to_card_account(group_id, amount=10)
    op.clean_cache()