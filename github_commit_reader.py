import requests
from datetime import datetime, timedelta
import pytz

GITHUB_API_URL = "https://api.github.com"

# 개인 액세스 토큰을 환경변수나 별도 파일로 안전하게 관리하는 것이 좋습니다.
GITHUB_TOKEN = ""


def get_today_commits(username):
    """
    주어진 GitHub 사용자 계정이 오늘 커밋한 내역을 가져옵니다.
    """
    # 오늘 날짜(한국 시간 기준) 구하기
    korea_tz = pytz.timezone("Asia/Seoul")
    now = datetime.now(korea_tz)
    start_of_week = now - timedelta(days=7)

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    # 이벤트(푸시, PR 등)에서 커밋 푸시만 필터링
    url = f"{GITHUB_API_URL}/users/{username}/events"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"에러 발생: {response.status_code} - {response.text}")
        return []

    events = response.json()
    print(events)
    today_commits = []
    for event in events:
        if event["type"] == "PushEvent":
            event_time = (
                datetime.strptime(event["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                .replace(tzinfo=pytz.UTC)
                .astimezone(korea_tz)
            )
            if event_time >= start_of_week:
                repo = event["repo"]["name"]
                for commit in event["payload"]["commits"]:
                    commit_info = {
                        "repo": repo,
                        "message": commit["message"],
                        "url": f'https://github.com/{repo}/commit/{commit["sha"]}',
                        "time": event_time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    today_commits.append(commit_info)
    return today_commits


def main():
    username = "tmdrl5779"
    commits = get_today_commits(username)
    if commits:
        print(f"오늘의 커밋 {len(commits)}개:")
        for c in commits:
            print(f'[{c["time"]}] {c["repo"]}: {c["message"]}\n  {c["url"]}')
    else:
        print("오늘 커밋이 없습니다.")


if __name__ == "__main__":
    main()
