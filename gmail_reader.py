import base64
from datetime import datetime, timedelta
import email.utils
import pytz


def get_gmail_messages(service, user_id="me", start_date=None, end_date=None):
    """
    Gmail 메시지를 가져옵니다.

    Args:
        service: Gmail API 서비스 객체
        user_id (str): 사용자 ID (기본값: "me")
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

        # 날짜 형식 변환
        start_str = (start_date - timedelta(days=1)).strftime("%Y/%m/%d")
        end_str = (end_date + timedelta(days=1)).strftime(
            "%Y/%m/%d"
        )  # 다음날로 설정하여 당일 포함

        print(f"start_str: {start_str}, end_str: {end_str} 날짜 범위 조회")

        # 메시지 목록을 가져옵니다 (날짜 필터 적용)
        results = (
            service.users()
            .messages()
            .list(
                userId=user_id,
                q=f"after:{start_str} before:{end_str}",
                maxResults=100,
            )
            .execute()
        )

        messages = results.get("messages", [])

        if not messages:
            return []

        mail_list = []

        for message in messages:
            obj = {}
            msg = (
                service.users()
                .messages()
                .get(userId=user_id, id=message["id"])
                .execute()
            )

            # 메일 헤더에서 제목과 발신자 정보를 추출합니다
            headers = msg["payload"]["headers"]
            subject = next(h["value"] for h in headers if h["name"] == "Subject")
            sender = next(h["value"] for h in headers if h["name"] == "From")
            date_str = next(h["value"] for h in headers if h["name"] == "Date")

            # 날짜를 한국 시간으로 변환
            date_tuple = email.utils.parsedate_tz(date_str)
            if date_tuple:
                local_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                korea_tz = pytz.timezone("Asia/Seoul")
                korea_date = local_date.astimezone(korea_tz)
                date = korea_date
            else:
                date = date_str

            start_date = start_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            ).astimezone(korea_tz)
            end_date = end_date.replace(
                hour=23, minute=59, second=59, microsecond=999999
            ).astimezone(korea_tz)

            if not start_date <= date <= end_date:
                continue

            obj["subject"] = subject
            obj["sender"] = sender
            obj["date"] = date
            obj["content"] = ""

            # 메일 본문이 있는 경우 출력합니다
            if "parts" in msg["payload"]:
                for part in msg["payload"]["parts"]:
                    if part["mimeType"] == "text/plain":
                        data = part["body"]["data"]
                        text = base64.urlsafe_b64decode(data).decode()
                        obj["content"] = text

            mail_list.append(obj)

    except Exception as e:
        print(f"에러 발생: {e}")

    return mail_list
