#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest 配置文件
设置 Mock 环境、Fixtures
"""
import pytest
import asyncio
import sys
import os
from unittest.mock import patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session", autouse=True)
def setup_mock_environment():
    """测试会话开始前设置 Mock 环境"""
    os.environ["BLUECLAW_TEST_MODE"] = "1"
    os.environ["MOCK_LLM"] = "1"
    os.environ["MOCK_VIS"] = "1"
    
    yield
    
    # 清理
    os.environ.pop("BLUECLAW_TEST_MODE", None)
    os.environ.pop("MOCK_LLM", None)
    os.environ.pop("MOCK_VIS", None)


@pytest.fixture
def event_loop():
    """提供事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_vms():
    """提供 Mock VMS"""
    from tests.mocks.mock_vms import MockVMS
    return MockVMS()


@pytest.fixture
def mock_vlm():
    """提供 Mock VLM"""
    from tests.mocks.mock_vlm import MockVLM
    return MockVLM()


@pytest.fixture
def mock_mpl():
    """提供 Mock MPL"""
    from tests.mocks.mock_mpl import MockMPL
    return MockMPL()


@pytest.fixture
def patch_vis_modules(mock_vms, mock_vlm, mock_mpl):
    """自动 patch 所有 Vis 模块为 Mock 版本"""
    with patch('backend.vis.vms.vms', mock_vms), \
         patch('backend.vis.vlm.vlm', mock_vlm), \
         patch('backend.vis.mpl.mpl', mock_mpl):
        yield {
            'vms': mock_vms,
            'vlm': mock_vlm,
            'mpl': mock_mpl
        }
