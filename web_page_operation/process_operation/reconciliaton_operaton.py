from web_page_operation.process_operation import reconciliation_data

"""
期末余额=期初余额+（当月发生额）；
USD期初余额总计=USD钱包期初余额+USD数字商务卡期初余额+USD收单期初余额，其余总计公式同理；
钱包业务当月发生额=钱包账户充值+钱包账户入金+卡账户转入+收单提现-钱包账户转出-钱包账户出金-入金手续费-出金手续费；
卡账户业务当月发生额=卡账户充值+数字商务卡转入-开卡费-卡账户转出-卡账户充值手续费；
数字商务卡当月发生额=数字商务卡充值+数字商务卡退款-数字商务卡转出-数字商务卡消费-本地消费手续费-跨境消费手续费-撤销手续费；
收单业务当月发生额=收单金额-提现金额-提现手续费；
RYT业务当月发生额=购入金额+每日收益金额-赎回金额；
RYT币种与美元之间的汇率值取决于客户申请查看对账单的当下时间，具体到秒。
"""
class ReconciliationOperation():
    def __init__(self):
        self.reconciliation_data = reconciliation_data.ReconciliationData()


    def get_wallet_entry_data(self, wallet_currency):
        """
        获取入账的钱包数据
        :param wallet_currency: 钱包币种
        :return:
        """
        #1.付款/pay_out拒绝??法币
        wallet_count_pay_out_failed = self.reconciliation_data.get_wallet_count_for_pay_out(transaction_status='failed')
        print(wallet_count_pay_out_failed)
        # 2.获取pay_in金额 (已完成和进行中)
        wallet_count_crypto_payin_completed = self.reconciliation_data.get_wallet_count_for_crypto_payin(wallet_currency,transaction_status='completed')
        wallet_count_crypto_payin_pending = self.reconciliation_data.get_wallet_count_for_crypto_payin(wallet_currency,transaction_status='pending')
        wallet_count_crypto_payin = wallet_count_crypto_payin_completed + wallet_count_crypto_payin_pending
        print(wallet_count_crypto_payin)
        # 3.充值（法币充值） (已完成和进行中)
        wallet_count_chain_deposit_completed = self.reconciliation_data.get_wallet_count_for_chain_deposit(wallet_currency,transaction_status='completed')
        wallet_count_chain_deposit_pending = self.reconciliation_data.get_wallet_count_for_chain_deposit(wallet_currency,transaction_status='pending')
        wallet_count_chain_deposit = wallet_count_chain_deposit_completed + wallet_count_chain_deposit_pending
        print(wallet_count_chain_deposit)
        # 4. RYT - 购入拒接
        wallet_count_ryt_purchase_rejected = self.reconciliation_data.get_RYT_failed_refund_data('USDC')
        print(wallet_count_ryt_purchase_rejected)
        # 5. RYR - 赎回
        wallet_count_ryt_crypto_contract_out= self.reconciliation_data.get_RYT_crypto_contract_out()
        print(wallet_count_ryt_crypto_contract_out)
        # 6. 稳定币提现





    def get_wallet_expend_data(self, wallet_currency):
        """
        获取出账的钱包数据
        :param wallet_currency: 钱包币种
        :return:
        """
        # 1.付款/pay_out
        wallet_count_pay_out_completed = self.reconciliation_data.get_wallet_count_for_pay_out(
            transaction_status='completed')
        wallet_count_pay_out_pending = self.reconciliation_data.get_wallet_count_for_pay_out(
            transaction_status='pending')
        wallet_count_pay_out = wallet_count_pay_out_completed + wallet_count_pay_out_pending
        print(wallet_count_pay_out)

        # 2.转出
        wallet_count_wallet_transfer_completed = self.reconciliation_data.get_wallet_count_for_chain_withdraw(wallet_currency
        ,transaction_status='completed')
        wallet_count_wallet_transfer_pending = self.reconciliation_data.get_wallet_count_for_chain_withdraw(wallet_currency
        ,transaction_status='pending')
        wallet_count_wallet_transfer = wallet_count_wallet_transfer_completed + wallet_count_wallet_transfer_pending
        print(wallet_count_wallet_transfer)
        # 3. RYT 购入
        wallet_count_ryt_crypto_contract_in = self.reconciliation_data.get_RYT_crypto_contract_in()
        print(wallet_count_ryt_crypto_contract_in)

        # 4. RYT - 赎回拒绝
        wallet_count_ryt_crypto_contract_out= self.reconciliation_data.get_RYT_failed_refund_data('RYT')
        print(wallet_count_ryt_crypto_contract_out)

        # 5.商务卡充值(进行中/已完成)
        wallet_count_deposit_completed_data = self.reconciliation_data.get_card_deposit_data(wallet_currency,status='completed')
        wallet_count_deposit_pending_data = self.reconciliation_data.get_card_deposit_data(wallet_currency,status='pending')
        wallet_count_deposit = wallet_count_deposit_completed_data + wallet_count_deposit_pending_data
        print(wallet_count_deposit)

if __name__ == '__main__':
    reconciliation_operation = ReconciliationOperation()
    reconciliation_operation.get_wallet_expend_data('USDC')
