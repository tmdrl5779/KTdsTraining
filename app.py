import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import streamlit as st
from openai_common import create_chat_model
from langchain_core.messages.chat import ChatMessage
import graph as gh
from langchain_core.messages import HumanMessage
from video_indexer import (
    find_video_id_by_name,
    delete_video,
    upload_video,
    create_summary,
    get_summary,
    get_video_index,
)
import time
from streamlit_option_menu import option_menu
from datetime import datetime
import traceback


load_dotenv()

st.set_page_config(layout="wide")

st.title("📝 업무 정리 Agent 📝")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "graph" not in st.session_state:
    st.session_state["graph"] = gh.create_graph()

if "llm" not in st.session_state:
    st.session_state["llm"] = create_chat_model("openai")

if "config" not in st.session_state:
    st.session_state["config"] = {"configurable": {"thread_id": "1"}}

if "access_token" not in st.session_state:
    st.session_state["access_token"] = None

if "summary" not in st.session_state:
    st.session_state["summary"] = []


# 새로운 메시지를 추가
def add_message(role, message):
    st.session_state["messages"].append(ChatMessage(role=role, content=message))


# 메세지 출력
def print_messages():
    for chat_message in st.session_state["messages"]:
        if chat_message["role"] == "user":
            st.chat_message("user", avatar="🧑‍💻").markdown(chat_message["content"])
        elif chat_message["role"] == "assistant":
            st.chat_message("assistant", avatar="🤖").markdown(chat_message["content"])


# 사이드바 생성
with st.sidebar:
    selected = option_menu(
        "메뉴",
        ["채팅", "문서 정리 결과", "설정"],
        icons=["chat", "file-earmark-text"],
        menu_icon="cast",
        default_index=0,
    )

    # 구분선
    st.divider()

    # 구분선
    st.divider()

    # 도움말 섹션
    with st.expander("ℹ️ 도움말"):
        st.info(
            """
        - 그래프는 현재 워크플로우의 구조를 보여줍니다
        """
        )


# 1. dialog 함수 정의
@st.dialog("동영상 파일 업로드")
def upload_dialog():
    uploaded_file = st.file_uploader("동영상 파일을 선택하세요", type=["mp4"])

    input = {
        "file_summary": "",
    }

    if uploaded_file is not None:

        st.info("Azure Video Indexer에 영상을 업로드 중입니다...")

        access_token = st.session_state["access_token"]

        if access_token is None:
            error_message = "액세스 토큰이 등록되지 않았습니다."
            st.session_state.messages.append(
                {"role": "assistant", "content": error_message}
            )
            st.chat_message("assistant", avatar="🤖").markdown(error_message)

            k = 0
            for step in gh.process(
                input, graph, st.session_state["config"], file_success=True
            ):
                # messages의 마지막 메시지를 표시
                last_message = step["messages"][-1]
                if last_message.type == "ai":
                    st.session_state.messages.append(
                        {"role": "assistant", "content": last_message.content}
                    )
                if "final_summary" in step and k != 0:
                    if "is_first" in step:
                        print(step["is_first"], step["final_summary"])
                        if not step["is_first"] and step["final_summary"]:
                            print("<<<<<<<<<<<<<<<<<<<<<<<")
                            st.session_state["summary"].append(
                                {
                                    "date": datetime.now().strftime(
                                        "%Y-%m-%d-%H-%M-%S"
                                    ),
                                    "final_summary": step["final_summary"],
                                }
                            )
                k += 1
            st.rerun()

        try:
            existing_video_id = find_video_id_by_name(access_token, uploaded_file)
            print(existing_video_id)
            if existing_video_id:
                delete_video(access_token, existing_video_id)

            response = upload_video(access_token, uploaded_file)
            st.success("업로드 완료! 영상 분석 중... (최대 1~2분 소요)")
            # 테스트트

            time.sleep(1)
            st.session_state.messages.append({"role": "assistant", "content": response})

            video_id = response["id"]
            # 인덱싱이 끝날 때까지 대기
            progress = st.progress(0)
            i = 0
            while True:
                time.sleep(5)
                index = get_video_index(access_token, video_id)
                state = index["state"]
                print(state)
                if i < 15:
                    progress.progress((i + 1) * 5)
                if state == "Processed":
                    break
                i += 1

            progress.progress(100)
            summary = create_summary(access_token, video_id)
            summary_id = summary["id"]
            st.success("분석 완료! 요약 중... ")

            print(summary_id)

            # 인덱싱이 끝날 때까지 대기
            progress = st.progress(0)
            j = 0

            while True:
                time.sleep(5)
                summary = get_summary(access_token, video_id, summary_id)
                state = summary["state"]
                print(state)
                if j < 15:
                    progress.progress((j + 1) * 5)
                if state == "Processed":
                    break
                j += 1

            progress.progress(100)

            print(summary["summary"])

            st.success("요약 완료! ")

            file_summary = summary["summary"]
            input["file_summary"] = file_summary

            k = 0
            for step in gh.process(
                input, graph, st.session_state["config"], file_success=True
            ):
                # messages의 마지막 메시지를 표시
                last_message = step["messages"][-1]
                if last_message.type == "ai":
                    # st.chat_message("assistant", avatar="🤖").markdown(last_message.content)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": last_message.content}
                    )

                if "final_summary" in step and k != 0:
                    if "is_first" in step:
                        print(step["is_first"], step["final_summary"])
                        if not step["is_first"] and step["final_summary"]:
                            print("<<<<<<<<<<<<<<<<<<<<<<<")
                            st.session_state["summary"].append(
                                {
                                    "date": datetime.now().strftime(
                                        "%Y-%m-%d-%H-%M-%S"
                                    ),
                                    "final_summary": step["final_summary"],
                                }
                            )
                k += 1

            st.rerun()
        except Exception as e:
            full_traceback = traceback.format_exc()
            error_message = f"파일 분석 중 오류가 발생했습니다. {e}\n\n{full_traceback}"
            st.session_state.messages.append(
                {"role": "assistant", "content": error_message}
            )
            st.chat_message("assistant", avatar="🤖").markdown(error_message)

            k = 0

            for step in gh.process(
                input, graph, st.session_state["config"], file_success=True
            ):
                # messages의 마지막 메시지를 표시
                last_message = step["messages"][-1]
                if last_message.type == "ai":
                    st.session_state.messages.append(
                        {"role": "assistant", "content": last_message.content}
                    )
                if "final_summary" in step and k != 0:
                    if "is_first" in step:
                        print(step["is_first"], step["final_summary"])
                        if not step["is_first"] and step["final_summary"]:
                            print("<<<<<<<<<<<<<<<<<<<<<<<")
                            st.session_state["summary"].append(
                                {
                                    "date": datetime.now().strftime(
                                        "%Y-%m-%d-%H-%M-%S"
                                    ),
                                    "final_summary": step["final_summary"],
                                }
                            )
                k += 1
            st.rerun()


