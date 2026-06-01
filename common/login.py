from common.simple_request import HttpRequest
import hashlib
from common import read_and_save_tool
from common.execute import set_env, get_env, get_config_section
class Login():
    """
    登陆操作
    """

    def __init__(self):
        self.http_request = HttpRequest()
        self.access_token = None
        self.is_authenticated = False
        """可变的参数"""
        self.config = read_and_save_tool.ConfigTools()
        self.path = get_config_section()
        self.url = 'http://192.168.0.45:5555'
        # self.url = self.config.get_url_data()
    #配置是登陆admin还是中台
    def set_user_data(self, EMAIL, PASSWORD):
        self.email = self.config.get_login_data(EMAIL)
        self.password = self.config.get_login_data(PASSWORD)
        return  self.email, self.password

    def get_md5(self, PASSWORD):
        md5 = hashlib.md5()
        md5.update(PASSWORD.encode('utf-8'))
        self.password = md5.hexdigest()  # 保存MD5值到实例变量
        return self.password

    def login(self,EMAIL, PASSWORD):
        email,password = self.set_user_data(EMAIL, PASSWORD)
        self.password = self.get_md5(password)
        params = {"loginMethod": "email", "password": self.password, "email": email, "laissezPasser": False,
                  "language": "zh_CN"}
        if 'ADMIN' in EMAIL:
            api_name = '管理员-登录'
        else:
            api_name = '用户-登录'
        self.login_url = self.url + '/web/user/login'
        access_token = self.http_request.requests('POST', self.login_url, params, nested_keys=['data', 'accessToken'])
        return access_token


    def authenticate(self,EMAIL, PASSWORD):
        """from
        执行登录并更新请求头中的认证信息（仅在未认证或认证过期时执行）
        """

        access_token = self.login(EMAIL, PASSWORD)

        if access_token is None:
            raise RuntimeError(f"Login failed: could not retrieve access token, please check the login URL configuration")

        if 'ADMIN' in EMAIL:
            print("Admin Authentication successful")
            token = 'Bearer ' + access_token
            self.config.save_value(self.path,'admin_access_token',token)
        else:
            print("Authentication successful")
            token = 'Bearer ' + access_token
            self.config.save_value(self.path,'access_token',token)
        self.http_request.update_headers({'authorization': token})
        return self.http_request

    #执行中台登陆和admin登陆的操作
    def login_tools(self):
        # self.authenticate('ADMIN_EMAIL', 'ADMIN_PASSWORD')
        self.authenticate('EMAIL', 'PASSWORD')






if __name__ == '__main__':
    a = Login()

    # 第一次调用会执行认证
    a.login_tools()

