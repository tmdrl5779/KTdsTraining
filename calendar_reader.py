from datetime import datetime, timedelta
import pytz


def get_calendar_events(service, start_date=None, end_date=None):
    """
    캘린더 일정을 가져옵니다.

    Args:
        service: Google Calendar API 서비스 객체
        start_date (datetime): 시작 날짜 (기본값: 오늘 자정)
        end_date (datetime): 종료 날짜 (기본값: 현재 시간)
    """
    try:
        # 날짜 설정
        korea_tz = pytz.timezone("Asia/Seoul")
        now = datetime.now(korea_tz)

        if start_date is None:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if end_date is None:
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        print(f"start_date: {start_date}, end_date: {end_date} 날짜 범위 조회")

        # 일정 가져오기
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_date.isoformat(),
                timeMax=end_date.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])

        if not events:
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
                # event_obj["start"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
                if start_dt < start_date.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ):
                    start_dt = start_date.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                start = start_dt.strftime("%Y-%m-%d %H:%M:%S")
            else:  # 종일 일정인 경우
                # event_obj["start"] = "종일"
                start = start_date.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ).strftime("%Y-%m-%d %H:%M:%S")

            # 종료 시간
            end = event["end"].get("dateTime", event["end"].get("date"))
            if "T" in end:  # 시간이 포함된 경우
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                end_dt = end_dt.astimezone(korea_tz)
                # event_obj["end"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
                if end_dt > end_date.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                ):
                    end_dt = end_date.replace(
                        hour=23, minute=59, second=59, microsecond=999999
                    )
                end = end_dt.strftime("%Y-%m-%d %H:%M:%S")

            else:  # 종일 일정인 경우
                # event_obj["end"] = "종일"
                end = end_date.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                ).strftime("%Y-%m-%d %H:%M:%S")

            event_obj["date"] = start + " ~ " + end

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
