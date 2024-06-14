import requests
import time

while True :
    start = time.perf_counter()
    response = requests.post("http://localhost:8010/ask", data={"Q_CNTS":"안녕하세요."})
    print(response.status_code)
    response_data = response.json()
    end = time.perf_counter()
    print(end - start)
    print(response_data)