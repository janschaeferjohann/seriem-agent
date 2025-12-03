"""WebSocket endpoint for streaming chat responses."""

import json

from fastapi import WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage, AIMessage

from app.agents import get_agent_executor, TOOLS


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
                
                # Stream events from the agent
                async for event in agent.astream_events(
                    {"messages": messages},
                    version="v2",
                    config={"recursion_limit": 75}
                ):
                    kind = event.get("event")
                    
                    # Handle streaming text from model
                    if kind == "on_chat_model_stream":
                        chunk = event.get("data", {}).get("chunk")
                        if chunk:
                            # Handle different content formats
                            content = getattr(chunk, "content", None)
                            if content:
                                if isinstance(content, str) and content:
                                    full_response += content
                                    await websocket.send_text(json.dumps({
                                        "type": "stream",
                                        "content": content,
                                    }))
                                elif isinstance(content, list):
                                    for item in content:
                                        if isinstance(item, dict) and item.get("type") == "text":
                                            text = item.get("text", "")
                                            if text:
                                                full_response += text
                                                await websocket.send_text(json.dumps({
                                                    "type": "stream",
                                                    "content": text,
                                                }))
                    
                    # Handle tool calls
                    elif kind == "on_tool_start":
                        tool_name = event.get("name", "unknown")
                        tool_input = event.get("data", {}).get("input", {})
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
                        await websocket.send_text(json.dumps({
                            "type": "tool_result",
                            "content": {
                                "name": tool_name,
                                "result": str(tool_output),
                            },
                        }))
                    
                    # Capture final response from chain end
                    elif kind == "on_chain_end":
                        output = event.get("data", {}).get("output", {})
                        if isinstance(output, dict) and "messages" in output:
                            last_msg = output["messages"][-1] if output["messages"] else None
                            if last_msg and hasattr(last_msg, "content"):
                                content = last_msg.content
                                if isinstance(content, str) and content and content != full_response:
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
                
            except Exception as e:
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
