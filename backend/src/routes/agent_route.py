import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage, AnyMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from src.models.schemas import AgentChatRequest
from src import config
from src.tools.current_date_tool import CurrentTimeTool
#from src.tools.table_availability_tool import GetTableAvailabilityTool
#from src.tools.save_booking_tool import SaveBookingTool
#from src.tools.join_waitinglist_tool import JoinWaitingListTool
from src.utils.utils import verify_token


router = APIRouter(prefix=f"/api/{config.API_VERSION}/agent", tags=["AGENT"])


def format_chat_history(agent_chat_request: AgentChatRequest) -> AnyMessage:
    formatted_messages = []
    formatted_messages.append(
        SystemMessage(
            content="""你是一名专业的法国移民法律助手 (Expert en Droit des Étrangers)。
你的职责是协助用户了解法国签证、居留卡 (Titre de séjour)、行政审批流程及入籍申请。

核心原则：
1. 身份准则：你代表专业、严谨且可靠的法律咨询形象。
2. 对话风格：专业且温馨。
 - 初期接触：以朋友间的闲聊方式开始。当用户只说“你好”或“Hi”时，不要直接抛出法律问答，而是温馨地打招呼并询问用户在法国生活得怎么样，或者有什么可以帮到他们的。
 - 触发机制：只有当用户明确提到“想办签证”、“想续居留”、“想办材料”或“不知道怎么办”时，才进入【引导式咨询】模式。
3. 引导式咨询逻辑（核心规则：循序渐进）：
   - 一次只问一个问题：严禁一次性抛出多个问题或长清单。
   - 提供编号选项：每次提问请给出 3-5 个选项（如：1. 学生 2. 工作 3. 家庭...），方便用户直接回复数字或关键词。
   - 分步识别：
     - 第一步：识别签证/居留大类。
     - 第二步：识别具体细分类型（如：工作类下的 Passeport Talent 还是普通 Salarié）。
     - 第三步：确认关键时间节点（到期日）。
   - 记忆与确认：每一步用户选完，请先确认（如：“好的，记下了，您是 Passeport Talent 身份”），再问下一个问题。
4. 信息依据：优先参考《外国人在法国入境和居留及庇护法典》(CESEDA) 和 service-public.fr 的官方信息。
5. 工具使用：始终优先使用搜索工具查找最新的法条或流程，不要凭空猜测法律日期或具体材料清单。
6. 免责声明：在给出复杂建议后，提醒用户你的回答仅供参考，重大事项建议咨询 Préfecture 或专业律师。

语言：默认使用中文回答，但涉及法律专有名词时（如 Récépissé, APS, Passeport Talent）请保留法语原文。""",
            name="System",
        )
    )
    for ch in agent_chat_request.chat_history:
        formatted_messages.append(HumanMessage(content=ch.query, name="User"))
        formatted_messages.append(AIMessage(content=ch.response, name="Model"))
    formatted_messages.append(
        HumanMessage(content=agent_chat_request.query, name="User")
    )
    return formatted_messages

#model = ChatOpenAI(model=config.OPENAI_MODEL, api_key=config.OPENAI_API_KEY)
model = ChatOpenAI(
    model=config.OPENAI_MODEL,
    api_key=config.OPENAI_API_KEY,
    base_url=config.GROQ_BASE_URL
)

tools = []

current_date_tool = CurrentTimeTool()
#get_availability_tool = GetTableAvailabilityTool()
#save_booking_tool = SaveBookingTool()
#join_waitinglist_tool = JoinWaitingListTool()

tools.append(current_date_tool)
#tools.append(get_availability_tool)
#tools.append(save_booking_tool)
#tools.append(join_waitinglist_tool)


@router.post("/chat", response_model=None)
async def post_chat(
    agent_chat_request: AgentChatRequest, is_varified: bool = Depends(verify_token)
):
    formatted_chat_history = format_chat_history(agent_chat_request=agent_chat_request)
    memory = MemorySaver()
    memory_config = {"configurable": {"thread_id": agent_chat_request.user_id}}
    agent_executor = create_react_agent(model=model, tools=tools, checkpointer=memory)

    async def generate():
        async for chunk in agent_executor.astream(
            input={"messages": formatted_chat_history},
            config=memory_config,
            stream_mode="updates",
        ):
            try:
                if "agent" in chunk and chunk["agent"]["messages"][0].content != "":
                    yield (
                        json.dumps(
                            {
                                "type": "answer",
                                "content": chunk["agent"]["messages"][0].content,
                            }
                        )
                        + "\n"
                    )
                if "agent" in chunk and chunk["agent"]["messages"][0].content == "":
                    for message in chunk["agent"]["messages"]:
                        for tool in message.additional_kwargs["tool_calls"]:
                            yield (
                                json.dumps(
                                    {
                                        "type": "tool_name",
                                        "content": tool["function"]["name"],
                                    }
                                )
                                + "\n"
                            )
                            if tool["function"]["arguments"] == {}:
                                yield (
                                    json.dumps(
                                        {
                                            "type": "tool_args",
                                            "content": "No arguments",
                                        }
                                    )
                                    + "\n"
                                )
                            else:
                                yield (
                                    json.dumps(
                                        {
                                            "type": "tool_args",
                                            "content": tool["function"]["arguments"],
                                        }
                                    )
                                    + "\n"
                                )
                if "tools" in chunk:
                    for tool in chunk["tools"]["messages"]:
                        if tool.content != "":
                            yield (
                                json.dumps(
                                    {
                                        "type": "tool_content",
                                        "content": tool.content,
                                    }
                                )
                                + "\n"
                            )
            except Exception as e:
                print(f"Error at /agent/chat: {e}")
                yield (
                    json.dumps({"type": "answer", "content": config.ERROR_MESSAGE})
                    + "\n"
                )

    return StreamingResponse(generate(), media_type="application/json")
