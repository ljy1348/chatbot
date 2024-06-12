async def get_embedding(client, query, url):
    response = await client.post(url + "v1/embeddings", json={"input": query})
    if response.status_code == 200:
        embedding = response.json()['data'][0]['embedding']
        return embedding
    else:
        raise Exception("질문 임베딩에 실패 하였습니다.")

async def llm_chat_completions(client, instruction, prompt, url, max_tokens = 5, temperature = 0.1):
    request_data = {
        "messages" : [
        {"role":"system", "content":instruction}
        ,{"role":"user", "content":prompt}
    ]
        ,"max_tokens" : max_tokens
        ,"temperature" : temperature
    }

    response = await client.post(url + "v1/chat/completions", json=request_data)
    if response.status_code == 200:
        answer = response.json()['choices'][0]['message']['content']
        return answer
    else:
        raise Exception("답변 생성에 실패 하였습니다.")

async def llm_completions(client, prompt, url, max_tokens = 5, temperature = 0.1):
    request_data = {
        "prompt" : prompt
        ,"max_tokens" : max_tokens
        ,"temperature" : temperature
    }

    response = await client.post(url + "v1/completions", json=request_data)
    if response.status_code == 200:
        answer = response.json()['choices'][0]['text']
        return answer
    else:
        raise Exception("답변 생성에 실패 하였습니다.")