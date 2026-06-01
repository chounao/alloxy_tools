from web_page_operation.card_function.card_transaction.card_transaction_record import CardTransactionRecord
import json

"""
计算商务卡的充值、消费、退款、退回、清算金额
卡账户业务当月发生额=卡账户充值+数字商务卡转入-开卡费-卡账户转出-卡账户充值手续费；
数字商务卡当月发生额=数字商务卡充值+数字商务卡退款-数字商务卡转出-数字商务卡消费-本地消费手续费-跨境消费手续费-撤销手续费；


"""


class CardTransactionCount:
    def __init__(self):
        self.card_transaction_record = CardTransactionRecord()

    """
    计算卡账户交易类型：充值，转出，卡交易授权
    交易状态：已完成，进行中，失败
    """
    def _get_transaction_count(self, transaction_type, is_card_account=True,date=None):
        """
        通用交易数据获取方法
        :param transaction_type: 交易类型
        :param is_card_account: 是否为卡账户交易
        :return: (总金额, 总手续费)
        """
        if is_card_account:
            amount, fee = self.card_transaction_record.get_card_account_count(transaction_type=transaction_type,date=date)
        else:
            amount, fee = self.card_transaction_record.get_card_count(transaction_type=transaction_type,date=date)
        print(f'{transaction_type}交易数据:', amount, fee)
        return amount, fee
    def get_card_account_in_count(self,date=None):
        """
        获取商务卡账户交易充值数据
        :return: (总金额, 总手续费)
        """
        all_in_amount, all_in_fee = self._get_transaction_count(transaction_type='vcc_in', is_card_account=True,date=date)
        print('商务卡账户交易充值数据:', all_in_amount, all_in_fee)
        return all_in_amount, all_in_fee

    def get_card_account_out_count(self,date=None):
        """
        获取商务卡账户交易转出数据
        :return: (总金额, 总手续费)
        """
        all_out_amount, all_out_fee = self._get_transaction_count(transaction_type='vcc_out', is_card_account=True,date=date)
        print('商务卡账户交易转出数据:', all_out_amount, all_out_fee)
        return all_out_amount, all_out_fee

    def get_card_account_authorization_fee_account(self,date=None):
        """
        获取商务卡账户交易授权费用数据
        :return: (总金额, 总手续费)
        """
        all_authorization_amount, all_authorization_fee = self._get_transaction_count(
            transaction_type='card_transaction_authorization_fee', is_card_account=True,date=date)
        print('商务卡账户交易授权费用数据:', all_authorization_amount, all_authorization_fee)
        return all_authorization_amount, all_authorization_fee
    def get_card_account_system_recharge_count(self,date=None):
        """
        获取商务卡账户交易系统充值数据
        :return: (总金额, 总手续费)
        """
        all_system_recharge_amount, all_system_recharge_fee = self._get_transaction_count(
            transaction_type='system_recharge', is_card_account=True,date=date)
        print('商务卡账户交易系统充值数据:', all_system_recharge_amount, all_system_recharge_fee)
        return all_system_recharge_amount, all_system_recharge_fee
    def get_card_account_system_deduction_count(self,date=None):
        """
        获取商务卡账户交易系统扣款数据
        :return: (总金额, 总手续费)
        """
        all_system_deduction_amount, all_system_deduction_fee = self._get_transaction_count(
            transaction_type='system_deduction', is_card_account=True,date=date)
        print('商务卡账户交易系统扣款数据:', all_system_deduction_amount, all_system_deduction_fee)
        return all_system_deduction_amount, all_system_deduction_fee

    def get_card_holder_kyc_fee_out_count(self,date=None):
        """
        获取商务卡账户交易KYC手续费数据
        :return: (总金额, 总手续费)
        """
        all_kyc_fee_out_amount, all_kyc_fee_out_fee = self._get_transaction_count(
            transaction_type='card_holder_kyc_fee_out', is_card_account=True,date=date)
        print('商务卡持卡人认证费:', all_kyc_fee_out_amount, all_kyc_fee_out_fee)
        return all_kyc_fee_out_amount, all_kyc_fee_out_fee

    def get_card_holder_kyc_fee_refund_count(self,date=None):
        """
        获取商务卡账户交易KYC手续费退款数据
        :return: (总金额, 总手续费)
        """
        all_kyc_fee_refund_amount, all_kyc_fee_refund_fee = self._get_transaction_count(
            transaction_type='card_holder_kyc_fee_refund', is_card_account=True,date=date)
        print('商务卡持卡人认证费退款:', all_kyc_fee_refund_amount, all_kyc_fee_refund_fee)
        return all_kyc_fee_refund_amount, all_kyc_fee_refund_fee


    def get_logistics_fee_count(self,date=None):
        """
        获取商务卡账户交易物流费用数据
        :return: (总金额, 总手续费)
        """
        all_logistics_fee_amount, all_logistics_fee_fee = self._get_transaction_count(
            transaction_type='logistics_fee', is_card_account=False,date=date)
        print('商务卡账户交易物流费用数据:', all_logistics_fee_amount, all_logistics_fee_fee)
        return all_logistics_fee_amount, all_logistics_fee_fee





        # 数字商务卡
    def get_card_consumption_count(self,date=None):
        """
        获取商务卡账户交易消费数据
        :return: (总金额, 总手续费)
        """
        all_consumption_amount, all_consumption_fee = self._get_transaction_count(
            transaction_type='card_consume', is_card_account=False,date=date)
        print('商务卡账户交易消费数据:', all_consumption_amount, all_consumption_fee)
        return all_consumption_amount, all_consumption_fee

    def get_card_clearance_count(self,date=None):
        """
        获取商务卡账户交易清算数据
        :return: (总金额, 总手续费)
        """
        all_clearance_amount, all_clearance_fee = self._get_transaction_count(
            transaction_type='card_clearing',is_card_account=False,date=date)
        print('商务卡账户交易清算数据:', all_clearance_amount, all_clearance_fee)
        return all_clearance_amount, all_clearance_fee

    def get_card_reversal_count(self,date=None):
        """
        获取商务卡账户交易退回数据
        :return: (总金额, 总手续费)
        """
        all_reversal_amount, all_reversal_fee = self._get_transaction_count(
            transaction_type='card_reversal', is_card_account=False,date=date)
        print('商务卡账户交易退回数据:', all_reversal_amount, all_reversal_fee)
        return all_reversal_amount, all_reversal_fee

    def get_card_refund_count(self,date=None):
        """
        获取商务卡账户交易退款数据
        :return: (总金额, 总手续费)
        """
        all_refund_amount, all_refund_fee = self._get_transaction_count(transaction_type='card_refund',is_card_account=False,date=date)
        print('商务卡账户交易退款数据:', all_refund_amount, all_refund_fee)
        return all_refund_amount, all_refund_fee

    def get_card_deposit_count(self,date=None):
        """
        获取商务卡账户交易转入数据
        :return: (总金额, 总手续费)
        """
        all_deposit_amount, all_deposit_fee = self._get_transaction_count(
            transaction_type='card_deposit',is_card_account=False,date=date)
        print('商务卡账户交易转入数据:', all_deposit_amount, all_deposit_fee)
        return all_deposit_amount, all_deposit_fee

    def get_card_to_card_count(self,date=None):
        """
        获取商务卡账户交易转出数据
        :return: (总金额, 总手续费)
        """
        all_to_card_amount, all_to_card_fee = self._get_transaction_count(
            transaction_type='card_to_card_account',is_card_account=False,date=date)
        print('商务卡账户交易转出数据:', all_to_card_amount, all_to_card_fee)
        return all_to_card_amount, all_to_card_fee

    def get_card_clearance_deduction_count(self,date=None):
        """
        获取商务卡账户清算扣款
        :return: (总金额, 总手续费)
        """
        all_clearance_deduction_amount, all_clearance_deduction_fee = self._get_transaction_count(
            transaction_type='card_clearing_deduction',is_card_account=False,date=date)
        print('商务卡账户清算扣款数据:', all_clearance_deduction_amount, all_clearance_deduction_fee)
        return all_clearance_deduction_amount, all_clearance_deduction_fee

    def get_card_clearance_refund_count(self,date=None):
        """
        获取商务卡账户清算退款
        :return: (总金额, 总手续费)
        """
        all_clearance_refund_amount, all_clearance_refund_fee = self._get_transaction_count(
            transaction_type='card_clearing_refund',is_card_account=False,date=date)
        print('商务卡账户清算退款数据:', all_clearance_refund_amount, all_clearance_refund_fee)
        return all_clearance_refund_amount, all_clearance_refund_fee

    def get_authorization_fee_count(self, date=None):
        """
        获取商务卡账户清算退款
        :return: (总金额, 总手续费)
        """
        all_authorization_fee_amount, all_authorization_fee_fee = self._get_transaction_count(
            transaction_type='card_transaction_authorization_fee', is_card_account=False, date=date)
        print('商务卡账户授权费数据:', all_authorization_fee_amount, all_authorization_fee_fee)
        return all_authorization_fee_amount, all_authorization_fee_fee

    def calculate_card_account_business_count(self, date):
        """
        计算卡账户业务数量
        :return: 卡账户业务数量及详细信息
        卡账户业务当月发生额 = 卡账户充值 - 卡账户转出 - 卡授权费
        """
        card_in_amount, card_in_fee = self.get_card_account_in_count(date)  # 卡账户充值
        card_out_amount, card_out_fee = self.get_card_account_out_count(date)  # 卡账户转出
        card_authorization_amount, card_authorization_fee = self.get_card_account_authorization_fee_account(date)  # 卡授权费
        card_system_deduction_amount, card_system_deduction_fee = self.get_card_account_system_deduction_count(date)  # 卡账户系统扣款
        card_system_recharge_amount, card_system_recharge_fee = self.get_card_account_system_recharge_count(date)  # 卡账户系统充值
        card_holder_kyc_fee_out_amount, card_holder_kyc_fee_out_fee = self.get_card_holder_kyc_fee_out_count(date) # 卡账户KYC费
        card_holder_kyc_fee_refund_amount, card_holder_kyc_fee_refund_fee = self.get_card_holder_kyc_fee_refund_count(date) # 卡账户KYC费退款
        logistics_fee_amount, logistics_fee_fee = self.get_logistics_fee_count(date) # 卡账户物流费用

        wallet_consumption_amount = card_in_amount + card_in_fee #钱包转到卡账户的金额 卡账户的进账金额只有card_in_amount
        card_out_all_amount = card_out_amount + card_out_fee #充值到商务卡的金额
        card_authorization_all_amount = card_authorization_amount + card_authorization_fee #卡授权费所有费用
        card_system_deduction_all_amount = card_system_deduction_amount + card_system_deduction_fee #卡账户系统扣款所有费用
        card_system_recharge_all_amount = card_system_recharge_amount + card_system_recharge_fee #卡账户系统充值所有费用

        card_holder_kyc_fee_out_all_amount = card_holder_kyc_fee_out_amount + card_holder_kyc_fee_out_fee #卡账户KYC费所有费用
        card_holder_kyc_fee_refund_all_amount = card_holder_kyc_fee_refund_amount - card_holder_kyc_fee_refund_fee #卡账户KYC费退款所有费用
        logistics_fee_all_amount = logistics_fee_amount + logistics_fee_fee #卡账户物流费用所有费用



        card_account_business_amount = (
                card_in_amount -  # 卡账户充值
                card_out_all_amount -# 卡账户转出所有费用
                card_authorization_all_amount  # 卡授权费所有费用
                + card_system_recharge_all_amount # 卡账户系统充值所有费用
                - card_system_deduction_all_amount # 卡账户系统扣款所有费用
                - card_holder_kyc_fee_out_all_amount # 卡账户KYC费所有费用
                + card_holder_kyc_fee_refund_all_amount # 卡账户KYC费退款所有费用
                - logistics_fee_all_amount # 卡账户物流费用所有费用

        )
        print('卡账户业务当月发生额:', card_account_business_amount,
              '卡账户充值:', card_in_amount,
              '卡账户转出:', card_out_all_amount,
              '卡授权费:', card_authorization_all_amount,
              '卡账户系统充值:', card_system_recharge_all_amount,
              '卡账户系统扣款:', card_system_deduction_all_amount,
              '卡账户KYC费:', card_holder_kyc_fee_out_all_amount,
              '卡账户KYC费退款:', card_holder_kyc_fee_refund_all_amount,
              '卡账户物流费用:', logistics_fee_all_amount,
        )
        return {
            '卡账户业务当月发生额': card_account_business_amount,
            'details': {
                '钱包转到卡账户的金额': wallet_consumption_amount,
                '卡账户业务当月发生额': card_account_business_amount,
                '卡账户充值': card_in_amount,
                '卡账户转出': card_out_all_amount,
                '卡授权费': card_authorization_all_amount,
                '卡账户系统充值': card_system_recharge_all_amount,
                '卡账户系统扣款': card_system_deduction_all_amount,
                '卡账户KYC费': card_holder_kyc_fee_out_all_amount,
                '卡账户KYC费退款': card_holder_kyc_fee_refund_all_amount,
                '卡账户物流费用': logistics_fee_all_amount,
                '卡账账号支出总和': card_out_all_amount + card_authorization_all_amount+card_system_deduction_all_amount+card_holder_kyc_fee_out_all_amount+logistics_fee_all_amount,
                '卡账户收入总和': card_in_amount + card_system_recharge_all_amount +card_holder_kyc_fee_refund_all_amount
            }
        }


    def calculate_digital_card_business_amount(self, date):
        """
        计算数字商务卡当月发生额
        数字商务卡当月发生额=数字商务卡充值+数字商务卡退款-数字商务卡转出-数字商务卡消费-本地消费手续费-跨境消费手续费-撤销手续费
        :return: 数字商务卡当月发生额及详细信息
        """
        # 获取各项数据
        all_consumption_amount, all_consumption_fee = self.get_card_consumption_count(date) #卡消费
        all_clearance_amount, all_clearance_fee = self.get_card_clearance_count(date) #卡清算
        all_reversal_amount, all_reversal_fee = self.get_card_reversal_count(date) #卡退款
        all_refund_amount, all_refund_fee = self.get_card_refund_count(date) #卡退款
        all_deposit_amount, all_deposit_fee = self.get_card_deposit_count(date) #卡充值
        all_to_card_amount, all_to_card_fee = self.get_card_to_card_count(date) #卡转出(转出到卡)
        all_clearance_deduction_amount, all_clearance_deduction_fee = self.get_card_clearance_deduction_count(date) #卡清算扣款
        all_clearance_refund_amount, all_clearance_refund_fee = self.get_card_clearance_refund_count(date) #卡清算退款
        all_authorization_fee_amount, all_authorization_fee_fee = self.get_authorization_fee_count(date) #卡授权费
        # 数字商务卡充值
        deposit_amount = all_deposit_amount - all_deposit_fee #卡充值 ：充值到商务卡的金额-充值手续费
        #数字商务卡转出
        to_card_amount = all_to_card_amount  #卡转出 ：从商务卡转出的金额
        # 数字商务卡消费
        consumption_amount = all_consumption_amount + all_consumption_fee #卡消费 ：消费到商务卡的金额+消费手续费
        #数字商务卡清算
        clearance_amount = all_clearance_amount + all_clearance_fee #卡清算 ：从商务卡清算的金额+清算手续费
        #数字商务卡撤销
        reversal_amount = all_reversal_amount + all_reversal_fee #卡撤销 ：从商务卡撤销的金额+撤销手续费
        #数字商务卡退款
        refund_amount = all_refund_amount + all_refund_fee #卡退款 ：从商务卡退款的金额+退款手续费
        #数字商务卡清算扣款
        clearance_deduction_amount = all_clearance_deduction_amount + all_clearance_deduction_fee #卡清算扣款 ：从商务卡清算扣款的金额+清算扣款手续费
        #数字商务卡退款
        clearance_refund_amount = all_clearance_refund_amount + all_clearance_refund_fee
        #卡授权费
        authorization_fee_amount = all_authorization_fee_fee #卡授权费 ：从商务卡授权费的金额+授权费手续费



        # 计算数字商务卡当月发生额
        digital_card_business_amount = (
                deposit_amount +  # 数字商务卡充值
                clearance_amount + # 数字商务卡清算
                reversal_amount +  # 数字商务卡撤销
                refund_amount - # 数字商务卡退款
                clearance_deduction_amount + #数字商务卡清算扣款
                clearance_refund_amount- #数字商务卡清算退款
                consumption_amount - #商务卡消费
                to_card_amount  - authorization_fee_amount  #数字商务卡转出
            # 本地消费手续费、跨境消费手续费、撤销手续费暂时未分离
        )

        return {
            '数字商务卡当月发生额': digital_card_business_amount,
            'details': {'数字商务卡充值:':deposit_amount,
                '数字商务卡转出:': to_card_amount,
                '数字商务卡消费:': consumption_amount,
                '数字商务卡清算:': clearance_amount,
                '数字商务卡撤销:': reversal_amount,
                '数字商务卡退款:': refund_amount,
                '数字商务卡清算扣款:': clearance_deduction_amount,
                '数字商务卡清算退款:': clearance_refund_amount,
                        '数字商务卡授权费:': authorization_fee_amount
            }
        }



# 新增的计算方法调用
if __name__ == '__main__':
    date = '202511'
    card_transaction_count = CardTransactionCount()

    # 优化后的代码：将结果保存到文件并格式化输出
    with open('card_transaction_count.txt', 'w', encoding='utf-8') as f:
        # 卡管理业务部分
        f.write("=== 卡管理业务 ===\n")
        card_account_result = card_transaction_count.calculate_card_account_business_count(date)
        f.write(f"数字商务卡账户业务：{json.dumps(card_account_result, ensure_ascii=False, indent=2)}\n")

        # 数字商务卡当月发生额部分
        f.write("\n=== 数字商务卡当月发生额 ===\n")
        digital_card_result = card_transaction_count.calculate_digital_card_business_amount(date)
        f.write(
            f"数字商务卡当月发生额：{json.dumps(digital_card_result, ensure_ascii=False, indent=2, default=lambda x: list(x) if isinstance(x, set) else str(x))}\n")

