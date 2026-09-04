
from common.simple_request import HttpRequest
from common import read_and_save_tool
from common.execute import get_config_section

class PayerPage:
    def __init__(self, user_http=None, admin_http=None):
        self.user_http = user_http or HttpRequest(user_type='user')
        self.admin_http = admin_http or HttpRequest(user_type='admin')

        self.config = read_and_save_tool.ConfigTools()
        self.config_url = self.config.get_url_data()
        self.config_section = get_config_section()
        self.url = self.config.get_url_data()





    def get_payer_id(self):
        url = self.url + '/web/crypto/payer/fiat?page=1&take=10'
        payer_id = self.user_http.requests('get',url, nested_keys=['data','list', 0, 'id'])
        print(payer_id)


    def delect_payer(self, payer_id):
        url = self.url + f'/web/crypto/payer/fiat/{payer_id}'
        self.user_http.requests('delete',url)














if __name__ == '__main__':
    payer_page = PayerPage()
    num = 100
    for i in range(num):
        payer_id = payer_page.get_payer_id()
        payer_page.delect_payer(payer_id)