import requests
import json
from datetime import datetime, timezone, timedelta
import pytz

GITHUB_API_URL = "https://api.github.com"


def get_commits(username, github_token, start_date=None, end_date=None):
    """
    주어진 GitHub 사용자 계정의 커밋 내역을 가져옵니다.

    Args:
        username (str): GitHub 사용자명
        github_token (str): GitHub 개인 액세스 토큰
        start_date (datetime): 시작 날짜 (기본값: 오늘 자정)
        end_date (datetime): 종료 날짜 (기본값: 현재 시간)
    """
    # 날짜 설정
    korea_tz = pytz.timezone("Asia/Seoul")
    now = datetime.now(korea_tz)

    if start_date is None:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if end_date is None:
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json",
    }

    print(f"start_date: {start_date}, end_date: {end_date} 날짜 범위 조회")

    # 이벤트(푸시, PR 등)에서 커밋 푸시만 필터링
    url = f"{GITHUB_API_URL}/users/{username}/events"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"에러 발생: {response.status_code} - {response.text}")
        return [], response.status_code

    print("======================git info===========================")
    print(response.json())
    print("============================================================")

    events = response.json()
    commit_list = []
    for event in events:
        if event["type"] == "PushEvent":
            event_time = (
                datetime.strptime(event["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                .replace(tzinfo=pytz.UTC)
                .astimezone(korea_tz)
            )

            # Convert all times to UTC for comparison
            start_date_utc = start_date.astimezone(korea_tz)
            end_date_utc = end_date.astimezone(korea_tz)

            if start_date_utc <= event_time <= end_date_utc:
                repo = event["repo"]["name"]
                for commit in event["payload"]["commits"]:
                    commit_info = {
                        "repo": repo,
                        "message": commit["message"],
                        "time": event_time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    commit_list.append(commit_info)
    return commit_list, response.status_code
