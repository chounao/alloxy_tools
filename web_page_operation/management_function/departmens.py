from common.simple_request import HttpRequest
from common import read_and_save_tool


class structure():
    """
    组织管理模块
    """
    def __init__(self, user_http=None):
        self.http_request = user_http or HttpRequest(user_type='user')
        self.config = read_and_save_tool.ConfigTools()
        # self.authority = self.config.get_value('TEST_CONFIG', 'URL')

    def get_department_id(self,department_name):
        """
        管理-获取部门列表
        :param department_name: 部门名称
        :return: 部门id
        """
        # url = f"{self.authority}/web/rbac/departments"
        # method, url = self.config.get_data_from_name('管理-获取部门列表')
        root_department_id = self.http_request.send_request(api_name='管理-获取部门列表',
                                                            jsonpath_expr='$.data[0].department_id')
        new_department_id = self.http_request.send_request(api_name='管理-获取部门列表',
                                                            jsonpath_expr=f'$..children[?(@.name == "{department_name}")].department_id')
        if new_department_id:
            return new_department_id, root_department_id
        else:
            return root_department_id

    def create_department(self, department_name):
        """
        管理-创建部门
        :param department_name: 部门名称
        :return:
        """
        # method, url = self.config.get_data_from_name('管理-创建部门')
        data = {
            "name": department_name,
            "parent_department_id": self.get_department_id(department_name)
        }
        self.http_request.send_request(api_name='管理-创建部门', data=data)
        new_department_id, root_department_id = self.get_department_id(department_name)
        print(new_department_id, root_department_id)
        return new_department_id, root_department_id


    def put_department(self,department_new_name):
        """
        管理-更新部门
        :param department_new_name: 新部门名称
        :return:
        """
        # url = f"{self.authority}/web/rbac/departments"
        # method, url = self.config.get_data_from_name(api_name='管理-更新部门')
        new_department_id, root_department_id = self.get_department_id(department_name)
        if new_department_id and root_department_id:
            data = {
                "name": department_new_name,
                "parent_department_id": root_department_id,
                "department_id": new_department_id
            }
            response = self.http_request.send_request(api_name='管理-更新部门', data=data)
            return response

    def delete_department(self, department_new_name):
        """
        管理-删除部门
        :param new_department_id: 部门id
        :return:
        """
        # url = f"{self.authority}/web/rbac/departments/{new_department_id}"

        new_department_id, root_department_id = self.get_department_id(department_new_name)
        # print(new_department_id, root_department_id)
        if new_department_id and root_department_id:
            # method, url = self.config.get_data_from_name(api_name='管理-删除部门',replace_data={'id':new_department_id})
            # print( url)
            response = self.http_request.send_request(api_name='管理-删除部门',replace_data={'id':new_department_id})
            return response

if __name__ == '__main__':
    department_name = 'test_department'
    department_new_name = 'test_department_new'

    structure = structure()
    structure.create_department(department_name)
    structure.put_department(department_new_name)
    structure.delete_department(department_new_name)
