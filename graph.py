from typing import TypedDict, Annotated, List, Literal, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from datetime import datetime
import re, json
from openai_common import create_chat_model
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from IPython.display import Image, display
from langchain_core.output_parsers import StrOutputParser
from google_common import get_google_service
from gmail_reader import get_gmail_messages
from calendar_reader import get_calendar_events
from github_commit_reader import get_commits
from langgraph.checkpoint.memory import MemorySaver
import pytz
from langchain_core.runnables import RunnableConfig
import pandas as pd
import io
import os


llm = create_chat_model("azure")


class State(MessagesState):
    user_input: str
    services_list: list[str]
    date: dict[str, str]
    google_mail_message: list[dict[str, str]]
    google_calendar_message: list[dict[str, str | list[str]]]
    github_commit_message: list[dict[str, str]]
    final_summary: str
    excel_check: bool
    is_first: bool
    username: str
    github_token: str
    excel_obj: dict[str, str]
    is_file: bool
    file_summary: str


# 노드 : 사용자의 입력에서 날짜 및 서비스 추출 -> llm 사용
def extraction_node(state: State) -> State:

    print("======== extraction_node ==========")

    system_prompt = """당신은 사용자의 입력에서 서비스와 날짜를 추출하는 전문가입니다.
    현재 날짜는 {current_date}입니다.
    현재 연도는 {current_year}년입니다.
    현재 월은 {current_month}월입니다.
    현재 일은 {current_day}일입니다.

    ##절대 따라야할 규칙##
    - 만약 날짜만 언급되었다면 구글 메일, 구글 캘린더, 깃허브 3개를 모두 반환해야 합니다 (예: "오늘", "어제부터 오늘까지", "이번 주", "지난 달")
    - 만약 서비스만 언급되었고 날짜는 언급되지 않았다면 날짜는 오늘 날짜로 반환해야 합니다
    - 만약 서비스와 날짜가 모두 언급되지 않았다면 서비스는 빈 배열, 날짜는 빈문자열로 세팅합니다
 

    1. 서비스 추출 규칙
    - 사용자가 '일', '기록', '업무', '서비스 이름' 등의 키워드를 사용하여 정보를 요청했다면 서비스를 추출합니다
    - 구글 메일, 구글 캘린더, 깃허브 중에서 언급된 서비스를 찾아야 합니다
    - 구글 메일, 구글 캘린더, 깃허브 외에 언급된 서비스는 찾지 않습니다
    - 서비스 이름은 정확히 "gmail", "calendar", "github"로 반환해야 합니다

    2. 날짜 추출 규칙
    - 사용자가 '정리해줘', '알려줘', '보여줘', '출력해줘', "추출해줘" 등의 키워드를 사용하여 정보를 요청했다면 날짜를 추출합니다
    - 사용자 입력에서 날짜 기간을 찾아야 합니다 (예: "어제부터 오늘까지", "이번 주", "지난 달")
    - 날짜는 시작일과 종료일 형식으로 반환해야 합니다
    - 날짜 형식은 "YYYY/MM/DD"여야 합니다
    - "어제", "오늘", "내일"과 같은 상대적인 날짜는 현재 날짜({current_date})를 기준으로 계산해야 합니다
    - "이번 주", "저번 주", "다음 주"와 같은 상대적인 기간은 현재 날짜({current_date})를 기준으로 계산해야 합니다
    - 날짜 기간을 찾을 수 없다면 오늘 날짜를 시작일과 종료일로 사용합니다

    3. 엑셀 추출 규칙
    - 사용자가 '엑셀로 추출해줘' 등의 키워드를 사용하여 정보를 요청했다면 엑셀로 추출합니다

    입력 예시:
    "오늘 한일 알려줘" -> 서비스는 구글 메일, 구글 캘린더, 깃허브 3개를 모두 반환, 날짜는 오늘 날짜로 반환
    "어제부터 오늘까지 한일 알려줘" -> 서비스는 구글 메일, 구글 캘린더, 깃허브 3개를 모두 반환, 날짜는 어제부터 오늘까지 날짜로 반환
    "이번 주 한일 알려줘" -> 서비스는 구글 메일, 구글 캘린더, 깃허브 3개를 모두 반환, 날짜는 이번 주 날짜로 반환
    "지난 달 한일 알려줘" -> 서비스는 구글 메일, 구글 캘린더, 깃허브 3개를 모두 반환, 날짜는 지난 달 날짜로 반환
    "6/13에 한일 알려줘" -> 서비스는 구글 메일, 구글 캘린더, 깃허브 3개를 모두 반환, 날짜는 해당 날짜로 반환
    "6/13, 6/15 한일 알려줘" -> 서비스는 구글 메일, 구글 캘린더, 깃허브 3개를 모두 반환, 날짜는 해당 날짜 기간으로 반환
    "어제부터 오늘까지 구글 메일과 깃허브 기록 알려줘" -> 서비스는 구글 메일, 깃허브 2개를 반환, 날짜는 어제부터 오늘까지 날짜로 반환
    "이번 주 구글 캘린더 일정 알려줘" -> 서비스는 구글 캘린더 1개를 반환, 날짜는 이번 주 날짜로 반환

    출력 형식:
    {{
        "services_list": ["gmail", "calendar", "github"],
        "date": {{
            "start_date": "YYYY/MM/DD",
            "end_date": "YYYY/MM/DD"
        }},
        "excel": true
    }}
    """

    user_prompt = """
    사용자의 입력에서 서비스와 날짜를 추출하여 반환해주세요.

    [User Input]
    {user_input}

    [extraction]
    """

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", user_prompt)]
    )

    # 현재 날짜 정보 가져오기
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_year = datetime.now().year
    current_month = datetime.now().month
    current_day = datetime.now().day

    extraction_chain = prompt | llm | StrOutputParser()
    result = extraction_chain.invoke(
        {
            "user_input": state["user_input"],
            "current_date": current_date,
            "current_year": current_year,
            "current_month": current_month,
            "current_day": current_day,
        }
    )

    # 결과가 빈 딕셔너리인 경우 기본값 설정
    result = json.loads(result)

    print(result)
    if result["services_list"] == []:
        return {
            "services_list": [],
            "date": {"start_date": "", "end_date": ""},
            "excel_check": False,
            "is_first": True,
            "final_summary": "",
            "google_mail_message": [],
            "google_calendar_message": [],
            "github_commit_message": [],
            "username": "",
            "github_token": "",
            "is_file": False,
            "excel_obj": {},
            "file_summary": "",
            "messages": [
                AIMessage(
                    content="서비스(구글 메일, 구글 캘린더, 깃허브)와 날짜를 추출에 실패하였습니다.\n\n 3개 서비스중 하나를 말씀해주세요.\n\n 예시: 오늘 업무 정리해줘\n\n 예시: 이번 주 업무 정리해줘\n\n 예시: 6/9 구글 메일 업무 정리해줘\n\n 예시: 6/9 깃허브 정리해줘\n\n 예시: 6/9 구글 캘린더 업무 정리해줘 "
                )
            ],
        }

    return {
        "services_list": result["services_list"],
        "date": result["date"],
        "excel_check": result["excel"],
        "is_first": True,
        "final_summary": "",
        "google_mail_message": [],
        "google_calendar_message": [],
        "github_commit_message": [],
        "username": "",
        "github_token": "",
        "is_file": False,
        "excel_obj": {},
        "file_summary": "",
        "messages": [
            AIMessage(
                content="🔄서비스(구글 메일, 구글 캘린더, 깃허브)와 날짜를 추출하는 중입니다..."
            )
        ],
    }


