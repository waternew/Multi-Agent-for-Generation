#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : llm.py
"""
from typing import Optional

from metagpt.configs.llm_config import LLMConfig
from metagpt.context import Context
from metagpt.provider.base_llm import BaseLLM


def LLM(llm_config: Optional[LLMConfig] = None, context: Context = None) -> BaseLLM:
    """get the default llm provider if name is None"""
    ctx = context or Context()
    print('context', context)
    print('Context()', Context())
    print('========= llm_config =========')
    print('llm_config', llm_config)
    print('========= llm_config =========')

    if llm_config is not None:
        print('llm_config is not None')
        return ctx.llm_with_cost_manager_from_llm_config(llm_config)
    print('llm_config is None')

    return ctx.llm()
