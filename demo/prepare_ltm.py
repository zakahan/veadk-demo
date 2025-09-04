import asyncio

from google.adk.events import Event
from google.adk.sessions import Session
from google.genai import types
from veadk.memory.long_term_memory import LongTermMemory

APP_NAME = "demo"
USER_ID = "user"

ltm = LongTermMemory(
    backend="viking",
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



# # 验证你有没有add进去
# x= asyncio.run(
#     ltm.search_memory(app_name=APP_NAME,user_id=USER_ID,query="最近我在看什么")
# )
#
# print(x)
