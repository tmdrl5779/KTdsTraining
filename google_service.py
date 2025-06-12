import os.path
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle

# Google API 스코프 설정
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def get_google_service(api_name):
    """Google API 서비스를 생성하고 반환합니다."""
    creds = None

    # token.pickle 파일이 있으면 저장된 인증 정보를 불러옵니다
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # 유효한 인증 정보가 없으면 새로 인증을 진행합니다
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # 인증 정보를 파일로 저장합니다
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    # API 이름에 따라 적절한 서비스 반환
    if api_name == "gmail":
        return build("gmail", "v1", credentials=creds)
    elif api_name == "calendar":
        return build("calendar", "v3", credentials=creds)
    else:
        raise ValueError(f"지원하지 않는 API: {api_name}")
