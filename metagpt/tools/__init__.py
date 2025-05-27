#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 15:35
@Author  : alexanderwu
@File    : __init__.py
"""

from metagpt.tools import libs  # this registers all tools
from metagpt.tools.tool_registry import TOOL_REGISTRY, register_tool
# from metagpt.tools.tool_registry import TOOL_REGISTRY
from metagpt.tools.tool_convert import convert_code_to_tool_schema, convert_code_to_tool_schema_ast
from metagpt.tools.tool_data_type import Tool, ToolSchema
from metagpt.configs.search_config import SearchEngineType
from metagpt.configs.browser_config import WebBrowserEngineType

# from metagpt.tools.libs.shell import shell_execute

_ = libs, TOOL_REGISTRY  # Avoid pre-commit error


class SearchInterface:
    async def asearch(self, *args, **kwargs):
        ...


# __all__ = ["SearchEngineType", "WebBrowserEngineType", "TOOL_REGISTRY", "register_tool", "convert_code_to_tool_schema", "convert_code_to_tool_schema_ast", "Tool", "ToolSchema", "shell_execute"]
__all__ = ["SearchEngineType", "WebBrowserEngineType", "TOOL_REGISTRY"]
