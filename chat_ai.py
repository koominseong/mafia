import os
# 크로스도메인 문제 해결 라이브러리 (웹서버와 포트나 도메인이 다르기 때문에 필요)
from openai import OpenAI
from langchain_openai import ChatOpenAI  # chatgpt 연결 클래스
# from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage  # 프롬프트 생성용 클래스
from langchain.output_parsers import PydanticOutputParser  # 출력 형태 고정하기 위해 활용
from pydantic import BaseModel, Field, validator  # 최신 Pydantic v2를 직접 사용

from typing import Literal  # Literal 임포트
import tiktoken
from datetime import datetime
import json
import re

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
    point: str = Field(description="""Players who want to hear the next story only from possible player except own""")


def chat_withGPT(player, chat_history, players, possible_targets, chat_max_token_limit=65536):
    # while num_tokens_from_messages(str(chat_history), model=GPT_MODEL) > chat_max_token_limit:
    #     chat_history.pop(0)

    SYS_PROMPT = f"""An AI chatbot that participated in a game of mafia.
Determine your conversational personality and tone of voice based on your player information.
Refer to the game rules and act according to the game role assigned to you.
chat history of the participants to continue the conversation.
After answering, be sure to ask one of the remaining players to continue the conversation.

PLAYER INFO :
{player.get_prompt_charactor()}

GAME RULES : 
-밤
 밤에 능력을 사용하는 직업은 능력을 사용할 대상을 정할 수 있다. 마피아들은 합의를 통해 죽일 사람 한 명을 정한다.
-낮
 낮이 되면 마피아의 처형을 비롯한 몇몇 직업의 능력 사용 결과가 공개된다. 단, 마피아가 처형 대상을 고르지 못해 아무도 죽지 않은 경우 "조용하게 밤이 지나갔습니다." 라는 문구가 나온다.
 토론 시간이 끝나면 투표 시간으로 넘어간다.
 여론 조사 화면이 투표 화면으로 변하며, 기본적으로 한 사람당 한 명에게 투표할 수 있다. 정치인의 투표는 두 표로 인정된다.(득표 결과창에서는 한 표로 표시됨)
 투표는 자기 자신에게도 할 수 있는데, 이를 '자투'라고 한다. 플레이어들이 토론을 통해 딱히 누군가를 투표로 죽일 필요가 없다고 판단하는 경우, 아무도 죽이지 않기 위해 자투를 하기로 합의하기도 한다.
 투표 시간이 끝나면 최종적인 득표 결과가 공개된다. 누가 누구에게 투표했는지는 공개되지 않는다.
 최다 득표자가 결정된 경우 아래 최후의 반론으로 넘어가며, 최다 득표자가 두 명 이상이거나 투표를 하지 않은 경우 바로 밤으로 넘어간다.
 투표에서 최다 득표자로 선정된 플레이어는 '최후의 반론'에 올라간다.
 최후의 반론 시간에는 최후에 반론에 올라간 해당 플레이어만 채팅을 할 수 있다.
 최후의 반론이 끝나면 마지막으로 해당 플레이어를 죽일 것인지 말 것인지 결정하는 찬반투표를 진행한다. 과반수 이상이 찬성을 선택하면 해당 플레이어는 처형당하고, 찬성보다 반대가 더 많다면 처형되지 않고 밤으로 넘어간다. 누가 찬성/반대를 했는지는 공개되지 않는다.
 이렇게 낮과 밤을 계속 번갈아가면서 진행하여 한쪽 팀이 이길 때까지 계속해서 진행하는 게임이다.
-승리조건
 어느 한 팀이 판정 시기에 승리 조건을 충족하는 즉시 해당 팀의 승리로 게임이 종료된다.
 판정 시기는 매일 2번으로 밤이 끝나고 낮으로 넘어갈 때, 찬반 투표가 종료되고 밤으로 넘어갈 때다.
 만약 복수의 팀이 동시에 승리 조건을 충족할 경우, 마피아팀 > 시민팀 순서로 우위를 갖는다.
 -마피아팀 승리 조건
  마피아팀의 머릿수≥시민팀의 머릿수
 -시민팀 승리 조건
  모든 마피아팀 사망
 정치인은 머릿수가 2개로 판정된다.
-직업 설명
 -마피아팀
  -마피아
   밤마다 플레이어 1명을 지목하여 죽일 수 있다
  -스파이
   밤마다 플레이어 중 하나를 선택하여 그 사람의 직업을 알아낼 수 있다.
   군인을 조사시 군인도 스파이가 누군지 알 수 있다.
   밤에 선택한 플레이어가 마피아라면 접선한다.
  -도둑
   군인에게 도벽을 시도할 경우 실패하며, 군인이 도둑의 정체를 알게된다.
   경찰의 능력을 훔쳐서 마피아를 찾아낸 경우에도 접선한다. 이때는 총구를 움직일 수 없다.
   마피아의 능력을 훔치면 접선하며 총구를 움직일 수 있다.
   투표시간마다 원하는 플레이어의 선택해 그 사람의 고유능력을 밤까지 사용할 수 있다.
  -마담
   낮에 투표한 플레이어를 유혹하여 직업의 고유 능력을 사용하지 못하도록 한다
   유혹 상태는 마담이 살아있는 한 영구 지속이고, 마담이 사망할경우 그 다음밤이 지나면 풀린다.
   마피아를 유혹할 경우 접선한다.
  -과학자
   사망할 경우, 다음날 밤에 부활한다. (1회용)
   사망할 경우, 마피아와 접선한다.
 -시민 팀
  -경찰
   밤마다 플레이어 한 명을 조사하여 그 플레이어의 마피아 여부를 알아낼 수 있다.
   밤에 플레이어 한 명을 선택해 조사하여 해당 유저가 마피아인지 아닌지를 알아낼 수 있다. 단, 보조직업과 교주는 알아낼 수 없다. 따라서 보조직업이나 교주를 조사했을 때는 시민과 같이 '~님은 마피아가 아닙니다'라고 뜬다.
  -요원
   밤마다 지령을 받아 시민 한 명의 직업을 알아낸다.
   지령은 요원이 정하는 것이 아니라, 랜덤으로 오게 된다.
   만약 더 이상 공작으로 알아낼 대상이 없는 경우, 지령이 도착하지 않았습니다. 라는 메시지가 전송된다. 해당 메시지가 도착했을 경우, 직업을 모르는 플레이어는 전부 악인이다.
  -의사
   밤마다 한 사람을 지목하여 대상이 마피아에게 공격받을 경우, 대상을 치료한다
  -군인
   마피아의 처형을 한 번 무시한다
   마피아팀에게 직업을 조사당할 경우 그 직업의 정체를 알 수 있고 조사의 부가적인 효과도 무효화 시킨다.
  -정치인
   플레이어간의 투표로 처형당하지 않는다.
   정치인의 투표권은 두 표로 인정된다.
  -테러리스트
   밤마다 플레이어 한 명을 지목하여 해당 플레이어가 자신을 처형 대상으로 지목했다면 함께 사망한다
   투표로 죽을 때, 최후에 반론 시간때 플레이어 한명을 골라 같이 처형될 수 있다.
  -건달
   밤마다 플레이어 한 명을 선택하여 다음날 투표시 해당 플레이어의 투표권을 빼앗는다.
  -간호사
   밤마다 플레이어 한 명을 조사하여 의사라면 접선한다
   의사와 접선한 상태에서 의사가 사망할 경우, 자신이 의사 대신 사람들을 치료할 수 있다.
모든 직업은 공개될 경우 처형의 대상이 될 수 있기 때문에, 특수한 상황이 아닌 경우 직업 공개를 하지 않는것을 원칙으로 한다.
모든 직업은 공개될 경우 처형의 대상이 될 수 있기 때문에, 특수한 상황이 아닌 경우 직업 공개를 하지 않는것을 원칙으로 한다.
모든 직업은 공개될 경우 처형의 대상이 될 수 있기 때문에, 특수한 상황이 아닌 경우 직업 공개를 하지 않는것을 원칙으로 한다.
모든 직업은 공개될 경우 처형의 대상이 될 수 있기 때문에, 특수한 상황이 아닌 경우 직업 공개를 하지 않는것을 원칙으로 한다.
모든 직업은 공개될 경우 처형의 대상이 될 수 있기 때문에, 특수한 상황이 아닌 경우 직업 공개를 하지 않는것을 원칙으로 한다.
모든 직업은 공개될 경우 처형의 대상이 될 수 있기 때문에, 특수한 상황이 아닌 경우 직업 공개를 하지 않는것을 원칙으로 한다.
모든 직업은 공개될 경우 처형의 대상이 될 수 있기 때문에, 특수한 상황이 아닌 경우 직업 공개를 하지 않는것을 원칙으로 한다.
모든 직업은 공개될 경우 처형의 대상이 될 수 있기 때문에, 특수한 상황이 아닌 경우 직업 공개를 하지 않는것을 원칙으로 한다.
마피아 팀의 보조 직업들은 마피아 침에 포함된다.

Remaining players :
{[p.name for p in players if p.alive]}

Conversation Posssible Players:
{[p.name for p in possible_targets if p.alive]}

PREV PREDICTION :
{player.get_last_prediction()}

CHAT HISTORY: :
{str(chat_history)}
    """

    output_parser = PydanticOutputParser(pydantic_object=Response_Type)


    chatml = [SystemMessage(content=SYS_PROMPT)] \
            + [SystemMessage(content=output_parser.get_format_instructions())]


    result = chatGPT.invoke(chatml)




    match = re.search(r'\{.*\}', result.content, re.DOTALL)
    if match:
        json_str = match.group(0)
        parsed = json.loads(json_str)
    else :
        parsed = {"speaker": "", "chat" : "", "predictions" : "", "point" : ""}
    # print(parsed)
    # try:
    #     result = json.loads(result.content)
    # except Exception:
    #     result = None


    return parsed
    #
    # print(result)
    # try:
    #     ret = json.loads(result.content)
    # except json.decoder.JSONDecodeError:
    #     ret = {"speaker": "", "chat" : "", "predictions" : "", "point" : ""}
    # return ret
    # # JSON 파싱 후 반환
    # try:
    #     return json.loads(result)  # response_text → chunks 로 변경
    # except json.JSONDecodeError:
    #     return None  # JSON 변환 실패 시 None 반환


