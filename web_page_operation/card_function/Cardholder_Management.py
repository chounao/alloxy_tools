from common.simple_request import HttpRequest
from common import logger
from common import get_time, read_and_save_tool


"""
持卡人管理：
    1.新建持卡人
    2.查询持卡人
    3.详情持卡人
    4.冻结持卡人
    5.删除持卡人

"""
logger = logger.logger()
class CardTransactionCount:
    def __init__(self, user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()

    def get_department_data(self):
        """
        获取部门数据
        :return:
        """
        test_department_id= self.http_request.send_request(api_name='管理-获取部门列表',jsonpath_expr='$..children[?(@.name=="测试部门")].department_id')
        # print(test_department_id)
        return test_department_id


    def get_user_data(self):
        """
        获取用户数据
        :return:
        """
        test_department_id = self.get_department_data()
        data ={
            'department_id':test_department_id
        }
        test_user = self.http_request.send_request(api_name='管理-获取成员列表',dict_data = data,jsonpath_expr='$.data.data[1]')
        test_user_id = test_user.get('id')
        test_user_first_name = test_user.get('first_name')
        test_user_last_name = test_user.get('last_name')
        test_user_phone = test_user.get('phone')
        test_user_email = test_user.get('email')

        # print(test_user_id,test_user_first_name,test_user_last_name,test_user_phone,test_user_email)
        return test_department_id,test_user_id,test_user_first_name,test_user_last_name,test_user_phone,test_user_email


    #获取国家信息
    def get_country_data(self):
        """
        获取国家数据
        :return:
        """
        data= {
            'business_type':'common'
        }
        country_data = self.http_request.send_request(api_name='获取国家信息',dict_data = data,jsonpath_expr='$..data[0]')
        ISO_data = country_data['iso3']
        country_code = country_data['country_code']
        country_name = country_data['country_name']
        province_name = country_data['province'][0]['province_name']
        return ISO_data,country_code,country_name,province_name
    def create_card_holder(self):
        test_department_id,test_user_id, test_user_first_name, test_user_last_name, test_user_phone, test_user_email = self.get_user_data()
        ISO_data,country_code,country_name,province_name = self.get_country_data()
        self.card_holder_id = None
        body = {
                "is_external": 0,
                "first_name": test_user_first_name,
                "last_name": test_user_last_name,
                "birthday": "2025-10-17",
                "id_document_type": "NationalID",
                "id_document_number": "999999",
                "phone": test_user_phone,
                "email": test_user_email,
                "label": "123",
                "country": country_name,
                "province": province_name,
                "city": "hangzhou",
                "address": "alex",
                "rbac_department_id": test_department_id,
                "user_id": test_user_id,
                "area_code": country_code,
                "iso_code": ISO_data
            }
        response = self.http_request.send_request(api_name='创建虚拟卡持有人',data = body)
        if response.status_code == 201:
            logger.info('创建虚拟卡持有人成功')
            self.card_holder_id = self.http_request.send_request(api_name='获取虚拟卡持有人列表',jsonpath_expr='$.data.list[?(@.first_name=="%s" && @.last_name=="%s")].id' % (test_user_first_name,test_user_last_name))
        else:
            logger.error('创建虚拟卡持有人失败')
        print(response)
        return self.card_holder_id
    #详情操作
    def get_card_holder_detail(self):
        """
        获取虚拟卡持有人详情
        :return:
        """
        if self.card_holder_id:
            response = self.http_request.send_request(api_name='详情虚拟卡持有人',replace_data={'id':self.card_holder_id})
            if response.status_code == 200:
                logger.info('获取虚拟卡持有人详情成功')
            else:
                logger.error('获取虚拟卡持有人详情失败')
            print(response)
        else:
            logger.error('虚拟卡持有人ID为空')

    #冻结操作
    def freeze_card_holder(self):
        """
        冻结虚拟卡持有人
        :return:
        """
        body = {
            "status": 'BAN'
        }
        if self.card_holder_id:
            response = self.http_request.send_request(api_name='更新虚拟卡持有人',replace_data={'id':self.card_holder_id},data = body)
            if response.status_code == 200:
                logger.info('冻结虚拟卡持有人成功')
            else:
                logger.error('冻结虚拟卡持有人失败')
            print(response)
        else:
            logger.error('虚拟卡持有人ID为空')
    #解冻操作
    def unfreeze_card_holder(self):
        """
        解冻虚拟卡持有人
        :return:
        """
        body = {
            "status": 'ACTIVE'
        }
        if self.card_holder_id:
            response = self.http_request.send_request(api_name='更新虚拟卡持有人',replace_data={'id':self.card_holder_id},data = body)
            if response.status_code == 200:
                logger.info('解冻虚拟卡持有人成功')
            else:
                logger.error('解冻虚拟卡持有人失败')
            print(response)
        else:
            logger.error('虚拟卡持有人ID为空')

    #删除操作
    def delete_card_holder(self):
        """
        删除虚拟卡持有人
        :return:
        """
        if self.card_holder_id:
            response = self.http_request.send_request(api_name='删除虚拟卡持有人',replace_data={'id':self.card_holder_id})
            if response.status_code == 200:
                logger.info('删除虚拟卡持有人成功')
            else:
                logger.error('删除虚拟卡持有人失败')
            print(response)
        else:
            logger.error('虚拟卡持有人ID为空')


if __name__ == '__main__':
    card_transaction_count = CardTransactionCount()
    # card_transaction_count.get_department_data()
    # card_transaction_count.get_user_data()
    card_transaction_count.create_card_holder()