# 노드 : 서비스로 라우팅
def conditional_service_node(state: State) -> str:
    """services_list를 기반으로 다음 노드 결정"""
    services = state.get("services_list", [])

    if not services:  # 리스트가 비어있으면
        if state.get("is_first"):
            return "summary"
        else:
            return "is_file"

    # 첫 번째 서비스로 이동
    service = services[0]

    return service


def conditional_analyze_query_node(state: State) -> str:
    """analyze_query를 기반으로 다음 노드 결정"""
    is_file = state.get("is_file")
    if is_file:
        return "file"
    else:
        return "summary"


# 노드 : 엑셀 라우팅
def conditional_excel_node(state: State) -> str:
    """excel을 기반으로 다음 노드 결정"""
    excel_check = state.get("excel_check")

    if excel_check:
        return "excel"
    else:
        return END


# 노드 : gmail_message
def create_gmail_message_node(state: State) -> State:
    print("======== gmail_message ==========")
    services_list = state.get("services_list")
    services_list.pop(0)

    gmail_service = get_google_service("gmail")

    # 날짜 문자열을 datetime 객체로 변환
    start_date_str = state.get("date").get("start_date")
    end_date_str = state.get("date").get("end_date")

    # YYYY/MM/DD 형식의 문자열을 datetime 객체로 변환
    start_date = datetime.strptime(start_date_str, "%Y/%m/%d")
    end_date = datetime.strptime(end_date_str, "%Y/%m/%d")

    gmail_message = get_gmail_messages(
        service=gmail_service, start_date=start_date, end_date=end_date
    )
    print(gmail_message)

    return {
        "services_list": services_list,
        "google_mail_message": gmail_message,
        "is_first": False,
        "messages": [
            AIMessage(
                content=f"🔄구글 메일 데이터를 추출하는 중입니다...({start_date_str} ~ {end_date_str})"
            )
        ],
    }


