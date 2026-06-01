from common.simple_request import HttpRequest
from common import read_and_save_tool
from faker import Faker
import random
import hashlib


class UserOperation:
    """
    用户管理的操作
    """

    def __init__(self, http_request=None):
        self.http_request = http_request or HttpRequest()
        self.config = read_and_save_tool.ConfigTools()
        self.password = self.config.get_value('TEST_CONFIG', 'password')
        self.created_user_info = None
        self._cached_user_id = None

    def get_role_id(self):
        """
        获取角色ID
        :return: 角色ID
        """
        # method, url = self.config.get_data_from_name('管理-获取角色列表')
        role_id = self.http_request.send_request(api_name='管理-获取角色列表', jsonpath_expr='$.data[?(@.name == "测试")].id')
        # print(role_id)
        if role_id:
            return role_id
        else:
            raise ValueError("未找到名称为'测试'的角色")
    def get_department_id(self):
        """
        获取部门ID
        :return: 部门ID
        """
        # method, url = self.config.get_data_from_name('管理-获取部门列表')
        department_id = self.http_request.send_request(api_name='管理-获取部门列表', jsonpath_expr="$.data[0].children[?(@.name == '测试部门')].department_id")
        # print(department_id)
        if department_id:
            return department_id
        else:
            raise ValueError("未找到名称为'测试部门'的部门")
    def mock_data(self):
        """
        生成模拟用户数据
        :return: 模拟用户数据 (last_name, first_name, phone, email)
        """
        fake = Faker('en_US')
        last_name = fake.last_name()
        first_name = fake.first_name()
        phone = f"1{random.choice('3456789')}{''.join([str(random.randint(0, 9)) for _ in range(9)])}"
        email = fake.email()
        return last_name, first_name, phone, email

    def create_user(self):
        """
        管理-创建成员
        :param role_id: 角色ID
        :param department_id: 部门ID
        :return: (first_name, last_name) 用户信息
        """
        # 如果已创建用户且有缓存，直接返回缓存信息
        if self.created_user_info and self._cached_user_id:
            return (self.created_user_info["first_name"],
                    self.created_user_info["last_name"])

        last_name, first_name, phone, email = self.mock_data()
        role_id = self.get_role_id()
        department_id = self.get_department_id()
        # method, url = self.config.get_data_from_name('管理-创建成员')

        data = {
            "last_name": last_name,
            "first_name": first_name,
            "role_id": role_id,
            "department_id": department_id,
            "phone": phone,
            "email": email
        }

        self.http_request.send_request(api_name='管理-创建成员', data=data)

        # 缓存用户信息
        self.created_user_info = {
            "first_name": first_name,
            "last_name": last_name,
            "role_id": role_id,
            "department_id": department_id,
            "phone": phone,
            "email": email
        }
        self._cached_user_id = None  # 清除旧的用户ID缓存

        return first_name, last_name

    def get_user_id(self):
        """
        管理-获取成员列表
        :return: 用户ID
        """
        # 使用缓存的用户ID
        if self._cached_user_id:
            return self._cached_user_id

        if not self.created_user_info:
            raise ValueError("没有已创建的用户信息，请先调用create_user方法")

        first_name = self.created_user_info["first_name"]
        last_name = self.created_user_info["last_name"]
        print(first_name, last_name)
        # method, url = self.config.get_data_from_name('管理-获取成员列表')
        # url = url+'?page=1&take=10&name='
        user_id = self.http_request.send_request(api_name='管理-获取成员列表',ping_data='page=1&take=10&name=',
            jsonpath_expr=f'$.data.data[?(@.first_name == \'{first_name}\')].id'
        )
        print(user_id)
        if user_id:
            self._cached_user_id = user_id  # 缓存用户ID

        return user_id

    def update_user(self):
        """
        管理-更新成员
        :param role_id: 角色ID
        :param department_id: 部门ID
        :return: response
        """
        user_id = self.get_user_id()
        if not user_id:
            raise ValueError("无法获取用户ID，请确认用户已创建")

        last_name, first_name, phone, email = self.mock_data()
        # method, url = self.config.get_data_from_name('管理-更新成员')
        role_id = self.get_role_id()
        department_id = self.get_department_id()
        data = {
            "last_name": last_name,
            "first_name": first_name,
            "role_id": role_id,
            "department_id": department_id,
            "phone": phone,
            "email": email,
            "member_id": user_id
        }

        response = self.http_request.send_request(api_name='管理-更新成员', data=data)

        # 更新缓存的用户信息
        if self.created_user_info:
            self.created_user_info.update({
                "first_name": first_name,
                "last_name": last_name,
                "role_id": role_id,
                "department_id": department_id,
                "phone": phone,
                "email": email
            })
            self._cached_user_id = user_id  # 更新缓存的用户ID

        return response

    def get_md5_password(self):
        """
        获取MD5加密的密码
        :return: MD5加密后的密码
        """
        md5 = hashlib.md5()
        md5.update(self.password.encode('utf-8'))
        return md5.hexdigest()

    def reset_password(self, user_id=None):
        """
        管理-重置成员密码
        :param user_id: 成员ID（可选，默认使用已创建的用户ID）
        :return: response
        """
        if not user_id:
            user_id = self.get_user_id()
            if not user_id:
                raise ValueError("无法获取用户ID，请提供用户ID或确认用户已创建")

        data = {
            "id": user_id,
            "password": self.get_md5_password()
        }

        # method, url = self.config.get_data_from_name('管理-重置成员密码')
        response = self.http_request.send_request(api_name='管理-重置成员密码', data=data)
        return response

    def delete_user(self, user_id=None):
        """
        管理-删除成员
        :param user_id: 成员ID（可选，默认使用已创建的用户ID）
        :return: response
        """
        if not user_id:
            user_id = self.get_user_id()
            if not user_id:
                raise ValueError("无法获取用户ID，请提供用户ID或确认用户已创建")

        #method, url = self.config.get_data_from_name('管理-删除成员')
        data = {
            "id": user_id
        }

        response = self.http_request.send_request(api_name='管理-删除成员',data=data)

        # 清除缓存
        self.created_user_info = None
        self._cached_user_id = None

        return response

    def clear_cache(self):
        """
        清除用户缓存信息
        """
        self.created_user_info = None
        self._cached_user_id = None


if __name__ == '__main__':


    user_operation = UserOperation()
    user_operation.get_role_id()
    user_operation.get_department_id()
    # 创建用户
    first_name, last_name = user_operation.create_user()
    print(f"创建用户: {first_name} {last_name}")

    # 获取用户ID
    user_id = user_operation.get_user_id()
    print(f"用户ID: {user_id}")

    # 重置密码
    reset_response = user_operation.reset_password()
    print(f"重置密码响应: {reset_response}")

    # 删除用户
    delete_response = user_operation.delete_user()
    print(f"删除用户响应: {delete_response}")
