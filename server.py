from fastapi import FastAPI,Form, HTTPException, Request
from typing import Optional
from logging.handlers import TimedRotatingFileHandler
import dbutil
from dbutil import client
import setting
import llmapi
import httpx
import re
import googledriveutil
import time
import mysqlutil
import sql
import logging
import os
import traceback
import slackapi

app = FastAPI()
linked_col = client.get_collection(setting.col_names['연동'])
unlinked_col = client.get_collection(setting.col_names['미연동'])


def setup_logging():
    # 로그 디렉터리와 파일 경로 설정
    log_directory = "logs"
    log_file_path = os.path.join(log_directory, "server.log")
    os.makedirs(log_directory, exist_ok=True)  # 로그 디렉터리 생성

    # 로그 핸들러 설정
    handler = TimedRotatingFileHandler(
        filename=log_file_path,
        when="midnight",
        interval=1,
        backupCount=7,  # 7일 동안 로그 파일 보관
        encoding='utf-8'
    )

    # 로그 포맷터 설정
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # 로그 레벨과 핸들러 적용
    logging.basicConfig(level=logging.DEBUG, handlers=[handler])


# 로깅 설정 호출
setup_logging()

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

from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": f"HTTP Exception: {exc.detail}"},
    )

@app.post("/dbupdate")
async def dbupdate():
    global linked_col, unlinked_col
    await googledriveutil.save_xlsx_to_drive(setting.file_id, "temp.xlsx")
    await dbutil.db_update()
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
    - A_CNTS: LLM 서버로부터 받은 답변
    - CX_YN : 고객센터로 바로 연결
    """

    global linked_col, unlinked_col

    is_linked = HT_TIN is not None
    is_test = True if DEVICE_UUID.lower().startswith('d') else (True if DEVICE_UUID.lower().startswith('s') else False)
    start = time.perf_counter()
    url = setting.llm_ips[0]
    col = linked_col if is_linked else unlinked_col
    user_id = HT_TIN if is_linked else (HP_NO if HP_NO is not None else DEVICE_UUID)
    async with httpx.AsyncClient(timeout=10) as client :
        try :
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
            CX_YN = 'N'
            answer_result = 'Y'
            try :
                finded_number = find_first_number(chat)
                answer = search_data[int(finded_number)]['상담사']
                if 'code' in answer :
                    answer = '상담사에게 연결 합니다.'
                    CX_YN = 'Y'
                    answer_result = 'N'
                answer_reference = search_data[int(finded_number)]['고객']
                try :
                    answer_category = search_data[int(finded_number)]['카테고리']
                except :
                    answer_category = ''
            except :
                answer = '적절한 faq를 찾지 못 하였습니다.'
                answer_reference = ''
                answer_category = ''
                answer_result = 'N'
        except Exception as e :
            exc_info = traceback.format_exc()
            last_line = exc_info.strip().split('\n')[-1]
            logging.exception()
            print(last_line)
            logging.info(last_line)
            raise HTTPException(status_code=500, detail="An error occurred")
    end = time.perf_counter()
    generation_time = end - start
    print_process()
    sqldata = (Q_CNTS, answer, chat, faq_list, answer_reference, answer_category, user_id, generation_time, answer_result)
    if is_test :
        await mysqlutil.save_to_db(sql.insert_chat_history_test, sqldata)
    else :
        await mysqlutil.save_to_db(sql.insert_chat_history, sqldata)
    result_str = f"""질문 : {Q_CNTS}
답변 : {answer}
참고질문 : {answer_reference}
답변 시간 : {generation_time}
카테고리 : {answer_category}
유저 : {user_id}
"""
    logging.info(result_str)
    print(result_str)
    if is_test :
        return {"A_CNTS": answer, "CX_YN": CX_YN}
    if is_linked :
        slackapi.Slack.post_message(setting.slack_channel_id['연동 알림'], result_str)
    else :
        slackapi.Slack.post_message(setting.slack_channel_id['미연동 알림'], result_str)
    return {"A_CNTS":answer, "CX_YN":CX_YN}




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)