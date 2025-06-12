import base64
from datetime import datetime
import email.utils
import pytz


def get_gmail_messages(service, user_id="me"):
    """오늘 하루치 메일을 가져옵니다."""
    try:
        # 오늘 날짜를 YYYY/MM/DD 형식으로 가져옵니다
        today = datetime.now().strftime("%Y/%m/%d")

        # 메시지 목록을 가져옵니다 (오늘 날짜 필터 적용)
        results = (
            service.users()
            .messages()
            .list(
                userId=user_id,
                q=f"after:{today}",
                maxResults=100,
            )
            .execute()
        )

        messages = results.get("messages", [])

        if not messages:
            return

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
                date = korea_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                date = date_str

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
