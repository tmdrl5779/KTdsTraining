import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import streamlit as st
from openai_common import create_chat_model
from langchain_core.messages.chat import ChatMessage
import graph as gh
from langchain_core.messages import HumanMessage

st.title("🤖 업무 정리 Agent")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "graph" not in st.session_state:
    st.session_state["graph"] = gh.create_graph()

if "llm" not in st.session_state:
    st.session_state["llm"] = create_chat_model("openai")

if "config" not in st.session_state:
    st.session_state["config"] = {"configurable": {"thread_id": "1"}}


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
    st.title("📊 워크플로우 대시보드")

    # 그래프 섹션
    st.subheader("워크플로우 그래프")
    if "graph" in st.session_state:
        st.image(
            st.session_state["graph"].get_graph().draw_mermaid_png(),
            caption="현재 워크플로우 구조",
            use_container_width=True,
        )

    # 구분선
    st.divider()

    # 도움말 섹션
    with st.expander("ℹ️ 도움말"):
        st.info(
            """
        - 그래프는 현재 워크플로우의 구조를 보여줍니다
        """
        )


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

    if len(st.session_state["messages"]) > 1:
        previous_message = st.session_state["messages"][-2]["content"]
        if (
            previous_message
            == "깃허브 사용자 ID와 토큰을 입력해주세요. ex)username, ghp_123..."
        ):
            github = True

    # process 함수를 사용하여 상태 변화를 스트리밍
    for step in gh.process(input, graph, st.session_state["config"], github):
        # messages의 마지막 메시지를 표시
        last_message = step["messages"][-1]
        if last_message.type == "ai":
            st.chat_message("assistant", avatar="🤖").markdown(last_message.content)
            st.session_state.messages.append(
                {"role": "assistant", "content": last_message.content}
            )
