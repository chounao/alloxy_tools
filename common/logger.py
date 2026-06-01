import logging
import time
import os

BASE_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# 日志配置
LOG_PATH = os.path.join(BASE_PATH, 'log')
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH, exist_ok=True)

class Logger(object):
    def __init__(self):
        self.logname = os.path.join(LOG_PATH, "{}.log".format(time.strftime("%Y_%m_%d")))
        self.logger = logging.getLogger('log')
        self.logger.setLevel(logging.DEBUG)

        # 避免重复添加 handler
        if not self.logger.handlers:
            self.formater = logging.Formatter(
                '[%(asctime)s][%(filename)s %(lineno)d][%(levelname)s]: %(message)s')

            self.filelogger = logging.FileHandler(self.logname, mode='a', encoding="UTF-8")
            self.console = logging.StreamHandler()

            self.filelogger.setLevel(logging.DEBUG)
            self.console.setLevel(logging.DEBUG)

            self.filelogger.setFormatter(self.formater)
            self.console.setFormatter(self.formater)

            self.logger.addHandler(self.filelogger)
            self.logger.addHandler(self.console)


logger = Logger().logger

if __name__ == '__main__':
    logger.info("---测试开始---")
    logger.debug("---测试结束---")
