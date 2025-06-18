from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
import os
from langchain_openai import ChatOpenAI
from langchain_openai import AzureChatOpenAI
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel


# API KEY 정보로드
load_dotenv()


def create_chat_model(client: str):
    print(os.getenv("AZURE_INFERENCE_ENDPOINT"))
    print(os.getenv("AZURE_INFERENCE_CREDENTIAL"))
    print(os.getenv("CHAT_MODEL"))
    print(os.getenv("AZURE_INFERENCE_API_VERSION"))

    if client == "azure":
        return AzureChatOpenAI(
            azure_endpoint=os.environ["AZURE_INFERENCE_ENDPOINT"],
            api_key=os.environ["AZURE_INFERENCE_CREDENTIAL"],
            azure_deployment=os.getenv("CHAT_MODEL"),
            api_version=os.getenv("AZURE_INFERENCE_API_VERSION"),
        )
    elif client == "openai":
        return ChatOpenAI(model=os.getenv("CHAT_MODEL"))
