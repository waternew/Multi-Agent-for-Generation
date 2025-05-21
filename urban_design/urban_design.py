import asyncio
import sys
import fire

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.roles.di.data_interpreter import DataInterpreter

from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team


async def main(image_path: str, requirement: str):
    pass




if __name__ == "__main__":
    image_path = ""
    requirement = ""
    asyncio.run(main(image_path, requirement))