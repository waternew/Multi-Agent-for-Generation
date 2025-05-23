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
    
    The image is provided in base64 format. You should be able to see the image content directly. If you cannot see the image, please respond with an error message.
    
    Please focus on:
    1. Accessibility features (ramps, elevators, etc.)
    2. User experience (seating, walkways, etc.)
    3. Overall usability of the space
    
    Return feedback format:
    [UsabilityAgent]
    [description]: what you see in the image,
    [rating_score]: 0-10,
    [reason]: brief explanation,
    [suggestion]: brief improvement suggestion
    
    Return ``` your feedback here ``` with NO other texts.
    """
    name: str = "UsabilityAction"

    async def run(self, content: str, image_base64: str):
        prompt = self.PROMPT_TEMPLATE.format(content=content)
        # print("\n\n=============== UsabilityAction type(prompt) ===============\n\n", type(prompt))
        # print("\n\n=============== UsabilityAction prompt ===============\n\n", prompt)
        # print("\n\n=============== UsabilityAction type(content) ===============\n\n", type(content))
        # print("\n\n=============== UsabilityAction content ===============\n\n", content)
        # print("\n\n=============== UsabilityAction type(image_base64) ===============\n\n", type(image_base64))
        # print("\n\n=============== UsabilityAction image_base64 ===============\n\n", image_base64)
        # raise

        rsp = await self._aask(prompt=prompt, system_msgs=None, images=[image_base64])
        print("\n\n=============== UsabilityAction rsp ===============\n\n", rsp)
        # print("\n\n=============== UsabilityAction type(image_base64) ===============\n\n", type(image_base64))
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
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        msg = self.get_memories(k=1)[0]  # find the most recent messages
        code_text = await todo.run(msg.content, self.image_base64)
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))
        print("\n\n=============== UsabilityAgent msg ===============\n\n", msg)
        return msg


class VitalityAction(Action):
    PROMPT_TEMPLATE: str = """
    You are an urban design expert. Please analyze the image and evaluate it from a vitality perspective (urban space, landscape, culture).
    
    The image is provided in base64 format. You should be able to see the image content directly. If you cannot see the image, please respond with an error message.

    Please focus on:
    1. Urban space utilization
    2. Landscape features
    3. Cultural elements
    
    Return feedback format:
    [VitalityAgent]
    [description]: what you see in the image,
    [rating_score]: 0-10,
    [reason]: brief explanation,
    [suggestion]: brief improvement suggestion
    
    Return ``` your feedback here ``` with NO other texts.
    """
    name: str = "VitalityAction"

    async def run(self, content: str, image_base64: str):
        prompt = self.PROMPT_TEMPLATE.format(content=content)
        rsp = await self._aask(prompt=prompt, system_msgs=None, images=[image_base64])
        print("\n\n=============== VitalityAction rsp ===============\n\n", rsp)
        # print("\n\n=============== VitalityAction type(image_base64) ===============\n\n", type(image_base64))
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
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        msg = self.get_memories(k=1)[0]  # find the most recent messages
        code_text = await todo.run(msg.content, self.image_base64)
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))
        print("\n\n=============== VitalityAction msg ===============\n\n", msg)
        return msg


class SafetyAction(Action):
    PROMPT_TEMPLATE: str = """
    You are an urban design expert. You will receive an image in base64 format. Please analyze the image and evaluate it from a safety perspective (pedestrians, cyclists, vehicles).
    
    The image is provided in base64 format. You should be able to see the image content directly. If you cannot see the image, please respond with an error message.
    
    Please focus on:
    1. Pedestrian safety
    2. Cyclist safety
    3. Vehicle safety
    
    Return feedback format:
    [SafetyAgent]
    [description]: what you see in the image,
    [rating_score]: 0-10,
    [reason]: brief explanation,
    [suggestion]: brief improvement suggestion
    
    Return ``` your feedback here ``` with NO other texts.
    """
    name: str = "SafetyAction"

    async def run(self, content: str, image_base64: str):
        prompt = self.PROMPT_TEMPLATE.format(content=content)
        rsp = await self._aask(prompt=prompt, system_msgs=None, images=[image_base64])
        print("\n\n=============== SafetyAction rsp ===============\n\n", rsp)
        # print("\n\n=============== SafetyAction type(image_base64) ===============\n\n", type(image_base64))
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
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        msg = self.get_memories(k=1)[0]  # find the most recent messages
        code_text = await todo.run(msg.content, self.image_base64)
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))
        print("\n\n=============== SafetyAgent msg ===============\n\n", msg)
        return msg


class SummaryAction(Action):
    PROMPT_TEMPLATE: str = """
    You are a summary expert. You will receive evaluation results from 3 evaluation agents.
    First, validate and contain actual image analysis.
    If any evaluation result indicates that the image was not accessible or analyzable, return an error message. Please save the error message to the file: {save_path}
        
    If all evaluations are valid, print your feedback and save the following format:
    [SummaryAgent]
    [evaluation_results]:
    "UsabilityAgent evaluation results": summary the usability feedback from UsabilityAgent using a sentence, including the rating score, the reason, and the suggestion for improvement,
    "VitalityAgent evaluation results": summary the vitality feedback from VitalityAgent using a sentence, including the rating score, the reason, and the suggestion for improvement,
    "SafetyAgent evaluation results": summary the safety feedback from SafetyAgent using a sentence, including the rating score, the reason, and the suggestion for improvement
    [summary_results]:
    "summary": "brief summary from your own analysis
    "conflicts": "key conflicts from your own analysis
    "final_suggestion": "final improvement suggestion from your own analysis
    
    If any evaluation is invalid, print your feedback and save the following format:
    [SummaryAgent]
    "summary_error": One or more evaluations failed to analyze the image properly
    
    Return ``` your_feedback here ``` with NO other texts.
    """
    name: str = "SummaryAction"

    async def run(self, save_path: str, evaluation_results: str = "", content: str = ""):
        print("\n\n=============== SummaryAction save_path ===============\n\n", save_path)
        print("\n\n=============== SummaryAction evaluation_results ===============\n\n", evaluation_results)
        print("\n\n=============== SummaryAction content ===============\n\n", content)
        # raise
        prompt = self.PROMPT_TEMPLATE.format(
            save_path=save_path,
            evaluation_results=evaluation_results,
            content=content
        )
        rsp = await self._aask(prompt)
        print("\n\n=============== SummaryAction rsp ===============\n\n", rsp)
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
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        
        # 获取所有评估结果
        msgs = self.get_memories()
        print("\n\n=============== SummaryAgent msgs ===============\n\n", msgs)
        
        # 将所有评估结果组合成一个字符串
        evaluation_results = "\n".join([msg.content for msg in msgs])
        print("\n\n=============== SummaryAgent evaluation_results ===============\n\n", evaluation_results)
        
        # 获取原始的用户需求
        user_msg = self.get_memories(k=1)[0]  # 获取第一条消息（用户需求）
        print("\n\n=============== SummaryAgent user_msg ===============\n\n", user_msg)
        # raise
        
        # 调用SummaryAction的run方法
        code_text = await todo.run(
            save_path=self.save_path,
            evaluation_results=evaluation_results,
            content=user_msg.content
        )

        finally_message = Message(content=code_text, role=self.profile, cause_by=type(todo))
        with open(self.save_path, "w") as f:
            f.write(finally_message.content)

        return finally_message



def encode_image(image_path: Path | str) -> str:
    """Encodes image to base64."""    
    with open(image_path, "rb") as img_file:
        b64code = b64encode(img_file.read()).decode('utf-8')
        return b64code


async def main(
        idea: str = "",
        image_path: str = "",
        save_path: str = "",
        investment: float = 15.0,
        n_round: int = 1,
        add_human: bool = False,
):
    # 读取并转换图片
    image_base64 = encode_image(image_path)
    # print("\n\n=============== image_base64 ===============\n\n", image_base64)
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
    save_path = f"{save_dir}/2_image_compressed_4o_suggestion-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    idea = f"This is an urban design image. You need to hire 3 evaluation agents (UsabilityAgent, VitalityAgent, SafetyAgent) to give specific evaluation of the image, and 1 summary agent (SummaryAgent) to give a summary of the evaluation results based on the evaluation results of the 3 agents and find the conflicts and unify their suggestions and give a final suggestion for improvement."

    asyncio.run(main(idea=idea, image_path=image_path, save_path=save_path))
