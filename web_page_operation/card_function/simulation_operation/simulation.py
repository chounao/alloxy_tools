import json

import requests
import common.logger
from common import read_and_save_tool
from amount_calculation import AmountCalculation
logger = common.logger.logger
class SimulationOperation:
    """
    模拟操作消耗
    """

    def __init__(self):
        #初始化
        self.config = read_and_save_tool.ConfigTools()
        self.logger = common.logger.logger
        self.amount_calculation = AmountCalculation()
        # 环境配置 - 添加 None 检查
        self.cardID = self.amount_calculation.cardID if hasattr(self.amount_calculation,
                                                                'cardID') and self.amount_calculation.cardID is not None else None
        self.id = self.amount_calculation.id if hasattr(self.amount_calculation,
                                                        'id') and self.amount_calculation.id is not None else None
        self.amount = self.amount_calculation.amount if hasattr(self.amount_calculation,
                                                                'amount') and self.amount_calculation.amount is not None else 0.0  # 消费的金额
        self.refund_amount = self.amount_calculation.refund_amount if hasattr(self.amount_calculation,
                                                                              'refund_amount') and self.amount_calculation.refund_amount is not None else 0.0  # 退款金额
        self.reversal_amount = self.amount_calculation.reversal_amount if hasattr(self.amount_calculation,
                                                                                  'reversal_amount') and self.amount_calculation.reversal_amount is not None else 0.0  # 撤销的金额
        # 请求头配置
        self.headers = {
            "accept": "application/json",
            "Accept-Version": "v1.0",
            "content-type": "application/json",
            "x-reap-api-key": "uymf84as61ztqstfxmpn58pkd",
            #'x-reap-api-key':'jr8o9rb88cpbst1ykbuszy2ox',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6',
        }

        # 初始化会话
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.base_url = "https://sandbox.api.caas.reap.global"

    def authorisation(self):
        # 验证必要参数
        if self.cardID is None:
            raise ValueError("cardID 不能为空")
        if self.amount is None:
            raise ValueError("amount 不能为空")
        """消费"""
        url = f"{self.base_url}/simulate/authorisation"
        payload = {
            "cardID": self.cardID,
            "billAmount": self.amount,
            "transactionCurrency": "344"
        }
        # 修复：移除手动json.dumps，让requests自动处理
        response = self.session.post(url, json=payload)
        print('消费操作')
        print(f"响应内容: {response.text}")
        print(f"响应时间: {response.elapsed.total_seconds()}秒")


        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f"请求失败: {response.status_code} - {response.text}")

        try:
            transaction_id = response.json().get('id')
            if not transaction_id:
                raise ValueError("未获取到有效的交易ID")
            self.amount_calculation.authorisation_calculate()
            return transaction_id
        except ValueError as e:
            self.logger.error(f"JSON解析失败: {e}")
            raise

    def settlement(self, transaction_id):
        """清算"""
        try:
            url = f"{self.base_url}/simulate/{transaction_id}/clearing"
            payload = {
                "transactionAmount": 5,"transactionCurrency": "344"

            }
            response = self.session.post(url, json=payload)
            response.raise_for_status()

            print("清算")
            print(response.text)

        except Exception as e:
            print(f"清算操作失败: {e}")

    def refund(self, transaction_id):
        """退款"""
        # 验证参数
        if self.refund_amount is None:
            raise ValueError("refund_amount 不能为空")

        try:
            url = f"{self.base_url}/simulate/{transaction_id}/refund"
            payload = {
                "billAmount": self.refund_amount
            }
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            self.amount_calculation.refund_calculate()
        except Exception as e:
            print(f"退款操作失败: {e}")

    def reversal(self, transaction_id):
        """撤销"""
        if self.reversal_amount is None:
            raise ValueError("reversal_amount 不能为空")
        try:
            url = f"{self.base_url}/simulate/{transaction_id}/reversal"
            payload = {
                "billAmount": self.reversal_amount,"transactionCurrency": "344"
            }
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            self.amount_calculation.reversal_calculate()
        except Exception as e:
            print(f"撤销操作失败: {e}")

    def get_authorisation_list(self):
        """查询消费列表"""
        try:
            url = f"{self.base_url}/cards/{self.cardID}/transactions"
            response = self.session.get(url)
            response.raise_for_status()

            items = response.json().get('items', [])
            total_amount = 0

            for item in items:
                if 'transaction_amount' in item:
                    try:
                        total_amount += float(item['transaction_amount'])
                    except ValueError:
                        print(f"警告: 无法转换交易金额: {item['transaction_amount']}")
                else:
                    print(f"警告: 跳过缺少 transaction_amount 的项目: {item}")

            print(f"总金额: {total_amount}")

        except Exception as e:
            print(f"查询消费列表失败: {e}")


if __name__ == '__main__':
    simulation_operation = SimulationOperation()


    #消费
    try:
        transaction_id = simulation_operation.authorisation()
        if transaction_id:
            pass
    except Exception as e:
        print(f"程序执行出错: {e}")

    #撤销
    # try:
    #
    #     # transaction_id = simulation_operation.authorisation()
    #     transaction_id = 'tid_PHHgqW0CxS'
    #     if transaction_id:
    #         simulation_operation.reversal(transaction_id)
    # except Exception as e:
    #     print(f"程序执行出错: {e}")



    # #退款
    # try:
    #     # transaction_id = simulation_operation.authorisation()
    #     transaction_id = 'tid_PHHgqW0CxS'
    #     if transaction_id:
    #         # simulation_operation.settlement(transaction_id)
    #         simulation_operation.refund(transaction_id)
    # except Exception as e:
    #     print(f"程序执行出错: {e}")
    #
