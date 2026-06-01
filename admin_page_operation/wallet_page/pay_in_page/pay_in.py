from common.simple_request import HttpRequest
from common import read_and_save_tool
from web_page_operation.wallet_function.pay_in_operation.pay_in_process import PayInProcess
from common.get_time import GetTime
from common import logger
import os
import json
logger = logger.logger
"""
admin后台-pay_in操作
"""

class AdminPayInPage:
    def __init__(self, http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()

        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.get_time = GetTime()

    # 获取充值订单信息
    def get_pay_in_order_info(self,status,date):
        """
        获取充值订单信息
        :param status: 订单状态
        :param date: 日期
        :return: 充值订单信息
        """
        all_transaction_data = []
        page = 1

        while True:
            start_time, end_time = self.get_time.get_time_range(date)

            url = self.config_url + f'/admin/crypto/payin?page={page}&take=100&approval_status={status}&created_at[]={start_time}&created_at[]={end_time}'
            transaction_data = self.http_request.gets(url,nested_keys=['data','data'])
            if not transaction_data or len(transaction_data) == 0:  # 检查交易数据是否为空或长度为0，如果是则跳出循环
                break
            all_transaction_data.extend(transaction_data)
            # 检查是否有更多数据
            total_count = self.http_request.gets(url, nested_keys=['data', 'count'])
            if total_count and len(all_transaction_data) >= total_count:
                break

            page += 1

        logger.info(f"总共获取到{len(all_transaction_data)}条记录")
        # print(all_transaction_data)


        with open(f'pay_in_{date}.json', 'w', encoding='utf-8') as f:
            json.dump(all_transaction_data, f, ensure_ascii=False, indent=4)
        #返回保存的路径
        if not hasattr(self, 'save_path'):
            self.save_path = os.getcwd()
        save_path = os.path.join(self.save_path, f'pay_in_{date}.json')
        # print(save_path)
        return save_path,all_transaction_data


    def up_status(self,source_order_id, status):
        """
        更新订单状态
        :param source_order_id: 订单id
        :param status: 订单状态 ('success' 或 'failed')
        :return: 订单状态更新结果
        """
        url = self.config_url + '/web/crypto/yellow-card/webhook'

        # 准备数据
        data = {
            "id": source_order_id,
            "sequenceId": "nWNZ915HysILuR4s",
            "status": "processing",
            "apiKey": "1ff95e41cf69ebbb5b827ba2092853a3",
            "executedAt": 1754989692004
        }

        # 根据状态设置事件类型
        if status == 'success':
            data["event"] = "COLLECTION.SETTLEMENT_COMPLETE"
        else:
            data["event"] = "COLLECTION.FAILED"

        # 更新请求头并发送请求
        self.http_request.update_headers({'x-yc-signature': 'test666777888999test='})
        result = self.http_request.posts(url, data, nested_keys=['data'])

        print(f"订单 {source_order_id} 状态更新为 {status}: {result}")
        return result

    def up_status_by_id(self,transaction_id):
        url = self.config_url + '/admin/crypto/payin/approval'
        data = {
            'id': transaction_id,
            'opinion': 'test',
            'status': "completed"
        }
        result = self.http_request.posts(url, data)
        print(result)
if __name__ == '__main__':
    pay_in = PayInProcess()
    admin_pay_in = AdminPayInPage()


    """
    执行所有流程
    """
    # source_order_id,transaction_id = pay_in.pay_in(3000,'XAF', 'USDT',)
    # admin_pay_in.up_status(source_order_id, 'success')
    # admin_pay_in.up_status_by_id(transaction_id)


    """
    只执行三方会掉的订单状态更新
    """
    source_order_id = '20aeb2d7-aa02-5d05-b63d-6f7e36e85854'
    admin_pay_in.up_status(source_order_id, 'success')



    # admin_pay_in.get_pay_in_order_info(status='admin_completed',date='202612')