
"""

寻汇的卡只能在uat环境验证
date:2026-6-03

"""
from datetime import datetime
from common.Sql import DatabaseConnection
import json
import time
import requests
from common.simple_request import HttpRequest
from common import read_and_save_tool
from common.execute import get_config_section



TEST_ENTERPRISE_ID = '9498570428'
UAT_ENTERPRISE_ID = '9738483283'
merchantCountry = 'US'
class SunRateTools:

    def __init__(self, user_http=None, admin_http=None):
        self.user_http = user_http or HttpRequest(user_type='user')
        self.admin_http = admin_http or HttpRequest(user_type='admin')

        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.config_section = get_config_section()
        self.url = self.config.get_url_data()
        if self.config_section == 'TEST_CONFIG':
            self.enterprise_id = TEST_ENTERPRISE_ID
        else:
            self.enterprise_id = UAT_ENTERPRISE_ID
        # 模拟交易接口
        self.card_base_url = f'{self.url}/web/virtual-card/simulate-transaction'
        self._card_data_cache = {}

    # 数据库获取参数
    def get_raw_data(self, source_id):

        with DatabaseConnection() as db:
            result = db.execute_sql(
                "SELECT raw FROM virtual_card_transaction_webhook WHERE transaction_id = %s ORDER BY created_at desc limit 1;",
                (source_id,)
            )
            if result:
                first_row = result[0]
                # 处理返回结果为字典或元组的情况
                if isinstance(first_row, dict):
                    # 如果已经是字典，直接返回
                    return first_row
                elif isinstance(first_row, (list, tuple)):
                    # 如果是元组或列表，提取第一个元素
                    raw_value = first_row[0]
                    if isinstance(raw_value, str):
                        # 如果是字符串，进行JSON解析
                        result_json = json.loads(raw_value)
                        return result_json
                    elif isinstance(raw_value, dict):
                        # 如果已经是字典，直接返回
                        return raw_value
                    else:
                        return raw_value
                else:
                    return first_row
            return None

    # h获取第三方费用
    def get_google_or_app_fee(self, last4):
        source_id = self.get_source_id(last4)
        raw = self.get_raw_data(source_id)

        """
        手续费扣费金额明细。
        transactionFeeAmount：交易手续费金额；
        crossBroadFeeAmount：跨境手续费金额；
        conversionFeeAmount：汇率转换费金额；
        refundFeeAmount：退款手续费金额；
        voidFeeAmount：撤销手续费金额；
        gatewayFeeAmount：网关手续费金额；
        authFailedFeeAmount：失败交易手续费金额
        ；fundInFeeAmount：汇入手续费金额；
        applePayCostFeeAmount：apply支付成本金额
        """
        feeDeductionAmount = raw.get('feeDeductionAmount', 0)
        return feeDeductionAmount

    # 获取card信息
    def get_card_data(self, last4, force_refresh=False):
        if not force_refresh and last4 in self._card_data_cache:
            return self._card_data_cache[last4]
        data_url = f'{self.url}/admin/virtual-card/get-all-cards?page=1&take=20'

        try:
            response = self.admin_http.requests('get', data_url)
            if response is None:
                raise Exception("请求失败，未获取到响应")
            response.raise_for_status()
            data = response.json()
            card_data_list = data['data']['list']
            for card in card_data_list:
                if card['last4'] == last4:
                    bank_card_id = card['bank_card_id']
                    card_id = card['id']
                    category = card['category'] # 卡片类型recharge share
                    product_code = card['vcc_product_code'] # 卡片产品代码
                    print(f"bank_card_id: {bank_card_id}, card_id: {card_id}", "卡片类型:", category, "卡片产品代码:", product_code)
                    self._card_data_cache[last4] = (bank_card_id, card_id, category, product_code)
                    return bank_card_id, card_id, category, product_code

            raise Exception(f"未找到后四位为 {last4} 的卡片")
        except requests.exceptions.RequestException as e:
            raise Exception(f"获取卡片信息失败: {str(e)}")
        except (KeyError, ValueError) as e:
            raise Exception(f"响应数据格式错误: {str(e)}")

    # 根据卡片类型获取数据结构
    def get_fee_type(self, last4, card_type_fee_name):
        bank_card_id, card_id, category ,product_code= self.get_card_data(last4)

        if category == 'recharge':
            card_type, card_type_fee = self.get_transaction_type('寻汇虚拟储值卡', card_type_fee_name)
        else:
            raise ValueError(f"未知的卡片类型: '{category}'")
        return card_type, card_type_fee

    # 根据卡片产品代码判断是美卡还是港卡然后自己的判断流程
    def get_card_type_for_code(self,last4):
        bank_card_id, card_id, category, product_code = self.get_card_data(last4)
        if product_code == 'sunrate-apay':
            return 'sunrate-apay'
        elif product_code == 'sunrate-hk':
            return 'sunrate-hk'
        elif product_code == 'sunrate-us':
            return 'sunrate-us'
        else:
            raise ValueError(f"未知的卡片产品代码: '{product_code}'")

    # 把当前时间转格式
    def get_requestId(self):
        return datetime.now().strftime('%Y%m%d%H%M%S')

    # 获取卡信息进行bodu传参数
    def get_card_info(self, card_id):
        self.card_url = f'{self.url}/web/virtual-card/card-cvv/{card_id}'
        try:
            response = self.user_http.requests('get', self.card_url)
            if response is None:
                raise Exception("请求失败，未获取到响应")

            response.raise_for_status()
            data = response.json()

            if 'data' not in data:
                raise ValueError("响应数据中缺少 'data' 字段")

            card_data = data['data']
            cvv = card_data.get('cvv')
            expirationDate = card_data.get('expirationDate')

            if cvv is None or expirationDate is None:
                raise ValueError("响应数据中缺少 'cvv' 或 'expirationDate' 字段")

            return cvv, expirationDate
        except requests.exceptions.RequestException as e:
            raise Exception(f"获取卡片信息失败: {str(e)}")
        except (ValueError, KeyError) as e:
            raise Exception(f"解析卡片信息失败: {str(e)}")

    # 获取请求体的数据body
    def get_request_data(self, last4, txnType, amount, card_id, originTransactionId=None):
        productCode = self.get_card_type_for_code(last4)
        times = self.get_requestId()
        cvv, expirationDate = self.get_card_info(card_id)
        body = {
            "requestId": times,
            "cardID": card_id,
            "cvv": cvv,
            "expirationDate": expirationDate,
            "originTransactionId": originTransactionId,
            "txnCurrency": "USD",
            "txnAmount": amount,
            "txnType": txnType,
            "mcc": "1234",
            "merchantName": "Ryan",
            "merchantCountry": merchantCountry,
            "merchantCity": "test",
            "merchantPostcode": "12345"
        }
        if txnType == 'auth':
            body['originTransactionId'] = ''
        if productCode == 'photon-us':
            body['productCode'] = 'photon-us'
        return body

    # 获取手续费类型type
    def get_transaction_type(self, card_type_name, card_type_fee_name):
        """
        根据卡片类型名称和费用类型名称获取对应的交易类型和费用字段

        Args:
            card_type_name: 卡片类型名称，如'寻汇虚拟储值卡'
            card_type_fee_name: 费用类型名称，如'充值'、'本地消费'等

        Returns:
            tuple: (card_type, card_type_fee)
                   - card_type: 卡片类型标识
                   - card_type_fee: 费用字段列表 [每笔费用, 比例费用]

        Raises:
            ValueError: 当卡片类型或费用类型无效时抛出
        """

        card_type_dict = {
            '寻汇虚拟储值卡': 'sunrate_recharge_virtual'
        }

        card_fee_type_dict = {
            '充值': ['card_recharge_fee_per_count', 'card_recharge_fee_prorate'],
            '本地消费': ['card_local_consume_fee_per_count', 'card_local_consume_fee_prorate'],
            '跨境消费': ['card_cross_border_consume_fee_per_count', 'card_cross_border_consume_fee_prorate'],
            'ATM提现': ['card_atm_withdraw_fee_per_count', 'card_atm_withdraw_fee_prorate'],
            '退款': ['card_refund_fee_per_count', 'card_refund_fee_prorate'],
            '撤销': ['card_reversal_fee_per_count', 'card_reversal_fee_prorate']
        }

        card_type = card_type_dict.get(card_type_name)
        if card_type is None:
            raise ValueError(f"无效的卡片类型: '{card_type_name}'。支持的类型: {list(card_type_dict.keys())}")

        card_type_fee = card_fee_type_dict.get(card_type_fee_name)
        if card_type_fee is None:
            raise ValueError(f"无效的费用类型: '{card_type_fee_name}'。支持的类型: {list(card_fee_type_dict.keys())}")

        return card_type, card_type_fee

    # 获取三方返回的数据
    def get_card_balance(self, card_id):

        time.sleep(6)
        URL = f'{self.config_url}/web/virtual-card/photon-card-detail/{card_id}'
        response = self.user_http.requests('get', URL)
        if response is None:
            raise requests.exceptions.HTTPError("请求失败，未获取到响应")

        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f"请求失败: {response.status_code} - {response.text}")

        data = response.json()

        # 验证返回数据结构
        if 'data' not in data:
            raise ValueError("响应数据中缺少 'data' 字段")

        if 'availableTransactionLimit' in data['data']:
            value = data['data']['availableTransactionLimit']
            if value == 0:
                if 'cardBalance' in data['data']:
                    balance_value = data['data']['cardBalance']
                else:
                     balance_value = 0
            else:
                balance_value = value
        elif 'cardBalance' in data['data']:
            balance_value = data['data']['cardBalance']
        else:
            raise ValueError("响应数据中缺少 'availableTransactionLimit' 或 'cardBalance' 字段")

        return balance_value

     # 获取开卡费
    def get_open_card_fee(self, last4, card_type_fee_name):

        card_type, card_type_fee = self.get_fee_type(last4, card_type_fee_name)
        open_card_fee_url = f'{self.url}/admin/virtual-card/open-card-fee-list?page=1&take=10&identifier_id={self.enterprise_id}'

        try:
            response = self.admin_http.requests('get', open_card_fee_url)


            if response is None:
                raise Exception("请求失败，未获取到响应")

            response.raise_for_status()
            data = response.json()

            # 验证数据结构
            if 'data' not in data or 'list' not in data['data']:
                raise ValueError("响应数据结构异常，缺少 'data' 或 'list' 字段")

            # 获取指定卡片类型的费用
            usd_num = data['data']['list'][0].get(card_type, [None])

            if usd_num is None:
                raise ValueError(f"未找到卡片类型 '{card_type}' 的开卡费用")

            return usd_num

        except requests.exceptions.RequestException as e:
            raise Exception(f"获取开卡费请求失败: {str(e)}")
        except (ValueError, KeyError) as e:
            raise Exception(f"解析开卡费数据失败: {str(e)}")

    # 获取交易手续费用
    def get_transaction_fee(self, last4, card_type_fee_name):

        card_type, card_type_fee = self.get_fee_type(last4, card_type_fee_name)
        product_code = self.get_card_type_for_code(last4)

        transaction_fee_url = f'{self.url}/admin/virtual-card/transaction-fee-list?page=1&take=100&identifier_id={self.enterprise_id}'

        try:
            response = self.admin_http.requests('get', transaction_fee_url)

            if response is None:
                raise Exception("请求失败，未获取到响应")

            response.raise_for_status()
            data = response.json()

            # 验证数据结构
            if 'data' not in data or 'list' not in data['data']:
                raise ValueError("响应数据结构异常，缺少 'data' 或 'list' 字段")

            # 获取指定卡片类型的费用配置
            data_list = data['data']['list'][0].get(card_type)
            if data_list is None:
                raise ValueError(f"未找到卡片类型 '{card_type}' 的交易手续费配置")


            fee_config_0 = data_list.get(card_type_fee[0])
            fee_config_1 = data_list.get(card_type_fee[1])

            if fee_config_0 is None or fee_config_1 is None:
                raise ValueError(f"未找到卡片类型 '{card_type}' 的费用类型 '{card_type_fee_name}' 的配置")

            fee_per_count = fee_config_0.get(product_code)
            fee_prorate = fee_config_1.get(product_code)

            if fee_per_count is None or fee_prorate is None:
                raise ValueError(f"未找到区域 '{product_code}' 的费用配置")

            return fee_per_count, fee_prorate

        except requests.exceptions.RequestException as e:
            raise Exception(f"获取交易手续费请求失败: {str(e)}")
        except (ValueError, KeyError, AttributeError) as e:
            raise Exception(f"解析交易手续费数据失败: {str(e)}")

    # 获取交易授权费
    def get_authorization_fee(self, last4,amount):
        card_type, card_type_fee = self.get_fee_type(last4, '本地消费')
        product_code = self.get_card_type_for_code(last4)
        authorization_url = f'{self.url}/admin/virtual-card/auth-fee-list?page=1&take=10&identifier_id={self.enterprise_id}'
        try:
            response = self.admin_http.requests('get', authorization_url)
            if response is None:
                raise Exception("请求失败，未获取到响应")
            response.raise_for_status()
            data = response.json()

            # 验证数据结构
            if 'data' not in data or 'list' not in data['data']:
                raise ValueError("响应数据结构异常，缺少 'data' 或 'list' 字段")

            data_list = data['data']['list'][0].get(card_type).get(product_code)
            for i in data_list:

                if i['min'] <= amount <= i['max']:
                    print(f'授权费为为：{i['fee']}')
                    return i['fee']
        except requests.exceptions.RequestException as e:
            raise Exception(f"获取授权费请求失败: {str(e)}")

    #计算消费手续费
    def calculate_transaction_fee(self,last):
        if merchantCountry == 'HK':
            fee_per_count, fee_prorate = self.get_transaction_fee(last, '本地消费')
        else:
            fee_per_count, fee_prorate = self.get_transaction_fee(last, '跨境消费')

        #缺少交易授权费
        print('交易手续费',fee_per_count, fee_prorate)
        return fee_per_count, fee_prorate

    # 获取source_id退款时候用
    def get_source_id(self, last4):
        time.sleep(3)
        self.transaction_url = f'{self.url}/admin/virtual-card/get-all-transactions?page=1&take=10&transaction_sub_type=card'
        try:
            response = self.admin_http.requests('get', self.transaction_url)
            if response is None:
                raise Exception("请求失败，未获取到响应")
            response.raise_for_status()
            data = response.json()
            data_list = data['data']['list']
            for transaction in data_list:
                if transaction['vc_last4'] == last4 and transaction['vc_customerType'] == 'Consumer':
                    source_id = transaction['source_id']
                    return source_id
            raise Exception(f"未找到后四位为 {last4} 且类型为 Consumer 的交易")
        except requests.exceptions.RequestException as e:
            raise Exception(f"获取交易信息失败: {str(e)}")
        except (KeyError, ValueError) as e:
            raise Exception(f"响应数据格式错误: {str(e)}")

    # 计算退款手续费
    def calculate_refund_fee(self, last4,amount):
        fee_per_count, fee_prorate = self.get_transaction_fee(last4, '退款')
        all_refund_num = fee_prorate* amount+ fee_per_count
        print('退款手续费',all_refund_num)
        return all_refund_num

    # 进行操作消费等操作流程
    def card_operation(self,last4, txnType,bank_card_id ,amount,originTransactionId=None):

        body = self.get_request_data(last4,txnType, amount, bank_card_id,originTransactionId)
        response = self.user_http.requests('post', self.card_base_url, data=body)
        if response is None:
            raise requests.exceptions.HTTPError("请求失败，未获取到响应")

        if response.status_code != 201:
            raise requests.exceptions.HTTPError(f"请求失败: {response.status_code} - {response.text}")

        return body
    # 获取所有费用相关内容
    def get_all_fee_info(self,last4,amount):


        # 共享手续费
        fee_per_count, fee_prorate = self.calculate_transaction_fee(last4)
        print('固定消费手续费：', fee_per_count, '费率：', fee_prorate)
        num2 = amount + fee_per_count + fee_prorate * amount
        num3 = self.get_authorization_fee(last4, amount)
        print('手续费和消费金额：', num2, '授权费：', num3)


    # 消费
    def card_consume(self,amount, last4):
        bank_card_id, card_id, category ,product_code= self.get_card_data(last4)
        # 共享手续费
        fee_per_count, fee_prorate = self.calculate_transaction_fee(last4)
        print('手续费：',fee_per_count,'费率：',fee_prorate)
        num2 = amount + fee_per_count + fee_prorate* amount
        num3 = self.get_authorization_fee( last4,amount) - 0.25
        print('手续费和消费金额：',num2,'授权费：',num3)



    # 退款
    def card_refund(self, amount, last4,originTransactionId):
        bank_card_id, card_id, category ,product_code= self.get_card_data(last4)
        num1 = self.get_card_balance(bank_card_id)
        print('退款前的金额', num1)
        # 退款
        self.card_operation(last4 ,'refund',bank_card_id,amount,originTransactionId)
        # 获取共享卡的实际余额
        num2 = self.calculate_refund_fee(last4,amount)
        fee_per_count, fee_prorate = self.calculate_transaction_fee(last4)
        num3 = fee_prorate* amount
        print('退还的消费手续费',num3)
        num4 = num1 - num2 + num3 +amount
        print('剩下额度',num4)
        later_num = self.get_card_balance(bank_card_id)
        print('三方返回的值',later_num)

    # 获取共享卡的实际余额
    def get_card_balance_data(self, last4):
        bank_card_id, card_id, category ,product_code = self.get_card_data(last4)
        num = self.get_card_balance(bank_card_id)
        print(num)


    # ==================== 寻汇卡相关 API ==============================

    def get_acct_jnl_list(self, acct_id):
        """
        查询寻汇卡渠道账户流水

        :param txn_date: 交易日期，格式如 '2026-06-03'，默认使用今天
        :param current: 页码，默认 '1'
        :param size: 每页大小，默认 '100'
        :param acct_id: 账户ID
        :return: 账户流水数据
        """

        txn_date = datetime.now().strftime('%Y-%m-%d')

        url = f'{self.url}/web/virtual-card/getAcctJnlList'


        data = {
            "txnDate": txn_date,
            "pageInfo": {
                "current": 1,
                "size": 100
            },
            "acctId": acct_id
        }

        response = self.user_http.requests('post', url, data)
        print("查询寻汇卡渠道账户流水")
        print(response.json())
        return response

    def get_acct_bal_list(self, acct_id):
        """
        查询寻汇卡账户余额

        :param acct_id: 账户ID
        :return: 账户余额数据
        """
        url = f'{self.url}/web/virtual-card/getAcctBalList'


        data = {
            "acctId": acct_id
        }


        response = self.user_http.requests('post', url, data)
        print("查询寻汇卡账户余额")
        print( response.json())

        return response

    def get_sunrate_card_info(self, acct_id, last4):
        """
        查询虚拟卡信息

        :param acct_id: 账户ID
        :param card_id: 卡ID
        :return: 虚拟卡信息
        """
        url = f'{self.url}/web/virtual-card/getSunrateCardInfo'

        bank_card_id, card_id, category, product_code = self.get_card_data(last4)
        data = {
            "acctId": acct_id,
            "cardId": bank_card_id
        }


        response = self.user_http.posts(url, data=data)
        print("查询虚拟卡信息")
        print( response.json())

        # 恢复默认请求头
        return response
    #查询注册用户
    def get_register_user(self):
        """
        查询注册用户

        :param acct_id: 账户ID
        :return: 注册用户信息
        """
        url = f'{self.url}/web/virtual-card/getRegisterUser'
        body ={"acctId": "63877812", "outBizId": "mq0bzcszqr8jvwlhvhb"}

        requests = self.user_http.requests("post",url, body)
        print("查询注册用户")
        print(requests.json())
        return  requests
if __name__ == '__main__':
    import sys
    from common.execute import set_env

    # 切换到目标环境，避免使用默认的 test 环境
    set_env('uat')


    amount = 21
    acct_id = '63877812'

    # 创建SunRateTools对象
    sun_rate_tools = SunRateTools()

    """
    消费
    """
    last4 = '3603'
    # sun_rate_tools.card_consume(amount,last4)
    # sun_rate_tools.get_all_fee_info(last4,amount)



    sun_rate_tools.get_acct_jnl_list(acct_id)
    sun_rate_tools.get_acct_bal_list(acct_id)
    # sun_rate_tools.get_sunrate_card_info(acct_id,last4)
    # sun_rate_tools.get_register_user()


    """
    退款
    """
    # source_id="IT2056322630953320448"
    # photon_pay_tools.card_refund(amount,last4,source_id)






