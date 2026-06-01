
from common.simple_request import HttpRequest
from common import read_and_save_tool


class ToCheckout:
    """
    对账操作
    """
    def __init__(self, http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()
        self.config = read_and_save_tool.ConfigTools()



    #创建提现订单
    def create_order(self,currency,amount,memo):
        """
                发送金额
                创建提现订单
                :param currency: 币种
                :param amount: 金额
                :param memo: 备注
                :return:
                """
        # method, url = self.config.get_data_from_name('创建提现订单')
        body = {"amount": amount, "memo": memo, "check_method": "email", "access_code": "123456", "currency": currency}
        self.http_request.send_request(api_name='创建提现订单', data=body, nested_keys=['data'])


    #h获取订单id
    def get_order_id(self,memo):
        """
        获取订单id
        :return:
        """
        dict_data = {
            "page":1,
            "take":20,
            "order_type":"withdraw"
        }
        #method, url = self.config.get_data_from_name('获取订单列表', typename='?page=1&take=20&order_type=withdraw')
        order = self.http_request.send_request(api_name='获取订单列表',dict_data=dict_data, jsonpath_expr='$.data.list[?(@.memo=="{}")]'.format(memo))
        print( order)
        # order_id = order[0]['merchant_trade_no']
        id_no= order[0]['id']
        print('当前订单id为：',id_no)
        return id_no

    # def callback_checkout(self,order_id):
    #     """
    #     回调检查
    #     :return:
    #     """
    #     # order_id = '1'
    #
    #     body = {
    #         "main_order": {
    #             "batch_id": order_id,
    #             "merchant_id": 12333543,
    #             "status": "SUCCESS",
    #             "client_id": "IEnVmNifZmIWJHXf",
    #             "pay_back_status": "NO",
    #             "channel_id": "二十世纪福克斯"
    #         },
    #         "suborders": [
    #             {
    #                 "merchant_id": 12333543,
    #                 "channel_id": "二十世纪福克斯",
    #                 "suborder_id": "35127272666562571",
    #                 "chain": "ARBEVM",
    #                 "address": "0xe06D79b2C626527AEA8CC2D46346283241D89D64",
    #                 "currency": "USDT",
    #                 "amount": "0.02997",
    #                 "fee": "0.05",
    #                 "tx_id": "0xde98bdef43f1cd6e1af2c4184091819eef3172955220c7c63ab7b8fddba12b72",
    #                 "memo": "",
    #                 "status": "DONE",
    #                 "merchant_withdraw_id": order_id,
    #                 "fee_type": 1,
    #                 "batch_withdraw_id": order_id,
    #                 "desc": "",
    #                 "reconciliation_status": 0,
    #                 "is_placed": 1,
    #                 "finish_time": 1753155263000,
    #                 "sub_amount": "0.07997",
    #                 "done_amount": "0.02997"
    #             }
    #         ]
    #     }
    #     body = json.dumps(body)
    #
    #
    #     response = self.session.post(self.url, body)
    #     print('回调状态码为：',response.status_code)
    #     print('回调响应内容为：',response.text)








