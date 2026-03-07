# Deepseek V3.2 Thinking Mode + Tool Calls 流式处理模块
# 支持在思考模式下边思考边调用工具，显著降低响应延迟

import json
import logging
import time
from typing import Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
from openai import AsyncOpenAI
from src.utils.config import settings

logger = logging.getLogger(__name__)

def ts() -> str:
    """返回当前时间戳字符串"""
    return time.strftime('%H:%M:%S')


class ChunkType(Enum):
    """流式输出块类型"""
    REASONING = "reasoning"      # 思考链内容
    TOOL_CALL = "tool_call"      # 工具调用请求
    CONTENT = "content"          # 最终回答内容
    ERROR = "error"              # 错误信息


@dataclass
class StreamChunk:
    """流式输出块"""
    type: ChunkType
    content: str = ""
    tool_call: Optional[dict] = None
    is_final: bool = False


# 初始化异步 OpenAI 客户端 (兼容 Deepseek API)
_async_client: Optional[AsyncOpenAI] = None

def get_async_client() -> AsyncOpenAI:
    """获取异步 OpenAI 客户端单例"""
    global _async_client
    if _async_client is None:
        import httpx
        # 设置超时：连接 10s，读取流 60s，写入 30s
        timeout = httpx.Timeout(60.0, connect=10.0)
        _async_client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            timeout=timeout
        )
    return _async_client


