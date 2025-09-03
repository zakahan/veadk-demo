import asyncio
import time

from google.adk.events import Event
from google.adk.sessions import Session
from google.genai import types
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from veadk import Agent, Runner
from veadk.knowledgebase import KnowledgeBase
from veadk.memory.long_term_memory import LongTermMemory
from veadk.tracing.telemetry.exporters.cozeloop_exporter import CozeloopExporter
from veadk.tracing.telemetry.exporters.apmplus_exporter import APMPlusExporter
from veadk.tracing.telemetry.opentelemetry_tracer import OpentelemetryTracer

from mock_data import mock_data


APP_NAME = "analysis-app"
USER_ID = "user_id"



exporters = [APMPlusExporter()]
tracer = OpentelemetryTracer(exporters=exporters)
# ----------------------------------------------------------------------------------------
# 我这里先用local为例子了，local的不具备持久化，可以反复操作
# 这里事先准备好一个knowledgebase，用于agent知识
kb = KnowledgeBase(
    backend="local",
)

kb.add(
    data = mock_data,
    app_name = APP_NAME
)

# 事先准备一个长期记忆模块用于agent长期记忆
ltm = LongTermMemory(
    backend="local",
)

asyncio.run(        # 注意这个是异步的，正常情况add操作是不会这样处理的，这是我mock数据的时候用的，正常情况是不会这样写的
    ltm.add_session_to_memory(      # 这里就直接往长期记忆中添加一个session，用于agent长期记忆
        session=Session(
            id="test_session_id",
            app_name=APP_NAME,
            user_id=USER_ID,
            events=[
                Event(
                    invocation_id="test_invocation_id",
                    author="user",
                    branch=None,
                    content=types.Content(
                        parts=[types.Part(text="最近我在看《自卑与超越》")],
                        role="user",
                    ),
                )
            ],
        )
    )
)

# ----------------------------------------------------------------------------------------
# 计算器mcp工具
# mcptool (你可以理解为这是一个mcp的client），它会连接到一个mcp server，然后作为tools提供给agent使用
mcp_tool = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=["mcp_server.py"],
        )
    )
)

agent = Agent(
    name="chat_agent",
    description="聊天agent",
    instruction="你可以调用工具来进行计算，可以调用知识库，可以调用长期记忆，注意：任何涉及到计算的工作，你必须调用计算工具来算，不允许你自己来计算，",
    tools=[mcp_tool],
    knowledgebase=kb,
    long_term_memory=ltm,
    tracers=[tracer],
)

runner = Runner(
    agent,
    app_name=APP_NAME,
    user_id=USER_ID
)



if __name__ == "__main__":
    messsages = [
        "我上次在看什么书来着，这本书是什么类型的书？作者是谁？",
        "心理学方面的书吗？我记得还有一个叫弗洛伊德的，他和这个作者差多少岁？"
    ]

    for i, message in enumerate(messsages):
        completion = asyncio.run(
            runner.run(
                messages=message,
                session_id="asdfghjkl",
                save_tracing_data=True,
            )
        )

        print("="*20)
        print("第", i + 1, "轮对话：")
        print("User：", message)
        print("Model:", completion)

    # time.sleep(3)

