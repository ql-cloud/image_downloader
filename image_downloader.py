import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from io import BytesIO
import warnings
from urllib3.exceptions import InsecureRequestWarning
import threading
import sys

# 禁用证书验证警告
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# 配置参数
TIMEOUT = 0.55
MAX_RETRIES = 3
NUM_THREADS = 5
SAVE_DIR = r"需改"
# 模拟旧版浏览器请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36'
}

# 线程锁用于输出同步
print_lock = threading.Lock()
# 全局变量记录是否忽略证书验证和已保存图片数量
ignore_cert = False
saved_count = 0

def download_image():
    global ignore_cert, saved_count
    url = '需改'
    for retry in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=TIMEOUT, verify=not ignore_cert, headers=HEADERS)
            resp.raise_for_status()
            try:
                img = Image.open(BytesIO(resp.content))
                img.verify()
            except (IOError, SyntaxError):
                with print_lock:
                    print("图片损坏，跳过保存")
                    sys.stdout.flush()
                return
            # 确保保存目录存在
            if not os.path.exists(SAVE_DIR):
                os.makedirs(SAVE_DIR)
            file_name = os.path.join(SAVE_DIR, f"image_{int(time.time() * 1000)}.jpg")
            with open(file_name, 'wb') as f:
                f.write(resp.content)
            saved_count += 1
            with print_lock:
                print(f"图片已保存为 {file_name}，已保存 {saved_count} 个")
                sys.stdout.flush()
            break
        except requests.exceptions.SSLError:
            if not ignore_cert:
                choice = input("证书验证超时，是否忽略并继续访问？(y/n): ")
                if choice.lower() == 'y':
                    ignore_cert = True
                else:
                    with print_lock:
                        print("取消当前请求，重新发起连接")
                        sys.stdout.flush()
                    return
        except requests.exceptions.RequestException:
            if retry < MAX_RETRIES - 1:
                with print_lock:
                    print(f"请求超时，正在进行第 {retry + 1} 次重试")
                    sys.stdout.flush()
            else:
                with print_lock:
                    print("请求超时，已达到最大重试次数，放弃本次请求")
                    sys.stdout.flush()

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        while True:
            executor.submit(download_image)
            time.sleep(0.001)
    