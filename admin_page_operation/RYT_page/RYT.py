from common.simple_request import HttpRequest
from common import read_and_save_tool
from web_page_operation.RYT_function import RYT_operation
from common.get_time import GetTime
from common import logger
logger = logger.logger
import json
import os


class AdminRYTPage:
    def __init__(self, admin_http=None):
        self.http_request = admin_http or HttpRequest(user_type='admin')
        self.config = read_and_save_tool.ConfigTools()
        self.rytoperation = RYT_operation.RYT_Operation()
        self.config_url = self.config.get_url_data()
        self.time = GetTime()

    def get_RYT_order_info(self,status,date,business_type):
        """
        获取RYT出金订单信息
        :param status: 订单状态
        :param date: 日期
        :return: RYT出金订单信息
        """
        all_transaction_data = []
        page = 1

        while True:
            start_time, end_time = self.time.get_time_range(date)

            url = self.config_url + f'/admin/contract/getRytTransactionList?page={page}&take=100&business_type={business_type}&start_time={start_time}&end_time={end_time}&process_status={status}'
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

        with open(f'RYT_{business_type}_{date}.json', 'w', encoding='utf-8') as f:
            json.dump(all_transaction_data, f, ensure_ascii=False, indent=4)
        #返回保存的路径
        if not hasattr(self, 'save_path'):
            self.save_path = os.getcwd()
        save_path = os.path.join(self.save_path, f'RYT_{business_type}_{date}.json')
        print(save_path)
        return save_path,all_transaction_data
    def admin_RYT(self,id_no,status):
        """
        状态：rejected
            completed
        管理员后台-审批RYT出金
        :param id_no: 订单id
        :return: 审批结果
        """
        set_status = None
        if status == '通过':
            set_status = 'completed'
        elif status == '拒绝':
            set_status = 'rejected'
        url = self.config.get_url_data() + '/admin/contract/approvalRytTransactionList'
        data = {
            'id_no': id_no,
            'process_status': set_status
        }
        result = self.http_request.post(url, data)
        print(result)
    def admin_RYT_in(self,amount,status):
        """
        管理员后台-审批RYT入金
        :param amount: 金额
        :return: 审批结果
        """
        id_no = self.rytoperation.buy_ryt(amount)
        self.admin_RYT(id_no,status)
        print('成功操作RYT入金')



    def admin_RYT_out(self,amount,status):
        """
        管理员后台-审批RYT出金
        :param amount: 金额
        :return: 审批结果
        """
        id_no = self.rytoperation.sell_ryt(amount)
        self.admin_RYT(id_no,status)
        print('成功操作RYT出金')

if __name__ == '__main__':
    admin_ryt = AdminRYTPage()
    # admin_ryt.admin_RYT_in(10,'通过')
    # admin_ryt.admin_RYT_out(1,'拒绝')
    admin_ryt.get_RYT_order_info('completed','202509','crypto_contract_in')

