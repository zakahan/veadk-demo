# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd. and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from contextlib import asynccontextmanager
from typing import Callable

from agent import agent_run_config

from fastapi import FastAPI
from fastapi.routing import APIRoute

from fastmcp import FastMCP

from starlette.routing import Route

from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from a2a.types import AgentProvider

from veadk.a2a.ve_a2a_server import init_app
from veadk.runner import Runner
from veadk.tracing.telemetry.exporters.apmplus_exporter import APMPlusExporter
from veadk.tracing.telemetry.exporters.cozeloop_exporter import CozeloopExporter
from veadk.tracing.telemetry.exporters.tls_exporter import TLSExporter
from veadk.tracing.telemetry.opentelemetry_tracer import OpentelemetryTracer
from veadk.types import AgentRunConfig
from veadk.utils.logger import get_logger

logger = get_logger(__name__)

assert isinstance(agent_run_config, AgentRunConfig), (
    f"Invalid agent_run_config type: {type(agent_run_config)}, expected `AgentRunConfig`"
)

app_name = agent_run_config.app_name
agent = agent_run_config.agent
short_term_memory = agent_run_config.short_term_memory

VEFAAS_REGION = os.getenv("APP_REGION", "cn-beijing")
VEFAAS_FUNC_ID = os.getenv("_FAAS_FUNC_ID", "")
agent_card_builder = AgentCardBuilder(agent=agent, provider=AgentProvider(organization="Volcengine Agent Development Kit (VeADK)", url=f"https://console.volcengine.com/vefaas/region:vefaas+{VEFAAS_REGION}/function/detail/{VEFAAS_FUNC_ID}"))


def load_tracer() -> None:
    EXPORTER_REGISTRY = {
        "VEADK_TRACER_APMPLUS": APMPlusExporter,
        "VEADK_TRACER_COZELOOP": CozeloopExporter,
        "VEADK_TRACER_TLS": TLSExporter,
    }

    exporters = []
    for env_var, exporter_cls in EXPORTER_REGISTRY.items():
        if os.getenv(env_var, "").lower() == "true":
            if (
                agent.tracers
                and isinstance(agent.tracers[0], OpentelemetryTracer)
                and any(isinstance(e, exporter_cls) for e in agent.tracers[0].exporters)
            ):
                logger.warning(
                    f"Exporter {exporter_cls.__name__} is already defined in agent.tracers[0].exporters. These two exporters will be used at the same time. As a result, your data may be uploaded twice."
                )
            else:
                exporters.append(exporter_cls())

    tracer = OpentelemetryTracer(name="veadk_tracer", exporters=exporters)
    agent_run_config.agent.tracers.extend([tracer])


def build_mcp_run_agent_func() -> Callable:
    runner = Runner(
        agent=agent,
        short_term_memory=short_term_memory,
        app_name=app_name,
        user_id="",
    )

    async def run_agent(
        user_input: str,
        user_id: str = "mcp_user",
        session_id: str = "mcp_session",
    ) -> str:
        # Set user_id for runner
        runner.user_id = user_id

        # Running agent and get final output
        final_output = await runner.run(
            messages=user_input,
            session_id=session_id,
        )
        return final_output

    run_agent_doc = f"""{agent.description}
    Args:
        user_input: User's input message (required).
        user_id: User identifier. Defaults to "mcp_user".
        session_id: Session identifier. Defaults to "mcp_session".
    Returns:
        Final agent response as a string."""

    run_agent.__doc__ = run_agent_doc

    return run_agent


async def agent_card() -> dict:
    agent_card = await agent_card_builder.build()
    return agent_card.model_dump()


load_tracer()

# Build a run_agent function for building MCP server
run_agent_func = build_mcp_run_agent_func()

a2a_app = init_app(
    server_url="0.0.0.0",
    app_name=app_name,
    agent=agent,
    short_term_memory=short_term_memory,
)

a2a_app.post("/run_agent", operation_id="run_agent", tags=["mcp"])(run_agent_func)
a2a_app.get("/agent_card", operation_id="agent_card", tags=["mcp"])(agent_card)


# === Build mcp server ===

mcp = FastMCP.from_fastapi(app=a2a_app, name=app_name, include_tags={"mcp"})

# Create MCP ASGI app
mcp_app = mcp.http_app(path="/", transport="streamable-http")


# Combined lifespan management
@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    async with mcp_app.lifespan(app):
        yield


# Create main FastAPI app with combined lifespan
app = FastAPI(
    title=a2a_app.title,
    version=a2a_app.version,
    lifespan=combined_lifespan,
    openapi_url=None,
    docs_url=None,
    redoc_url=None
)

# Mount A2A routes to main app
for route in a2a_app.routes:
    app.routes.append(route)

# Mount MCP server at /mcp endpoint
app.mount("/mcp", mcp_app)


# remove openapi routes
paths = ["/openapi.json", "/docs", "/redoc"]
new_routes = []
for route in app.router.routes:
    if isinstance(route, (APIRoute, Route)) and route.path in paths:
        continue
    new_routes.append(route)
app.router.routes = new_routes

# === Build mcp server end ===
