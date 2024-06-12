import asyncio
import httpx
import time

# async def send_async_request(client, url, data):
#     response = await client.post(url, data=data)
#     print(response.status_code, response.json())
#
# async def send_async_requests(url: str, num_requests: int):
#     async with httpx.AsyncClient(timeout=600) as client:
#         tasks = []
#         tasks.append(send_async_request(client, "http://127.0.0.1:8010/dbupdate", {}))
#         for i in range(num_requests):
#             data = {
#                 "INQ_VIEW": f"view_{i}",
#                 "DEVICE_UUID": f"uuid_{i}",
#                 "HP_NO": f"hp_{i}",
#                 "Q_CNTS": f"question_{i}",
#                 "HT_TIN": f"ht_tin_{i}"
#             }
#             task = send_async_request(client, url, data)
#             tasks.append(task)
#         start = time.perf_counter()
#         await asyncio.gather(*tasks)
#         end = time.perf_counter()
#         print(end - start)
#
#
# # 테스트 실행
# if __name__ == "__main__":
#     url = "http://127.0.0.1:8010/ask"  # 테스트할 서버의 URL
#     num_requests = 10  # 보낼 요청의 수
#     asyncio.run(send_async_requests(url, num_requests))

import requests
requests.post("http://localhost:8010/dbupdate")