async def stream_with_thinking_tools(
    messages: list,
    tools: list,
    tool_executor: Callable[[str, dict], Any],
    max_tool_rounds: int = 5,
    total_timeout: float = 60.0  # 总超时时间
):
    """
    Deepseek V3.2 Thinking Mode + Tool Calls 流式调用。
    
    实现"边思考边调用工具"的核心逻辑：
    1. 启用 thinking mode 发起流式请求
    2. 流式接收 reasoning_content 和 tool_calls
    3. 如有工具调用，执行工具并回传结果，继续循环
    4. 直到获得最终 content 为止
    
    Args:
        messages: 对话历史
        tools: 工具定义列表
        tool_executor: 工具执行函数，签名为 (name, args) -> result
        max_tool_rounds: 最大工具调用轮数，防止无限循环
    
    Yields:
        StreamChunk: 流式输出块（思考/工具调用/内容）
    """
    client = get_async_client()
    current_messages = list(messages)  # 复制，避免修改原列表
    total_start = time.time()
    
    # 添加总体超时检查
    async def check_total_timeout():
        while time.time() - total_start < total_timeout:
            await asyncio.sleep(1)
        logger.error(f"[ThinkingStream] Total timeout ({total_timeout}s) reached")
        return
    
    # 启动超时检查任务
    import asyncio
    timeout_task = asyncio.create_task(check_total_timeout())
    
    try:
        for round_idx in range(max_tool_rounds):
            round_start = time.time()
            logger.info(f"[{ts()}] [ThinkingStream] Round {round_idx + 1} starting...")
            
            # 计算当前消息大小（用于调试）
            total_chars = sum(len(str(m.get('content', '') or '')) for m in current_messages)
            logger.info(f"[{ts()}] [ThinkingStream] Messages: {len(current_messages)}, ~{total_chars} chars")
            
            # V3.1 修复：全部使用非流式请求以提高稳定性和避免卡死
            use_stream = False  # 禁用流式模式
        
        try:
            if use_stream:
                stream = await client.chat.completions.create(
                    model="deepseek-chat",
                    messages=current_messages,
                    tools=tools if tools else None,
                    stream=True
                )
            else:
                # 非流式请求：直接获取完整响应
                logger.info(f"[{ts()}] [ThinkingStream] Using non-stream mode for round {round_idx + 1}")
                response = await client.chat.completions.create(
                    model="deepseek-chat",
                    messages=current_messages,
                    tools=tools if tools else None,
                    stream=False
                )
        except Exception as e:
            logger.error(f"[{ts()}] [ThinkingStream] API call failed: {e}")
            yield StreamChunk(type=ChunkType.ERROR, content=str(e))
            return
        
        # 收集本轮响应
        reasoning_content = ""
        content = ""
        tool_calls_data = []  # 存储工具调用信息
        current_tool_call = None
        chunk_count = 0
        last_chunk_time = time.time()
        
        if use_stream:
            # 流式模式：逐 chunk 处理
            logger.info(f"[{ts()}] [ThinkingStream] Starting stream iteration...")
            
            # 调试：写入文件日志精确定位卡住位置
            with open("debug_stream.log", "a", encoding="utf-8") as f:
                f.write(f"\n[{ts()}] Round {round_idx + 1}: Starting async for loop, messages={len(current_messages)}, chars={total_chars}\n")
            
            # 保存最后一个chunk用于获取完整响应
            last_chunk = None
            
            async for chunk in stream:
                chunk_count += 1
                now = time.time()
                if chunk_count % 10 == 0:
                    logger.info(f"[{ts()}] [ThinkingStream] Received {chunk_count} chunks, elapsed {now - round_start:.2f}s")
                last_chunk_time = now
                last_chunk = chunk
                
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue
                
                # 调试：输出完整的delta对象（只输出一次）
                if chunk_count == 1:
                    logger.info(f"[{ts()}] [ThinkingStream] Delta object: {delta}")
                
                # 处理思考链
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    reasoning_content += delta.reasoning_content
                    # 可选：流式输出思考内容（当前不展示给用户）
                    # yield StreamChunk(type=ChunkType.REASONING, content=delta.reasoning_content)
                
                # 处理最终内容
                if delta.content:
                    content += delta.content
                    yield StreamChunk(type=ChunkType.CONTENT, content=delta.content)
                
                # 处理工具调用
                if delta.tool_calls:
                    logger.info(f"[{ts()}] [ThinkingStream] Received tool_calls delta: {delta.tool_calls}")
                    for tc in delta.tool_calls:
                        logger.info(f"[{ts()}] [ThinkingStream] Processing tool_call: index={tc.index}, id={tc.id}, function={tc.function}")
                        if tc.index is not None:
                            # 新工具调用开始
                            while len(tool_calls_data) <= tc.index:
                                tool_calls_data.append({
                                    "id": "",
                                    "name": "",
                                    "arguments": ""
                                })
                            current_tool_call = tool_calls_data[tc.index]
                        
                        if tc.id:
                            current_tool_call["id"] = tc.id
                            logger.info(f"[{ts()}] [ThinkingStream] Set tool id: {tc.id}")
                        if tc.function:
                            if tc.function.name:
                                current_tool_call["name"] = tc.function.name
                                logger.info(f"[{ts()}] [ThinkingStream] Set tool name: {tc.function.name}")
                            if tc.function.arguments:
                                current_tool_call["arguments"] += tc.function.arguments
                                logger.info(f"[{ts()}] [ThinkingStream] Appended args: {tc.function.arguments}")
                else:
                    # 调试：记录没有工具调用的情况
                    if hasattr(delta, 'tool_calls'):
                        logger.debug(f"[{ts()}] [ThinkingStream] delta.tool_calls is None or empty")
            
            # 调试：确认循环结束
            with open("debug_stream.log", "a", encoding="utf-8") as f:
                f.write(f"[{ts()}] Round {round_idx + 1}: async for loop EXITED, chunk_count={chunk_count}\n")
            
            # 检查流结束状态
            finish_reason = last_chunk.choices[0].finish_reason if last_chunk and last_chunk.choices else None
            
            # DeepSeek修复：如果finish_reason=tool_calls但没有工具调用数据，尝试从完整消息中获取
            if finish_reason == "tool_calls" and not tool_calls_data and last_chunk:
                logger.info(f"[{ts()}] [ThinkingStream] DeepSeek fix: trying to get tool_calls from complete message")
                try:
                    # 获取完整的message对象
                    message = last_chunk.choices[0].message if hasattr(last_chunk.choices[0], 'message') else None
                    if message and hasattr(message, 'tool_calls') and message.tool_calls:
                        logger.info(f"[{ts()}] [ThinkingStream] Found tool_calls in complete message: {message.tool_calls}")
                        for tc in message.tool_calls:
                            tool_calls_data.append({
                                "id": tc.id,
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            })
                            logger.info(f"[{ts()}] [ThinkingStream] Added tool call: {tc.function.name}")
                except Exception as e:
                    logger.error(f"[{ts()}] [ThinkingStream] Error extracting tool_calls from complete message: {e}")
        else:
            # 非流式模式：直接处理完整响应
            with open("debug_stream.log", "a", encoding="utf-8") as f:
                f.write(f"\n[{ts()}] Round {round_idx + 1}: Non-stream mode, processing response\n")
            
            message = response.choices[0].message
            content = message.content or ""
            finish_reason = response.choices[0].finish_reason
            
            # 提取工具调用
            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls_data.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    })
            
            # 输出内容（如果有）
            if content:
                yield StreamChunk(type=ChunkType.CONTENT, content=content)
            
            logger.info(f"[{ts()}] [ThinkingStream] Non-stream response: content={len(content)} chars, tools={len(tool_calls_data)}")
        
        round_time = time.time() - round_start
        logger.info(f"[{ts()}] [ThinkingStream] Round {round_idx + 1} finished. finish_reason={finish_reason}, tools={len(tool_calls_data)}, chunks={chunk_count}, round_time={round_time:.2f}s")
        
        # 调试：输出工具调用数据
        if tool_calls_data:
            logger.info(f"[{ts()}] [ThinkingStream] Tool calls data: {tool_calls_data}")
        else:
            logger.warning(f"[{ts()}] [ThinkingStream] No tool calls data despite finish_reason={finish_reason}")
        
        # 记录思考链（用于调试）
        if reasoning_content:
            logger.debug(f"[ThinkingStream] Reasoning: {reasoning_content[:200]}...")
        
        # 如果没有工具调用，说明已完成
        if not tool_calls_data or all(not tc["name"] for tc in tool_calls_data):
            total_time = time.time() - total_start
            logger.info(f"[{ts()}] [ThinkingStream] Completed. Total time: {total_time:.2f}s")
            # 取消超时任务
            if 'timeout_task' in locals():
                timeout_task.cancel()
            yield StreamChunk(type=ChunkType.CONTENT, content="", is_final=True)
            return
        
        # 有工具调用，构建 assistant message 并执行工具
        # 限制单轮最多 5 个工具调用，支持一次读取所有记忆文件
        MAX_TOOLS_PER_ROUND = 5
        filtered_tool_calls = [tc for tc in tool_calls_data if tc["name"]][:MAX_TOOLS_PER_ROUND]
        
        if len(tool_calls_data) > MAX_TOOLS_PER_ROUND:
            skipped = [tc["name"] for tc in tool_calls_data if tc["name"]][MAX_TOOLS_PER_ROUND:]
            logger.warning(f"[ThinkingStream] Limiting tools to {MAX_TOOLS_PER_ROUND}, skipped: {skipped}")
        
        assistant_message = {
            "role": "assistant",
            "content": content or None,
            "tool_calls": [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"]
                    }
                }
                for tc in filtered_tool_calls
            ]
        }
        
        # 如果有 reasoning_content，需要回传（同一问题的多轮调用）
        if reasoning_content:
            assistant_message["reasoning_content"] = reasoning_content
        
        current_messages.append(assistant_message)
        
        # 执行工具并收集结果
        with open("debug_stream.log", "a", encoding="utf-8") as f:
            f.write(f"[{ts()}] Round {round_idx + 1}: About to execute {len(filtered_tool_calls)} tools\n")
        
        for tc in filtered_tool_calls:
            
            try:
                args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                logger.info(f"[ThinkingStream] Executing tool: {tc['name']}({args})")
                
                with open("debug_stream.log", "a", encoding="utf-8") as f:
                    f.write(f"[{ts()}] Executing tool: {tc['name']}\n")
                
                # 通知调用方正在执行工具
                try:
                    yield StreamChunk(
                        type=ChunkType.TOOL_CALL, 
                        content=f"正在调用 {tc['name']}...",
                        tool_call={"name": tc["name"], "args": args}
                    )
                except Exception as yield_error:
                    logger.error(f"[ThinkingStream] Yield error: {yield_error}")
                
                # 执行工具（添加超时保护）
                try:
                    import asyncio
                    result = await asyncio.wait_for(
                        tool_executor(tc["name"], args), 
                        timeout=30.0  # 30秒超时
                    )
                    logger.info(f"[ThinkingStream] Tool {tc['name']} returned {len(str(result))} chars")
                except asyncio.TimeoutError:
                    logger.error(f"[ThinkingStream] Tool {tc['name']} timeout after 30s")
                    result = f"工具执行超时: {tc['name']}"
                except Exception as tool_error:
                    logger.error(f"[ThinkingStream] Tool execution error: {tool_error}")
                    result = f"工具执行失败: {str(tool_error)}"
                
                # 将工具结果加入消息
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": str(result) if result else "执行成功"
                })
                
                logger.info(f"[ThinkingStream] Tool {tc['name']} returned {len(str(result))} chars")
                
            except Exception as e:
                logger.error(f"[ThinkingStream] Tool execution failed: {e}")
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": f"工具执行失败: {str(e)}"
                })
        
        # 继续下一轮（让模型处理工具结果）
    
    # 超过最大轮数
    logger.warning(f"[ThinkingStream] Max tool rounds ({max_tool_rounds}) exceeded")
    yield StreamChunk(type=ChunkType.ERROR, content="工具调用轮数超限")
    
    finally:
        # 取消超时任务
        if 'timeout_task' in locals():
            timeout_task.cancel()


async def stream_with_fallback(
    messages: list,
    tools: list,
    tool_executor: Callable[[str, dict], Any],
    fallback_llm,
    use_thinking: bool = True
):
    """
    带 fallback 的流式调用。
    
    优先使用 Thinking Mode，失败时回退到普通流式调用。
    
    Args:
        messages: 对话历史
        tools: 工具定义
        tool_executor: 工具执行函数
        fallback_llm: 降级使用的 LLM（LangChain ChatOpenAI）
        use_thinking: 是否启用思考模式
    """
    if use_thinking:
        try:
            async for chunk in stream_with_thinking_tools(messages, tools, tool_executor):
                if chunk.type == ChunkType.ERROR:
                    logger.warning(f"[Fallback] Thinking mode error, falling back: {chunk.content}")
                    break
                yield chunk
            else:
                # 正常完成，直接返回
                return
        except Exception as e:
            logger.error(f"[Fallback] Thinking mode failed: {e}")
    
    # Fallback 到普通流式调用（不使用 thinking mode）
    logger.info("[Fallback] Using standard streaming without thinking mode")
    async for chunk in fallback_llm.astream(messages):
        yield StreamChunk(type=ChunkType.CONTENT, content=chunk.content)
