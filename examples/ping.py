#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/4/22 14:28
@Author  : alexanderwu
@File    : ping.py
"""

import asyncio
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.configs.llm_config import LLMConfig


async def ask_and_print(question: str, llm: LLM, system_prompt) -> str:
    logger.info(f"Q: {question}")
    print('--------question--------', question)
    rsp = await llm.aask(question, system_msgs=[system_prompt])
    logger.info(f"A: {rsp}")
    logger.info("\n")
    return rsp


async def main():
    # 创建 LLMConfig 实例
    # llm_config = LLMConfig(
    #     api_type="openai",
    #     model="gpt-3.5-turbo",
    #     base_url="https://chatapi.littlewheat.com/v1",
    #     api_key="sk-5rDGIzSL8UFIinrxFp60MPFq3JsqdLVLKHOWJK2GGOFIgLoR"
    # )
    
    # 使用配置创建 LLM 实例
    # llm = LLM(llm_config=llm_config)
    llm = LLM()
    await ask_and_print("ping?", llm, "Just answer pong when ping.")


if __name__ == "__main__":
    asyncio.run(main())
