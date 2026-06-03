
from common.simple_request import HttpRequest
from common.Sql import DatabaseConnection
from common import read_and_save_tool
from common.execute import set_env, get_env, get_config_section
from urllib.parse import urlparse, parse_qs

class AmountCalculation:
    """
    模拟操作消耗
    """

    def __init__(self, user_http=None, admin_http=None):
        self.user_http = user_http or HttpRequest(user_type='user')
        self.admin_http = admin_http or HttpRequest(user_type='admin')
        # 环境配置
        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.config_section = get_config_section()
        """
        需要修改的地方：  根据不同环境配置修改
                        self.account_id 后台：发展不错有限公司ID ：929ff175-e26b-43ad-ba02-467756bff867
                        self.cardID  dda32efd-bf58-4c58-a504-378b3f4aadf7
                        self.id 34cf86dc-b6f7-4c54-bcc1-a2e4a4c75b4c

        """
        # 配置参数 后四位7912


        if self.config_section == 'TEST_CONFIG':

            body='https://test.d1b76915868gf9.amplifyapp.com/app/card/detail?id=5b7060c8-cb88-456e-a4a2-b4d84afade61&bank_card_id=71862094-990f-4234-a150-8d3f87f58a64'
            parsed_url = urlparse(body)
            query_params = parse_qs(parsed_url.query)

            # 提取参数值（parse_qs返回的是列表，取第一个元素）
            result = {  
                "id": query_params.get("id", [None])[0],
                "bank_card_id": query_params.get("bank_card_id", [None])[0]
            }
            # print(result['id'], result['bank_card_id'])

            self.cardID = result['bank_card_id']  # 商务卡卡号的id
            self.id = result['id']  # 商务卡平台的id
            self.legal_name = "很有钱发展不错有限公司"
            self.account_id = '929ff175-e26b-43ad-ba02-467756bff867'  # admin 平台的id
        else:
            body = 'https://uat.alloyx-payment.net/app/card/detail?id=7079ad88-d1c1-4f38-8a5b-040c8e44de22&bank_card_id=cc4a5c8a-7b3d-46f1-98ae-11bf8d9255f2'
            parsed_url = urlparse(body)
            query_params = parse_qs(parsed_url.query)

            # 提取参数值（parse_qs返回的是列表，取第一个元素）
            result = {
                "id": query_params.get("id", [None])[0],
                "bank_card_id": query_params.get("bank_card_id", [None])[0]
            }
            self.cardID = result['bank_card_id']  # 商务卡卡号的id
            self.id = result['id']  # 商务卡平台的id
            self.legal_name = "AlloyX Limited"
            self.account_id = '6a7df467-da43-440a-84dc-9e3e86e9dccf'  # admin 平台的id



        self.amount =3 # 消费的金额
        self.refund_amount = 1.5  # 退款金额
        self.reversal_amount = 0.2  # 撤销的金额


        # 初始化数据库连接并获取汇率
        with DatabaseConnection() as db:
            result = db.execute_sql("SELECT rate FROM currency_rate c WHERE c.from_currency = 'HKD';")
            self.hkd_rate = float(result[0][0]) if result else 0.0
        # 获取后台设置的各种费率




        # 获取商务卡余额
        get_card_data_url = self.config_url+ '/web/virtual-card/card/{}'.format(self.id)
        try:
            self.card_data = float(self.http_request.get(
                url=get_card_data_url,
                nested_keys=['data', 'b_available']
            ))
        except (ValueError, TypeError, KeyError):
            self.card_data = 0.0
        # self.card_data = float('27.08860000')

        # 初始化各种费率
        self._initialize_fees()
        self.return_fee = 0.0


    def get_card_balance(self):
        """
        获取卡余额
        获取虚拟卡总余额和卡账户总余额
        :return:
        """
        # URL = self.authority + "/web/virtual-card/card-balance"
        balance = self.http_request.send_request(api_name='获取虚拟卡总余额和卡账户总余额',nested_keys=['data'])
        card_AccountBalance = balance['cardAccountBalance']  # 账户余额
        card_Balance = balance['cardBalance']  # 卡内余额
        return card_AccountBalance, card_Balance

    def _initialize_fees(self):
        """初始化各种手续费费率"""
        # self.enterprise_id = self.http_request.get(
        #     url=self.config_url + '/admin/account/get-account-fee-list?page=1&take=500',
        #     jsonpath_expr=f'$.data.list[0][?(@.legal_name=="{self.legal_name}")].id'
        # )
        # print(self.enterprise_id)
        # 获取amin后台设置url
        self.admin_url = self.config_url + '/admin/account/get-account-fee-list?page=1&take=10&account_id={}'.format(
            self.account_id)
        self.data = self.http_request.gets(
            url=self.admin_url,
            nested_keys=['data', 'list', 0]
        )
        # print(self.data)

        try:
            # 消费费率（本地）
            self.authorisation_per_rate = float(self.data.get('card_local_consume_fee_prorate', 0))
            self.authorisation_per_count = float(self.data.get('card_local_consume_fee_per_count', 0))

            # 退款费率
            self.refund_per_count = float(self.data.get('card_refund_fee_per_count', 0))
            self.refund_per_rate = float(self.data.get('card_refund_fee_prorate', 0))

            # 撤销费率
            self.reversal_per_count = float(self.data.get('card_reversal_fee_per_count', 0))
            self.reversal_per_rate = float(self.data.get('card_reversal_fee_prorate', 0))


            self.card_transaction_authorization_fee_per_count = float(self.data.get('card_transaction_authorization_fee_per_count', 0))
        except (ValueError, TypeError, KeyError) as e:
            print(f"费率初始化失败: {e}")
            #设置默认费率
            self.authorisation_per_rate = 0.003
            self.authorisation_per_count = 0.4
            self.refund_per_count = 0.0
            self.refund_per_rate = 0.0
            self.reversal_per_count = 0.0
            self.reversal_per_rate = 0.0

    def _calculate_fee(self, amount, rate, fixed_fee,authorisation_count = None):
        """计算手续费"""
        return amount * rate + fixed_fee +authorisation_count

    def _format_currency(self, amount):
        """格式化货币显示"""
        return f"{amount:.8f}"

    def authorisation_calculate(self):
        """消费"""
        card_AccountBalance, card_Balance = self.get_card_balance()

        # 费用计算
        card_balance_before = card_Balance
        card_data_before = self.card_data
        usd_amount = self.amount * self.hkd_rate  # 转换为USD
        fee = self._calculate_fee(usd_amount, self.authorisation_per_rate, self.authorisation_per_count,0)
        self.return_fee = self._calculate_fee(usd_amount, self.authorisation_per_rate, 0,0)
        total_amount = usd_amount + fee  # 计算总金额
        card_balance_after = card_Balance - total_amount - self.card_transaction_authorization_fee_per_count
        card_data_after = self.card_data - total_amount - self.card_transaction_authorization_fee_per_count




        # 打印详细信息
        print(f"消费 {usd_amount},百分比手续费{self.return_fee}")
        print(
            f'消费前卡账户余额 {self._format_currency(card_balance_before)}，卡余额 {self._format_currency(card_data_before)}')
        print(f'固定手续费 {self.authorisation_per_count}，比例手续费 {self.authorisation_per_rate}，授权费 {self.card_transaction_authorization_fee_per_count}')
        print(
            f'消费金额 {self._format_currency(usd_amount)}，入账金额 {self._format_currency(total_amount)}，手续费 {self._format_currency(fee)}')
        print(
            f'消费后卡账户余额 {self._format_currency(card_balance_after)}，卡余额 {self._format_currency(card_data_after)}')

    def refund_calculate(self):
        """退款"""

        card_AccountBalance, card_Balance = self.get_card_balance()

        # 费用计算
        card_balance_before = card_Balance
        card_data_before = self.card_data

        # 确保必要参数不为 None
        if self.refund_amount is None:
            raise ValueError("退款金额 (refund_amount) 不能为空")
        if self.amount is None:
            raise ValueError("原始消费金额 (amount) 不能为空")
        if self.hkd_rate is None or self.hkd_rate == 0:
            raise ValueError("汇率 (hkd_rate) 无效")

        usd_amount = self.refund_amount * self.hkd_rate  # 转换为USD
        authorisation_amount = self.amount * self.hkd_rate  # 消费的usd

        # 防止除零错误
        if authorisation_amount == 0:
            raise ValueError("原始消费金额不能为零")

        # 确保 return_fee 已初始化
        if self.return_fee is None:
            print("⚠️  警告: return_fee 未初始化，使用默认值 0.0")
            self.return_fee = 0.0

        refund_fee = self._calculate_fee(usd_amount, self.refund_per_rate, self.refund_per_count, 0)
        refund_authorisation_fee = usd_amount / authorisation_amount * self.return_fee
        all_fee = refund_fee - refund_authorisation_fee
        actual_amount = usd_amount - refund_fee + refund_authorisation_fee

        card_balance_after = 0.0
        card_data_after = 0.0
        if actual_amount <= 0:
            actual_amount = 0
            card_balance_after = card_Balance + actual_amount
            card_data_after = self.card_data + actual_amount
        else:
            card_balance_after = card_Balance + actual_amount
            card_data_after = self.card_data + actual_amount

        print(f"退款 {usd_amount}")
        print(
            f'退款前卡账户余额 {self._format_currency(card_balance_before)}，卡余额 {self._format_currency(card_data_before)}')
        print(f'固定手续费 {self.refund_per_count}，比例手续费 {self.refund_per_rate}')
        print(
            f'退款金额 {self._format_currency(usd_amount)}，入账金额 {self._format_currency(actual_amount)}，手续费 {self._format_currency(all_fee)},退款的手续费 {self._format_currency(refund_fee)}，需要退回的消费手续费 {self._format_currency(refund_authorisation_fee)}')
        print(
            f'退款后卡账户余额 {self._format_currency(card_balance_after)}，卡余额 {self._format_currency(card_data_after)}')


    def reversal_calculate(self):
        """撤销"""
        card_AccountBalance, card_Balance = self.get_card_balance()


        # 费用计算
        card_balance_before = card_Balance
        card_data_before = self.card_data
        usd_amount = self.reversal_amount * self.hkd_rate  # 转换为USD
        authorisation_amount = self.amount * self.hkd_rate  # 消费的usd
        reversal_fee = self._calculate_fee(usd_amount, self.refund_per_rate, self.refund_per_count, 0)  # 退款的手续费
        reversal_authorisation_fee = usd_amount / authorisation_amount * self.return_fee  # 退款退回消费手续费
        all_fee = reversal_fee - reversal_authorisation_fee  #
        actual_amount = usd_amount - reversal_fee + reversal_authorisation_fee
        if actual_amount <= 0:
            actual_amount = 0
            card_balance_after = card_Balance + actual_amount
            card_data_after = self.card_data + actual_amount
        else:
            card_balance_after = card_Balance + actual_amount
            card_data_after = self.card_data + actual_amount


        print(f"撤销 {usd_amount}")
        print(
            f'撤销前卡账户余额 {self._format_currency(card_balance_before)}，卡余额 {self._format_currency(card_data_before)}')
        print(f'固定手续费 {self.reversal_per_count}，比例手续费 {self.reversal_per_rate}')
        print(
            f'撤销金额 {self._format_currency(usd_amount)}，入账金额 {self._format_currency(actual_amount)}，手续费 {self._format_currency(all_fee)},撤销的手续费 {self._format_currency(reversal_fee)}，需要退回的消费手续费 {self._format_currency(reversal_authorisation_fee)}')
        print(
            f'撤销后卡账户余额 {self._format_currency(card_balance_after)}，卡余额 {self._format_currency(card_data_after)}')







if __name__ == '__main__':
    amount_calculation = AmountCalculation()
    amount_calculation._initialize_fees()
