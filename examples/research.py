#!/usr/bin/env python

import asyncio
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
print('sys.path', sys.path)
# # 设置环境变量
# os.environ["METAGPT_PROJECT_ROOT"] = str(Path(__file__).parent.parent.absolute())
# print("Set METAGPT_PROJECT_ROOT to:", os.environ["METAGPT_PROJECT_ROOT"])

from metagpt.roles.researcher import RESEARCH_PATH, Researcher
from metagpt.const import METAGPT_ROOT

async def main():
    # print('Current working directory:', os.getcwd())
    # print('RESEARCH_PATH:', RESEARCH_PATH)
    print('METAGPT_ROOT:', METAGPT_ROOT) # correct
    # print('Environment METAGPT_PROJECT_ROOT:', os.getenv("METAGPT_PROJECT_ROOT"))
    
    topic = "dataiku vs. datarobot"
    role = Researcher(language="en-us")
    await role.run(topic)
    await asyncio.sleep(3)  # 暂停1秒
    print(f"save report to {RESEARCH_PATH / f'{topic}.md'}.")


if __name__ == "__main__":
    asyncio.run(main())
