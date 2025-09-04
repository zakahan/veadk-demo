from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters
from veadk import Agent
from veadk.knowledgebase import KnowledgeBase
from veadk.memory.long_term_memory import LongTermMemory
from veadk.tracing.telemetry.exporters.cozeloop_exporter import CozeloopExporter
from veadk.tracing.telemetry.opentelemetry_tracer import OpentelemetryTracer

from .mock_data import mock_data

APP_NAME = "demo"
USER_ID = "user"

exporters = [CozeloopExporter()]
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
    backend="viking",
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

root_agent = Agent(
    name="chat_agent",
    description="聊天agent",
    instruction="你可以调用工具来进行计算，可以调用知识库，可以调用长期记忆，注意：任何涉及到计算的工作，你必须调用计算工具来算，不允许你自己来计算，",
    tools=[mcp_tool],
    knowledgebase=kb,
    long_term_memory=ltm,
    tracers=[tracer],
)
