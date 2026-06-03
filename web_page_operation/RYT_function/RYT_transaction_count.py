import RYT_transaction_record
import json
from common.simple_request import HttpRequest
class RYT_transaction_count:
    def __init__(self, user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.ryt_transaction_record = RYT_transaction_record.TransactionProcessor(user_http)
    def ryt_count(self,date):
        dict_status = {
            '进行中': 'pending_approval',
            '已完成': 'completed',
            # '已拒绝': 'rejected',
        }

        with open('ryt_transaction_count.txt', 'w') as f:
            for status, status_code in dict_status.items():
                line = f"\n=== {status, status_code} 状态 ===\n"
                f.write(line)
                print( line)
                faild_ryt_amount, faild_wallet_amount = self.ryt_transaction_record.get_RYT_failed_refund_data('usdc',status = status_code,date=date)
                out_ryt_amount, out_wallet_amount = self.ryt_transaction_record.get_RYT_crypto_contract_out(status = status_code,date=date)
                in_ryt_amount, in_wallet_amount = self.ryt_transaction_record.get_RYT_crypto_contract_in(status = status_code,date=date)

                line = {
                    # '失败退款RYT数量': faild_ryt_amount,
                    # '失败退款钱包金额': faild_wallet_amount,
                    '赎回RYT数量': out_ryt_amount,
                    # '赎回钱包金额': out_wallet_amount,
                    '购入RYT数量': in_ryt_amount,
                    # '购入钱包金额': in_wallet_amount,
                }
                f.write(f"详细信息:{json.dumps(line, ensure_ascii=False, indent=4)}\n")


if __name__ == '__main__':
        date = '202511'
        ryt_transaction_count = RYT_transaction_count()
        ryt_transaction_count.ryt_count(date)
