import time
import requests
import threading
from functools import wraps
import json

def retry(max_retry):
    def decorator_retry(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retry:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Retrying... ({retries+1}/{max_retry})")
                    retries += 1
                    time.sleep(1)  # Wait for 1 second before retrying
            print(f"Max retries exceeded ({max_retry})")
        return wrapper
    return decorator_retry

log_server_url = 'http://localhost'

class Log:
    """不推荐其他文件导入此类。推荐导入本文件的 logger 对象"""
    def __init__(self, meta_param="viking", remote=False):
        self.remote = remote
        self.url = log_server_url
        if not self.url:
            self.remote = False
        self.meta_param = meta_param
        
    @retry(3)
    def info(self, message):
        threading.Thread(target=self._send_log, args=(message, "info")).start()
        
    @retry(3)
    def error(self, message):
        threading.Thread(target=self._send_log, args=(message, "error")).start()

    def _send_log(self, message, level):
        print(message)
        if self.remote:
            data = {"message": message, "param": self.meta_param, "level": level}
            requests.post(self.url, json.dumps(data)).raise_for_status()
        timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with open('logfile.txt', 'a', encoding='utf-8') as f:
            f.write(f"{timestr}\t{message}\n")

logger = Log('rembg')  # Global object, created once, used anywhere
logger.info("服务启动...")