# 노드 : calendar_message
def create_calendar_message_node(state: State) -> State:
    print("======== calendar_message ==========")
    services_list = state.get("services_list")
    services_list.pop(0)

    calendar_service = get_google_service("calendar")

    start_date_str = state.get("date").get("start_date")
    end_date_str = state.get("date").get("end_date")

    # YYYY/MM/DD 형식의 문자열을 datetime 객체로 변환하고 시간대 정보 추가
    korea_tz = pytz.timezone("Asia/Seoul")
    start_date = datetime.strptime(start_date_str, "%Y/%m/%d").replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=korea_tz
    )
    end_date = datetime.strptime(end_date_str, "%Y/%m/%d").replace(
        hour=23, minute=59, second=59, microsecond=999999, tzinfo=korea_tz
    )

    calendar_message = get_calendar_events(
        service=calendar_service, start_date=start_date, end_date=end_date
    )
    print(calendar_message)

    return {
        "services_list": services_list,
        "google_calendar_message": calendar_message,
        "is_first": False,
        "messages": [
            AIMessage(
                content=f"🔄구글 캘린더 데이터를 추출하는 중입니다...({start_date_str} ~ {end_date_str})"
            )
        ],
    }


# 노드 : github_token
def create_github_token_node(state: State) -> State:
    print("======== github_token ==========")
    services_list = state.get("services_list")
    services_list.pop(0)

    return {
        "services_list": services_list,
        "messages": [
            AIMessage(
                content="깃허브 사용자 ID와 토큰을 입력해주세요. ex)username, ghp_123..."
            )
        ],
    }


