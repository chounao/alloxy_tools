import os
import common.logger

# 全局环境变量
_current_env = 'test'
_current_config_section = 'TEST_CONFIG'
_logger = None


def _get_logger():
    """
    获取日志记录器（懒加载）
    """
    global _logger
    if _logger is None:
        _logger = common.logger.logger
    return _logger


def set_env(env):
    """
    设置环境，自动切换配置

    Args:
        env: 环境名称 ('test', 'uat', 'prod')

    Returns:
        str: 对应的配置section名称

    Raises:
        ValueError: 当传入无效环境名称时抛出
    """
    global _current_env, _current_config_section

    if not env or not isinstance(env, str):
        raise ValueError('Environment must be a non-empty string')

    env = env.lower().strip()

    env_config_map = {
        'test': 'TEST_CONFIG',
        'uat': 'UAT_CONFIG',
        'prod': 'PROD_CONFIG'
    }

    if env not in env_config_map:
        raise ValueError(f'Invalid environment: "{env}". Must be one of: {", ".join(env_config_map.keys())}')

    _current_config_section = env_config_map[env]
    _current_env = env
    os.environ['APP_ENV'] = env

    _get_logger().debug(f"Environment switched to: {env} (config: {_current_config_section})")

    return _current_config_section


def get_env():
    """
    获取当前环境

    Returns:
        str: 当前环境名称
    """
    return _current_env


def get_config_section():
    """
    获取当前配置section

    Returns:
        str: 当前配置section名称
    """
    return _current_config_section


def init_default_env(env='test'):
    """
    初始化默认环境（用于测试或脚本启动）

    Args:
        env: 环境名称，默认为 'test'
    """
    set_env(env)
    logger = _get_logger()
    logger.info(f"---测试开始---执行的是{env}环境")


if __name__ == '__main__':
    import sys
    # 将 common.execute 映射到当前模块，避免双重加载导致环境变量不同步
    sys.modules.setdefault('common.execute', sys.modules['__main__'])

    # 初始化默认环境
    init_default_env('uat')

    # 执行登录认证
    from common import login

    login_instance = login.Login()
    user_req, admin_req = login_instance.login_tools()



