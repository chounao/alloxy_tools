import json
from decimal import getcontext
import decimal
import math
from common.simple_request import HttpRequest
from common import read_and_save_tool
import ast

class PayMentIn:
    def __init__(self,http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()
        self.config = read_and_save_tool.ConfigTools()
        self.authority = self.config.get_value('TEST_CONFIG', 'URL')
        self.list = []
        self.county = self.config.get_value('PAY_IN_COUNTY', 'pay_in_county')
    # def get_chain(self):
    #     url = self.authority + '/web/crypto/chain'
    #     data = self.http_request.get(url)
    #     print(data)
    #     return data
    # def get_country_info_data(self):
    #     url = self.authority + '/web/country/country-info/?business_type=yellowcard_payin'
    #     data = self.http_request.get(url)
    #     print(data)
    #     return data
    
    def get_fiat_in_fee(self):
        url = self.authority + '/web/crypto/get-fiat-in-fee'
        rate_fee = self.http_request.get(url,nested_keys = ['data'])
        USDT_fee = rate_fee['rate']['USDT']
        USDC_fee = rate_fee['rate']['USDC']
        per_count = rate_fee['per_count']
        prorate = rate_fee['prorate']
        # print(USDT_fee,USDC_fee)
        print(f'USDT手续费:{USDT_fee},USDC手续费:{USDC_fee},每笔固定手续费:{per_count},每笔手续费比例:{prorate}')
        return USDT_fee,USDC_fee,per_count,prorate
        
    def get_fee(self,from_currency,to_currency):
        """
        钱包-获取汇率
        :param from_currency: 充值币种
        :param to_currency: 到账币种
        :return:
        """
        url_body ={
            "from_currency": from_currency,
            "to_currency": to_currency
        }
        #url = self.authority + f'/web/crypto/rates?from_currency={{from_currency}}&to_currency={{to_currency}}'.format(from_currency=from_currency,to_currency=to_currency)
        data = self.http_request.send_request(api_name='钱包-获取汇率',dict_data=url_body,nested_keys = ['data','data'])

        if data is None:
            # 处理数据为空的情况
            raise ValueError("Failed to fetch fee data")
        buy = data['buy']
        locale = data['locale']
        print( buy,locale)
        return buy, locale

    def custom_round(self, value):
        """
        自定义舍入规则：小数点后第三位不为0则进位，为0则舍去
        """
        # 将数值乘以100，获取前两位小数
        multiplied = value * 100
        # 获取第三位小数
        third_decimal = int((value * 1000) % 10)
        # 如果第三位小数不为0，则进位；否则舍去
        if third_decimal != 0:
            return math.ceil(multiplied) / 100
        else:
            return math.floor(multiplied) / 100

    #充值操作
    def pay_in(self, currency_data, from_currency, to_currency):
        """
        钱包-提交payin请求
        :param currency_data: 充值金额
        :param from_currency: 充值币种
        :param to_currency: 到账币种
        :return:
        """
        # 只调用一次 get_fee 方法

        fee_data = self.get_fee(from_currency, to_currency)
        fee = fee_data[0]
        # getcontext().prec = 20
        # getcontext().rounding = decimal.ROUND_DOWN
        # a = Decimal(currency_data)
        # b = Decimal(fee)
        # # 除法运算
        # result = a / b
        # # amount = "{0:.15f}".format(result)
        # amount =  f"{result:.10f}"
        amount = currency_data / fee
        print(amount)
        country = fee_data[1]
        url = self.authority + '/web/crypto/submit-collection'
        # 使用自定义舍入规则

        data = {
            "type": "fiat",
            "country": country,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount": currency_data
        }
        # a = self.http_request.post(url,data,nested_keys=['data','savePayinOrder','source_order_id'])
        try:
            savePayinOrder = self.http_request.send_request(api_name = '钱包-提交payin请求',data = data, nested_keys=['data', 'savePayinOrder'])
            source_order_id = savePayinOrder['source_order_id']
            transaction_id = savePayinOrder['transaction_id']
        # print(a)
        # return a

        # USDT_fee,USDC_fee,per_count,prorate = self.get_fiat_in_fee()
        # USDT_fee = float(USDT_fee)
        # USDC_fee = float(USDC_fee)
        # amount =float(amount)
        # #计算USDT
        # service_charge_USDT = self.custom_round(amount * prorate + per_count *USDT_fee)
        # estimated_amount_USDT = amount - service_charge_USDT
        # a = amount * prorate + per_count *USDT_fee
        #
        #
        #
        # #计算USDC
        # service_charge_USDC = self.custom_round(amount * prorate + per_count *USDC_fee)
        # estimated_amount_USDC = amount - service_charge_USDC
        # b = amount * prorate + per_count *USDC_fee
        # #
        # print(f'没有四舍五入的USDT手续费:{a}')
        # print(f'没有四舍五入的USDC手续费:{b}')
        # print(f'USDT手续费:{service_charge_USDT},预计到账:{estimated_amount_USDT}')
        # print(f'USDC手续费:{service_charge_USDC},预计到账:{estimated_amount_USDC}')
        # print(data)
        except json.JSONDecodeError:
            print("响应内容不是合法的 JSON：")
            return None
        return source_order_id,transaction_id




if __name__ == '__main__':
    pay_ment_in = PayMentIn()
    config = read_and_save_tool.ConfigTools()

    # county = ast.literal_eval(config.get_value('PAY_IN_COUNTY', 'pay_in_county'))
    #
    # for key,value in county.items():
    #     pay_ment_in.pay_in(3000,value,'USDT')
    #

    # currency = {
    #     'BWP': [150, 1000000],# 博茨瓦纳
    #     'XAF': [1000, 10000000],# 加蓬
    #     'MWK': [2000, 750000],# 马拉维
    #     'NGN': [2500, 30000000],# 尼日利亚
    #     'RWF': [1500, 10000000], # 卢旺达
    #     'ZAR': [0, 0],            # 南非
    #     'TZS': [2500, 40000000],# 坦桑尼亚
    #     'UGX': [15000, 36000000],# 乌干达
    #     'ZMW': [100, 15000000]# 赞比亚
    #
    # }
    # to_currency = ['USDT','USDC']
    # count_list = []
    #
    # for i in to_currency:
    #     print(f"----------------------------------------------------------------------------------------------------------执行的是{i}----------------------------------------------------------------------------------------------------------")
    #     for country ,value in currency.items():
    #             print("执行的是小于最小值的情况")
    #             a = pay_ment_in.pay_in(value[0]-1,country,i)
    #             if a != None:
    #                 count_list.append(a)
    #             print("x"*50)
    #             print("执行的是大于最大值的情况")
    #             b =  pay_ment_in.pay_in(value[1]+1,country,i)
    #             if b != None:
    #                 count_list.append(b)
    #             print("x" * 50)
    #             print("执行边界最小值")
    #             c =pay_ment_in.pay_in(value[0],country,i)
    #             if c != None:
    #                 count_list.append(c)
    #             print("*" * 150)
    #             print("执行正常最大值")
    #             d = pay_ment_in.pay_in(value[1],country,i)
    #             if d != None:
    #                 count_list.append(d)
    #             print("*" * 150)
    # print(count_list)
    # for id in count_list:
    #     pay_ment_in.up_status(id)