if selected == "문서 정리 결과":
    summary_list = st.session_state.get("summary", [])
    if summary_list:
        options = [(f"{i+1}. {s['date']}") for i, s in enumerate(summary_list)]
        selected_idx = st.selectbox(
            "정리된 문서 선택",
            range(len(summary_list)),
            format_func=lambda i: options[i],
        )
        st.markdown(summary_list[selected_idx]["final_summary"])
    else:
        st.info("아직 정리된 문서가 없습니다.")

if selected == "설정":
    col1, col2 = st.columns(2)
    # 액세스 토큰 입력 섹션
    with col1:
        st.subheader("Azure Video Indexer 설정")
        access_token = st.text_input("액세스 토큰을 입력하세요", type="password")
        if st.button("토큰 저장"):
            if access_token:
                st.session_state["access_token"] = access_token
                st.success("액세스 토큰이 저장되었습니다!")
            else:
                st.error("액세스 토큰을 입력해주세요!")

    # 그래프 섹션
    with col2:
        st.subheader("워크플로우 구조")
        if "graph" in st.session_state:
            st.image(
                st.session_state["graph"].get_graph().draw_mermaid_png(),
                caption="현재 워크플로우 구조",
                use_container_width=True,
            )

if selected == "채팅":
    print_messages()

    # Handle user input
    if user_input := st.chat_input("메세지를 입력하세요"):
        graph = st.session_state["graph"]

        # 사용자 입력
        st.chat_message("user", avatar="🧑‍💻").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        input = {
            "user_input": user_input,
            "messages": [HumanMessage(content=user_input)],
        }

        github = False
        file_upload = False

        if len(st.session_state["messages"]) > 1:
            previous_message = st.session_state["messages"][-2]["content"]
            if (
                previous_message
                == "깃허브 사용자 ID와 토큰을 입력해주세요. ex)username, ghp_123..."
            ):
                github = True
            elif previous_message == "추가적으로 정리할 파일이 있나요?":
                file_upload = True

        k = 0
        # process 함수를 사용하여 상태 변화를 스트리밍
        for step in gh.process(
            input,
            graph,
            st.session_state["config"],
            github=github,
            file_upload=file_upload,
        ):
            # messages의 마지막 메시지를 표시
            last_message = step["messages"][-1]
            if last_message.type == "ai":
                st.chat_message("assistant", avatar="🤖").markdown(last_message.content)
                st.session_state.messages.append(
                    {"role": "assistant", "content": last_message.content}
                )

            if "final_summary" in step and k != 0:
                if "is_first" in step:
                    print(step["is_first"], step["final_summary"])
                    if not step["is_first"] and step["final_summary"]:
                        print("<<<<<<<<<<<<<<<<<<<<<<<")
                        st.session_state["summary"].append(
                            {
                                "date": datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
                                "final_summary": step["final_summary"],
                            }
                        )
            k += 1
            # is_file이 있는 경우에만 모달 창 띄우기
            if "is_file" in step:
                if step["is_file"]:
                    upload_dialog()


# if len(st.session_state["messages"]) > 0:
#     previous_message2 = st.session_state["messages"][-1]["content"]
#     if previous_message2 == "파일 분석을 위해 파일을 업로드해주세요":
#         upload_dialog()
