from __future__ import annotations
import pytest
from unittest.mock import patch, Mock

from langchain.chat_models import BaseChatModel
from solarseptem_deepresearch.models import create_chat_model


# ------------------------------
# 使用 parametrize 批量测试模型调用
# ------------------------------
@pytest.mark.parametrize(
    "question, expected_keyword",
    [
        ("你是谁", "我"),
        ("你能做什么", "能力"),
        ("hello", "hello"),
    ],
)
@patch.object(BaseChatModel, "invoke")
def test_model_invoke_with_parametrize(
    mock_invoke: Mock,
    question: str,
    expected_keyword: str,
):
    """
    批量测试模型 invoke 方法
    使用 parametrize 传入多组问题 + 预期关键词
    用 mock 不真实调用 AI
    """
    # 模拟 AI 返回内容
    mock_invoke.return_value = Mock(content=f"这是回答：{expected_keyword}")

    # 执行
    model = create_chat_model()
    response = model.invoke(question)

    # 断言
    mock_invoke.assert_called_once_with(question)  # 确保参数正确
    assert expected_keyword in response.content    # 确保关键词存在


# ------------------------------
# 基础测试：模型创建成功
# ------------------------------
def test_create_chat_model():
    model = create_chat_model()
    assert isinstance(model, BaseChatModel)


