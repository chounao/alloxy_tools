from web_page_operation.wallet_function.wallet_transaction_record import WalletTransactionRecord
import json
"""
计算不同交易类型和状态的金额和手续费
USD期初余额总计=USD钱包期初余额+USD数字商务卡期初余额+USD收单期初余额，其余总计公式同理；
钱包业务当月发生额=钱包账户充值+钱包账户入金+卡账户转入+收单提现-钱包账户转出-钱包账户出金-入金手续费-出金手续费；
"""


class WalletTransactionSummary:
    # 【常量配置】转入、转出交易类型清单，和wallet_transaction_record保持一致
    IN_TRADE_TYPES = [
        "法币充值",
        "链上充值",
        "卡账户转入",
        "商户提现",
        "失败退款",
        "赎回",
        "系统充值"
    ]
    OUT_TRADE_TYPES = [
        "链上提现",
        "加密付款",
        "申购",
        "卡账户充值",
        "系统扣款"
    ]

    def __init__(self):
        self.wallet_record = WalletTransactionRecord()

    @staticmethod
    def _get_item_value(data_dict, trade_type, curr, status):
        """工具函数：安全读取summary里的total_amount / total_fee，不存在返回0"""
        node = data_dict.get(trade_type, {}).get(curr, {}).get(status, {})
        amount = node.get("total_amount", 0.0)
        fee = node.get("total_fee", 0.0)
        return amount, fee

    def wallet_transfer_in(self, currency, status, date):
        """
        转入类：法币充值，链上充值，卡账户转入，商户提现，失败退款，赎回，系统充值
        :param currency: 币种
        :param status: 状态
        :return: dict {交易类型: {total_amount, total_fee}}
        """
        summary_data = self.wallet_record.get_all_transaction_summary(
            currency=currency,
            status=status,
            date=date
        )
        result = {}
        for t_type in self.IN_TRADE_TYPES:
            amt, fee = self._get_item_value(summary_data, t_type, currency, status)
            result[t_type] = {"total_amount": amt, "total_fee": fee}
        return result

    def wallet_transfer_out(self, currency, status, date):
        """
        转出类：链上提现, 加密付款, 申购, 卡账户充值, 系统扣款
        :param currency: 币种
        :param status: 状态
        :return: dict {交易类型: {total_amount, total_fee}}
        """
        summary_data = self.wallet_record.get_all_transaction_summary(
            currency=currency,
            status=status,
            date=date
        )
        result = {}
        for t_type in self.OUT_TRADE_TYPES:
            amt, fee = self._get_item_value(summary_data, t_type, currency, status)
            result[t_type] = {"total_amount": amt, "total_fee": fee}
        return result

    @staticmethod
    def calc_net_amount(trade_name, raw_amount, raw_fee):
        """
        【业务公式集中管理】每种交易类型，计算扣手续费后的净额
        你原来的所有单项计算逻辑全部放这里，修改规则只需要改这一处
        """
        if trade_name == "链上充值":
            return raw_amount - raw_fee
        elif trade_name == "法币充值":
            return raw_amount - raw_fee
        elif trade_name == "加密付款":
            return abs(raw_amount - raw_fee)
        elif trade_name == "链上提现":
            return abs(raw_amount - raw_fee)
        elif trade_name == "失败退款":
            return raw_amount + raw_fee
        elif trade_name == "商户提现":
            return raw_amount - raw_fee
        elif trade_name == "申购":
            return abs(raw_amount - raw_fee)
        elif trade_name == "赎回":
            return raw_amount - raw_fee
        elif trade_name == "卡账户充值":
            return abs(raw_amount - raw_fee)
        elif trade_name == "卡账户转入":
            return raw_amount - raw_fee
        elif trade_name == "系统充值":
            return raw_amount
        elif trade_name == "系统扣款":
            return abs(raw_amount)
        else:
            return 0.0

    def get_wallet_business_amount(self, currency, status, date):
        """
        计算钱包业务当月发生额
        钱包业务当月发生额=钱包账户充值+钱包账户入金+卡账户转入+收单提现-钱包账户转出-钱包账户出金-入金手续费-出金手续费
        :param currency: 币种
        :param status: 状态
        :return: 钱包业务发生额相关各项数据
        """
        transfer_in_data = self.wallet_transfer_in(currency, status, date)
        transfer_out_data = self.wallet_transfer_out(currency, status, date)

        # 先计算每一类净额
        net_map = {}
        for name, item in transfer_in_data.items():
            net_map[name] = self.calc_net_amount(name, item["total_amount"], item["total_fee"])
        for name, item in transfer_out_data.items():
            net_map[name] = self.calc_net_amount(name, item["total_amount"], item["total_fee"])

        # 业务发生额计算公式（完全沿用你原来的加减逻辑）
        wallet_business_amount = (
                net_map["链上充值"]
                + net_map["法币充值"]
                - net_map["加密付款"]
                - net_map["链上提现"]
                - net_map["失败退款"]
                - net_map["商户提现"]
                - net_map["申购"]
                + net_map["赎回"]
                - net_map["卡账户充值"]
                + net_map["卡账户转入"]
                + net_map["系统充值"]
                - net_map["系统扣款"]
        )

        # out汇总，保留你原来的details.out结构
        out_amount_sum = 0.0
        out_fee_sum = 0.0
        out_amount_dict = {}
        out_fee_dict = {}
        for name in self.OUT_TRADE_TYPES:
            amt = transfer_out_data[name]["total_amount"]
            fee = transfer_out_data[name]["total_fee"]
            out_amount_dict[name] = amt
            out_fee_dict[name] = fee
            out_amount_sum += abs(amt)
            out_fee_sum += abs(fee)

        details = {
            "currency": currency,
            "out": {
                "amount": {**out_amount_dict, "总金额": out_amount_sum},
                "fee": {**out_fee_dict, "总金额": out_fee_sum}
            }
        }

        return {
            'wallet_business_amount': wallet_business_amount,
            'details': details
        }


if __name__ == '__main__':
    date = '202511'
    currency = ['USDC', 'USDT']
    wallet_summary = WalletTransactionSummary()

    with open('wallet_business_amount_output.txt', 'w', encoding='utf-8') as f:
        for status in ['completed', 'pending']:
            line = f"=== {status} 状态 ===\n"
            f.write(line)
            print(line.strip())

            for curr in currency:
                line1 = f"币种: {curr}\n"
                f.write(line1)
                business_amount = wallet_summary.get_wallet_business_amount(curr, status, date)
                line2 = f"钱包业务发生额: {json.dumps(business_amount['wallet_business_amount'], ensure_ascii=False, indent=2)}\n"
                f.write(line2)
                line3 = f"详细信息: {json.dumps(business_amount['details'], ensure_ascii=False, indent=2)}\n"
                f.write(line3)
                print(f"币种:{line1}，钱包发生额：{line2},详情：{line3}")