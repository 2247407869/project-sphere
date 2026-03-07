import pytest
import sys
import os

# 将项目根目录添加到路径以便导入 main.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from main import format_sse
except ImportError:
    # 允许在函数尚未定义时导入失败，以便 TDD 流程正常进行
    def format_sse(event, content):
        raise NotImplementedError("format_sse is not yet implemented in main.py")

def test_format_sse_single_line():
    """测试单行输出"""
    event = "content"
    content = "hello"
    expected = "event: content\ndata: hello\n\n"
    assert format_sse(event, content) == expected

def test_format_sse_multi_line_newline():
    """测试多行输出 (\\n)"""
    event = "content"
    content = "line1\nline2"
    expected = "event: content\ndata: line1\ndata: line2\n\n"
    assert format_sse(event, content) == expected

def test_format_sse_multi_line_crlf():
    """测试多行输出 (\\r\\n)"""
    event = "status"
    content = "thinking\r\nsearching"
    # 我们期望 helper 能统一处理换行符
    expected = "event: status\ndata: thinking\ndata: searching\n\n"
    # 注意：如果 implementation 只是简单 split('\n')，\r 会残留在行尾，测试会捕捉到这个 Bug
    assert format_sse(event, content) == expected

def test_format_sse_empty_content():
    """测试空内容"""
    event = "done"
    content = ""
    expected = "event: done\ndata: \n\n"
    assert format_sse(event, content) == expected

def test_format_sse_multiple_newlines():
    """测试连续换行"""
    event = "content"
    content = "A\n\nB"
    expected = "event: content\ndata: A\ndata: \ndata: B\n\n"
    assert format_sse(event, content) == expected
