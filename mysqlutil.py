import asyncio
import aiomysql
import setting


# 데이터베이스 설정
host = setting.mysql_info['host']
port = setting.mysql_info['port']
user = setting.mysql_info['user']
password = setting.mysql_info['password']
db = setting.mysql_info['database']

async def save_to_db(query, data):
    # 데이터베이스 연결 생성
    conn = await aiomysql.connect(host=host, port=port, user=user, password=password, db=db)
    try:
        # 쿼리 실행을 위한 커서 생성
        async with conn.cursor() as cursor:
            # 쿼리 실행
            await cursor.execute(query, data)
            # 변경사항 커밋
            await conn.commit()
    finally:
        # 연결 종료
        conn.close()

