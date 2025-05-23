import os
import asyncio
import sys
import fire
from base64 import b64encode
from pathlib import Path
from io import BytesIO

import datetime

import cv2
import numpy as np
from PIL import Image
import json

from metagpt.const import METAGPT_ROOT, DEFAULT_WORKSPACE_ROOT
from metagpt.roles.di.data_interpreter import DataInterpreter

from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team



class UsabilityAction(Action):
    PROMPT_TEMPLATE: str = """
    You are an urban design expert. You will receive an image in base64 format. Please analyze the image and evaluate it from a usability perspective (accessibility, usability, user experience).
    
    The image is provided in base64 format. You should be able to see and analyze it.
    The image is provided in the following format: data:image/jpeg;base64,{image_base64}
    
    Return JSON format:
    {{
        "UsabilityAction": {{
            "rating_score": "0-10",
            "reason": "brief explanation",
            "suggestion": "brief improvement suggestion"
        }}
    }}
    
    Return ```json your_json_here ``` with NO other texts.
    """
    name: str = "UsabilityAction"

    async def run(self, image_base64: str):
        prompt = self.PROMPT_TEMPLATE.format(image_base64=image_base64)
        rsp = await self._aask(prompt)
        return rsp


class UsabilityAgent(Role):
    name: str = "UsabilityAgent"
    profile: str = "UsabilityAgent"

    def __init__(self, image_base64: str = "", **kwargs):
        super().__init__(**kwargs)
        self.image_base64 = image_base64
        self._watch([UserRequirement])
        self.set_actions([UsabilityAction])

    async def _act(self) -> Message:
        todo = self.rc.todo
        rsp = await todo.run(self.image_base64)
        return Message(content=rsp, role=self.profile, cause_by=type(todo))


class VitalityAction(Action):
    PROMPT_TEMPLATE: str = """
    You are an urban design expert. You will receive an image in base64 format. Please analyze the image and evaluate it from a vitality perspective (urban space, landscape, culture).
    
    The image is provided in base64 format. You should be able to see and analyze it.
    The image is provided in the following format: data:image/jpeg;base64,{image_base64}
    
    Return JSON format:
    {{
        "VitalityAction": {{
            "rating_score": "0-10",
            "reason": "brief explanation",
            "suggestion": "brief improvement suggestion"
        }}
    }}
    
    Return ```json your_json_here ``` with NO other texts.
    """
    name: str = "VitalityAction"

    async def run(self, image_base64: str):
        prompt = self.PROMPT_TEMPLATE.format(image_base64=image_base64)
        rsp = await self._aask(prompt)
        return rsp


class VitalityAgent(Role):
    name: str = "VitalityAgent"
    profile: str = "VitalityAgent"

    def __init__(self, image_base64: str = "", **kwargs):
        super().__init__(**kwargs)
        self.image_base64 = image_base64
        self._watch([UserRequirement])
        self.set_actions([VitalityAction])

    async def _act(self) -> Message:
        todo = self.rc.todo
        rsp = await todo.run(self.image_base64)
        return Message(content=rsp, role=self.profile, cause_by=type(todo))


class SafetyAction(Action):
    PROMPT_TEMPLATE: str = """
    You are an urban design expert. You will receive an image in base64 format. Please analyze the image and evaluate it from a safety perspective (pedestrians, cyclists, vehicles).
    
    The image is provided in base64 format. You should be able to see and analyze it.
    The image is provided in the following format: data:image/jpeg;base64,{image_base64}
    
    Return JSON format:
    {{
        "SafetyAction": {{
            "rating_score": "0-10",
            "reason": "brief explanation",
            "suggestion": "brief improvement suggestion"
        }}
    }}
    
    Return ```json your_json_here ``` with NO other texts.
    """
    name: str = "SafetyAction"

    async def run(self, image_base64: str):
        prompt = self.PROMPT_TEMPLATE.format(image_base64=image_base64)
        rsp = await self._aask(prompt)
        return rsp


class SafetyAgent(Role):
    name: str = "SafetyAgent"
    profile: str = "SafetyAgent"

    def __init__(self, image_base64: str = "", **kwargs):
        super().__init__(**kwargs)
        self.image_base64 = image_base64
        self._watch([UserRequirement])
        self.set_actions([SafetyAction])

    async def _act(self) -> Message:
        todo = self.rc.todo
        rsp = await todo.run(self.image_base64)
        return Message(content=rsp, role=self.profile, cause_by=type(todo))


