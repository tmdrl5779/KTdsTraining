from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
import os
from langchain_openai import ChatOpenAI
from langchain_openai import AzureChatOpenAI
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel

# API KEY 정보로드
load_dotenv()

def create_chat_model(client: str):
    if client == "azure":
        return AzureAIChatCompletionsModel(
            endpoint=os.environ["AZURE_INFERENCE_ENDPOINT"],
            credential=os.environ["AZURE_INFERENCE_CREDENTIAL"],
            model=os.getenv("CHAT_MODEL"),
        )
    elif client == "openai":
        return ChatOpenAI(model=os.getenv("CHAT_MODEL"))


def test_chat_model():
    messages = [
        SystemMessage(content="you are a helpful assistant"),
        HumanMessage(content="안녕!"),
    ]

    model = create_chat_model("openai")

    print(model.invoke(messages).content)
