from common.simple_request import HttpRequest
import hashlib
from common import read_and_save_tool
from common.execute import set_env, get_env, get_config_section
class Login():
    """
    登陆操作
    """

    def __init__(self):
        self.access_token = None
        self.is_authenticated = False
        """可变的参数"""
        self.config = read_and_save_tool.ConfigTools()
        self.path = get_config_section()
        self.url = self.config.get_url_data()

    #配置是登陆admin还是中台
    def set_user_data(self, EMAIL, PASSWORD):
        self.email = self.config.get_login_data(EMAIL)
        self.password = self.config.get_login_data(PASSWORD)
        return  self.email, self.password

    def get_md5(self, PASSWORD):
        md5 = hashlib.md5()
        md5.update(PASSWORD.encode('utf-8'))
        self.password = md5.hexdigest()
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
        http_request = HttpRequest()
        access_token = http_request.requests('POST', self.login_url, params, nested_keys=['data', 'accessToken'])
        return access_token


    def authenticate(self,EMAIL, PASSWORD):
        """
        执行登录并更新请求头中的认证信息（仅在未认证或认证过期时执行）
        """

        access_token = self.login(EMAIL, PASSWORD)

        if access_token is None:
            raise RuntimeError(
                f"Login failed for {EMAIL}: could not retrieve access token. "
                f"Server returned an error (check logs above for details). "
                f"Please verify the credentials in config.ini section [{self.path}] are correct."
            )
        if 'ADMIN' in EMAIL:
            print("Admin Authentication successful")
            token = 'Bearer ' + access_token
            self.config.save_value(self.path,'admin_access_token',token)
        else:
            print("Authentication successful")
            token = 'Bearer ' + access_token
            self.config.save_value(self.path,'access_token',token)

        return HttpRequest(user_type='admin' if 'ADMIN' in EMAIL else 'user')

    #执行中台登陆和admin登陆的操作
    def login_tools(self):
        """同时登录普通用户和管理员，返回 (user_http, admin_http) 两个HttpRequest实例"""
        user_http = self.authenticate('EMAIL', 'PASSWORD')
        admin_http = self.authenticate('ADMIN_EMAIL', 'ADMIN_PASSWORD')
        return user_http, admin_http






if __name__ == '__main__':
    login = Login()
    user_req, admin_req = login.login_tools()
