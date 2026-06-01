from web_page_operation.wallet_function.wallet_transaction_record import WalletTransactionRecord
import json
"""
计算不同交易类型和状态的金额和手续费
USD期初余额总计=USD钱包期初余额+USD数字商务卡期初余额+USD收单期初余额，其余总计公式同理；
钱包业务当月发生额=钱包账户充值+钱包账户入金+卡账户转入+收单提现-钱包账户转出-钱包账户出金-入金手续费-出金手续费；
"""


class WalletTransactionSummary():
    def __init__(self):
        self.wallet_record = WalletTransactionRecord()

    def wallet_transfer_in(self, currency, status,date):
        """
        法币充值，链上充值，加密转入
        :param currency: 币种
        :param status: 状态
        :return: 各种转入交易类型的总金额和手续费
        """

        # 获取所有转入类型的交易数据和汇总
        summary_data = self.wallet_record.get_all_transaction_summary(
            currency=currency,
            status=status,
            date=date

        )

        # 提取需要的转入类型数据
        crypto_payin = summary_data.get('法币充值', {}).get(currency, {}).get(status, {})
        chain_deposit = summary_data.get('链上充值', {}).get(currency, {}).get(status, {})
        card_account_to_wallet = summary_data.get('卡账户转入', {}).get(currency, {}).get(status, {})
        checkout_withdraw = summary_data.get('商户提现', {}).get(currency, {}).get(status, {})
        failed_refund = summary_data.get('失败退款', {}).get(currency, {}).get(status, {})
        redeem = summary_data.get('赎回', {}).get(currency, {}).get(status, {})
        system_recharge = summary_data.get('系统充值', {}).get(currency, {}).get(status, {})




        return {
            '法币充值': crypto_payin,
            '链上充值': chain_deposit,
            '卡账户转入': card_account_to_wallet,
            '商户提现': checkout_withdraw,
            '失败退款': failed_refund,
            '赎回': redeem,
            '系统充值': system_recharge
        }

    def wallet_transfer_out(self, currency, status, date):
        """
        加密转出, 链上提现, 加密付款, 失败退款
        :param currency: 币种
        :param status: 状态
        :return: 各种转出交易类型的总金额和手续费
        """

        # 获取所有转出类型的交易数据和汇总
        summary_data = self.wallet_record.get_all_transaction_summary(
            currency=currency,
            status=status,
            date=date
        )

        # 提取需要的转出类型数据

        chain_withdraw = summary_data.get('链上提现', {}).get(currency, {}).get(status, {})
        crypto_payout = summary_data.get('加密付款', {}).get(currency, {}).get(status, {})
        crypto_contract_in = summary_data.get('申购', {}).get(currency, {}).get(status, {})
        card_account_recharge = summary_data.get('卡账户充值', {}).get(currency, {}).get(status, {})
        system_deduction = summary_data.get('系统扣款', {}).get(currency, {}).get(status, {})




        return {
            '链上提现': chain_withdraw,
            '加密付款': crypto_payout,
            '申购': crypto_contract_in,
            '卡账户充值': card_account_recharge,
            '系统扣款': system_deduction
        }

    def get_wallet_business_amount(self, currency, status, date):
        """
        计算钱包业务当月发生额
        钱包业务当月发生额=钱包账户充值+钱包账户入金+卡账户转入+收单提现-钱包账户转出-钱包账户出金-入金手续费-出金手续费
        :param currency: 币种
        :param status: 状态
        :return: 钱包业务发生额相关各项数据
        """

        # 获取转入数据
        transfer_in_data = self.wallet_transfer_in(currency, status,date)

        # 获取转出数据
        transfer_out_data = self.wallet_transfer_out(currency, status, date)

        # 计算各项总金额（只统计实际金额，不包括手续费）
        # 正向金额（需要加上的）
        crypto_payin_amount = transfer_in_data['法币充值'].get('total_amount', 0)
        chain_deposit_amount = transfer_in_data['链上充值'].get('total_amount', 0)
        wallet_for_redeem_amount = transfer_in_data['赎回'].get('total_amount', 0)
        checkout_withdraw_amount = transfer_in_data['商户提现'].get('total_amount', 0)
        failed_refund_amount = transfer_in_data['失败退款'].get('total_amount', 0)
        card_to_wallet_deposit_amount = transfer_in_data['卡账户转入'].get('total_amount', 0)
        system_recharge_amount = transfer_in_data['系统充值'].get('total_amount', 0)



        crypto_payin_fee = transfer_in_data['法币充值'].get('total_fee', 0)
        chain_deposit_fee = transfer_in_data['链上充值'].get('total_fee', 0)
        wallet_for_redeem_fee = transfer_in_data['赎回'].get('total_fee', 0)
        checkout_withdraw_fee = transfer_in_data['商户提现'].get('total_fee', 0)
        failed_refund_fee = transfer_in_data['失败退款'].get('total_fee', 0)
        card_to_wallet_deposit_fee = transfer_in_data['卡账户转入'].get('total_fee', 0)



        # 负向金额（需要减去的）

        crypto_contract_in_amount= transfer_out_data['申购'].get('total_amount', 0)
        crypto_payout_amount = transfer_out_data['加密付款'].get('total_amount', 0)
        to_card_amount = transfer_out_data['卡账户充值'].get('total_amount', 0)
        chain_withdraw_amount = transfer_out_data['链上提现'].get('total_amount', 0)
        system_deduction_amount = transfer_out_data['系统扣款'].get('total_amount', 0)



        crypto_contract_in_fee = transfer_out_data['申购'].get('total_fee', 0)
        crypto_payout_fee = transfer_out_data['加密付款'].get('total_fee', 0)
        to_card_fee = transfer_out_data['卡账户充值'].get('total_fee', 0)
        chain_withdraw_fee = transfer_out_data['链上提现'].get('total_fee', 0)



        # 计算各种类型的金额
        # 链上充值 计算的是入账金额fee是正数 amount-fee
        wallet_for_chain_deposit = chain_deposit_amount - chain_deposit_fee

        # 法币充值 计算的是入账金额fee是正数 amount-fee
        wallet_for_crypto_payin = crypto_payin_amount - crypto_payin_fee

        # 加密付款 计算的是出账金额amount是负数，fee是正数，amount-fee 是出账金额 为负数
        wallet_for_crypto_payout = abs(crypto_payout_amount - crypto_payout_fee)

        # 链上提现 提现金额 amount是负数，fee是正数，amount-fee 是出账金额 为负数
        wallet_for_chain_withdraw = abs(chain_withdraw_amount - chain_withdraw_fee)

        # 失败退款 计算的是出账金额
        wallet_for_failed_refund = failed_refund_amount + failed_refund_fee

        # 收单提现 计算的是出账金额fee是正数 amount-fee
        wallet_for_checkout_withdraw = checkout_withdraw_amount-checkout_withdraw_fee

        #申购 计算的是入账金额 amount是负数，fee是正数，amount-fee 是出账金额 为负数
        wallet_for_crypto_contract_in = abs(crypto_contract_in_amount - crypto_contract_in_fee)

        # 赎回 计算的是入账金额 不含手续费fee是正数 amount-fee
        wallet_for_redeem = wallet_for_redeem_amount - wallet_for_redeem_fee

        # 卡账户充值 计算的是出账金额 amount是负数，fee是正数，amount-fee 是出账金额 为负数
        wallet_for_oo_card_deposit = abs(to_card_amount - to_card_fee)

        # 卡账户转入 充值入账金额
        wallet_for_card_to_wallet_deposit = card_to_wallet_deposit_amount - card_to_wallet_deposit_fee

        # 系统充值 计算的是入账金额
        wallet_for_system_recharge = system_recharge_amount

        # 系统扣款 计算的是出账金额 amount是负数，
        wallet_for_system_deduction = abs(system_deduction_amount)





        # 计算钱包业务当月发生额
        wallet_business_amount = (
            wallet_for_chain_deposit+
            wallet_for_crypto_payin-
            wallet_for_crypto_payout-
            wallet_for_chain_withdraw-
            wallet_for_failed_refund-
            wallet_for_checkout_withdraw-
            wallet_for_crypto_contract_in+
            wallet_for_redeem-
            wallet_for_oo_card_deposit+
            wallet_for_card_to_wallet_deposit+
            wallet_for_system_recharge-
            wallet_for_system_deduction

        )

        return {
            'wallet_business_amount': wallet_business_amount,
            'details': {
                'currency': currency,
                # 所有类型的不同的费用
                # 'fees': {
                #     '链上充值': chain_deposit_fee,
                #     '法币充值': crypto_payin_fee,
                #     '加密付款': crypto_payout_fee,
                #     '链上提现': chain_withdraw_fee,
                #     '失败退款': failed_refund_fee,
                #     '商户提现': checkout_withdraw_fee,
                #     '申购': crypto_contract_in_fee,
                #     '赎回': wallet_for_redeem_fee,
                #     '卡账户充值': to_card_fee,
                #     '卡账户转入': card_to_wallet_deposit_fee,
                #     # '系统充值': system_recharge_fee,
                #     # '系统扣款': system_deduction_fee,
                # },
                # 'amount':{
                #     '链上充值': chain_deposit_amount,
                #     '法币充值': crypto_payin_amount,
                #     '加密付款': crypto_payout_amount,
                #     '链上提现': chain_withdraw_amount,
                #     '失败退款': failed_refund_amount,
                #     '商户提现': checkout_withdraw_amount,
                #     '申购': crypto_contract_in_amount,
                #     '赎回': wallet_for_redeem_amount,
                #     '卡账户充值': to_card_amount,
                #     '卡账户转入': card_to_wallet_deposit_amount,
                #     '系统充值': system_recharge_amount,
                #     '系统扣款': system_deduction_amount,
                # },
                # #扣除手续费的金额
                # 'amounts': {
                #     '链上充值': wallet_for_chain_deposit,
                #     '法币充值': wallet_for_crypto_payin,
                #     '加密付款': wallet_for_crypto_payout,
                #     '链上提现': wallet_for_chain_withdraw,
                #     '失败退款': wallet_for_failed_refund,
                #     '商户提现': wallet_for_checkout_withdraw,
                #     '申购': wallet_for_crypto_contract_in,
                #     '赎回': wallet_for_redeem,
                #     '卡账户充值': wallet_for_oo_card_deposit,
                #     '卡账户转入': wallet_for_card_to_wallet_deposit,
                #     '系统充值': wallet_for_system_recharge,
                #     '系统扣款': wallet_for_system_deduction,
                # },
                # 'in':{
                #     'amount': {'链上充值': chain_deposit_amount,
                #                # '法币充值': crypto_payin_amount,
                #                '赎回': wallet_for_redeem_amount,'卡账户转入': card_to_wallet_deposit_amount,'系统充值': system_recharge_amount,
                #         '总金额': chain_deposit_amount+wallet_for_redeem_amount +card_to_wallet_deposit_amount+system_recharge_amount
                #     },
                #     'fee': {'链上充值': chain_deposit_fee,
                #             # '法币充值': crypto_payin_fee,
                #             '加密付款': crypto_payout_fee,'赎回': wallet_for_redeem_fee,'卡账户转入': card_to_wallet_deposit_fee,
                #
                #         '总金额': chain_deposit_fee+wallet_for_redeem_fee +card_to_wallet_deposit_fee
                #     }
                # },
                'out':{
                    'amount': {'加密付款': crypto_payout_amount,'链上提现': chain_withdraw_amount,'商户提现': checkout_withdraw_amount,'卡账户充值': to_card_amount,'系统扣款': system_deduction_amount,'申购': crypto_contract_in_amount,
                        '总金额': abs(crypto_payout_amount)+abs(chain_withdraw_amount)+abs(checkout_withdraw_amount)+abs(to_card_amount)+abs(system_deduction_amount)+abs(crypto_contract_in_amount)
                    },
                    'fee': {'加密付款': crypto_payout_fee,'链上提现': chain_withdraw_fee,'商户提现': checkout_withdraw_fee,'卡账户充值': to_card_fee,# '系统扣款': system_deduction_fee,
                            '申购': crypto_contract_in_fee,
                        '总金额': abs(crypto_payout_fee)+abs(chain_withdraw_fee)+abs(checkout_withdraw_fee)+abs(to_card_fee)+abs(crypto_contract_in_fee)
                    }
                },
                #
                # 'all_amount':{
                #     '入账': wallet_for_crypto_payin + #法币充值
                #             wallet_for_chain_deposit +#链上充值
                #             wallet_for_redeem + #赎回
                #             wallet_for_failed_refund + #失败退款
                #             wallet_for_card_to_wallet_deposit +#卡账户转入
                #             wallet_for_system_recharge , #系统充值
                #
                # '出账': wallet_for_crypto_payout + #加密付款
                #         wallet_for_chain_withdraw + #链上提现
                #         wallet_for_checkout_withdraw + #商户提现
                #         wallet_for_oo_card_deposit + #卡账户充值
                #         wallet_for_system_deduction + #系统扣款
                #         wallet_for_crypto_contract_in #申购
                #
                # }
            }}



