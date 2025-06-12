from datetime import datetime, timedelta
import pytz


def get_calendar_events(service, days=1):
    """오늘 하루 일정을 가져옵니다."""
    try:
        # 현재 시간을 한국 시간으로 설정
        korea_tz = pytz.timezone("Asia/Seoul")
        now = datetime.now(korea_tz)

        # 오늘 자정부터 다음날 자정까지
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # 일정 가져오기
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])

        if not events:
            print("오늘 일정이 없습니다.")
            return []

        event_list = []
        for event in events:
            event_obj = {}

            # 일정 제목
            event_obj["summary"] = event.get("summary", "제목 없음")

            # 시작 시간
            start = event["start"].get("dateTime", event["start"].get("date"))
            if "T" in start:  # 시간이 포함된 경우
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                start_dt = start_dt.astimezone(korea_tz)
                event_obj["start"] = start_dt.strftime("%H:%M")
            else:  # 종일 일정인 경우
                event_obj["start"] = "종일"

            # 종료 시간
            end = event["end"].get("dateTime", event["end"].get("date"))
            if "T" in end:  # 시간이 포함된 경우
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                end_dt = end_dt.astimezone(korea_tz)
                event_obj["end"] = end_dt.strftime("%H:%M")
            else:  # 종일 일정인 경우
                event_obj["end"] = "종일"

            # 장소
            event_obj["location"] = event.get("location", "장소 없음")

            # 설명
            event_obj["description"] = event.get("description", "설명 없음")

            # 참석자
            attendees = event.get("attendees", [])
            event_obj["attendees"] = (
                [attendee.get("email") for attendee in attendees] if attendees else []
            )

            event_list.append(event_obj)

        return event_list

    except Exception as e:
        print(f"에러 발생: {e}")
        return []
