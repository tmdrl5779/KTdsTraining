from google_service import get_google_service
from gmail_reader import get_gmail_messages
from calendar_reader import get_calendar_events

# Gmail 서비스 생성
gmail_service = get_google_service("gmail")

# Calendar 서비스 생성
calendar_service = get_google_service("calendar")

# Gmail 메일 가져오기
print("\n=== 오늘의 메일 ===")
mails = get_gmail_messages(gmail_service)
if mails:
    print(f"오늘 받은 메일 {len(mails)}개를 가져왔습니다:")
    for mail in mails:
        print("\n" + "=" * 50)
        print(f'제목: {mail["subject"]}')
        print(f'발신자: {mail["sender"]}')
        print(f'날짜: {mail["date"]}')
        if mail["content"]:
            print(f'내용: {mail["content"][:200]}...')

# Calendar 일정 가져오기
print("\n=== 오늘의 일정 ===")
events = get_calendar_events(calendar_service)
if events:
    print(f"오늘의 일정 {len(events)}개를 가져왔습니다:")
    for event in events:
        print("\n" + "=" * 50)
        print(f'제목: {event["summary"]}')
        print(f'시간: {event["start"]} - {event["end"]}')
        print(f'장소: {event["location"]}')
        if event["attendees"]:
            print(f'참석자: {", ".join(event["attendees"])}')
        if event["description"] != "설명 없음":
            print(f'설명: {event["description"]}')
