
from common.simple_request import HttpRequest
from common import read_and_save_tool
from common.get_time import GetTime
from common import logger
logger = logger.logger
import json
import os
"""
admin后台-pay_out操作
"""

class AdminPayOutPage:
    def __init__(self, http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()

        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.get_time = GetTime()
    def get_pay_out_order_info(self,status,date):
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

            url = self.config_url + f'/admin/crypto/crypto-to-cash?page={page}&take=100&approval_status={status}&created_at[]={start_time}&created_at[]={end_time}'
            transaction_data = self.http_request.gets(url,nested_keys=['data','list'])
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

        with open(f'pay_out_{date}.json', 'w', encoding='utf-8') as f:
            json.dump(all_transaction_data, f, ensure_ascii=False, indent=4)
        # 返回保存的路径
        if not hasattr(self, 'save_path'):
            self.save_path = os.getcwd()
        save_path = os.path.join(self.save_path, f'pay_out_{date}.json')
        print(save_path)
        return save_path, all_transaction_data

    # def get_pay_out_order_info(self, status, date, page=1, take=100):
    #     """
    #     获取充值订单信息及分页信息
    #     :param status: 订单状态
    #     :param date: 日期
    #     :param page: 页码，默认为1
    #     :param take: 每页数量，默认为100
    #     :return: dict 包含数据列表和分页信息
    #     """
    #     start_time, end_time = get_month_range(date)
    #     url = self.config_url + f'/admin/crypto/crypto-to-cash?page={page}&take={take}&approval_status={status}&created_at[]={start_time}&created_at[]={end_time}'
    #
    #     data_list = self.http_request.gets(url, nested_keys=['data', 'list'])
    #     total_count = self.http_request.gets(url, nested_keys=['data', 'count'])
    #     if not isinstance(total_count, (int, float)) or total_count is None:
    #         total_count = 0
    #     total_pages = (total_count + take - 1) // take  # 向上取整计算总页数
    #     print(len(data_list))
    #     return {
    #         'data': data_list,
    #         'pagination': {
    #             'current_page': page,
    #             'per_page': take,
    #             'total_count': total_count,
    #             'total_pages': total_pages
    #         }
    #     }

    def get_pay_out_list(self,from_currency,to_currency,memo):
        url = self.config_url + '/admin/crypto/crypto-to-cash?page=1&take=100'
        jsonpath_expr_str = f'''
                $.data.list[?(@.from_currency == "{from_currency}" && 
               @.to_currency == "{to_currency}" && 
               @.status == "{memo}")].id_no
                    '''
        id_no = self.http_request.get(url,nested_keys=['data','list',0,'id_no'])
        if id_no:
            return id_no
        else:
            print('未找到符合条件的id_no')
            return None
    def admin_pay_out(self,id_no,status):
        set_status = ''
        if status == '通过':
            set_status = 'admin_completed'
        elif status == '拒绝':
            set_status = 'admin_rejected'
        url = self.config_url + '/admin/crypto/approval-crypto-to-cash'
        data = {
            'id_no': id_no,
            'approval_remarks': 'test',
            'approval_status': set_status
        }
        response = self.http_request.post(url,data)
        return response



if __name__ == '__main__':
    amount = 100
    to_currency = 'KES'
    from_currency = 'USDT'
    memo = 'housing'
    #执行创建pay_out操作
    pay_out = AdminPayOutPage()
    # pay_out.fiat_transfer_out(amount,from_currency,to_currency, memo)
    #
    # #执行admin pay_out操作
    # admin_pay_out = AdminPayOutPage()
    # id_no = admin_pay_out.get_pay_out_list(from_currency,to_currency,memo)
    # # print(id_no)
    # admin_pay_out.admin_pay_out(id_no,'拒绝')
    pay_out_order_info = pay_out.get_pay_out_order_info(status='admin_completed', date='202509')
    print(pay_out_order_info)


