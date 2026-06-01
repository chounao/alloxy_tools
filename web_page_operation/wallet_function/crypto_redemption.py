import json
import requests
from typing import Dict, List, Tuple, Optional, Any


class PayMent:
    """
    用于加密货币页面pay_out功能操作
    """
    def __init__(self):
        self.token = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI4M2ZjMzVjNC0yYjBmLTQ1NjctOWRlMS04ZjUzNGUwMjRmNWIiLCJhY2NvdW50SWQiOiIwZGUyZWRmMC01YTliLTRjMWQtYTE5ZC0zY2QzZmMxZjAxNDciLCJsb2dpblRpbWUiOjE3NTQ5ODY2MDc4NzcsImxvZ2luVHlwZSI6IndlYiIsImlhdCI6MTc1NDk4NjYwNywiZXhwIjoxNzU1MDA4MjA3fQ.yZlbmQaRj2l7YKzLxae3QbMVlh9SgyIAU43HQXsA7kU'
        self.headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6',
        }
        self.wallet = 'AXCNH'
        self.authority = 'https://ax-api.pertest.tech/web/'
        self.session = requests.Session()
        self.fei_currency = ['BWP', 'KES', 'MWK', 'NGN', 'RWF', 'ZAR', 'TZS', 'UGX', 'ZMW']
        self.count = {
            'BWP': [150, 1000000],
            'KES': [500, 999999],
            'MWK': [5000, 20000000],
            'NGN': [1800, 30000000],
            'RWF': [1500, 10000000],
            'ZAR': [200, 500000],
            'TZS': [2500, 40000000],
            'UGX': [15000, 36000000],
            'ZMW': [100, 15000000]
        }

    def get_session(self) -> requests.Session:
        """获取带认证头的会话"""
        self.session.headers.update(self.headers)
        return self.session

    def get_chain(self) -> List[Dict]:
        """获取所有链的结果"""
        path = 'crypto/chain'
        url = self.authority + path
        response = self.get_session().get(url)
        return response.json()['data']['chainList']

    def get_fiat_fee(self) -> float:
        """获取所有法币手续费"""
        path = 'crypto/get-fiat-fee'
        url = self.authority + path
        response = self.get_session().get(url)
        return response.json()['data']['rate']['AXCNH']

    def get_AXCNH_Wallet(self) -> Optional[Dict]:
        """获取AXCNH钱包信息"""
        path = 'crypto/wallets?channel_chain_id=MATIC'
        url = self.authority + path
        response = self.get_session().get(url)
        wallet_list = response.json()['data']['list']

        for wallet in wallet_list:
            if wallet['currency'] == self.wallet:
                print('付款账户为：', self.wallet)
                return wallet
        return None

    def for_currency_get_fei(self, currency: str) -> Optional[float]:
        """获取指定货币的汇率"""
        try:
            path = f'crypto/get-fiat-rate?from_currency=AXCNH&to_currency={currency}'
            url = self.authority + path
            response = self.get_session().get(url)
            response.raise_for_status()
            data = response.json()

            if 'data' in data:
                return float(data['data'])
            else:
                print(f"Currency {currency}: Missing 'data' in response - {data}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error getting rate for {currency}: {e}")
            return None

    def get_payee_fee(self, currency: str) -> Optional[str]:
        """获取收款人ID"""
        try:
            path = f"crypto/payee/fiat?currency={currency}&payee_name=&page=1&take=100&status=active"
            url = self.authority + path
            response = self.get_session().get(url)
            data = response.json()

            if 'data' in data and data['data']['list']:
                return data['data']['list'][0]['id']
            else:
                print(f"Currency {currency}: No payee found in response - {data}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error getting payee for {currency}: {e}")
            return None

    def get_value(self, currency: str) -> Optional[Tuple[float, float, float, float]]:
        """计算货币的边界值"""
        rate = self.for_currency_get_fei(currency)

        if not rate:
            print(f"无法获取 {currency} 的汇率")
            return None

        if currency not in self.count:
            print(f"货币 {currency} 不在配置列表中")
            return None

        min_boundary = (self.count[currency][0] - 0.01) / rate
        max_boundary = (self.count[currency][1] + 0.01) / rate
        min_normal = self.count[currency][0] / rate
        max_normal = self.count[currency][1] / rate

        return min_boundary, max_boundary, min_normal, max_normal

    def get_body_dict(self, currency: str, index: int) -> Optional[Dict]:
        """构建请求体字典"""
        values = self.get_value(currency)
        if not values:
            return None

        value = values[index]
        to_currency_rate = self.for_currency_get_fei(currency)
        payee_id = self.get_payee_fee(currency)
        wallet_info = self.get_AXCNH_Wallet()

        if not wallet_info or 'id' not in wallet_info:
            raise ValueError("无法获取钱包ID")

        if not payee_id:
            raise ValueError("无法获取收款人ID")

        wallet_id = wallet_info['id']
        to_currency_amount = value * to_currency_rate

        return {
            "to_currency_rate": to_currency_rate,
            "to_currency_amount": to_currency_amount,
            "access_code": "123456",
            "amount": value,
            "check_method": "email",
            "payee_id": payee_id,
            "wallet_id": wallet_id,
            "memo": "gift",
            "attachments": []
        }

    def fiat_transfer_out(self, currency: str, index: int) -> Dict:
        """执行法币转账"""
        path = 'crypto/fiat-transfer-out'
        url = self.authority + path

        body_data = self.get_body_dict(currency, index)
        if not body_data:
            return {"error": "无法构建请求体"}

        try:
            response = self.get_session().post(url, json=body_data)

            result = {
                "status_code": response.status_code,
                "request_data": body_data,
                "response_text": response.text
            }

            if response.status_code == 201:
                print(f'请求成功: {response.status_code}')
                print(f'请求结果为: {body_data}')
                print(f'请求参数为to_currency_amount: {body_data.get("to_currency_amount")}')
                print(f"响应内容: {response.text}")
                print("=" * 40)
            else:
                print(f"请求失败，状态码: {response.status_code}")
                print(f'请求参数为to_currency_amount: {body_data.get("to_currency_amount")}')
                print(f'请求结果为: {body_data}')
                print(f"响应内容: {response.text}")
                print("=" * 40)

            return result
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {e}")
            return {"error": str(e)}


# 索引常量定义，提高可读性
BOUNDARY_MIN = 0  # 边界最小值
BOUNDARY_MAX = 1  # 边界最大值
NORMAL_MIN = 2  # 正常最小值
NORMAL_MAX = 3  # 正常最大值

if __name__ == '__main__':
    pay_ment = PayMent()

    # 测试单个货币
    currency = 'ZAR'
    print(f'目前操作的是: {currency}')

    print('执行边界最小值')
    pay_ment.fiat_transfer_out(currency, BOUNDARY_MIN)

    print('执行正常最小值')
    pay_ment.fiat_transfer_out(currency, NORMAL_MIN)

    print('执行边界最大值')
    pay_ment.fiat_transfer_out(currency, BOUNDARY_MAX)

    print('执行正常最大值')
    pay_ment.fiat_transfer_out(currency, NORMAL_MAX)