# 노드 : github_commit_message
def create_github_commit_message_node(state: State) -> State:
    print("======== github_commit_message ==========")

    start_date_str = state.get("date").get("start_date")
    end_date_str = state.get("date").get("end_date")

    # YYYY/MM/DD 형식의 문자열을 datetime 객체로 변환하고 시간대 정보 추가
    korea_tz = pytz.timezone("Asia/Seoul")
    start_date = datetime.strptime(start_date_str, "%Y/%m/%d").replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=korea_tz
    )
    end_date = datetime.strptime(end_date_str, "%Y/%m/%d").replace(
        hour=23, minute=59, second=59, microsecond=999999, tzinfo=korea_tz
    )

    system_prompt = """
    당신은 사용자의 입력에서 깃허브 사용자 ID와 깃허브 토큰을 추출하는 전문가입니다.

    ##절대 따라야할 규칙##
    - 사용자의 입력에서 깃허브 사용자 ID와 깃허브 토큰을 추출해야 합니다
    - 깃허브 토큰은 40자리이상 영문과 숫자로 이루어져 있습니다
    - 깃허브 토큰은 ghp_ 로 시작합니다
    - 반드시 JSON 형식으로만 출력해야 합니다
    - 다른 형식이나 설명은 절대 출력하지 마세요

    입력 예시:
    "username ghp_1234567890abcdef1234567890abcdef123456"

    출력 형식 (반드시 이 형식만 사용):
    {{
        "username": "깃허브 사용자 ID",
        "github_token": "깃허브 토큰"
    }}
    """

    user_prompt = """
    사용자의 입력에서 깃허브 사용자 ID와 깃허브 토큰을 추출하여 반환해주세요.

    [User Input]
    {user_input}

    [extraction]
    """

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", user_prompt)]
    )
    github_token_chain = prompt | llm | StrOutputParser()

    result = github_token_chain.invoke(
        {
            "user_input": state["user_input"],
        }
    )
    print("======== create_github_commit_message_node ==========")
    print(result)
    print("======== create_github_commit_message_node ==========")

    result = json.loads(result)

    print(result)

    commit_list, status_code = get_commits(
        username=result["username"],
        github_token=result["github_token"],
        start_date=start_date,
        end_date=end_date,
    )

    print(commit_list)

    if status_code != 200:
        return {
            "github_commit_message": [],
            "is_first": False,
            "messages": [
                AIMessage(
                    content=f"깃허브 사용자ID와 토큰 정보가 잘못되어 조회에 실패하였습니다.({start_date_str} ~ {end_date_str})"
                )
            ],
        }

    return {
        "github_commit_message": commit_list,
        "is_first": False,
        "messages": [
            AIMessage(
                content=f"🔄깃허브 커밋 데이터를 추출하는 중입니다...({start_date_str} ~ {end_date_str})"
            )
        ],
    }


def check_file_node(state: State) -> State:
    print("======== check_file_node ==========")

    return {
        "messages": [AIMessage(content="추가적으로 정리할 파일이 있나요?")],
    }


def analyze_query_node(state: State) -> State:
    print("======== analyze_query_node ==========")
    system_prompt = """
    당신은 사용자의 입력에서 긍정인지 부정인지 판단하는 전문가입니다.

    ##절대 따라야할 규칙##
    - 사용자의 입력에서 긍정인지 부정인지 판단해야 합니다
    - 반드시 yes 또는 no 로 출력해야 합니다
    - 다른 형식이나 설명은 절대 출력하지 마세요

    입력 예시:
    "어", "맞아", "있습니다.", "있어", "있어요" 등

    출력 형식 (반드시 이 형식만 사용):
    yes 또는 no
    """

    user_prompt = """
    사용자의 입력에서 긍정인지 부정인지 판단하여 반환해주세요.

    [User Input]
    {user_input}

    """

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", user_prompt)]
    )
    query_chain = prompt | llm | StrOutputParser()
    result = query_chain.invoke(
        {
            "user_input": state["user_input"],
        }
    )

    print(result)

    if result == "yes":
        return {
            "is_file": True,
        }
    else:
        return {
            "is_file": False,
        }


def create_file_node(state: State) -> State:
    print("======== create_file_node ==========")
    return {
        "messages": [AIMessage(content="파일 분석을 완료하였습니다.")],
        "is_file": False,
    }


