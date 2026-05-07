from __future__ import annotations

import asyncio
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastmcp import Client
from fastmcp.client.transports.stdio import PythonStdioTransport
from google import genai
from google.genai import types, errors


def _strip_ctx_from_schema(schema: dict) -> dict:
    schema = dict(schema or {})
    props = dict(schema.get("properties", {}))
    props.pop("ctx", None)
    schema["properties"] = props
    if "required" in schema:
        schema["required"] = [r for r in schema["required"] if r != "ctx"]
    return schema


def _mcp_tool_to_fn_declaration(tool: Any) -> types.FunctionDeclaration:
    params: Dict[str, Any] = getattr(tool, "inputSchema", None) or {"type": "object", "properties": {}}
    params = _strip_ctx_from_schema(params)
    desc = (getattr(tool, "description", None) or "").strip() or f"MCP tool: {tool.name}"
    return types.FunctionDeclaration(
        name=tool.name,
        description=desc,
        parameters_json_schema=params,
    )


def _load_skill_context(modules_dir: Path) -> str:
    skill_texts: List[str] = []
    for module_dir in sorted(modules_dir.iterdir()):
        if not module_dir.is_dir() or module_dir.name.startswith("_"):
            continue
        skill_file = module_dir / "SKILL.md"
        if skill_file.exists():
            skill_texts.append(skill_file.read_text())
    return "\n\n---\n\n".join(skill_texts)


def _build_system_content(mcp_tools, mcp_resources, skill_context: str = "") -> types.Content:
    tools_json = [
        {
            "name": t.name,
            "description": getattr(t, "description", ""),
            "input_schema": getattr(t, "inputSchema", None),
        }
        for t in mcp_tools
    ]

    resources_json = []
    for r in mcp_resources:
        uri_obj = getattr(r, "uri", None) or getattr(r, "name", None)
        uri_str = str(uri_obj) if uri_obj is not None else None
        resource_name = uri_str.split("/")[-1] if uri_str else None
        resources_json.append(
            {
                "uri": uri_str,
                "name": resource_name,
                "description": getattr(r, "description", ""),
            }
        )

    payload = {
        "mcp_tools": tools_json,
        "mcp_resources": resources_json,
        "instruction": (
            "You may call MCP tools using their schemas. "
            "Tools that operate on sequences accept either a resource name (e.g., 'pBR322') "
            "or a raw DNA sequence string. Prefer using resource names when available. "
            "The server will resolve resource names to their sequences automatically."
        ),
    }

    system_text = "SYSTEM CONTEXT (capabilities, not user input):\n" + json.dumps(payload, indent=2)
    if skill_context:
        system_text += "\n\n--- SKILL GUIDANCE ---\n\n" + skill_context

    return types.Content(
        role="model",
        parts=[types.Part.from_text(text=system_text)],
    )


def _prompt_result_to_contents(prompt_result: Any) -> List[types.Content]:
    msgs = getattr(prompt_result, "messages", None) or getattr(prompt_result, "message", None) or []
    out: List[types.Content] = []
    for m in msgs:
        role = getattr(m, "role", "user") or "user"
        content = getattr(m, "content", None)
        texts: List[str] = []
        if isinstance(content, str):
            texts = [content]
        elif isinstance(content, list):
            for part in content:
                t = getattr(part, "text", None)
                if t is None and isinstance(part, str):
                    t = part
                if t is not None:
                    texts.append(str(t))
        elif content is not None:
            texts = [str(content)]
        if texts:
            out.append(types.Content(role=role, parts=[types.Part.from_text(text="\n".join(texts))]))
    return out


@dataclass
class ToolEvent:
    tool_name: str
    args: Dict[str, Any]
    response: Dict[str, Any]


@dataclass
class EngineState:
    history: List[types.Content] = field(default_factory=list)
    last_tool_events: List[ToolEvent] = field(default_factory=list)
    last_generated_doc_path: Optional[str] = None


