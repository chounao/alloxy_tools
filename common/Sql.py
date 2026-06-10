"""
host: 'sandbox.c766gm8u2opc.ap-southeast-2.rds.amazonaws.com',
port: 5432,
username: 'random_0312',
password: 'UxpA_GoMhW8s7P84',
database: 'sandbox',
"""
import psycopg2
import logging
from common import read_and_save_tool


class DatabaseConnection:
    """
    数据库连接封装类
    """

    def __init__(self):
        """
        初始化数据库配置
        """
        self.db_config = {
            'host': 'sandbox.c766gm8u2opc.ap-southeast-2.rds.amazonaws.com',
            'port': 5432,
            'user': 'random_0312',
            'password': 'UxpA_GoMhW8s7P84',
            'database': 'uat_sandbox'
        }
        self.connection = None
        self.cursor = None

    def connect(self):
        """
        建立数据库连接

        Returns:
            bool: 连接是否成功
        """
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.cursor = self.connection.cursor()
            logging.info("数据库连接成功")
            return True
        except Exception as error:
            logging.error(f"数据库连接失败: {error}")
            return False

    def disconnect(self):
        """
        断开数据库连接
        """
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logging.info("数据库连接已关闭")
        except Exception as error:
            logging.error(f"关闭数据库连接时出错: {error}")

    def execute_query(self, query, params=None):
        """
        执行查询语句

        Args:
            query (str): SQL查询语句
            params (tuple, optional): 查询参数

        Returns:
            list: 查询结果
        """
        try:
            self.cursor.execute(query, params)
            result = self.cursor.fetchall()
            return result
        except Exception as error:
            logging.error(f"查询执行失败: {error}")
            return None

    def execute_update(self, query, params=None):
        """
        执行更新语句（INSERT, UPDATE, DELETE）

        Args:
            query (str): SQL更新语句
            params (tuple, optional): 更新参数

        Returns:
            bool: 执行是否成功
        """
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return True
        except Exception as error:
            logging.error(f"更新执行失败: {error}")
            self.connection.rollback()
            return False

    def execute_sql(self, query, params=None):
        """
        执行SQL语句，自动判断是查询还是更新操作

        Args:
            query (str): SQL语句
            params (tuple, optional): SQL参数

        Returns:
            list or bool: 查询返回结果列表，更新操作返回是否成功
        """
        try:
            # 检查数据库连接状态
            if not self.connection or not self.cursor:
                logging.warning("数据库未连接，正在尝试连接...")
                if not self.connect():
                    raise Exception("数据库连接失败")

            # 根据SQL语句类型选择执行方法
            query_lower = query.strip().lower()
            if query_lower.startswith(('select', 'with')):
                # 查询操作
                return self.execute_query(query, params)
            else:
                # 更新操作 (INSERT, UPDATE, DELETE等)
                return self.execute_update(query, params)

        except Exception as error:
            logging.error(f"SQL执行失败: {error}")
            return None

    def __enter__(self):
        """
        上下文管理器入口
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口
        """
        self.disconnect()


# 使用示例
if __name__ == "__main__":
    # 方法1: 使用with语句（推荐）
    ConfigTools = read_and_save_tool.ConfigTools()
    # with DatabaseConnection() as db:
    #     # 执行查询
    #     result = db.execute_sql("SELECT NAME,methods,PATH FROM rbac_api WHERE delete_at IS NULL;")
    #     if result:
    #         for i in result:
    #             ConfigTools.save_value('API_DATA', i[0], [i[1], i[2]])
    #     print('执行成功')


    # 方法2: 手动管理连接
    # db = DatabaseConnection()
    # if db.connect():
    #     result = db.execute_sql("SELECT current_database();")
    #     if result:
    #         print(f"当前数据库: {result[0][0]}")
    #     db.disconnect()
    #
    # with DatabaseConnection() as db:
    #     # 执行查询
    #     result_usdc = db.execute_sql("select rate from currency_rate c where c.from_currency = 'USDC' and c.to_currency = 'USD';")
    #     result_usdt = db.execute_sql("select rate from currency_rate c where c.from_currency = 'USDT' and c.to_currency = 'USD';")
    #     print(result_usdc)
    #     print(result_usdc[0][0])
    #     print(result_usdt[0][0])

