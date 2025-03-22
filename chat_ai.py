import os
# 플라스크 라이브러리 api 서버용
from flask import Flask, request, make_response, Response, jsonify
# 크로스도메인 문제 해결 라이브러리 (웹서버와 포트나 도메인이 다르기 때문에 필요)
from flask_cors import CORS
from openai import OpenAI
from langchain_openai import ChatOpenAI  # chatgpt 연결 클래스
from langchain.memory import ChatMessageHistory  # 버퍼에 데이터 넣기
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage  # 프롬프트 생성용 클래스
from langchain.output_parsers import PydanticOutputParser  # 출력 형태 고정하기 위해 활용
from pydantic import BaseModel, Field, validator  # 최신 Pydantic v2를 직접 사용

from typing import Literal  # Literal 임포트
import tiktoken
from datetime import datetime
import json



GPT_MODEL = 'gpt-4o'


chatGPT = ChatOpenAI(
    model=GPT_MODEL,
    temperature=0,
    verbose=False,
    max_tokens=4096,
    timeout=None
)



def num_tokens_from_messages(messages, model="gpt-4o"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        "gpt-4-turbo",
        "gpt-4-turbo-2024-04-09",
        "gpt-4o",
        "gpt-4o-2024-05-13",
    }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4o" in model:
        print(
            "Warning: gpt-4o may update over time. Returning num tokens assuming gpt-4o-2024-05-13.")
        return num_tokens_from_messages(messages, model="gpt-4o-2024-05-13")
    elif "gpt-4" in model:
        print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        num_tokens += tokens_per_name
        num_tokens += len(encoding.encode(message.content))

    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens



# Response Type 정의
class Response_Type(BaseModel):
    Speaker: str = Field(description="The speaker of the message")
    chat: str = Field(description="That player's conversation")
    predictions : str = Field(description="My predictions for each player's class based on conversations to date")
    point: str = Field(description="""Players who want to hear the next story""")


def chat_withGPT(player, chat_history, players, chat_max_token_limit=65536):
    while num_tokens_from_messages(str(chat_history), model=GPT_MODEL) > chat_max_token_limit:
        chat_history.pop(0)

    SYS_PROMPT = f"""An AI chatbot that participated in a game of mafia.
Determine your conversational personality and tone of voice based on your player information.
Refer to the game rules and act according to the game role assigned to you.
chat history of the participants to continue the conversation.
After answering, be sure to ask one of the remaining players to continue the conversation.

PLAYER INFO :
{player.get_prompt_charactor()}

GAME RULES :

Remaining players :
{[p.name for p in players if p.alive]}

PREV PREDICTION :
{player.get_last_prediction()}

CHAT HISTORY: :
{str(chat_history)}
    """

    output_parser = PydanticOutputParser(pydantic_object=Response_Type)


    chatml = [SystemMessage(content=SYS_PROMPT)] \
            + SystemMessage(content=output_parser.get_format_instructions())


    result = chatGPT.stream(chatml)

    chunks = ""

    for chunk in result:
        chunks += chunk.content
        yield chunk.content

    # JSON 파싱 후 반환
    try:
        return json.loads(chunks)  # response_text → chunks 로 변경
    except json.JSONDecodeError:
        return None  # JSON 변환 실패 시 None 반환
