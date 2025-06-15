from google_common import get_google_service
from gmail_reader import get_gmail_messages
from calendar_reader import get_calendar_events
from github_commit_reader import get_commits
from openai_common import create_chat_model

# Gmail 서비스 생성
gmail_service = get_google_service("gmail")

# Calendar 서비스 생성
calendar_service = get_google_service("calendar")

# Gmail 메일 가져오기
print("\n=== 메일 ===")
mails = get_gmail_messages(gmail_service)
if mails:
    print(f"받은 메일 {len(mails)}개를 가져왔습니다:")
    for mail in mails:
        print("\n" + "=" * 50)
        print(f'제목: {mail["subject"]}')
        print(f'발신자: {mail["sender"]}')
        print(f'날짜: {mail["date"]}')
        if mail["content"]:
            print(f'내용: {mail["content"][:200]}...')

# Calendar 일정 가져오기
print("\n=== 일정 ===")
events = get_calendar_events(calendar_service)
if events:
    print(f"일정 {len(events)}개를 가져왔습니다:")
    for event in events:
        print("\n" + "=" * 50)
        print(f'제목: {event["summary"]}')
        print(f'시간: {event["start"]} - {event["end"]}')
        print(f'장소: {event["location"]}')
        if event["attendees"]:
            print(f'참석자: {", ".join(event["attendees"])}')
        if event["description"] != "설명 없음":
            print(f'설명: {event["description"]}')


# 예시: 오늘 하루치 커밋 가져오기
# korea_tz = pytz.timezone("Asia/Seoul")
# now = datetime.now(korea_tz)
# start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

# commit_list = get_commits(username, github_token, start_date, now)

# Github 커밋 가져오기
print("\n=== 커밋 ===")
commit_list = get_commits("", "")

if commit_list:
    print(f"커밋 {len(commit_list)}개를 가져왔습니다:")
    for commit in commit_list:
        print("\n" + "=" * 50)
        print(f'저장소: {commit["repo"]}')
        print(f'시간: {commit["time"]}')
        print(f'메시지: {commit["message"]}')
