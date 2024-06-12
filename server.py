from fastapi import FastAPI,Form
from typing import Optional

import dbutil
from dbutil import client
import setting
import llmapi
import httpx
import re
import googledriveutil
import time

app = FastAPI()
linked_col = client.get_collection(setting.col_names['연동'])
unlinked_col = client.get_collection(setting.col_names['미연동'])

def index_prefix_to_string(search_data):
    re_str = ''
    for index ,data in enumerate(search_data):
        re_str += f'{index}번 FAQ : {data["고객"]}\n'
    return re_str

def find_first_number(string):
    match = re.search(r'\d{1,3}', string)
    if match:
        return match.group(0)
    else:
        return None

import psutil

# 현재 프로세스 객체 얻기
process = psutil.Process()

def print_process() :
    # 열린 파일 목록과 연결 목록 출력
    global process
    open_files = process.open_files()
    connections = process.connections()
    print("Open files:", len(open_files))
    print("Open connections:", len(connections))



@app.post("/dbupdate")
async def dbupdate():
    global linked_col, unlinked_col
    await googledriveutil.save_xlsx_to_drive(setting.file_id, "temp.xlsx")
    # await dbutil.db_update()
    # linked_col = client.get_collection('temp1')
    # unlinked_col = client.get_collection('temp2')
    # client.delete_collection(setting.col_names['연동'])
    # client.delete_collection(setting.col_names['미연동'])
    # linked_col.modify(setting.col_names['연동'])
    # unlinked_col.modify(setting.col_names['미연동'])

    return "ㅎㅇ"

@app.post("/ask")
async def post_ask( INQ_VIEW: Optional[str] = Form(None),
                    DEVICE_UUID: Optional[str] = Form(None),
                    HP_NO: Optional[str] = Form(None),
                    Q_CNTS: Optional[str] = Form(None),
                    HT_TIN: Optional[str] = Form(None)) :
    """
    사용자의 질문을 받아 LLM 서버로부터 답변을 얻는 API 엔드포인트입니다.

    Parameters:
    - INQ_VIEW (str): 문의 진입 화면 정보
    - DEVICE_UUID (str): 장치 UUID
    - HP_NO (str): 전화번호
    - Q_CNTS (str): 질문 내용
    - HT_TIN (str): 연동 정보

    Returns:
    - str: LLM 서버로부터 받은 답변
    """
    global linked_col, unlinked_col
    is_linked = HT_TIN is not None
    start = time.perf_counter()
    url = setting.llm_ips[0]
    col = linked_col if is_linked else unlinked_col
    user_id = HT_TIN if is_linked else (HP_NO if HP_NO is not None else DEVICE_UUID)
    async with httpx.AsyncClient(timeout=600) as client :
        # 임베딩 얻기
        embedding = await llmapi.get_embedding(client, Q_CNTS, url)
        # 임베딩으로 검색
        search_data = col.query(embedding, n_results=20)["metadatas"][0]
        # 검색해온 데이터 형식에 맞게 변형
        faq_list = index_prefix_to_string(search_data)
        # 리트리버와 질문으로 프롬프트 생성
        prompt = setting.create_prompt(Q_CNTS, faq_list)
        # 생성된 프롬프트로 답변 구하기
        chat = await llmapi.llm_chat_completions(client,setting.instruction,prompt,url)
        print(chat)
        # llm이 구해준 답변으로 실제 FAQ 답변 가져오기, llm이 원하는 형식으로 답변을 주지 않을 시 답변 실패 문구
        try :
            finded_number = find_first_number(chat)
            answer = search_data[int(finded_number)]['상담사']
        except :
            answer = '적절한 faq를 찾지 못 하였습니다.'
    end = time.perf_counter()
    print(end - start)
    print_process()
    return {"A_CNTS":answer}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)