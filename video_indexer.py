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


def get_access_token():
    url = f"https://api.videoindexer.ai/auth/{LOCATION}/Accounts/{ACCOUNT_ID}/AccessToken?allowEdit=true"
    headers = {"Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY}
    response = requests.get(url, headers=headers)
    return response.text


def find_video_id_by_name(access_token, video_name):
    print("access_token", access_token)
    print("video_name", video_name)
    print("location", LOCATION)
    print("account_id", ACCOUNT_ID)
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
