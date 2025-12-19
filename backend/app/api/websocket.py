"""WebSocket endpoint for streaming chat responses."""

import json
import re

from fastapi import WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage, AIMessage

from app.agents import get_agent_executor
from app.telemetry import get_telemetry_client


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming agent responses.
    
    Message format (client -> server):
    {
        "type": "message",
        "content": "user message here",
        "chat_history": []  // optional
    }
    
    Message format (server -> client):
    {
        "type": "stream" | "tool_call" | "tool_result" | "done" | "error",
        "content": "..."
    }
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") != "message":
                continue
            
            user_content = message.get("content", "")
            chat_history = message.get("chat_history", [])
            
            # Build messages list
            messages = []
            
            for msg in chat_history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
            
            messages.append(HumanMessage(content=user_content))
            
            try:
                # Get agent and stream response
                agent = get_agent_executor()
                
                full_response = ""
                suppressed_xml_echo = False
                suppressing_xml_echo = False
                last_xml_tool_output: str | None = None
                tool_depth = 0
                tool_call_count = 0  # Track total tool calls for telemetry

                # If an XML-producing tool already returned XML, do not let the model
                # echo that XML back as normal assistant text.
                XML_TOOL_NAMES = {
                    "generate_datamodel",
                    "generate_testcase_from_datamodel",
                    "modify_testcase_xml",
                }
                XML_START_RE = re.compile(r"<\?xml\b|</[A-Za-z_]|<[A-Za-z_]|<!--|<!\[CDATA\[")

                def _maybe_suppress_xml_echo(text: str) -> str:
                    """Return text to stream to client (possibly empty) and update suppression state."""
                    nonlocal suppressed_xml_echo, suppressing_xml_echo
                    if not text:
                        return text

                    if suppressing_xml_echo:
                        # Already suppressing: drop everything else.
                        suppressed_xml_echo = True
                        return ""

                    if not last_xml_tool_output:
                        return text

                    # Look for the first XML-ish token in the model stream.
                    match = XML_START_RE.search(text)
                    if not match:
                        return text

                    # Once an XML tool produced XML, treat any subsequent XML-looking stream
                    # as an echo and suppress it entirely.
                    suppressing_xml_echo = True
                    suppressed_xml_echo = True

                    # Keep only what came before the XML (if any); drop the XML itself.
                    return text[:match.start()].rstrip()
                
                # Stream events from the agent
                async for event in agent.astream_events(
                    {"messages": messages},
                    version="v2",
                    config={"recursion_limit": 75}
                ):
                    kind = event.get("event")
                    
                    # Handle streaming text from model
                    if kind == "on_chat_model_stream":
                        # IMPORTANT: do not stream model output while a tool is executing.
                        # This prevents nested/subagent model output (often large XML) from
                        # polluting the normal assistant message. The tool result already
                        # contains the generated content.
                        if tool_depth > 0:
                            continue

                        chunk = event.get("data", {}).get("chunk")
                        if chunk:
                            # Handle different content formats
                            content = getattr(chunk, "content", None)
                            if content:
                                if isinstance(content, str) and content:
                                    safe = _maybe_suppress_xml_echo(content)
                                    if safe:
                                        full_response += safe
                                        await websocket.send_text(json.dumps({
                                            "type": "stream",
                                            "content": safe,
                                        }))
                                elif isinstance(content, list):
                                    for item in content:
                                        if isinstance(item, dict) and item.get("type") == "text":
                                            text = item.get("text", "")
                                            if text:
                                                safe = _maybe_suppress_xml_echo(text)
                                                if safe:
                                                    full_response += safe
                                                    await websocket.send_text(json.dumps({
                                                        "type": "stream",
                                                        "content": safe,
                                                    }))
                    
                    # Handle tool calls
                    elif kind == "on_tool_start":
                        tool_name = event.get("name", "unknown")
                        tool_input = event.get("data", {}).get("input", {})
                        tool_depth += 1
                        tool_call_count += 1  # Increment for telemetry
                        await websocket.send_text(json.dumps({
                            "type": "tool_call",
                            "content": {
                                "name": tool_name,
                                "args": tool_input,
                            },
                        }))
                    
                    elif kind == "on_tool_end":
                        tool_name = event.get("name", "unknown")
                        tool_output = event.get("data", {}).get("output", "")
                        tool_output_str = str(tool_output)
                        tool_depth = max(0, tool_depth - 1)
                        await websocket.send_text(json.dumps({
                            "type": "tool_result",
                            "content": {
                                "name": tool_name,
                                "result": tool_output_str,
                            },
                        }))

                        # If the tool returned XML, remember it so we can suppress model echo.
                        if tool_name in XML_TOOL_NAMES:
                            stripped = tool_output_str.lstrip()
                            if stripped.startswith("<") and len(stripped) >= 200:
                                last_xml_tool_output = tool_output_str
                    
                    # Capture final response from chain end
                    elif kind == "on_chain_end":
                        output = event.get("data", {}).get("output", {})
                        if isinstance(output, dict) and "messages" in output:
                            last_msg = output["messages"][-1] if output["messages"] else None
                            if last_msg and hasattr(last_msg, "content"):
                                content = last_msg.content
                                if (
                                    isinstance(content, str)
                                    and content
                                    and content != full_response
                                    and not suppressed_xml_echo
                                ):
                                    # Only send if we haven't streamed this content
                                    if not full_response:
                                        full_response = content
                                        await websocket.send_text(json.dumps({
                                            "type": "stream",
                                            "content": content,
                                        }))
                
                # Send done signal
                await websocket.send_text(json.dumps({
                    "type": "done",
                    "content": full_response,
                }))
                
                # Emit telemetry for this chat turn
                telemetry = get_telemetry_client()
                if telemetry:
                    telemetry.emit_chat_turn(
                        message_length=len(user_content),
                        had_tool_calls=tool_call_count > 0,
                        tool_count=tool_call_count,
                        had_error=False,
                    )
                
            except Exception as e:
                # Emit error telemetry
                telemetry = get_telemetry_client()
                if telemetry:
                    telemetry.emit_chat_turn(
                        message_length=len(user_content),
                        had_tool_calls=False,
                        tool_count=0,
                        had_error=True,
                    )
                    telemetry.emit_error(
                        error_type="chat_error",
                        message=str(e),
                        context={"user_content_length": len(user_content)},
                    )
                
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": str(e),
                }))
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": str(e),
            }))
        except:
            pass