class MCPGeminiEngine:
    def __init__(
        self,
        project_dir: Path,
        model: str = "gemini-2.5-flash",
        max_429_retries: int = 5,
    ) -> None:
        self.project_dir = project_dir
        self.model = model
        self.max_429_retries = max_429_retries

        self.gemini = genai.Client()
        self.state = EngineState()

        self._mcp: Optional[Client] = None
        self._system_content: Optional[types.Content] = None
        self._config: Optional[types.GenerateContentConfig] = None

    async def _ensure_mcp(self) -> None:
        if self._mcp is not None and self._system_content is not None and self._config is not None:
            return

        server_script = self.project_dir / "server.py"
        server_log = self.project_dir / "server_subprocess.log"
        transport = PythonStdioTransport(
            script_path=server_script,
            python_cmd=sys.executable,
            cwd=str(self.project_dir),
            log_file=server_log,
        )
        self._mcp = Client(transport)
        await self._mcp.__aenter__()

        mcp_tools = await self._mcp.list_tools()
        mcp_resources = await self._mcp.list_resources()
        modules_dir = self.project_dir / "modules"
        skill_context = _load_skill_context(modules_dir)
        self._system_content = _build_system_content(mcp_tools, mcp_resources, skill_context)

        fn_decls = [_mcp_tool_to_fn_declaration(t) for t in mcp_tools]
        if fn_decls:
            tool_obj = types.Tool(function_declarations=fn_decls)
            self._config = types.GenerateContentConfig(tools=[tool_obj])
        else:
            self._config = types.GenerateContentConfig()

    def _safe_generate(self, contents: List[types.Content]) -> Any:
        backoff_seconds = 2
        last_error: Optional[Exception] = None
        for attempt in range(self.max_429_retries):
            try:
                return self.gemini.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=self._config,
                )
            except errors.ServerError as e:
                msg = str(e)
                if "503" in msg or "UNAVAILABLE" in msg:
                    wait = backoff_seconds * (2 ** attempt)
                    print(f"\n[Gemini busy (503). Retrying in {wait}s...]")
                    time.sleep(wait)
                    last_error = e
                    continue
                raise
            except errors.ClientError as e:
                msg = str(e)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg and attempt < self.max_429_retries - 1:
                    import re

                    match = re.search(r"retry[^\d]*(\d+(?:\.\d+)?)\s*s", msg, re.IGNORECASE)
                    if match:
                        wait = float(match.group(1)) + 1
                    else:
                        wait = backoff_seconds * (2 ** attempt)
                    wait = max(wait, 2)
                    print(f"\n[Rate limit hit (429). Retrying in {wait:.0f}s...]")
                    time.sleep(wait)
                    last_error = e
                    continue
                raise
        if last_error is not None:
            raise last_error
        raise RuntimeError("safe_generate failed without specific error")

    async def _run_tool_loop(
        self,
        initial_resp,
        contents: List[types.Content],
    ) -> Tuple[str | None, List[types.Content]]:
        assert self._mcp is not None
        mcp = self._mcp

        contents = list(contents)
        resp = initial_resp
        events: List[ToolEvent] = []
        generated_doc_path: Optional[str] = None

        while True:
            function_calls = resp.function_calls or []

            if not function_calls:
                reply = resp.text or "[No text response]"
                if not resp.candidates:
                    return resp.text or "", contents
                contents.append(resp.candidates[0].content)
                self.state.last_tool_events = events
                if generated_doc_path:
                    self.state.last_generated_doc_path = generated_doc_path
                return resp.text, contents

            fc_content = resp.candidates[0].content
            fr_parts: List[types.Part] = []

            for fc in function_calls:
                tool_name = fc.name
                tool_args = dict(fc.args or {})

                print(f"\n[Tool call] → {tool_name}")
                print(json.dumps(tool_args, indent=2))

                try:
                    tool_result = await mcp.call_tool(tool_name, tool_args)
                    if isinstance(tool_result, list):
                        result_data = "\n".join(
                            getattr(item, "text", str(item)) for item in tool_result
                        )
                    elif hasattr(tool_result, "content"):
                        result_data = "\n".join(
                            getattr(item, "text", str(item)) for item in tool_result.content
                        )
                    else:
                        result_data = str(tool_result)
                    fn_response = {"result": result_data}
                except Exception as e:
                    fn_response = {"error": str(e)}

                print(f"[Tool result] ← {tool_name}:")
                print(json.dumps(fn_response, indent=2))

                events.append(
                    ToolEvent(tool_name=tool_name, args=tool_args, response=fn_response)
                )

                if tool_name == "BUA Document Renderer" and "file_path" in result_data:
                    generated_doc_path = result_data

                fr_parts.append(
                    types.Part.from_function_response(name=tool_name, response=fn_response)
                )

            fr_content = types.Content(role="user", parts=fr_parts)
            contents.extend([fc_content, fr_content])
            resp = self._safe_generate(contents=contents)

    async def send_message(
        self,
        user_text: str,
        *,
        use_prompts_api: bool = False,
        prompt_name: Optional[str] = None,
        prompt_args: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str | None, EngineState]:
        await self._ensure_mcp()
        assert self._mcp is not None
        assert self._system_content is not None

        if use_prompts_api and prompt_name:
            prompt_args = prompt_args or {}
            prompt_result = await self._mcp.get_prompt(prompt_name, prompt_args)
            prompt_contents = _prompt_result_to_contents(prompt_result)
            if not prompt_contents:
                return "Prompt rendered no messages.", self.state
            initial_contents = [self._system_content, *prompt_contents]
            resp = self._safe_generate(contents=initial_contents)
            _, updated = await self._run_tool_loop(resp, initial_contents)
            self.state.history = updated
            return None, self.state

        user_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_text)],
        )
        self.state.history.append(user_content)
        current_contents = [self._system_content, *self.state.history]
        resp = self._safe_generate(contents=current_contents)
        final_text, updated = await self._run_tool_loop(resp, current_contents)
        new_entries = updated[len(current_contents) :]
        self.state.history.extend(new_entries)
        return final_text, self.state


async def cli_chat() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    engine = MCPGeminiEngine(project_dir=Path(__file__).parent)

    print("Type a request. Ctrl-C to quit.\n")
    while True:
        user_text = input("You: ").strip()
        if not user_text:
            continue
        reply, _ = await engine.send_message(user_text)
        if reply:
            print(f"\nGemini: {reply}\n")


if __name__ == "__main__":
    asyncio.run(cli_chat())

