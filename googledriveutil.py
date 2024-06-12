import aiohttp
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError


async def save_xlsx_to_drive(file_id, filename):
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {creds.token}"}
        params = {
            "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}/export"
        async with session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()  # 예외 처리를 위해 상태 코드 확인
            with open(filename, 'wb') as f:
                while True:
                    chunk = await response.content.read(1024)  # 1024 바이트씩 읽기
                    if not chunk:
                        break
                    f.write(chunk)


def upload_file(file_name, folderId):
    # 스코프 설정
    SCOPES = ['https://www.googleapis.com/auth/drive']

    # 사용자 인증 정보 불러오기
    creds = None
    # token.pickle 파일이 있으면, 이미 인증된 사용자 정보를 불러옵니다.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # 인증된 사용자 정보가 없다면, 새로운 인증을 진행합니다.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # 새로운 인증 정보를 token.pickle 파일에 저장합니다.
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # Google Drive API 클라이언트 구성
    service = build('drive', 'v3', credentials=creds)
    folderId = folderId

    # 파일 업로드
    file_metadata = {'name': file_name, 'parents': [folderId]}
    media = MediaFileUpload(file_name, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id').execute()

    print('File ID: %s' % file.get('id'))


def upload_sheet(df, name):
    # 스코프 설정
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    # 인증 정보를 가져오거나, 없다면 새로운 인증 토큰을 생성
    creds = None
    # 토큰 파일이 있으면 로드
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # 인증 토큰이 유효하지 않거나 없다면 새로 발급
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # 새로운 토큰 저장
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # Sheets API 서비스 객체 생성
    service = build('sheets', 'v4', credentials=creds)

    # 새 스프레드시트 생성 요청
    spreadsheet_body = {
        'properties': {
            'title': name
        },
        'sheets': [{'properties': {'title': 'sheet1'}}]
    }

    request = service.spreadsheets().create(body=spreadsheet_body)
    response = request.execute()

    # 생성된 스프레드시트의 ID 출력
    spreadsheet_id = response['spreadsheetId']

    # 데이터를 업로드할 스프레드시트 ID와 범위 지정
    spreadsheet_id = spreadsheet_id  # 스프레드시트 ID
    range_name = 'sheet1!A1'  # 데이터를 시작할 셀 주소

    # pandas DataFrame을 Google Sheets 형식으로 변환
    values = [df.columns.values.tolist()] + df.values.tolist()
    body = {
        'values': values
    }

    # 데이터를 스프레드시트에 쓰기
    request = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=range_name,
        valueInputOption='RAW', body=body)
    response = request.execute()

    print(response)