from common.simple_request import HttpRequest
from common import read_and_save_tool


class RYTFee:
    def __init__(self, user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
        self.authority = self.config.get_url_data()

    def get_wallets_data(self):
        """
        /web/crypto/wallets?currency=USDC 钱包-获取钱包列表
        钱包-获取钱包列表
        获取钱包数据
        :return:
        """
        data = {
            'currency': 'USDC'
        }
        amount = float(self.http_request.send_request(api_name = '钱包-获取钱包列表',dict_data= data,nested_keys=['data', 'list', 0, 'amount']))
        # print(amount)
        return amount

    def get_ryt_data(self):
        """
        /web/contract/getContractAccountInfo 获取合约账户当前情况
        获取当前ryt数量
        :return:
        """
        amount = float(self.http_request.send_request(api_name ='获取合约账户当前情况',nested_keys=['data','num']))
        print(amount)
        return  amount

    def get_RYT_fee(self):
        """
        RYT手续费
        :param currency: 币种  /web/contract/getRytSupply 获取ryt额度
        :param chain: 链
        :return:
        """

        data  =self.http_request.send_request(api_name ='获取ryt额度',nested_keys=['data'])
        RYT_fee = float(data['fee'])
        USDC_to_RYT_amountOut = float(data['amountOut'])
        RYT_amounOUT_fee = float(data['usdcRate'])
        return RYT_fee, USDC_to_RYT_amountOut, RYT_amounOUT_fee

    def buying_expenses_RYT(self, amount,wallet_before):
        """
        购买RYT手续费
        :param amount: 金额
        :return:
        """

        RYT_fee, USDC_to_RYT_amountOut, RYT_amounOUT_fee = self.get_RYT_fee()
        getByNum = amount * USDC_to_RYT_amountOut
        expendUsdcNum = amount * RYT_fee + amount
        nowUsdcNum = wallet_before - expendUsdcNum
        after_wallet = self.get_wallets_data()
        if abs(nowUsdcNum - after_wallet) > 1e-6:
            print("钱包数据有误",nowUsdcNum,after_wallet)
        else:
            print("钱包数据正常")


        print("现在USDC余额为：", nowUsdcNum,after_wallet)
        print(" Ryt数量为：", getByNum)

    def selling_expenses_RYT(self, amount, ryt_before):
        """
        出售RYT手续费
        :param amount: 金额
        :return:
        """

        RYT_fee, USDC_to_RYT_amountOut, RYT_amounOUT_fee = self.get_RYT_fee()

        usdcData = amount * RYT_amounOUT_fee
        actualUsdc = usdcData - usdcData * RYT_fee

        after_ryt_num = ryt_before - amount
        ryt_num = self.get_ryt_data()
        if abs(after_ryt_num - ryt_num) > 1e-6:
            print("RYT数据有误",after_ryt_num,ryt_num)
        else:
            print("RYT数据正常")

        print("预计到账：", actualUsdc)
