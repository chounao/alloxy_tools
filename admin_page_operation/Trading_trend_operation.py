"""
交易趋势图：
on-ramp：法币充值的到账数量，包含手续费，换算为USD
off-ramp：加密付款的支付数量，包含手续费，换算为USD
AX-Card：卡消费 + 清算扣款 + 手续费 + 交易授权费，所有值为增量，遇到退款为 -xx 。
AX-Wallet：加密付款、链上充值、法币充值、链上提现、收单提现、RYT申购和赎回，包含手续费，换算为USD。
"""

from web_page_operation.wallet_function.wallet_transaction_record import WalletTransactionRecord
#获取p法币充值的到账数量，包含手续费，换算为USD
class TradingTrendOperation:
    def __init__(self):
        self.wallet_record = WalletTransactionRecord()
        self.currency = ['USDT','USDC']

    def get_pay_in_completed_transaction_record(self):
        pay_in_usda_data =0.0
        for i in self.currency:
            amount,fee = self.wallet_record.get_cim_transaction_summary(currency=i,transaction_type_name='法币充值')#获取数据
            usd = self.wallet_record.get_usd_data(i,amount)#转成 USD
            pay_in_usda_data += usd #两种币种相加
        print(f'法币充值金额 {pay_in_usda_data}')
        return pay_in_usda_data
    #获取加密付款的支付数量，包含手续费，换算为USD
    def get_pay_out_completed_transaction_record(self):
        pay_out_usda_data =0.0
        for i in self.currency:
            amount,fee = self.wallet_record.get_cim_transaction_summary(currency=i,transaction_type_name='加密付款')#获取数据
            usd = self.wallet_record.get_usd_data(i,amount+ fee)#转成 USD
            pay_out_usda_data += usd #两种币种相加
        print(f'加密付款金额 {pay_out_usda_data}')
        return pay_out_usda_data
    # 获取上充值的到账数量，包含手续费，换算为USD
    def get_chain_deposit_completed_transaction_record(self):
        chain_deposit_usda_data =0.0
        for i in self.currency:
            amount,fee = self.wallet_record.get_cim_transaction_summary(currency=i,transaction_type_name='链上充值')#获取数据
            usd = self.wallet_record.get_usd_data(i,amount)#转成 USD
            chain_deposit_usda_data += usd #两种币种相加
        print(f'链上充值金额 {chain_deposit_usda_data}')
        return chain_deposit_usda_data
    #链上提现的到账数量，包含手续费，换算为USD
    def get_chain_withdraw_completed_transaction_record(self):
        chain_withdraw_usda_data =0.0
        for i in self.currency:
            amount,fee = self.wallet_record.get_cim_transaction_summary(currency=i,transaction_type_name='链上提现')#获取数据
            usd = self.wallet_record.get_usd_data(i,amount)#转成 USD
            chain_withdraw_usda_data += usd #两种币种相加
        print(f'链上提现金额 {chain_withdraw_usda_data}')
        return chain_withdraw_usda_data
    #收单提现的到账数量，包含手续费，换算为USD
    def get_checkout_withdraw_completed_transaction_record(self):
        checkout_withdraw_usda_data =0.0
        for i in self.currency:
            amount,fee = self.wallet_record.get_cim_transaction_summary(currency=i,transaction_type_name='商户提现')#获取数据
            usd = self.wallet_record.get_usd_data(i,amount+fee)#转成 USD
            checkout_withdraw_usda_data += usd #两种币种相加
        print(f'收单提现金额 {checkout_withdraw_usda_data}')
        return checkout_withdraw_usda_data
    #RYT申购的到账数量，包含手续费，换算为USD
    def get_ryt_crypto_contract_in_transaction_record(self):
        ryt_crypto_contract_in_usda_data =0.0
        for i in self.currency:
            amount,fee = self.wallet_record.get_cim_transaction_summary(currency=i,transaction_type_name='申购')#获取数据
            usd = self.wallet_record.get_usd_data(i,amount)#转成 USD
            ryt_crypto_contract_in_usda_data += usd #两种币种相加
        print(f'RYT申购金额 {ryt_crypto_contract_in_usda_data}')
        return ryt_crypto_contract_in_usda_data
    # 获取 RYT赎回金额，包含手续费，换算为USD
    def get_ryt_crypto_contract_out_transaction_record(self):
        yt_crypto_contract_out_usda_data =0.0
        for i in self.currency:
            amount,fee = self.wallet_record.get_cim_transaction_summary(currency=i,transaction_type_name='赎回')#获取数据
            usd = self.wallet_record.get_usd_data(i,amount)#转成 USD
            yt_crypto_contract_out_usda_data += usd #两种币种相加
        print(f'RYT赎回金额 {yt_crypto_contract_out_usda_data}')
        return yt_crypto_contract_out_usda_data
    #执行所有的数据
    def get_all_data(self):
        pay_in_usda_data = self.get_pay_in_completed_transaction_record()
        pay_out_usda_data = self.get_pay_out_completed_transaction_record()
        chain_deposit_usda_data = self.get_chain_deposit_completed_transaction_record()
        chain_withdraw_usda_data = self.get_chain_withdraw_completed_transaction_record()
        checkout_withdraw_usda_data = self.get_checkout_withdraw_completed_transaction_record()
        ryt_crypto_contract_in_usda_data = self.get_ryt_crypto_contract_in_transaction_record()
        yt_crypto_contract_out_usda_data = self.get_ryt_crypto_contract_out_transaction_record()

if __name__ == '__main__':
    trading_trend_operation = TradingTrendOperation()
    trading_trend_operation.get_all_data()