# 노드 : 요약 정리노드
def create_summary_node(state: State) -> State:

    print("======== summary_node ==========")

    system_prompt = """
    주어진 데이터를 정리해서 표로 만드세요.
    *중요*만약 is_first가 True 라면 표를 만들지 말고 사용자에게 입력이 잘못되어서, 구글 메일, 구글 캘린더, 깃허브 중에서 어떤 업무를 정리할지 친절하게 안내해주세요.
    *중요*만약 is_first가 False 라면 데이터를 gmail_message, calendar_message, github_commit_message, file_summary 를 정리해서 표로 만드세요.
    gmail_message, calendar_message, github_commit_message각 내용은 길지 않게 요약해서 정리해야 합니다.
    file_summary 는 요약하지 말고 내용 **한글로만 번역만**해서 정리해야 합니다.
    표의 열 이름은 시간, 요약, 서비스명 이며 각 데이터는 시간, 요약, 서비스명 형식으로 정리해야 합니다.
    날짜는 YYYY-MM-DD HH:MM:SS 형식으로 정리해야 합니다.
    표 외에는 다른말은 하지마세요
    
    [Data]
    is_first: {is_first}
    gmail_message: {gmail_message}
    calendar_message: {calendar_message}
    github_commit_message: {github_commit_message}
    file_summary: {file_summary}
    """

    user_prompt = """
    데이터를 정리해주세요
    """

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", user_prompt)]
    )
    summary_chain = prompt | llm | StrOutputParser()

    result = summary_chain.invoke(
        {
            "is_first": state.get("is_first", True),
            "gmail_message": state.get("google_mail_message", []),
            "calendar_message": state.get("google_calendar_message", []),
            "github_commit_message": state.get("github_commit_message", []),
            "file_summary": state.get("file_summary", ""),
        }
    )

    print(result)
    return {
        "final_summary": result,
        "messages": [AIMessage(content=result)],
    }


# 노드 : 엑셀 생성노드
def create_excel_node(state: State) -> State:
    print("======== excel_node ==========")
    try:
        # final_summary 데이터 가져오기
        final_summary = state.get("final_summary")

        system_prompt = """
        당신은 주어진 데이터를 pandas DataFrame에 맞는 JSON 형식으로 변환하는 전문가입니다.
        - 반드시 JSON 형식으로만 출력해야 합니다
        - 다른 형식이나 설명은 절대 출력하지 마세요
        
        입력 데이터는 다음과 같은 형식입니다:
        | 시간 | 요약 | 서비스명 |
        |-----|------|----------|
        | 2025-06-09 09:00:00 | 교육 | 구글 캘린더 |

        출력은 다음과 같은 JSON 형식이어야 합니다:
        [
            {{
                "시간": "2025-06-09 09:00:00",
                "요약": "교육", 
                "서비스명": "구글 캘린더"
            }},
            ...
        ]

        규칙:
        1. 모든 데이터는 리스트 안의 딕셔너리 형태로 변환되어야 합니다
        2. 각 딕셔너리는 "시간", "요약", "서비스명" 키를 가져야 합니다
        """

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("user", "{user_input}")]
        )
        # LLM을 사용하여 데이터 정규화
        excel_chain = prompt | llm | StrOutputParser()

        result = excel_chain.invoke(
            {
                "user_input": final_summary,
            }
        )

        data_dict = json.loads(result)
        print(data_dict)

        # 엑셀 파일 생성
        df = pd.DataFrame(data_dict)

        return {
            "messages": [
                AIMessage(content=f"엑셀 데이터를 생성하였습니다.\n\n{data_dict}")
            ],
            "excel_obj": data_dict,
        }

    except Exception as e:
        return {
            "messages": [AIMessage(content=f"엑셀 파일 생성 중 오류 발생: {str(e)}")]
        }


def upload_excel_to_blob(state: State) -> State:
    print("======== upload_excel_to_blob ==========")

    # 현재 시간을 파일명에 포함
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f"work_summary_{current_time}.xlsx"

    # 여기 수정해야힘
    # # DataFrame을 엑셀 파일로 변환
    # excel_buffer = io.BytesIO()
    # df.to_excel(excel_buffer, index=False, engine="openpyxl")
    # excel_buffer.seek(0)

    # # Azure Blob Storage 연결
    # connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    # container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")

    # blob_service_client = BlobServiceClient.from_connection_string(
    #     connection_string
    # )
    # container_client = blob_service_client.get_container_client(container_name)

    # # Blob에 파일 업로드
    # blob_client = container_client.get_blob_client(excel_filename)
    # blob_client.upload_blob(excel_buffer.getvalue(), overwrite=True)

    # # Blob URL 생성
    # blob_url = blob_client.url

    # print(f"엑셀 파일이 Azure Blob Storage에 업로드되었습니다: {blob_url}")

    # # state에 blob URL 저장
    # state["excel_obj"] = {"blob_url": blob_url}
    pass


