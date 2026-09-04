from collections import Counter
from decimal import Decimal

from common.simple_request import HttpRequest
from common import read_and_save_tool
from common.execute import get_config_section


class CalculateTheMonthlyFee:
    def __init__(self, user_http=None, admin_http=None):
        self.user_http = user_http or HttpRequest(user_type='user')
        self.admin_http = admin_http or HttpRequest(user_type='admin')

        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.config_section = get_config_section()
        self.url = self.config.get_url_data()
        self.product_rates = {
            "US SHARE CARD": 3,
            "HK SHARE CARD": 1,
            "493728": 0,
            "414631": 0
        }
    def get_card_bin_count(self):
        page = 1
        take = 100
        bin_count = Counter()

        while True:
            card_list_url = (
                f'{self.url}/web/virtual-card/get-card-list'
                f'?page={page}&take={take}&category=recharge'
            )

            response = self.user_http.requests('get', card_list_url)
            response.raise_for_status()

            res_json = response.json()
            card_list = res_json.get("data", {}).get("list", [])

            if not card_list:
                break

            active_bin_list = [
                item.get("product_name")
                for item in card_list
                if item.get("status") == "ACTIVE" and item.get("product_name")
            ]

            bin_count.update(active_bin_list)

            if len(card_list) < take:
                break

            page += 1
        # 定义产品费率映射表，便于维护和扩展
        # product_rates = {
        #     "US SHARE CARD": 3,
        #     "HK SHARE CARD": 1,
        #     "493728": 0,
        #     "414631": 0
        # }

        print("ACTIVE 状态下不同卡 BIN 数量：")
        all_num = 0  # 初始化总和为0

        for product_name, count in bin_count.items():
            print(f"product_name: {product_name}, count: {count}")
            # 根据产品名称获取费率，未定义的产品费率默认为0
            rate = self.product_rates.get(product_name, 0)
            all_num += count * rate

        print(f"不同 product_name 总数: {len(bin_count)}")
        print(f"all_num: {all_num}")

        return all_num
        # print("ACTIVE 状态下不同卡 BIN 数量：")
        # for card_bin, count in bin_count.items():
        #     print(f"product_name: {card_bin}, count: {count}")
        #
        # print(f"不同 product_name 总数: {len(bin_count)}")
        #
        # return dict(bin_count)

    def get_card_group_count(self):
        page = 1
        take = 100
        bin_count = Counter()

        while True:
            card_list_url = (
                f'{self.url}/web/virtual-card/card-group-card-list'
                f'?page={page}&take={take}&category=recharge'
            )

            response = self.user_http.requests('get', card_list_url)
            response.raise_for_status()

            res_json = response.json()
            data = res_json.get("data") or {}
            card_group_list = data.get("list") or []

            if not card_group_list:
                break

            for card_group in card_group_list:
                card_list= card_group.get("cards") or []
                for card in card_list:
                    if card.get("status") == "ACTIVE" and card.get("product_name"):
                        bin_count.update([card.get("product_name")])

            if len(card_group_list) < take:
                break

            page += 1

        # 定义产品费率映射表，便于维护和扩展
        # product_rates = {
        #     "US SHARE CARD": 3,
        #     "HK SHARE CARD": 1,
        #     "493728": 0,
        #     "414631": 0
        # }

        print("ACTIVE 状态下不同卡 BIN 数量：")
        all_num = 0  # 初始化总和为0

        for product_name, count in bin_count.items():
            print(f"product_name: {product_name}, count: {count}")
            # 根据产品名称获取费率，未定义的产品费率默认为0
            rate = self.product_rates.get(product_name, 0)
            all_num += count * rate

        print(f"不同 product_name 总数: {len(bin_count)}")
        print(f"all_num: {all_num}")

        return all_num

    def get_transaction_count(self):
        page = 1
        take = 100
        amount_count = Counter()
        all_transaction_count = 0
        total = 0

        while True:
            transaction_list_url = (
                f'{self.url}/web/virtual-card/transaction-list'
                f'?page={page}&take={take}&transaction_sub_type=card_account&created_at[]=2026-07-01+00:00&created_at[]=2026-07-31+00:00'
            )

            response = self.user_http.requests('get', transaction_list_url)
            response.raise_for_status()

            res_json = response.json()
            data = res_json.get("data") or {}
            total = data.get("total", 0)
            transaction_list = data.get("list") or []
            #
            # print(f"page: {page}, 当前页数量: {len(transaction_list)}, 接口total: {total}")

            if not transaction_list:
                break

            all_transaction_count += len(transaction_list)

            for transaction in transaction_list:
                trade_amount = transaction.get("trade_amount")

                if (
                        transaction.get("status") == "completed"
                        and transaction.get("transaction_type") == "card_monthly_fee"
                        and trade_amount is not None
                ):
                    amount_count.update([Decimal(str(trade_amount))])

            if all_transaction_count >= total:
                break

            page += 1


        print("不同卡金额数量：")
        for amount, count in amount_count.items():
            print(f"trade_amount: {amount}, count: {count}")


        print(f"不同金额总数: {len(amount_count)}")
        print("🚀" * 20)
        total_amount = sum(amount * count for amount, count in amount_count.items())
        print(f"从交易明细查看卡账户的月费: {total_amount}")
        print("🚀" * 20)
        return {
            "amount_count": dict(amount_count),
            "total_amount": total_amount,
            "transaction_total": total,
            "get_transaction_count": all_transaction_count
        }



if __name__ == '__main__':
    calculate_the_monthly_fee = CalculateTheMonthlyFee()
    num1 = calculate_the_monthly_fee.get_card_bin_count()
    num2 = calculate_the_monthly_fee.get_card_group_count()
    print("🚀"*20)
    print(f"储值卡喝共享卡的月费总和: {num1+num2}")
    print("🚀"*20)
    calculate_the_monthly_fee.get_transaction_count()