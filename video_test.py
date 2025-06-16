import streamlit as st
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Azure Video Indexer 정보
SUBSCRIPTION_KEY = os.environ["SUBSCRIPTION_KEY"]
LOCATION = os.environ["LOCATION"]
ACCOUNT_ID = os.environ["ACCOUNT_ID"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]


def get_access_token():
    url = f"https://api.videoindexer.ai/auth/{LOCATION}/Accounts/{ACCOUNT_ID}/AccessToken?allowEdit=true"
    headers = {"Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY}
    response = requests.get(url, headers=headers)
    return response.text


def find_video_id_by_name(access_token, video_name):
    url = f"https://api.videoindexer.ai/{LOCATION}/Accounts/{ACCOUNT_ID}/Videos?accessToken={access_token}&name={video_name}"
    response = requests.get(url)
    videos = response.json().get("results", [])
    for video in videos:
        print(video.get("name"), video_name.name)
        if video.get("name") == video_name.name:
            return video.get("id")
    return None


def delete_video(access_token, video_id):
    url = f"https://api.videoindexer.ai/{LOCATION}/Accounts/{ACCOUNT_ID}/Videos/{video_id}?accessToken={access_token}"
    try:
        requests.delete(url)
    except Exception as e:
        print(e)


def upload_video(access_token, video_file):
    url = f"https://api.videoindexer.ai/{LOCATION}/Accounts/{ACCOUNT_ID}/Videos?accessToken={access_token}&name={video_file.name}"
    files = {"file": (video_file.name, video_file, "video/mp4")}
    response = requests.post(url, files=files)
    print(response.json())
    return response.json()["id"]


def create_summary(access_token, video_id):
    url = f"https://api.videoindexer.ai/{LOCATION}/Accounts/{ACCOUNT_ID}/Videos/{video_id}/Summaries/Textual?accessToken={access_token}&length=Short&style=Formal&deploymentName=gpt-4o-mini"
    response = requests.post(url)
    return response.json()


def get_summary(access_token, video_id, summary_id):
    url = f"https://api.videoindexer.ai/{LOCATION}/Accounts/{ACCOUNT_ID}/Videos/{video_id}/Summaries/Textual/{summary_id}?accessToken={access_token}"

    response = requests.get(url)
    return response.json()


def get_video_index(access_token, video_id):
    url = f"https://api.videoindexer.ai/{LOCATION}/Accounts/{ACCOUNT_ID}/Videos/{video_id}/Index?accessToken={access_token}"
    response = requests.get(url)
    return response.json()


# 1. dialog 함수 정의
@st.dialog("동영상 파일 업로드")
def upload_dialog():
    uploaded_file = st.file_uploader(
        "동영상 파일을 선택하세요", type=["mp4", "mov", "avi"]
    )
    if uploaded_file is not None:

        st.info("Azure Video Indexer에 영상을 업로드 중입니다...")
        access_token = ACCESS_TOKEN

        existing_video_id = find_video_id_by_name(access_token, uploaded_file)
        print(existing_video_id)
        if existing_video_id:
            delete_video(access_token, existing_video_id)

        video_id = upload_video(access_token, uploaded_file)
        st.success("업로드 완료! 영상 분석 중... (최대 1~2분 소요)")

        # 인덱싱이 끝날 때까지 대기
        progress = st.progress(0)
        # for i in range(20):
        i = 0
        while True:
            time.sleep(10)
            index = get_video_index(access_token, video_id)
            state = index["state"]
            print(state)
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
            time.sleep(10)
            summary = get_summary(access_token, video_id, summary_id)
            state = summary["state"]
            print(state)
            progress.progress((j + 1) * 5)
            if state == "Processed":
                break
            j += 1

        progress.progress(100)

        print(summary["summary"])

        st.success("요약 완료! ")

        # 요약 결과 추출
        # summary = index.get("summarizedInsights", {}).get("shortSummaries", [])
        # if summary:
        #     st.session_state["summary"] = summary
        #     st.success("요약이 완료되었습니다! 메인화면에서 결과를 확인하세요.")
        # else:
        #     st.warning("요약 결과를 찾을 수 없습니다.")


# upload_dialog()

print(get_access_token())
