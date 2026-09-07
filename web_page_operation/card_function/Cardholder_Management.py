from common.simple_request import HttpRequest

from common import get_time, read_and_save_tool, logger
import random

"""
持卡人管理：
    1.新建持卡人
    2.查询持卡人
    3.详情持卡人
    4.冻结持卡人
    5.删除持卡人

"""
logger = logger.Logger()
class CardTransactionCount:
    def __init__(self, user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()

        self.url = self.config.get_url_data()
    def get_department_data(self):
        """
        获取部门数据
        :return:
        """
        test_department_id= self.http_request.gets(self.url +'/web/rbac/departments',jsonpath_expr='$..children[?(@.name=="测试部门")].department_id')
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
        test_user = self.http_request.gets(self.url+f'/web/rbac/members?department_id={test_department_id}',jsonpath_expr='$.data.data[1]')
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
        print(test_department_id,test_user_id, test_user_first_name, test_user_last_name, test_user_phone, test_user_email)
        ISO_data,country_code,country_name,province_name = self.get_country_data()
        print(ISO_data,country_code,country_name,province_name)
        self.card_holder_id = None
        # body = {
        #         "is_external": 0,
        #         "first_name": test_user_first_name,
        #         "last_name": test_user_last_name,
        #         "birthday": "2025-10-17",
        #         "id_document_type": "NationalID",
        #         "id_document_number": "999999",
        #         "phone": test_user_phone,
        #         "email": test_user_email,
        #         "label": "123",
        #         "country": country_name,
        #         "province": province_name,
        #         "city": "hangzhou",
        #         "address": "alex",
        #         "rbac_department_id": test_department_id,
        #         "user_id": test_user_id,
        #         "area_code": country_code,
        #         "iso_code": ISO_data
        #     }

        # 随机5位小写字母（允许重复版本，如果要不重复就保留sample）
        random_str1 = ''.join(random.sample('abcdefghijklmnopqrstuvwxyz', 5))
        # 允许字母重复写法：''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=5))
        random_str2 = ''.join(random.sample('abcdefghijklmnopqrstuvwxyz', 5))

        # 合法模拟身份证（前17位数字，最后一位数字/X）
        id_body = ''.join(random.choices('0123456789', k=17))
        last_char = random.choice('0123456789X')
        random_id_number = id_body + last_char

        # 合法国内手机号：1开头，后面10位随机数字
        phone_head = random.choice(['130', '131', '132', '133', '134', '135', '136', '137', '138', '139',
                                    '150', '151', '152', '153', '155', '156', '157', '158', '159',
                                    '180', '181', '182', '183', '184', '185', '186', '187', '188', '189'])
        phone_tail = ''.join(random.choices('0123456789', k=8))
        random_phone_number = phone_head + phone_tail

        # 随机邮箱，账号允许字母数字重复
        email_prefix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
        random_email = f"{email_prefix}@gmail.com"
        create_card_holder_payload = {
                "channel_code": "photon-hk,photon-us",
                "is_external": 1,
                "first_name": random_str1,
                "last_name": random_str2,
                "birthday": "1983-09-06",
                "sex": "female",
                "id_document_type": "Passport",
                "id_document_number": random_id_number,
                "phone": random_phone_number,
                "email": random_email,
                "portrait": "https://sandbox-hangzhou-web.s3.ap-southeast-2.amazonaws.com/929ff175-e26b-43ad-ba02-467756bff867/2026-09-07/202609071527259684650.jpg",
                "reverseSide": "https://sandbox-hangzhou-web.s3.ap-southeast-2.amazonaws.com/929ff175-e26b-43ad-ba02-467756bff867/2026-09-07/202609071527262597139.jpg",
                "country": "AI",
                "province": "North Side",
                "city": "shanghuan",
                "address": "FlatD7FKoShingBuildingNos4866KoShingStreet",
                "postal_code": "0000000",
                "isSameAsPersonalAddress": True,
                "handFilePath": "https://sandbox-hangzhou-web.s3.ap-southeast-2.amazonaws.com/929ff175-e26b-43ad-ba02-467756bff867/2026-09-07/202609071527552458244.png",
                "area_code": "86",
                "iso_code": "AIA"
                }





        response = self.http_request.posts(self.url+'/web/virtual-card/create-card-holders',data=create_card_holder_payload)
        if response.status_code == 201:
            logger.info('创建虚拟卡持有人成功')
            self.card_holder_id = self.http_request.posts(self.url+'/web/virtual-card/get-holders?page=1&take=100',jsonpath_expr='$.data.list[?(@.first_name=="%s" && @.last_name=="%s")].id' % (random_str1,random_str2))
        else:
            logger.error('创建虚拟卡持有人失败')
        print(response)
        print(self.card_holder_id)
        return self.card_holder_id
    #详情操作
    def get_card_holder_detail(self):
        """
        获取虚拟卡持有人详情
        :return:
        """
        if self.card_holder_id:
            response = self.http_request.gets(self.url+f'/web/virtual-card/holders/{self.card_holder_id}')
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
            "status": 'FROZEN'
        }
        if self.card_holder_id:
            response = self.http_request.patch(self.url+f'/web/virtual-card/holders/{self.card_holder_id}',data=body)
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
            response = self.http_request.patch(self.url+f'/web/virtual-card/holders/{self.card_holder_id}',data=body)
            if response.status_code == 200:
                logger.info('解冻虚拟卡持有人成功')
            else:
                logger.error('解冻虚拟卡持有人失败')
            print(response)
        else:
            logger.error('虚拟卡持有人ID为空')




if __name__ == '__main__':
    card_transaction_count = CardTransactionCount()
    # card_transaction_count.get_department_data()
    # card_transaction_count.get_user_data()
    card_transaction_count.create_card_holder()