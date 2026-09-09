# card_function/card_transaction_count.py
from typing import Optional, Tuple, Dict, Any, List
import json
from card_transaction_record import CardTransactionRecord


class CardTransactionCount:
    # ========== 交易类型配置常量 ==========
    # sub_type: card_account / card / card_share_group
    TRANS_CFG = {
        # -------------------- 共享卡组 card_share_group --------------------
        "card_clearing_sg": {"trans_type": "card_clearing", "sub_type": "card_share_group", "desc": "共享卡组-清算"},
        "card_reversal_sg": {"trans_type": "card_reversal", "sub_type": "card_share_group", "desc": "共享卡组-退回"},
        "card_refund_sg": {"trans_type": "card_refund", "sub_type": "card_share_group", "desc": "共享卡组-退款"},
        "card_deposit_sg": {"trans_type": "card_deposit", "sub_type": "card_share_group", "desc": "共享卡组-卡转入"},
        "card_to_card_account_sg": {"trans_type": "card_to_card_account", "sub_type": "card_share_group", "desc": "共享卡组-卡转出"},
        "card_clearing_deduction_sg": {"trans_type": "card_clearing_deduction", "sub_type": "card_share_group", "desc": "共享卡组-卡清算扣款"},
        "card_clearing_refund_sg": {"trans_type": "card_clearing_refund", "sub_type": "card_share_group", "desc": "共享卡组-卡清算退款"},
        "card_transaction_authorization_fee_sg": {"trans_type": "card_transaction_authorization_fee", "sub_type": "card_share_group", "desc": "共享卡组-卡授权费"},
        "card_atm_sg": {"trans_type": "card_atm", "sub_type": "card_share_group", "desc": "共享卡组-ATM取款"},
        "card_declined_refund_sg": {"trans_type": "card_declined_refund", "sub_type": "card_share_group", "desc": "共享卡组-失败退款"},
        "card_tradable_amount_update_sg": {"trans_type": "card_tradable_amount_update", "sub_type": "card_share_group", "desc": "共享卡组-可交易金额更新"},
        "vcsg_in": {"trans_type": "vcsg_in", "sub_type": "card_share_group", "desc": "共享卡组转入"},
        "vcsg_out": {"trans_type": "vcsg_out", "sub_type": "card_share_group", "desc": "共享卡组转出"},

        # -------------------- 账户 card_account --------------------
        "vcc_in": {"trans_type": "vcc_in", "sub_type": "card_account", "desc": "账户-充值"},
        "vcc_out": {"trans_type": "vcc_out", "sub_type": "card_account", "desc": "账户-转出"},
        "card_transaction_authorization_fee_acc": {"trans_type": "card_transaction_authorization_fee", "sub_type": "card_account", "desc": "账户-卡授权费"},
        "system_deduction": {"trans_type": "system_deduction", "sub_type": "card_account", "desc": "账户-系统扣款"},
        "system_recharge": {"trans_type": "system_recharge", "sub_type": "card_account", "desc": "账户-系统充值"},
        "card_holder_kyc_fee_out": {"trans_type": "card_holder_kyc_fee_out", "sub_type": "card_account", "desc": "账户-持卡人KYC费"},
        "card_holder_kyc_fee_refund": {"trans_type": "card_holder_kyc_fee_refund", "sub_type": "card_account", "desc": "账户-持卡人KYC费退款"},
        "logistics_fee": {"trans_type": "logistics_fee", "sub_type": "card_account", "desc": "账户-物流费用"},
        "card_create_virtual": {"trans_type": "card_create_virtual", "sub_type": "card_account", "desc": "账户-创建虚拟卡"},
        "card_create_physical": {"trans_type": "card_create_physical", "sub_type": "card_account", "desc": "账户-创建实体卡"},
        "card_monthly_fee": {"trans_type": "card_monthly_fee", "sub_type": "card_account", "desc": "账户-卡月费"},

        # -------------------- 商务卡 card --------------------
        "card_consume_biz": {"trans_type": "card_consume", "sub_type": "card", "desc": "商务卡-消费"},
        "card_clearing_biz": {"trans_type": "card_clearing", "sub_type": "card", "desc": "商务卡-清算"},
        "card_reversal_biz": {"trans_type": "card_reversal", "sub_type": "card", "desc": "商务卡-退回"},
        "card_refund_biz": {"trans_type": "card_refund", "sub_type": "card", "desc": "商务卡-退款"},
        "card_deposit_biz": {"trans_type": "card_deposit", "sub_type": "card", "desc": "商务卡-卡转入"},
        "card_to_card_account_biz": {"trans_type": "card_to_card_account", "sub_type": "card", "desc": "商务卡-卡转出"},
        "card_clearing_deduction_biz": {"trans_type": "card_clearing_deduction", "sub_type": "card", "desc": "商务卡-卡清算扣款"},
        "card_clearing_refund_biz": {"trans_type": "card_clearing_refund", "sub_type": "card", "desc": "商务卡-卡清算退款"},
        "card_transaction_authorization_fee_biz": {"trans_type": "card_transaction_authorization_fee", "sub_type": "card", "desc": "商务卡-卡授权费"},
        "card_atm_biz": {"trans_type": "card_atm", "sub_type": "card", "desc": "商务卡-ATM取款"},
        "card_declined_refund_biz": {"trans_type": "card_declined_refund", "sub_type": "card", "desc": "商务卡-失败退款"},
        "system_deduction_biz": {"trans_type": "system_deduction", "sub_type": "card", "desc": "商务卡-系统扣款"},
        "system_recharge_biz": {"trans_type": "system_recharge", "sub_type": "card", "desc": "商务卡-系统充值"},
    }

    def __init__(self, user_http=None):
        self.card_transaction_record = CardTransactionRecord(user_http=user_http)
        # cache key: (trans_type, sub_type, date)
        self._cache: Dict[Tuple[str, str, Optional[str]], Tuple[float, float]] = {}

    def clear_cache(self):
        """清空缓存，切换月份调用前执行"""
        self._cache.clear()

    def _fetch_trade(self, cfg_key: str, date: str) -> Tuple[float, float]:
        """获取单条交易，带缓存+异常捕获，失败返回(0,0)"""
        cfg = self.TRANS_CFG[cfg_key]
        trans_type = cfg["trans_type"]
        sub_type = cfg["sub_type"]
        desc = cfg["desc"]
        cache_key = (trans_type, sub_type, date)

        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            if sub_type == "card_account":
                amount, fee = self.card_transaction_record.get_card_account_count(trans_type, date)
            elif sub_type == "card":
                amount, fee = self.card_transaction_record.get_card_count(trans_type, date)
            elif sub_type == "card_share_group":
                amount, fee = self.card_transaction_record.get_shared_card_count(trans_type, date)
            else:
                raise ValueError(f"不支持的sub_type:{sub_type}")

            self._cache[cache_key] = (amount, fee)
            print(f'{desc} 交易数据: amount={amount}, fee={fee}')
            return amount, fee
        except Exception as e:
            print(f"⚠️ 查询【{desc}】异常: {str(e)}，该条数据置0继续执行")
            return 0.0, 0.0

    def _calc_amount(self, date: str, income_keys: List[str], expend_keys: List[str]) -> Tuple[Dict[str, float], float, float, float]:
        """批量汇总交易，返回明细、总收入、总支出、净额"""
        detail = {}
        total_in = 0.0
        total_out = 0.0

        for k in income_keys:
            amt, _ = self._fetch_trade(k, date)
            desc = self.TRANS_CFG[k]["desc"]
            detail[desc] = amt
            total_in += amt

        for k in expend_keys:
            amt, _ = self._fetch_trade(k, date)
            desc = self.TRANS_CFG[k]["desc"]
            detail[desc] = amt
            total_out += amt

        net_amount = total_in - total_out
        detail["收入合计"] = total_in
        detail["支出合计"] = total_out
        return detail, total_in, total_out, net_amount

    def calculate_card_account_business_count(self, date: str) -> Dict[str, Any]:
        """账户业务当月发生额"""
        income_keys = [
            "vcc_in",
            "system_recharge",
            "card_holder_kyc_fee_refund"
        ]
        expend_keys = [
            "vcc_out",
            "card_transaction_authorization_fee_acc",
            "system_deduction",
            "card_holder_kyc_fee_out",
            "logistics_fee",
            "card_create_virtual",
            "card_create_physical",
            "card_monthly_fee"
        ]
        detail, total_in, total_out, net = self._calc_amount(date, income_keys, expend_keys)
        res = {
            "账户业务当月发生额": round(net, 4),
            "details": detail
        }
        print(f"\n【账户业务当月发生额】: {net:.4f}")
        return res

    def calculate_share_group_business_amount(self, date: str) -> Dict[str, Any]:
        """共享卡组当月发生额"""
        income_keys = [
            "card_clearing_sg",
            "card_reversal_sg",
            "card_refund_sg",
            "card_deposit_sg",
            "card_clearing_refund_sg",
            "card_declined_refund_sg",
            "vcsg_in"
        ]
        expend_keys = [
            "card_to_card_account_sg",
            "card_clearing_deduction_sg",
            "card_transaction_authorization_fee_sg",
            "card_atm_sg",
            "card_tradable_amount_update_sg",
            "vcsg_out"
        ]
        detail, total_in, total_out, net = self._calc_amount(date, income_keys, expend_keys)
        res = {
            "共享卡组当月发生额": round(net, 4),
            "details": detail
        }
        print(f"\n【共享卡组当月发生额】: {net:.4f}")
        return res

    def calculate_digital_card_business_amount(self, date: str) -> Dict[str, Any]:
        """商务卡当月发生额"""
        income_keys = [
            "card_clearing_biz",
            "card_reversal_biz",
            "card_refund_biz",
            "card_deposit_biz",
            "card_clearing_refund_biz",
            "card_declined_refund_biz",
            "system_recharge_biz"
        ]
        expend_keys = [
            "card_consume_biz",
            "card_to_card_account_biz",
            "card_clearing_deduction_biz",
            "card_transaction_authorization_fee_biz",
            "card_atm_biz",
            "system_deduction_biz"
        ]
        detail, total_in, total_out, net = self._calc_amount(date, income_keys, expend_keys)
        res = {
            "商务卡当月发生额": round(net, 4),
            "details": detail
        }
        print(f"\n【商务卡当月发生额】: {net:.4f}")
        return res


if __name__ == '__main__':
    calc_date = '202608'
    card_counter = CardTransactionCount()
    card_counter.clear_cache()

    with open('card_transaction_count.txt', 'w', encoding='utf-8') as f:
        f.write("=== 账户业务当月发生额 ===\n")
        account_result = card_counter.calculate_card_account_business_count(calc_date)
        f.write(json.dumps(account_result, ensure_ascii=False, indent=2))

        f.write("\n\n=== 共享卡组当月发生额 ===\n")
        sg_result = card_counter.calculate_share_group_business_amount(calc_date)
        f.write(json.dumps(sg_result, ensure_ascii=False, indent=2))

        f.write("\n\n=== 商务卡当月发生额 ===\n")
        biz_result = card_counter.calculate_digital_card_business_amount(calc_date)
        f.write(json.dumps(biz_result, ensure_ascii=False, indent=2))
