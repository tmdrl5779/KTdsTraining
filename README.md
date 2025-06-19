# 📝업무 정리 Agent

## 사용 기술
- Azure openai
- Azure AI Video Indexer
- Azure web app
- Azure Storage Account
- LangChain
- Langgraph
- Streamlit

## 기능
- 사용자의 입력을 분석하여 날짜, 서비스를 추출합니다.
- 추출된 날짜로 해당 서비스에 API 를 호출하여 데이터를 수집합니다.
- 수집한 데이터를 LLM을 통해 정제합니다.
- 추가로 정리가 필요한 파일(동영상만 지원)을 업로드하여 파일은 분석합니다.
- 분석된 파일을 LLM 을 통해 정제합니다.
- 최종 결과로 해당 데이터를 표로 생성하여 사용자 화면에 노출합니다.

## 플로우
![image](https://github.com/user-attachments/assets/f5c19eb1-0c51-429b-9dba-dcd52ea13bba)


## UI
사용자의 질의에 따라 작업을 수행합니다.
![image](https://github.com/user-attachments/assets/c8a724f4-c98c-45d4-864f-82fa93a635cd)

최종 결과를 저장합니다.
![image](https://github.com/user-attachments/assets/aa3265c9-c91c-4524-8691-6aaae1cb0633)

Azure AI Video Indexer 접근에 필요한 액세스 토큰을 설정합니다.
![image](https://github.com/user-attachments/assets/a245c0b2-41c5-4c4c-8036-cc19ec453d7c)
