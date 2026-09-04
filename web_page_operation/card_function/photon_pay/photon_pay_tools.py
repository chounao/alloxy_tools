from datetime import datetime
import json
import time
import requests

from common.Sql import DatabaseConnection
from common.simple_request import HttpRequest
from common import read_and_save_tool
from common.execute import get_config_section


TEST_ENTERPRISE_ID = '9498570428'
UAT_ENTERPRISE_ID = '9738483283'
MERCHANT_COUNTRY = 'US'


class PhotonPayTools:

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

        self.card_base_url = f'{self.url}/web/virtual-card/simulate-transaction'
        self._card_data_cache = {}
        self._fee_data_cache = {}

    # 数据库获取参数
    def get_raw_data(self, source_id):
        with DatabaseConnection() as db:
            result = db.execute_sql(
                "SELECT raw FROM virtual_card_transaction_webhook "
                "WHERE transaction_id = %s ORDER BY created_at desc limit 1;",
                (source_id,)
            )

            if not result:
                return None

            first_row = result[0]
            if isinstance(first_row, dict):
                raw_value = first_row.get('raw', first_row)
            elif isinstance(first_row, (list, tuple)):
                raw_value = first_row[0]
            else:
                raw_value = first_row

            if isinstance(raw_value, str):
                return json.loads(raw_value)

            return raw_value

    # 获取第三方费用
    def get_google_or_app_fee(self, last4):
        source_id = self.get_source_id(last4)
        raw = self.get_raw_data(source_id) or {}

        """
        手续费扣费金额明细：
        transactionFeeAmount：交易手续费金额；
        crossBroadFeeAmount：跨境手续费金额；
        conversionFeeAmount：汇率转换费金额；
        refundFeeAmount：退款手续费金额；
        voidFeeAmount：撤销手续费金额；
        gatewayFeeAmount：网关手续费金额；
        authFailedFeeAmount：失败交易手续费金额；
        fundInFeeAmount：汇入手续费金额；
        applePayCostFeeAmount：apple支付成本金额
        """
        fee_deduction_amount = raw.get('feeDeductionAmount', 0)
        return fee_deduction_amount

    # 获取card信息
    def get_card_data(self, last4, force_refresh=False):
        if not force_refresh and last4 in self._card_data_cache:
            return self._card_data_cache[last4]

        data_url = f'{self.url}/admin/virtual-card/get-all-cards?page=1&take=200'

        try:
            response = self.admin_http.requests('get', data_url)
            if response is None:
                raise Exception("请求失败，未获取到响应")

            response.raise_for_status()
            data = response.json()
            card_data_list = data.get('data', {}).get('list', [])

            for card in card_data_list:
                if card.get('last4') == last4:
                    bank_card_id = card.get('bank_card_id')
                    card_id = card.get('id')
                    category = card.get('category')
                    product_code = card.get('vcc_product_code')
                    product_name = card.get('product_name')

                    if not all([bank_card_id, card_id, category, product_code, product_name]):
                        raise ValueError(f"卡片数据字段缺失: {card}")

                    print(
                        f"bank_card_id: {bank_card_id}, card_id: {card_id}",
                        "卡片类型:", category,
                        "卡片产品代码:", product_code,
                        "卡片产品名称:", product_name
                    )

                    card_data = (bank_card_id, card_id, category, product_code, product_name)
                    self._card_data_cache[last4] = card_data
                    return card_data

            raise Exception(f"未找到后四位为 {last4} 的卡片")

        except requests.exceptions.RequestException as e:
            raise Exception(f"获取卡片信息失败: {str(e)}")
        except (KeyError, ValueError) as e:
            raise Exception(f"响应数据格式错误: {str(e)}")

    # 根据卡片类型获取数据结构
    def get_fee_type(self, last4, card_type_fee_name):
        bank_card_id, card_id, category, product_code, product_name = self.get_card_data(last4)

        if category == 'recharge':
            card_type, card_type_fee = self.get_transaction_type('光子易虚拟储值卡', card_type_fee_name)
        elif category == 'share':
            card_type, card_type_fee = self.get_transaction_type('光子易虚拟共享卡', card_type_fee_name)
        else:
            raise ValueError(f"未知的卡片类型: '{category}'")

        return card_type, card_type_fee

    # 根据卡片产品代码判断是美卡还是港卡
    def get_card_type_for_code(self, last4):
        bank_card_id, card_id, category, product_code, product_name = self.get_card_data(last4)

        if product_code in ['photon-us', 'photon-hk']:
            return product_code, product_name

        raise ValueError(f"未知的卡片产品代码: '{product_code}'")

    # 把当前时间转格式
    def get_requestId(self):
        return datetime.now().strftime('%Y%m%d%H%M%S')

    # 获取卡信息进行body传参数
    def get_card_info(self, card_id):
        card_url = f'{self.url}/web/virtual-card/card-cvv/{card_id}'

        try:
            response = self.user_http.requests('get', card_url)
            if response is None:
                raise Exception("请求失败，未获取到响应")

            response.raise_for_status()
            data = response.json()

            if 'data' not in data:
                raise ValueError("响应数据中缺少 'data' 字段")

            card_data = data['data']
            cvv = card_data.get('cvv')
            expiration_date = card_data.get('expirationDate')

            if cvv is None or expiration_date is None:
                raise ValueError("响应数据中缺少 'cvv' 或 'expirationDate' 字段")

            return cvv, expiration_date

        except requests.exceptions.RequestException as e:
            raise Exception(f"获取卡片信息失败: {str(e)}")
        except (ValueError, KeyError) as e:
            raise Exception(f"解析卡片信息失败: {str(e)}")

    # 获取请求体的数据body
    def get_request_data(self, last4, txnType, amount, card_id, originTransactionId=None):
        product_code, product_name = self.get_card_type_for_code(last4)
        times = self.get_requestId()
        cvv, expiration_date = self.get_card_info(card_id)

        body = {
            "requestId": times,
            "cardID": card_id,
            "cvv": cvv,
            "expirationDate": expiration_date,
            "originTransactionId": originTransactionId,
            "txnCurrency": "USD",
            "txnAmount": amount,
            "txnType": txnType,
            "mcc": "1234",
            "merchantName": "Ryan",
            "merchantCountry": MERCHANT_COUNTRY,
            "merchantCity": "test",
            "merchantPostcode": "12345"
        }

        if txnType == 'auth':
            body['originTransactionId'] = ''

        if product_code == 'photon-us':
            body['productCode'] = 'photon-us'

        return body

    # 获取手续费类型type
    def get_transaction_type(self, card_type_name, card_type_fee_name):
        card_type_dict = {
            '光子易虚拟储值卡': 'photon_recharge_virtual',
            '光子易虚拟共享卡': 'photon_share_virtual',
            '光子易实体储值卡': 'photon_recharge_physical',
            '光子易实体共享卡': 'photon_share_physical'
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
        url = f'{self.config_url}/web/virtual-card/photon-card-detail/{card_id}'

        response = self.user_http.requests('get', url)
        if response is None:
            raise requests.exceptions.HTTPError("请求失败，未获取到响应")

        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f"请求失败: {response.status_code} - {response.text}")

        data = response.json()

        if 'data' not in data:
            raise ValueError("响应数据中缺少 'data' 字段")

        card_data = data['data']

        if 'availableTransactionLimit' in card_data:
            value = card_data['availableTransactionLimit']
            if value == 0:
                return card_data.get('cardBalance', 0)
            return value

        if 'cardBalance' in card_data:
            return card_data['cardBalance']

        raise ValueError("响应数据中缺少 'availableTransactionLimit' 或 'cardBalance' 字段")

    # 获取卡产品费用设置，根据企业id、product_code、product_name返回对应的数据
    def get_all_fee_data(self, product_code, product_name, force_refresh=False):
        cache_key = (product_code, product_name)
        if not force_refresh and cache_key in self._fee_data_cache:
            return self._fee_data_cache[cache_key]

        card_fee_url = (
            f'{self.url}/admin/virtual-card/card-fee'
            f'?page=1&take=10&identifier_id={self.enterprise_id}'
        )

        try:
            datas = self.admin_http.requests(
                'get',
                card_fee_url,
                jsonpath_expr='$.data.list[?(@.product_code=="%s")]' % (
                    product_code

                )
            )

            if not datas:
                raise ValueError(f"未找到费用配置: product_code={product_code}")
            #判断data的类型是否为列表，如果是列表说明是多个需要跟product_name匹配
            if isinstance(datas, list):
                for data in datas:
                    if data['product_name'] == product_name:
                        return data
            else:
                return datas
            # self._fee_data_cache[cache_key] = data
            # return data

        except requests.exceptions.RequestException as e:
            raise Exception(f"获取所有费用数据请求失败: {str(e)}")
        except (ValueError, KeyError) as e:
            raise Exception(f"解析所有费用数据失败: {str(e)}")

    # 根据卡后四位获取费用配置
    def get_fee_data_by_last4(self, last4):
        product_code, product_name = self.get_card_type_for_code(last4)
        data = self.get_all_fee_data(product_code, product_name)
        return data


    # 获取开卡费
    def get_open_card_fee(self, product_code, product_name):
        data = self.get_all_fee_data(product_code, product_name)
        open_card_fee = data.get('open_card_fee')
        return open_card_fee

    # 获取交易手续费用
    def get_transaction_fee(self, last4, card_type_fee_name):
        card_type, card_type_fee = self.get_fee_type(last4, card_type_fee_name)
        fee_data = self.get_fee_data_by_last4(last4)

        transaction_fee = fee_data.get('transaction_fee') or {}
        # print('手续费字段：', transaction_fee)

        fee_per_count = transaction_fee.get(card_type_fee[0])
        fee_prorate = transaction_fee.get(card_type_fee[1])

        if fee_per_count is None or fee_prorate is None:
            raise ValueError(f"未找到费用配置: {card_type} - {card_type_fee_name}")

        print('手续费：', fee_per_count, '费率：', fee_prorate)
        return fee_per_count, fee_prorate

    # 获取交易授权费
    def get_authorization_fee(self, last4, amount):
        fee_data = self.get_fee_data_by_last4(last4)
        authorization_fee = fee_data.get('auth_fee') or []

        for item in authorization_fee:
            if item['min'] <= amount <= item['max']:
                print(f"授权费为：{item['fee']}")
                return item['fee']

        return 0

    # 计算消费手续费
    def calculate_transaction_fee(self, last4):
        product_code, product_name = self.get_card_type_for_code(last4)
        print('产品代码：', product_code, product_name)

        if "hk" in product_code:
            fee_per_count, fee_prorate = self.get_transaction_fee(last4, '跨境消费')
        else:
            fee_per_count, fee_prorate = self.get_transaction_fee(last4, '本地消费')

        print('交易手续费', fee_per_count, fee_prorate)
        return fee_per_count, fee_prorate

    # 获取source_id退款时候用
    def get_source_id(self, last4):
        time.sleep(3)
        transaction_url = (
            f'{self.url}/admin/virtual-card/get-all-transactions'
            f'?page=1&take=10&transaction_sub_type=card'
        )

        try:
            response = self.admin_http.requests('get', transaction_url)
            if response is None:
                raise Exception("请求失败，未获取到响应")

            response.raise_for_status()
            data = response.json()
            data_list = data.get('data', {}).get('list', [])

            for transaction in data_list:
                if transaction.get('vc_last4') == last4 and transaction.get('vc_customerType') == 'Consumer':
                    print('找到交易', transaction)
                    source_id = transaction.get('source_id')
                    print('source_id', source_id)
                    return source_id

            raise Exception(f"未找到后四位为 {last4} 且类型为 Consumer 的交易")

        except requests.exceptions.RequestException as e:
            raise Exception(f"获取交易信息失败: {str(e)}")
        except (KeyError, ValueError) as e:
            raise Exception(f"响应数据格式错误: {str(e)}")

    # 计算退款手续费
    def calculate_refund_fee(self, last4, amount):
        card_type, card_type_fee = self.get_fee_type(last4, "退款")
        fee_data = self.get_fee_data_by_last4(last4)

        transaction_fee = fee_data.get('transaction_fee') or {}
        fee_per_count = transaction_fee.get(card_type_fee[0])
        fee_prorate = transaction_fee.get(card_type_fee[1])

        if fee_per_count is None or fee_prorate is None:
            raise ValueError(f"未找到退款费用配置: {card_type}")

        print('手续费：', fee_per_count, '费率：', fee_prorate)
        all_refund_num = fee_prorate * amount + fee_per_count
        return all_refund_num

    # 进行操作消费等操作流程
    def card_operation(self, last4, txnType, bank_card_id, amount, originTransactionId=None):
        body = self.get_request_data(last4, txnType, amount, bank_card_id, originTransactionId)
        response = self.user_http.requests('post', self.card_base_url, data=body)

        if response is None:
            raise requests.exceptions.HTTPError("请求失败，未获取到响应")

        if response.status_code != 201:
            raise requests.exceptions.HTTPError(f"请求失败: {response.status_code} - {response.text}")

        return body

    # 消费
    def card_consume(self, amount, last4):
        bank_card_id, card_id, category, product_code, product_name = self.get_card_data(last4)

        before_amount = self.get_card_balance(bank_card_id)
        print('消费前的金额', before_amount)

        self.card_operation(last4, 'auth', bank_card_id, amount)

        fee_per_count, fee_prorate = self.calculate_transaction_fee(last4)
        print('手续费：', fee_per_count, '费率：', fee_prorate)

        consume_amount = amount + fee_per_count + fee_prorate * amount
        authorization_fee = self.get_authorization_fee(last4, amount)
        print('消费：', consume_amount, '授权费：', authorization_fee)

        calculate_amount = before_amount - consume_amount - authorization_fee
        print('剩下额度', calculate_amount)

        later_amount = self.get_card_balance(bank_card_id)
        print('三方返回的值', later_amount)

        return {
            "before_amount": before_amount,
            "consume_amount": consume_amount,
            "authorization_fee": authorization_fee,
            "calculate_amount": calculate_amount,
            "later_amount": later_amount
        }

    # 退款
    def card_refund(self, amount, last4):
        bank_card_id, card_id, category, product_code, product_name = self.get_card_data(last4)

        before_amount = self.get_card_balance(bank_card_id)
        print('退款前的金额', before_amount)
        originTransactionId = self.get_source_id(last4)
        print('originTransactionId', originTransactionId)
        self.card_operation(last4, 'refund', bank_card_id, amount, originTransactionId)

        refund_fee = self.calculate_refund_fee(last4, amount)
        print('需要扣掉的退款费用', refund_fee)
        fee_per_count, fee_prorate = self.calculate_transaction_fee(last4)
        refund_transaction_fee = fee_prorate * amount
        print('退还的消费手续费', refund_transaction_fee)

        calculate_amount = before_amount - refund_fee + refund_transaction_fee + amount
        print('剩下额度', calculate_amount)

        later_amount = self.get_card_balance(bank_card_id)
        print('三方返回的值', later_amount)

        return {
            "before_amount": before_amount,
            "refund_fee": refund_fee,
            "refund_transaction_fee": refund_transaction_fee,
            "calculate_amount": calculate_amount,
            "later_amount": later_amount
        }
    # 撤销退款
    def card_reverse_refund(self, amount, last4):
        bank_card_id, card_id, category, product_code, product_name = self.get_card_data(last4)

        before_amount = self.get_card_balance(bank_card_id)
        print('退款前的金额', before_amount)
        originTransactionId = self.get_source_id(last4)
        self.card_operation(last4, 'void', bank_card_id, amount, originTransactionId)

        void_fee = self.calculate_refund_fee(last4, amount)
        print('需要扣掉的退款费用', void_fee)
        fee_per_count, fee_prorate = self.calculate_transaction_fee(last4)
        void_transaction_fee = fee_prorate * amount
        print('退还的消费手续费', void_transaction_fee)

        calculate_amount = before_amount - void_fee + void_transaction_fee + amount
        print('剩下额度', calculate_amount)

        later_amount = self.get_card_balance(bank_card_id)
        print('三方返回的值', later_amount)

        return {
            "before_amount": before_amount,
            "void_fee": void_fee,
            "void_transaction_fee": void_transaction_fee,
            "calculate_amount": calculate_amount,
            "later_amount": later_amount
        }
    # 获取source_id
    def get_source_id(self, last4):
        bank_card_id, card_id, category, product_code, product_name = self.get_card_data(last4)
        url = f"{self.url}/web/virtual-card/transaction-list?page=1&take=20&virtual_card_id={card_id}&transaction_type[]=card_consume&transaction_sub_type=card"
        sourceId = self.user_http.requests('get', url,jsonpath_expr= "$.data.list[0].source_id")
        if sourceId is None:
            url = f"{self.url}/web/virtual-card/transaction-list?page=1&take=20&virtual_card_id={card_id}&transaction_type=card_consume&transaction_sub_type=card_share_group"
            sourceId = self.user_http.requests('get', url, jsonpath_expr="$.data.list[0].source_id")
        print(sourceId)
        return sourceId

# 获取共享卡的实际余额
    def get_card_balance_data(self, last4):
        bank_card_id, card_id, category, product_code, product_name = self.get_card_data(last4)
        num = self.get_card_balance(bank_card_id)
        print(num)
        return num


if __name__ == '__main__':
    amount = 2
    last4 = '0914'

    photon_pay_tools = PhotonPayTools()



    """
    消费
    """
    photon_pay_tools.card_consume(amount, last4)



    """
    退款
    """
    time.sleep(5)
    photon_pay_tools.card_refund(amount, last4)


    """
    撤销
    """
    # time.sleep(5)
    # photon_pay_tools.card_reverse_refund(amount, last4)





