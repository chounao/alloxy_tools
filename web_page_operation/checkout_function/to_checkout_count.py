from to_checkout_transcation import ToCheckout
import json


class ToCheckoutCount():
    def __init__(self):
        self.to_checkout = ToCheckout()

    def checkout_count_to_file_by_status(self, date=None, currency=None):
        """
        将待结算订单数量按状态分类写入文件

        Args:
            date (str, optional): 查询日期，格式为YYYYMMDD
            currency (str, optional): 货币类型，如'USDT', 'USDC'

        Returns:
            dict: 包含所有状态数据的字典
        """
        status_mapping = {
            '进行中': 'open',
            '已完成': 'done',
            '待审核': 'withdraw_pending',
            '已拒绝': 'withdraw_rejected',
        }

        # 收集所有数据
        all_results = {}

        for status_name, status_code in status_mapping.items():
            all_results[status_name] = {}
            try:
                # 获取各种订单类型的数据
                withdraw_data,withdraw_amount, withdraw_fee = self.to_checkout.withdraw_data(
                    status=status_code, date=date, currency=currency)
                pay_data,pay_amount, pay_fee = self.to_checkout.pay_data(
                    status=status_code, date=date, currency=currency)
                refund_data,refund_amount, refund_fee = self.to_checkout.refund_data(
                    status=status_code, date=date, currency=currency)

                # 处理可能的解包错误
                # try:
                #     withdraw_data,withdraw_amount, withdraw_fee = withdraw_data if isinstance(withdraw_data, tuple) and len(
                #         withdraw_data) == 2 else (0.0, 0.0)
                # except (ValueError, TypeError):
                #     withdraw_data,withdraw_amount, withdraw_fee = 0.0, 0.0,0.0
                #
                # try:
                #     pay_data,pay_amount, pay_fee = pay_data if isinstance(pay_data, tuple) and len(pay_data) == 2 else (0.0, 0.0)
                # except (ValueError, TypeError):
                #     pay_data,pay_amount, pay_fee = 0.0, 0.0,0.0
                #
                # try:
                #     refund_data,refund_amount, refund_fee = refund_data if isinstance(refund_data, tuple) and len(
                #         refund_data) == 2 else (0.0, 0.0)
                # except (ValueError, TypeError):
                #     refund_data,refund_amount, refund_fee = 0.0, 0.0,0.0



                # 组织数据
                all_results[status_name] = {
                    'withdraw': {
                        'data': withdraw_data,
                        'amount': withdraw_amount,
                        'fee': withdraw_fee
                    },
                    'pay': {
                        'data': pay_data,
                        'amount': pay_amount,
                        'fee': pay_fee
                    },
                    'refund': {
                        'data': refund_data,
                        'amount': refund_amount,
                        'fee': refund_fee
                    }
                }
            except Exception as e:
                error_msg = f"处理状态 {status_name}, 货币 {currency} 时出错: {str(e)}"
                print(error_msg)
                all_results[status_name] = {'error': error_msg}

        # 写入文件
        # filename = f'to_checkout_count_by_status_{currency or "all"}.txt'
        # try:
        #     with open(filename, 'w', encoding='utf-8') as f:
        #         f.write("=== 待结算订单统计（按状态） ===\n")
        #         f.write(f"日期: {date or '未指定'}\n")
        #         f.write(f"货币: {currency or '未指定'}\n")
        #         f.write(f"{json.dumps(all_results, ensure_ascii=False, indent=2)}\n")
        # except Exception as e:
        #     print(f"写入文件 {filename} 时出错: {str(e)}")

        return all_results

    def check_count_to_bycurrencyandstatus(self, date=None):
        """
        将待结算订单数量按货币和状态分类写入文件

        Args:
            date (str, optional): 查询日期，格式为YYYYMMDD

        Returns:
            dict: 包含所有货币和状态数据的字典
        """
        currency_list = ['USDT', 'USDC']
        all_combined_results = {}

        for currency in currency_list:
            try:
                all_results = self.checkout_count_to_file_by_status(date=date, currency=currency)
                all_combined_results[currency] = all_results
            except Exception as e:
                error_msg = f"处理货币 {currency} 时出错: {str(e)}"
                print(error_msg)
                all_combined_results[currency] = {'error': error_msg}

        # 写入综合文件
        try:
            with open('to_checkout_count_by_currency_status.txt', 'w', encoding='utf-8') as f:
                f.write("=== 待结算订单统计（按货币和状态） ===\n")
                f.write(f"日期: {date or '未指定'}\n")
                f.write(f"{json.dumps(all_combined_results, ensure_ascii=False, indent=2)}\n")
        except Exception as e:
            print(f"写入综合文件时出错: {str(e)}")

        return all_combined_results


if __name__ == '__main__':
    date = '202511'

    to_checkout_count = ToCheckoutCount()
    # 执行按货币和状态的统计
    result = to_checkout_count.check_count_to_bycurrencyandstatus(date=date)
    print("待结算订单统计已完成，结果已保存到文件。")
