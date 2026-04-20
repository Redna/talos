from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class HUDData:
    memory_file_count: int
    last_files: list[str]
    urgency: str
    spend: float = 0.0


@dataclass
class ThinkRequest:
    focus: str
    tools: list[ToolDef]
    hud_data: HUDData


@dataclass
class ToolResultRequest:
    tool_call_id: str
    output: str
    success: bool


@dataclass
class RequestFoldRequest:
    synthesis: str


@dataclass
class RequestRestartRequest:
    reason: str


@dataclass
class SendMessageRequest:
    channel: str
    text: str


@dataclass
class EmitEventRequest:
    type: str
    payload: dict[str, Any]


@dataclass
class ToolCallResult:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ThinkResponse:
    assistant_message: str
    tool_calls: list[ToolCallResult]
    context_pct: float
    turn: int
    tokens_used: int
    folded: bool


@dataclass
class JSONRPCRequest:
    jsonrpc: str
    id: Any
    method: str
    params: dict[str, Any]


@dataclass
class RPCError:
    code: int
    message: str


@dataclass
class JSONRPCResponse:
    jsonrpc: str
    id: Any
    result: Optional[dict[str, Any]] = None
    error: Optional[RPCError] = None
