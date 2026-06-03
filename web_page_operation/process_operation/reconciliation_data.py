from common.simple_request import HttpRequest
from common import get_time, read_and_save_tool


class ReconciliationData:
    """
    对账操作
    """
    def __init__(self, user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        # self.authority = self.config.get_value('TEST_CONFIG', 'URL')
        self.time = get_time.get_current_month_range()


    def get_wallet_data(self,wallet_currency):
        """
        钱包-获取钱包列表
        :param wallet_currency: 钱包币种
        :return:
        """

        # wallet_url = self.authority + "/web/crypto/wallets"
        # wallet_data = self.http_request.get(wallet_url, jsonpath_expr=f'$.data.list[?(@.currency=="{wallet_currency}")]')
        wallet_data = self.http_request.send_request(api_name='钱包-获取钱包列表', jsonpath_expr=f'$.data.list[?(@.currency=="{wallet_currency}")]')
        wallet_price = float(wallet_data['price'])
        wallet_amount = wallet_data['amount']
        print(f'钱包{wallet_currency}余额为：',wallet_amount)
        print(f'钱包{wallet_currency}price为：',wallet_price)
        return wallet_price, wallet_price

    def get_wallet_reconciliation_data(self,from_currency=None, to_currency=None,
                               transaction_type=None, transaction_status=None):
        """
        钱包-交易记录
        :param from_currency: 转入币种:USDC/USDT
        :param to_currency: 转出币种:USDC/USDT
        :param transaction_type: 交易类型:crypto_payin 法币充值
                                        chain_deposit_page 链上充值
                                        crypto_exchange_in 加密转入
                                        crypto_exchange_out 加密转出
                                        chain_withdraw_page 链上提现
                                        crypto_payout 加密付款
                                        failed_refund 失败退款
        :param transaction_status: 交易状态:completed/failed/pending
        :return:
        """
        # 基础URL和必须的参数
        #base_url = f"{self.authority}/web/crypto/transaction?page=1&take=20"
        # 动态构建参数列表
        params = []
        # 只添加非空参数
        # if from_currency:
        #     params.append(f"from_currency={from_currency}")
        # if to_currency:
        #     params.append(f"to_currency={to_currency}")
        # if transaction_type:
        #     params.append(f"transaction_type={transaction_type}")
        # if transaction_status:
        #     params.append(f"transaction_status={transaction_status}")
        # 组合完整URL
        # reconciliation_url = base_url + "&" + "&".join(params)
        params_data ={
            'page':1,
            'take':20,
            'create_at[]':self.time[0],
            'create_at[]':self.time[1],

        }
        if from_currency:
            params_data['from_currency'] = from_currency
        if to_currency:
            params_data['to_currency'] = to_currency
        if transaction_type:
            params_data['transaction_type'] = transaction_type
        if transaction_status:
            params_data['transaction_status'] = transaction_status



        reconciliation_data = self.http_request.send_request(api_name='钱包-交易记录',dict_data=params_data, nested_keys=['data','list'])
        # print(reconciliation_data)
        # print(reconciliation_data['amount'])
        # print(reconciliation_data['fee'])
        # for i in reconciliation_data:
        #     print(i['amount'])
        #     print(i['fee'])
        return reconciliation_data

    def get_wallet_count_for_pay_out(self, transaction_status):
        """
        获取pay_out金额
        :return:
        """
        data = self.get_wallet_reconciliation_data(transaction_type='crypto_payout',
                                                   transaction_status=transaction_status)
        amount = 0
        fee = 0
        wallet_amount = 0
        for i in data:
            amount += float(i['amount'])
            fee += float(i['fee'])
            # print('充值金额:', amount, '充值手续费:', fee)
            wallet_amount = amount + fee
        print('钱包余额:', wallet_amount)
        return wallet_amount

    def get_wallet_count_for_chain_withdraw(self, wallet_currency, transaction_status):
        """
        获取chain_withdraw金额转出
        :return:
        """
        data = self.get_wallet_reconciliation_data(from_currency=wallet_currency,
                                                   transaction_type='chain_withdraw_page',
                                                   transaction_status=transaction_status)
        amount = 0
        fee = 0
        wallet_amount = 0
        for i in data:
            amount += float(i['amount'])
            fee += float(i['fee'])
            # print('充值金额:', amount, '充值手续费:', fee)
            wallet_amount = amount + fee
        print('钱包余额:', wallet_amount)
        return wallet_amount

    def get_wallet_count_for_crypto_payin(self, wallet_currency, transaction_status):
        """
        获取crypto_payin金额
        :return:
        """
        data = self.get_wallet_reconciliation_data(
            to_currency=wallet_currency,
            transaction_type='crypto_payin',
            transaction_status=transaction_status)
        amount = 0
        fee = 0
        wallet_amount = 0
        for i in data:
            amount += float(i['amount'])
            fee += float(i['fee'])
            wallet_amount = amount - fee
        print('钱包余额:', wallet_amount)
        return wallet_amount

    def get_wallet_count_for_chain_deposit(self, wallet_currency, transaction_status):
        """
        获取chain_deposit金额
        :return:
        """
        data = self.get_wallet_reconciliation_data(
            from_currency=wallet_currency,
            transaction_type='chain_deposit_page',
            transaction_status=transaction_status)
        amount = 0
        fee = 0
        wallet_amount = 0
        for i in data:
            amount += float(i['amount'])
            fee += float(i['fee'])

            wallet_amount = amount - fee
        print('钱包余额:', wallet_amount)
        return wallet_amount


    def get_order_reconciliation_data(self,status=None):
        """
        获取订单列表
        :param status: 交易状态:
                            open 进行中
                            close 已过期
                            done 已完成
                            withdraw_pending 待审核
                            withdraw_rejected 已拒绝
                            withdraw_completed 已完成
        :return:
        """
        # base_url = f"{self.authority}/web/checkout_page/order?page=1&take=20"
        # params = []
        #
        # # 添加时间参数（必须）
        # params.append(f"create_at[]={self.time[0]}")
        # params.append(f"create_at[]={self.time[1]}")
        # if status:
        #     params.append(f"status={status}")
        # reconciliation_url = base_url + "&" + "&".join(params)
        params_data = {
            'page': 1,
            'take': 20,
            'create_at[]': self.time[0],
            'create_at[]': self.time[1],

        }
        if status:
            params_data['status'] = status

        reconciliation_data = self.http_request.send_request(api_name='获取订单列表', dict_data=params_data, nested_keys=['data','list'])
        # for i in reconciliation_data:
        #     print(i['amount'])
        #     print(i['fee'])
        return reconciliation_data
    def get_ryt_data(self):
        """
        获取 ryt 余额
        :return:
        """
        base_url = self.config_url + "/web/contract/getContractAccountInfo"
        ryt_Balance = self.http_request.get(base_url, nested_keys=['data','num'])  # ryt 余额
        print(f'ryt 余额为：',ryt_Balance)

    def get_ryt_reconciliation_data(self,business_type=None):
        """
        获取 ryt 对账数据
        :param business_type: 业务类型:
                                1 购入crypto_contract_in
                                2 购入失败
                                3 赎回crypto_contract_out
                                4 赎回失败failed_refund

        :return:
        """
        base_url = self.config_url + "/web/contract/getRytTransactionList?page=1&take=20"
        params = []

        # 添加时间参数（必须）
        params.append(f"create_at[]={self.time[0]}")
        params.append(f"create_at[]={self.time[1]}")

        # 只添加非空参数
        if business_type:
            params.append(f"business_type={business_type}")
        reconciliation_url = base_url + "&" + "&".join(params)
        ryt_reconciliation_data = self.http_request.get(reconciliation_url,nested_keys=['data','list'])
        # for i in ryt_reconciliation_data:
        #     print(i['amount'])
        #     print(i['fee'])
        return ryt_reconciliation_data

    def get_RYT_failed_refund_data(self, wallet_currency):
        """
        获取 RYT 失败退款数据
        :param wallet_currency: 钱包币种 (如 USDT, USDC)
        :return: 钱包余额
        """
        data = self.get_ryt_reconciliation_data(business_type='failed_refund')
        # print(data)
        amount = 0
        fee = 0
        wallet_amount = 0
        if isinstance(data, list):
            failed_data = [
                item for item in data
                if isinstance(item, dict) and
                   (item.get('from_currency') == wallet_currency and
                    item.get('to_currency') == wallet_currency)
            ]
            # print(f'方法1 - 过滤后的失败退款数据为：', failed_data)

            for i in failed_data:
                amount += float(i['amount'])
                fee += float(i['fee'])
                wallet_amount = amount + fee
        print(f'{wallet_currency}钱包余额:', wallet_amount)

        return wallet_amount

    def get_RYT_crypto_contract_out(self):
        data = self.get_ryt_reconciliation_data(business_type='crypto_contract_out')
        amount = 0
        fee = 0
        wallet_amount = 0
        for i in data:
            amount += float(i['amount'])
            fee += float(i['fee'])
            wallet_amount = amount - fee
        print(f'钱包余额:', wallet_amount)

        return wallet_amount

    def get_RYT_crypto_contract_in(self):
        data = self.get_ryt_reconciliation_data(business_type='crypto_contract_in')
        amount = 0
        fee = 0
        wallet_amount = 0
        for i in data:
            amount += float(i['amount'])
            fee += float(i['fee'])
            wallet_amount = amount + fee
        print(f'钱包余额:', wallet_amount)

        return wallet_amount
    def get_card_balance(self):
        """
        获取卡余额
        获取虚拟卡总余额和卡账户总余额
        :return:
        """
        # base_url = self.authority + "/web/virtual-card/card-balance"
        balance = self.http_request.send_request(api_name='获取虚拟卡总余额和卡账户总余额', nested_keys=['data'])
        card_AccountBalance = balance['cardAccountBalance']  # 账户余额
        card_Balance = balance['cardBalance']  # 卡内余额
        print(f'商务卡账户余额为：',card_AccountBalance)
        print(f'商务卡卡内余额为：',card_Balance)
        return card_AccountBalance, card_Balance
    def get_card_reconciliation_data(self,transaction_type=None,status=None,transaction_sub_type=None):
        """
        获取商务卡对账数据
        获取交易列表
        :param transaction_type: 交易类型:cvcc_out 充值
                                        card_consume 消费
                                        card_payout 卡付款
                                        card_clearing 清算
                                        card_reversal 退回
                                        card_refund 退款
                                        vcc_in 充值
                                        vcc_out 转出
                                        card_transaction_authorization_fee 卡授权费
        :param status: 交易状态:completed/failed/pending
        :param transaction_sub_type: 交易子类型:card /card_account
        :return:
        """
        # base_url = f"{self.authority}/web/virtual-card/transtion-list?page=1&take=20"
        # params = []
        #
        # # 添加时间参数（必须）
        # params.append(f"create_at[]={self.time[0]}")
        # params.append(f"create_at[]={self.time[1]}")
        #
        # # 只添加非空参数
        # if transaction_sub_type:
        #     params.append(f"transaction_sub_type={transaction_sub_type}")
        # if transaction_type:
        #     params.append(f"transaction_type={transaction_type}")
        # if status:
        #     params.append(f"transaction_status={status}")
        #
        # # 组合完整URL
        # reconciliation_url = base_url + "&" + "&".join(params)
        params_data = {
            'page': 1,
            'take': 20,
            'create_at[]': self.time[0],
            'create_at[]': self.time[1],

        }
        if transaction_sub_type:
            params_data['transaction_sub_type'] = transaction_sub_type
        if transaction_type:
            params_data['transaction_type'] = transaction_type
        if transaction_type:
            params_data['transaction_type'] = transaction_type
        if status:
            params_data['status'] = status

        reconciliation_data = self.http_request.send_request(api_name='获取交易列表', dict_data=params_data, nested_keys=['data', 'list'])
        # for i in reconciliation_data:
        #     print(i['amount'])
        #     print(i['fee'])
        return reconciliation_data
    def get_card_deposit_data(self,wallet_currency,status):

        data = self.get_card_reconciliation_data(transaction_type='vcc_in',status=status,transaction_sub_type="card_account")
        print(f'{wallet_currency}充值数据:', data)
        amount = 0
        fee = 0
        wallet_amount = 0
        for i in data:
            if wallet_currency in i['description']:
                amount += float(i['amount'])
                wallet_amount = amount + fee
        print(f'{wallet_currency}充值数据:', wallet_amount)

        return wallet_amount






if __name__ == '__main__':
    reconciliation = ReconciliationData()
    reconciliation.get_wallet_data('USDC')
    # # 可以灵活调用，只传需要的参数
    reconciliation.get_wallet_reconciliation_data('USDC', 'USDC', None, 'completed')
    reconciliation.get_order_reconciliation_data(status='done')
    reconciliation.get_ryt_data()
    reconciliation.get_ryt_reconciliation_data(business_type='crypto_contract_in')
    reconciliation.get_card_balance()
    reconciliation.get_card_reconciliation_data(transaction_type='card_deposit', transaction_sub_type='card')
    reconciliation.get_wallet_count_for_pay_out( 'failed')



