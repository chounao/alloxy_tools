import wallet_transaction_record

""""
验证资产看板的数据。

"""

class Demo:
    def __init__(self):
        self.wallet_transaction_count = wallet_transaction_record.WalletTransactionRecord()

    def save_function(self, from_currency=None, to_currency=None,
                      transaction_type=None, transaction_status=None, id_no=None, amount_field=None):

        transaction_data = self.wallet_transaction_count.get_wallet_transaction_record(
            from_currency=from_currency,
            to_currency=to_currency,
            transaction_type=transaction_type,
            transaction_status=transaction_status,
            id_no=id_no
        )
        if not transaction_data:
            return 0.0, 0.0

        total_amount = 0.0
        total_fee = 0.0
        num = 0
        for data in transaction_data:
            try:
                amount_str = data.get(amount_field)  # 使用动态字段名
                fee_str = data.get('fee')

                amount = float(amount_str) if amount_str and str(amount_str).strip() else 0.0
                fee = float(fee_str) if fee_str and str(fee_str).strip() else 0.0
                num += 1
                total_amount += abs(amount)
                total_fee += abs(fee)
            except (ValueError, TypeError) as e:

                continue
        print(f'{transaction_type}交易数量:',num)

        return total_amount, total_fee


    def from_usdc_data(self,transaction_type,amount_field):
        USDT_total_amount, USDT_total_fee = self.save_function(
            from_currency='USDC',
            transaction_type=transaction_type,
            transaction_status='pending',
            amount_field= amount_field
        )
        return USDT_total_amount, USDT_total_fee
    def from_usdt_data(self,transaction_type,amount_field):
        USDT_total_amount, USDT_total_fee = self.save_function(
            from_currency='USDT',
            transaction_type=transaction_type,
            transaction_status='pending',
            amount_field= amount_field
        )
        return USDT_total_amount, USDT_total_fee

    def to_usdc_data(self,transaction_type,amount_field):
        USDT_total_amount, USDT_total_fee = self.save_function(
            to_currency='USDC',
            transaction_type=transaction_type,
            transaction_status='pending',
            amount_field= amount_field
        )
        return USDT_total_amount, USDT_total_fee
    def to_usdt_data(self,transaction_type,amount_field):
        USDT_total_amount, USDT_total_fee = self.save_function(
            to_currency='USDT',
            transaction_type=transaction_type,
            transaction_status='pending',
            amount_field= amount_field
        )
        return USDT_total_amount, USDT_total_fee
    #链上充值
    def chain_deposit_data(self):
        to_usdt_amount, to_usdt_fee = self.to_usdt_data(transaction_type='chain_deposit_page',amount_field='amount')
        to_usdc_amount, to_usdc_fee = self.to_usdc_data(transaction_type='chain_deposit_page',amount_field='amount')



        return to_usdt_amount, to_usdt_fee, to_usdc_amount, to_usdc_fee
    #链上提现
    def chain_withdraw_data(self):
        to_usdt_amount, to_usdt_fee = self.to_usdt_data(transaction_type='chain_withdraw_page',amount_field='amount')
        to_usdc_amount, to_usdc_fee = self.to_usdc_data(transaction_type='chain_withdraw_page',amount_field='amount')

        return to_usdt_amount, to_usdt_fee, to_usdc_amount, to_usdc_fee
    #pay_in
    def pay_in_data(self):
        to_usdt_amount, to_usdt_fee = self.to_usdt_data(transaction_type='crypto_payin',amount_field='to_currency_amount')
        to_usdc_amount, to_usdc_fee = self.to_usdc_data(transaction_type='crypto_payin',amount_field='to_currency_amount')

        return to_usdt_amount, to_usdt_fee, to_usdc_amount, to_usdc_fee
    #pay_out
    def pay_out_data(self):
        from_usdt_amount, from_usdt_fee = self.from_usdt_data(transaction_type='crypto_payout',amount_field='amount')
        from_usdc_amount, from_usdc_fee = self.from_usdc_data(transaction_type='crypto_payout',amount_field='amount')

        return from_usdt_amount, from_usdt_fee, from_usdc_amount, from_usdc_fee
    #chenckout
    def check_out_data(self):
        to_usdt_amount, to_usdt_fee = self.to_usdt_data(transaction_type='checkout_withdraw',amount_field='amount')
        to_usdc_amount, to_usdc_fee = self.to_usdc_data(transaction_type='checkout_withdraw',amount_field='amount')

        return to_usdt_amount, to_usdt_fee, to_usdc_amount, to_usdc_fee
    #ryt_in
    def ryt_in_data(self):
        from_usdc_amount, from_usdc_fee = self.from_usdc_data(transaction_type='crypto_contract_in',amount_field='amount')

        return from_usdc_amount, from_usdc_fee
    #ryt_out
    def ryt_out_data(self):
        to_usdc_amount, to_usdc_fee = self.to_usdc_data(transaction_type='crypto_contract_out',amount_field='amount')

        return to_usdc_amount, to_usdc_fee
    def get_data(self):
        to_usdt_amount0, to_usdt_fee0, to_usdc_amount0, to_usdc_fee0 = self.chain_deposit_data()
        to_usdt_amount1, to_usdt_fee1, to_usdc_amount1, to_usdc_fee1 = self.chain_withdraw_data()
        to_usdt_amount2, to_usdt_fee2, to_usdc_amount2, to_usdc_fee2 = self.pay_in_data()
        from_usdt_amount3, from_usdt_fee3, from_usdc_amount3, from_usdc_fee3 = self.pay_out_data()
        to_usdt_amount4, to_usdt_fee4, to_usdc_amount4, to_usdc_fee4 = self.check_out_data()
        from_usdc_amount5, from_usdc_fee5 = self.ryt_in_data()
        to_usdc_amount6, to_usdc_fee6 = self.ryt_out_data()
        print(f'链上充值USDT金额:{to_usdt_amount0},手续费:{to_usdt_fee0}')
        print(f'链上充值USDC金额:{to_usdc_amount0},手续费:{to_usdc_fee0}')
        print(f'链上提现USDT金额:{to_usdt_amount1},手续费:{to_usdt_fee1}')
        print(f'链上提现USDC金额:{to_usdc_amount1},手续费:{to_usdc_fee1}')
        print(f'pay_in USDT金额:{to_usdt_amount2},手续费:{to_usdt_fee2}')
        print(f'pay_in USDC金额:{to_usdc_amount2},手续费:{to_usdc_fee2}')
        print(f'pay_out USDT金额:{from_usdt_amount3},手续费:{from_usdt_fee3}')
        print(f'pay_out USDC金额:{from_usdc_amount3},手续费:{from_usdc_fee3}')
        print(f'check_out USDT金额:{to_usdt_amount4},手续费:{to_usdt_fee4}')
        print(f'check_out USDC金额:{to_usdc_amount4},手续费:{to_usdc_fee4}')
        print(f'ryt_in USDC金额:{from_usdc_amount5},手续费:{from_usdc_fee5}')
        print(f'ryt_out USDC金额:{to_usdc_amount6},手续费:{to_usdc_fee6}')


        usdt =(to_usdt_amount0 + to_usdt_amount1 + to_usdt_amount2 + from_usdt_amount3 + to_usdt_amount4
               # to_usdt_fee0 +to_usdt_fee1 + to_usdt_fee2 + from_usdt_fee3 + to_usdt_fee4
               )
        print(f'USDT总金额:{usdt}')
        usdc = (to_usdc_amount0+to_usdc_amount1 + to_usdc_amount2 + from_usdc_amount3 + to_usdc_amount4 + from_usdc_amount5 +to_usdc_amount6
                # to_usdc_fee0+to_usdc_fee1 + to_usdc_fee2 + from_usdc_fee3 + to_usdc_fee4+from_usdc_fee5 + to_usdc_fee6
                )
        print(f'USDC总金额:{usdc}')
        num = usdt *1.000303 + usdc * 0.999946
        num = num + 1913065.11
        print(f'数字货币总资产:{num}')
if __name__ == '__main__':
    demo = Demo()
    demo.get_data()