if __name__ == '__main__':
    date = '202511'
    currency = ['USDC', 'USDT']
    wallet_summary = WalletTransactionSummary()
    amount_body = ''


    with open('wallet_business_amount_output.txt', 'w', encoding='utf-8') as f:
        for status in ['completed', 'pending']:
        #for status in ['completed']:
            line = f"=== {status} 状态 ===\n"
            f.write(line)
            print(line.strip())  # 同时也打印到控制台

            for curr in currency:
                #获取钱包业务发生额
                line = f"币种: {curr}"
                f.write(line)


                business_amount = wallet_summary.get_wallet_business_amount(curr, status,date)
                # line = "钱包业务发生额: {}\n".format(business_amount['wallet_business_amount'])
                line = f"钱包业务发生额: {json.dumps(business_amount['wallet_business_amount'],ensure_ascii=False, indent=2)}\n"
                f.write(line)


                line = f"详细信息: {json.dumps(business_amount['details'], ensure_ascii=False, indent=2)}\n"
                f.write(line)

    """
    用于验证看板模块
    """
    # 如果是pending状态，获取到所有类型fee和amount的值，如果fee的值为负数变为正数相加，amount的值不变，
    # 最后将这两个值相加，得到钱包业务发生额
    # fee = 0.0
    # amount = 0.0
    # a = ['USDT', 'USDC']
    # for i in a:
    #     business_amount = wallet_summary.get_wallet_business_amount(currency=i, status='pending',date=date)
    #     print(business_amount['details']['fees'])
    #     print(business_amount['details']['amount'])
    #     for fee_type, fee_value in business_amount['details']['fees'].items():
    #         # 如果fee为负数，变为正数
    #
    #         fee += abs(fee_value)
    #
    #     for amount_type, amount_value in business_amount['details']['amount'].items():
    #         amount += abs(amount_value)
    #     print(i, fee, amount)


