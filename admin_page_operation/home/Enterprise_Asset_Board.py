# -*- coding: utf-8 -*-
import json
from common.simple_request import HttpRequest
from common import read_and_save_tool
from common import Sql

class EnterpriseAssetBoard:
    def __init__(self,admin_http=None):
        self.http_request = admin_http or HttpRequest(user_type='admin')
        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.sql = Sql.DatabaseConnection()
    def get_home_datas(self):
        data = self.http_request.send_request(api_name='首页-账户信息统计',nested_keys = ['data'])
        total_balance = data['total_balance']
        ryt_balance = data['ryt_balance']
        ryt_position = data['ryt_position']
        ryt_redeemable = data ['ryt_redeemable']
        ryt_return = data['ryt_return']
        crypto_balance_usdc = data['crypto_balance_usdc']
        crypto_balance_usdt = data['crypto_balance_usdt']
        crypto_balance = data['crypto_balance']
        card_account_balance = data['card_account_balance']
        card_balance = data['card_balance']
        card_total_balance = data['card_total_balance']
        checkout_balance = data['checkout_balance']
        checkout_pending_settlement_usdc = data['checkout_pending_settlement_usdc']
        checkout_pending_settlement_usdt = data['checkout_pending_settlement_usdt']
        checkout_withdrawable_usdc = data['checkout_withdrawable_usdc']
        checkout_withdrawable_usdt = data['checkout_withdrawable_usdt']
        return {
            "wallet":{'可用总余额':total_balance,
                      '加密钱包总余额':crypto_balance,
                       'USDC余额':crypto_balance_usdc,
                       'USDT余额':crypto_balance_usdt},
            "card":{'卡总余额':card_total_balance,
                   '数字商务卡余额':card_balance,
                   '卡账户余额':card_account_balance},
            "checkout_page":{'可用总余额':checkout_balance,
                        '待结算USDC':checkout_pending_settlement_usdc,
                        '待结算USDT':checkout_pending_settlement_usdt,
                        '可提现USDC':checkout_withdrawable_usdc,
                        '可提现USDT':checkout_withdrawable_usdt},
            "RYT_data":{"持仓":ryt_position,
                        '可赎回':ryt_redeemable,
                        'RYT可用余额':ryt_balance,
                        'RYT持仓返回':ryt_return} }

    #获取企业资产面板数据
    def get_enterprise_asset_board(self):
        url = f'{self.config_url}/admin/account/company-wealth-dashboard'
        data = self.http_request.get(url,nested_keys=['data'])
        print( data)
        return data

    #获取公司资产看板数据
    def get_company_asset_board(self,accountId):
        url = f'{self.config_url}/admin/account/enterprise-wealth-dashboard/{accountId}'
        data = self.http_request.get(url, nested_keys=['data'])
        print(data)
        return data

    def get_currency_rate(self):
        #验证CAS余额的
        all_num = []
        data = self.http_request.send_request(api_name='管理员-资产看板信息', nested_keys=['data'])

        # 提取各币种数量并组织为字典
        currency_map = {
            'ETH': data['arbitrum_eth'] + data['arbitrum_gas_eth'] + data['ethereum_gas_eth'] + data['ethereum_eth'],
            'POL': data['polygon_pol'] + data['polygon_gas_pol'],
            'AVAX': data['avalanche_gas_avax'] + data['avalanche_avax'],
            'BNB': data['bnb_bsc'] + data['bnb_gas_bsc'],
            'TRX': data['tron_trx'] + data['tron_gas_trx']
        }

        num_list = list(currency_map.keys())

        db = self.sql
        if not db.connect():
            raise ConnectionError("Failed to connect to database")

        try:
            for i in num_list:
                print(i)
                currency_amount = currency_map[i]
                result = db.execute_query(
                    "select rate from currency_rate  where from_currency = %s",
                    (i,)
                )
                if result:
                    rate = result[0][0]
                    print(f"{i}汇率为：{rate}")
                    converted_amount = float(currency_amount) * float(rate)
                    all_num.append(converted_amount)

                else:
                    raise ValueError(f"No rate found for currency: {i}")

            print(sum(all_num))

            return all_num
        except Exception as e:
            print(f"Database error: {e}")
            raise
        finally:
            if hasattr(db, 'close'):
                db.disconnect()# 假设 sql 类提供了 close 方法来释放连接


if __name__ == '__main__':

    e = EnterpriseAssetBoard()
    e.get_currency_rate()