import chromadb
import setting
import uuid
import llmapi

client = chromadb.PersistentClient()
try :
    client.delete_collection(setting.col_names['연동'])
except :
    pass
try :
    client.delete_collection(setting.col_names['미연동'])
except :
    pass
col1 = client.create_collection(setting.col_names['연동'])
col2 = client.create_collection(setting.col_names['미연동'])

ids = []
metadatas = []
embeddings = []
questions = ['aaaaaa', '안녕하세요', 'ssem입니다.', '이것은 테스트입니다.', '테스트 데이터 삽입용 입니다.']

import httpx

async def main() :
    async with httpx.AsyncClient() as client :
        for question in questions:
            embedding = await llmapi.get_embedding(client, question, setting.llm_ips[0])
            id = str(uuid.uuid4())
            metadata = {
                "고객" : question
                ,"상담사" : f" --[{question}]--에 대한 답변 입니다."
            }
            ids.append(id)
            metadatas.append(metadata)
            embeddings.append(embedding)
        col1.add(ids, metadatas=metadatas, embeddings=embeddings)
        col2.add(ids, metadatas=metadatas, embeddings=embeddings)

import asyncio
asyncio.run(main())

