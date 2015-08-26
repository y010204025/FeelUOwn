# -*- coding: utf8 -*-

import os
import json
import asyncio

from PyQt5.QtWidgets import QSystemTrayIcon

from .normalize import NetEaseAPI
from base.logger import LOG
from base.common import func_coroutine
from constants import DATA_PATH


netease_normalize = NetEaseAPI()
CONTROLLER = None


def init(controller):
    """init plugin """
    global CONTROLLER

    LOG.info("NetEase Plugin init")

    CONTROLLER = controller
    netease_normalize.ne.signal_load_progress.connect(CONTROLLER.on_web_load_progress)

    CONTROLLER.api = netease_normalize
    login_with_local_info()


def login_with_local_info():
    """
    1. load user info
    2. load cookies
    """
    if os.path.exists(DATA_PATH + netease_normalize.user_info_filename):
        with open(DATA_PATH + netease_normalize.user_info_filename) as f:
            data = f.read()
            data_dict = json.loads(data)
            if "uid" in data_dict:
                netease_normalize.set_user(data_dict)
                CONTROLLER.set_user(data_dict)

    if os.path.exists(DATA_PATH + netease_normalize.ne.cookies_filename):
        @func_coroutine
        def check_cookies():
            netease_normalize.ne.load_cookies()
            if netease_normalize.check_login_successful():
                CONTROLLER.set_login()
        check_cookies()
    else:
        LOG.info("找不到您的cookies文件，请您手动登录")
