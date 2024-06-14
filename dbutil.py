import chromadb
import httpx
import pandas as pd

import llmapi
import setting
import uuid

client = chromadb.PersistentClient()

def add_collection(name, ids, metadatas, embeddings) :
    try :
        client.delete_collection(name)
    except :
        pass
    col = client.create_collection(name, metadata={"hnsw:space": "cosine"})
    size = 5000
    i = 0
    while len(ids) > size :
        start = i*size
        if start > len(ids) :
            break
        ids1 = ids[start:start+size]
        metadatas1 = metadatas[start:start+size]
        embeddings1 = embeddings[start:start+size]
        col.add(ids=ids1, embeddings=embeddings1, metadatas=metadatas1)
        i += 1
    else :
        col.add(ids=ids, embeddings=embeddings, metadatas=metadatas)


import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

executor = ThreadPoolExecutor(max_workers=4)


async def read_excel(sheet_name):
    loop = asyncio.get_running_loop()
    # functools.partial을 사용하여 pd.read_excel에 필요한 인자들을 설정합니다.
    func = partial(pd.read_excel, 'temp.xlsx', sheet_name=sheet_name)
    # 별도의 스레드에서 Excel 파일을 읽습니다.
    df = await loop.run_in_executor(executor, func)
    return df


def edit_sheet_data(df):
    new_df = pd.DataFrame()
    cols_per_group = 5  # 기대되는 열 수

    for i in range(0, len(df.columns), cols_per_group):
        # 현재 그룹의 열 수를 계산
        current_group_size = min(cols_per_group, len(df.columns) - i)
        # 현재 그룹에 대한 열 이름 리스트 생성
        column_names = ["카테고리", "Q", "A(연동)", "A(미연동)", "비고"][:current_group_size]

        # 데이터 프레임의 일부를 복사하고 열 이름 설정
        temp_df = df.iloc[:, i:i + current_group_size].copy()
        temp_df.columns = column_names

        # 인덱스를 재설정하고 새 데이터프레임에 추가
        temp_df.reset_index(drop=True, inplace=True)
        new_df = pd.concat([new_df, temp_df], ignore_index=True)
    return new_df

async def db_update():
    df_combined = pd.DataFrame()
    sheet_names = pd.ExcelFile('temp.xlsx').sheet_names
    print("=====================엑셀 파일 시트 이름 가져오기")
    tasks = []
    for sheet_name in sheet_names:
        if sheet_name in setting.sheet_names:
            task = read_excel(sheet_name)
            tasks.append(task)
    print("=====================task 집어넣기")

    results = await asyncio.gather(*tasks)
    print("=====================task 실행완료")
    for df in results:
        df_combined = pd.concat([df_combined, df], ignore_index=True)
    print("=====================데이터 합치기")
    # try :
    #     df_custom = await read_excel(setting.sheet_name)
    #     new_df = edit_sheet_data(df_custom)
    #     df_combined = pd.concat([df_combined, new_df], ignore_index=True)
    # except :
    #     pass
    print(f"========================={len(df_combined)}")


    linked_ids = []
    linked_metadatas = []
    linked_embeddings = []
    unlinked_ids = []
    unlinked_metadatas = []
    unlinked_embeddings = []

    async with httpx.AsyncClient() as client :
        for _, row in df_combined.iterrows():
            if pd.isna(row['Q']) :
                continue
            question = row['Q']

            embedding = await llmapi.get_embedding(client, question, setting.llm_ips[0])

            if pd.isna(row['카테고리']) :
                category = ''
            else :
                category = row['카테고리']

            if pd.isna(row['A(연동)']) :
                pass
            else :
                linked_metadata = {
                    "고객" : question
                    ,"상담사" : row['A(연동)']
                    ,"카테고리" : category
                }
                linked_ids.append(str(uuid.uuid4()))
                linked_metadatas.append(linked_metadata)
                linked_embeddings.append(embedding)

            if pd.isna(row['A(미연동)']) :
                pass
            else :
                unlinked_metadata = {
                    "고객": question
                    , "상담사": row['A(미연동)']
                    , "카테고리": category
                }
                unlinked_ids.append(str(uuid.uuid4()))
                unlinked_metadatas.append(unlinked_metadata)
                unlinked_embeddings.append(embedding)
        add_collection('temp1', linked_ids, linked_metadatas, linked_embeddings)
        add_collection('temp2', unlinked_ids, unlinked_metadatas, unlinked_embeddings)
    return True