def create_graph():
    """그래프를 생성합니다."""
    # 그래프 생성
    workflow = StateGraph(State)

    # 노드 추가
    workflow.add_node("extraction_node", extraction_node)
    workflow.add_node("gmail_node", create_gmail_message_node)
    workflow.add_node("calendar_node", create_calendar_message_node)
    workflow.add_node("github_token_node", create_github_token_node)
    workflow.add_node("github_node", create_github_commit_message_node)
    workflow.add_node("check_file_node", check_file_node)
    workflow.add_node("analyze_query_node", analyze_query_node)
    workflow.add_node("file_node", create_file_node)
    workflow.add_node("summary_node", create_summary_node)
    workflow.add_node("excel_node", create_excel_node)
    workflow.add_node("upload_excel_to_blob", upload_excel_to_blob)

    workflow.add_edge(START, "extraction_node")
    workflow.add_edge("github_token_node", "github_node")
    workflow.add_edge("check_file_node", "analyze_query_node")
    workflow.add_edge("file_node", "summary_node")
    workflow.add_edge("excel_node", "upload_excel_to_blob")
    workflow.add_edge("upload_excel_to_blob", END)

    # 엣지 추가
    workflow.add_conditional_edges(
        "extraction_node",
        conditional_service_node,
        {
            "gmail": "gmail_node",
            "calendar": "calendar_node",
            "github": "github_token_node",
            "summary": "summary_node",
        },
    )

    workflow.add_conditional_edges(
        "gmail_node",
        conditional_service_node,
        {
            "calendar": "calendar_node",
            "github": "github_token_node",
            "is_file": "check_file_node",
        },
    )

    workflow.add_conditional_edges(
        "calendar_node",
        conditional_service_node,
        {
            "gmail": "gmail_node",
            "github": "github_token_node",
            "is_file": "check_file_node",
        },
    )

    workflow.add_conditional_edges(
        "github_node",
        conditional_service_node,
        {
            "gmail": "gmail_node",
            "calendar": "calendar_node",
            "is_file": "check_file_node",
        },
    )

    workflow.add_conditional_edges(
        "analyze_query_node",
        conditional_analyze_query_node,
        {
            "file": "file_node",
            "summary": "summary_node",
        },
    )

    workflow.add_conditional_edges(
        "summary_node",
        conditional_excel_node,
        {
            "excel": "excel_node",
            END: END,
        },
    )

    return workflow.compile(
        checkpointer=MemorySaver(),
        interrupt_after=["github_token_node", "check_file_node"],
        interrupt_before=["file_node"],
    )


# test = {
#     "user_input": "안녕하세요 어제 커밋 정리해주세요",
#     "messages": [HumanMessage(content="안녕하세요 어제 커밋 정리해주세요")],
# }


def process(
    user_input: dict[str, str],
    graph: CompiledStateGraph,
    config: Optional[RunnableConfig] = {},
    github: bool = False,
    file_upload: bool = False,
    file_success: bool = False,
):
    """사용자 입력을 처리합니다."""

    # github 토큰 입력
    if github:
        graph.update_state(config, user_input)
        print("==========   github  ==========")
        for step in graph.stream(None, config, stream_mode="values"):
            print("============================================================")
            print(step)
            print("============================================================")
            yield step
    elif file_upload:
        graph.update_state(config, user_input)
        print("==========   file_upload   ==========")
        for step in graph.stream(None, config, stream_mode="values"):
            print("============================================================")
            print(step)
            print("============================================================")
            yield step
    elif file_success:
        print("==========   file_success  ==========")
        is_first = True
        graph.update_state(config, user_input)
        for step in graph.stream(None, config, stream_mode="values"):
            print("============================================================")
            if is_first:
                is_first = False
                continue
            print(step)
            print("============================================================")
            yield step
    else:
        print("!!!!!!!!!!!!!!")
        for step in graph.stream(user_input, config, stream_mode="values"):
            print("============================================================")
            print(step)
            print("============================================================")
            yield step
