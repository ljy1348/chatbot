import requests
import time

while True :
    start = time.perf_counter()
    # response = requests.post("http://10.246.246.62:11111/ask", data={"Q_CNTS":"안녕하세요.", "DEVICE_UUID":"DVE"})
    response = requests.post("http://192.168.0.38:11111/ask", data={"Q_CNTS":"안녕하세요.", "DEVICE_UUID":"DVE"})
    print(response.status_code)
    response_data = response.json()
    end = time.perf_counter()
    print(end - start)
    print(response_data)