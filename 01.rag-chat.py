import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import streamlit as st


def main():
    load_dotenv()

    # Get environment variables
    openai_endpoint = os.getenv("OPENAI_ENDPOINT")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    chat_model = os.getenv("CHAT_MODEL")
    embedding_model = os.getenv("EMBEDDING_MODEL")
    search_endpoint = os.getenv("SEARCH_ENDPOINT")
    search_api_key = os.getenv("SEARCH_API_KEY")
    index_name = os.getenv("INDEX_NAME")

    # Initialize Azure OpenAI client
    chat_client = AzureOpenAI(
        api_version="2024-12-01-preview",
        azure_endpoint=openai_endpoint,
        api_key=openai_api_key,
    )

    st.title("Margie's Travel Assistant")
    st.title("Ask your travel-related questions below:")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "system",
                "content": "You are a travel assistant that provides information on travel services available from Margie's Travel.",
            }
        ]

    # Display chat history
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue

        st.chat_message(message["role"]).write(message["content"])

    # Function to get OpenAI response
    def get_openai_response(messages):
        rag_params = {
            "data_sources": [
                {
                    # he following params are used to search the index
                    "type": "azure_search",
                    "parameters": {
                        "endpoint": search_endpoint,
                        "index_name": index_name,
                        "authentication": {
                            "type": "api_key",
                            "key": search_api_key,
                        },
                        # The following params are used to vectorize the query
                        "query_type": "vector",
                        "embedding_dependency": {
                            "type": "deployment_name",
                            "deployment_name": embedding_model,
                        },
                    },
                }
            ],
        }

        # Submit the chat request with RAG parameters
        response = chat_client.chat.completions.create(
            model=chat_model, messages=messages, extra_body=rag_params
        )

        return response.choices[0].message.content

    # Handle user input
    if user_input := st.chat_input("메세지를 입력하세요"):
        # Save and display user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        # Generate and display assistant response
        with st.spinner("응답을 기다리는 중..."):
            assistant_response = get_openai_response(st.session_state.messages)

        st.session_state.messages.append(
            {"role": "assistant", "content": assistant_response}
        )
        st.chat_message("assistant").write(assistant_response)


if __name__ == "__main__":
    main()