class SummaryAction(Action):
    PROMPT_TEMPLATE: str = """
    You are a summary expert. You will receive evaluation results from 3 evaluation agents.
    First, validate if all evaluation results are valid and contain actual image analysis.
    If any evaluation result indicates that the image was not accessible or analyzable, return an error message. Please save the error message to the file: {save_path}
    
    Evaluation results:
    {evaluation_results}
    
    If all evaluations are valid, return JSON format:
    {{
        "SummaryAction": {{
            "evaluation_results": {{
                "usability": "usability feedback from UsabilityAgent",
                "vitality": "vitality feedback from VitalityAgent",
                "safety": "safety feedback from SafetyAgent"
            }},
            "summary_results": {{
                "summary": "brief summary from your own analysis",
                "conflicts": "key conflicts from your own analysis",
                "final_suggestion": "final improvement suggestion from your own analysis"
            }}
        }}
    }}
    
    If any evaluation is invalid, return JSON format:
    {{
        "SummaryAction": {{
            "error": "One or more evaluations failed to analyze the image properly",
            "invalid_evaluations": ["list of failed evaluation types"]
        }}
    }}
    
    Return ```json your_json_here ``` with NO other texts.
    """
    name: str = "SummaryAction"

    async def run(self, save_path: str, evaluation_results: str = ""):
        prompt = self.PROMPT_TEMPLATE.format(
            save_path=save_path,
            evaluation_results=evaluation_results
        )
        rsp = await self._aask(prompt)
        return rsp


class SummaryAgent(Role):
    name: str = "SummaryAgent"
    profile: str = "SummaryAgent"

    def __init__(self, save_path: str = "", **kwargs):
        super().__init__(**kwargs)
        self.save_path = save_path
        self._watch([UsabilityAction, VitalityAction, SafetyAction])
        self.set_actions([SummaryAction])

    async def _act(self) -> Message:
        todo = self.rc.todo
        # 获取所有评估结果
        memories = self.get_memories()
        # print("memories", memories)
        # raise
        evaluation_results = "\n".join([msg.content for msg in memories])
        
        rsp = await todo.run(self.save_path, evaluation_results)

        finally_message = Message(content=rsp, role=self.profile, cause_by=type(todo))
        with open(self.save_path, "w") as f:
            json.dump(finally_message.content, f)

        return finally_message



def encode_image(image_path: Path | str) -> str:
    """Encodes image to base64."""    
    with open(image_path, "rb") as img_file:
        b64code = b64encode(img_file.read()).decode('utf-8')
        return f"data:image/jpeg;base64,{b64code}"


async def main(
        idea: str = "",
        image_path: str = "",
        save_path: str = "",
        investment: float = 15.0,
        n_round: int = 1,
        add_human: bool = False,
):
    # 读取并转换图片
    # image = cv2.imread(image_path)
    # image = Image.fromarray(image)
    
    image_base64 = encode_image(image_path) # <class 'str'>

    # print("type(image_base64)", type(image_base64))
    # raise

    logger.info(idea)
    logger.info(f"Image loaded from: {image_path}")
    logger.info(f"Results will be saved to: {save_path}")

    team = Team()
    team.hire(
        [
            UsabilityAgent(image_base64=image_base64),
            VitalityAgent(image_base64=image_base64),
            SafetyAgent(image_base64=image_base64),
            SummaryAgent(save_path=save_path),
        ]
    )

    team.invest(investment=investment)
    team.run_project(idea)
    await team.run(n_round=n_round)


if __name__ == "__main__":
    save_dir = str(DEFAULT_WORKSPACE_ROOT / "urban_design")
    os.makedirs(save_dir, exist_ok=True)

    image_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data/2_image_compressed.jpg"
    save_path = f"{save_dir}/2_image_compressed_4o_suggestion-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    # image_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data/1_layout.png"
    # save_path = str(DEFAULT_WORKSPACE_ROOT / "urban_design" / f"1_layout_4o_suggestion-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    idea = f"This is an urban design image. You need to hire 3 evaluation agents (UsabilityAgent, VitalityAgent, SafetyAgent) to give specific evaluation of the image, and 1 summary agent (SummaryAgent) to give a summary of the evaluation results based on the evaluation results of the 3 agents and find the conflicts and unify their suggestions and give a final suggestion for improvement."

    asyncio.run(main(idea=idea, image_path=image_path, save_path=save_path))










# # without team
# async def main(image_path: str, requirement: str):
#     print("image_path", image_path)
#     print("requirement", requirement)
#     # raise
#     di = DataInterpreter()
#     await di.run(requirement)



# # without team
# if __name__ == "__main__":
#     # image_path = METAGPT_ROOT / "data" / "1_image.png"
#     image_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data/1_image.png"
#     save_path = DEFAULT_WORKSPACE_ROOT / "urban_design" / "1_image_improved.png"
#     # requirement = f"This is the path of an urban design image:{image_path}. You need to hire 3 evaluation agents to give specific evaluation of the image, and 1 summary agent to give a summary of the evaluation results based on the evaluation results of the 3 agents and find the conflicts and unify their suggestions and give a final suggestion for improvement. Specifically, first, you need to hire 1 agent to evaluate the image from the usability of urban design, 1 agent to evaluate the image from the vitality of urban design, and 1 agent to evaluate the image from the safety of urban design. Second, every agent should give a rating score between 0 and 10, and give a detailed explanation of the rating score, then give a suggestion for improvement. Third, you need to hire 1 agent to give a summary of the evaluation results, find the conflicts and unify their suggestions and give a final suggestion for improvement, and generate a new urban design image based on the final suggestion for improvement and save the image to the path:{save_path}."
#     # asyncio.run(main(image_path, requirement))
