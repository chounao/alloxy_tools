from common.simple_request import HttpRequest
from common import read_and_save_tool
import ast


class RoleManagement:
    def __init__(self, http_request=None):
        if http_request:
            self.http_request = http_request
        else:
            self.http_request = HttpRequest()
        self.config = read_and_save_tool.ConfigTools()
        self.menu_ids = ast.literal_eval(self.config.get_value('MENU_ID', "menu_ids"))
        self._cached_role_id = None  # 缓存角色ID

    def get_new_role_id(self, role_name):
        """
        管理-获取角色列表
        :param role_name: 角色名称
        :return: 角色id
        """
        #method, url = self.config.get_data_from_name('管理-获取角色列表')
        role_id = self.http_request.send_request(api_name='管理-获取角色列表', jsonpath_expr=f'$.data[?(@.name=="{role_name}")].id')
        print(role_id)
        return role_id

    def create_role(self, role_name):
        """
        管理-创建角色
        :param role_name: 角色名称
        :return: role_id
        """
        # 如果已经有缓存的角色ID，直接返回
        if self._cached_role_id:
            return self._cached_role_id

        # method, url = self.config.get_data_from_name('管理-创建角色')
        payload = {
            "role_name": role_name,
            "approval_limit": -1,
            "menu_ids": list(self.menu_ids)
        }
        self.http_request.send_request(api_name='管理-创建角色', data=payload)
        role_id = self.get_new_role_id(role_name)

        # 缓存角色ID
        self._cached_role_id = role_id
        return role_id

    def put_role_menu(self, role_name, new_role_name):
        """
        管理-更新角色
        :param role_name: 原始角色名称
        :param new_role_name: 新角色名称
        :return: response
        """
        role_id = self.create_role(role_name)
        if role_id:
           # method, url = self.config.get_data_from_name('管理-更新角色')
            payload = {
                "role_name": new_role_name,
                "approval_limit": -1,
                "menu_ids": list(self.menu_ids),
                "role_id": role_id
            }
            response = self.http_request.send_request(api_name='管理-更新角色', data=payload)
            return response
        return None

    def delete_role(self, role_name):
        """
        管理-删除角色
        :param role_name: 角色名称
        :return: response
        """
        role_id = self.create_role(role_name)
        if role_id:
            #method, url = self.config.get_data_from_name('管理-删除角色')
            payload = {
                "id": role_id
            }
            response = self.http_request.send_request(api_name='管理-删除角色', data=payload)
            # 清除缓存
            self._cached_role_id = None
            return response
        return None

    def clear_cache(self):
        """
        清除缓存的角色ID
        """
        self._cached_role_id = None


if __name__ == '__main__':
    role_name = "test_role"
    new_role_name = "new_role"

    role = RoleManagement()

    # 创建角色
    created_role_id = role.create_role(role_name)
    print(f"创建的角色ID: {created_role_id}")

    # 更新角色
    update_response = role.put_role_menu(role_name, new_role_name)
    print(f"更新角色响应: {update_response}")

    # 删除角色
    delete_response = role.delete_role(role_name)
    print(f"删除角色响应: {delete_response}")
