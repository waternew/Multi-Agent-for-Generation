import asyncio
import sys
import fire

from metagpt.const import METAGPT_ROOT, DEFAULT_WORKSPACE_ROOT
from metagpt.roles.di.data_interpreter import DataInterpreter

from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team


async def main(image_path: str, requirement: str):
    print("image_path", image_path)
    print("requirement", requirement)
    # raise
    di = DataInterpreter()
    await di.run(requirement)


if __name__ == "__main__":
    # image_path = METAGPT_ROOT / "data" / "1_image.png"
    image_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data/1_layout.png"
    # image_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data/1_image.png"
    save_path = DEFAULT_WORKSPACE_ROOT / "urban_design" / "1_image_improved.png"
    requirement = f"This is the path of an urban design image:{image_path}. You need to hire 3 evaluation agents to give specific evaluation of the image, and 1 summary agent to give a summary of the evaluation results based on the evaluation results of the 3 agents and find the conflicts and unify their suggestions and give a final suggestion for improvement. Specifically, first, you need to hire 1 agent to evaluate the image from the usability of urban design, 1 agent to evaluate the image from the vitality of urban design, and 1 agent to evaluate the image from the safety of urban design. Second, every agent should give a rating score between 0 and 10, and give a detailed explanation of the rating score, then give a suggestion for improvement. Third, you need to hire 1 agent to give a summary of the evaluation results, find the conflicts and unify their suggestions and give a final suggestion for improvement, and generate a new urban design image based on the final suggestion for improvement and save the image to the path:{save_path}."
    asyncio.run(main(image_path, requirement))