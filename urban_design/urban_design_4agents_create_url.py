import os
import asyncio
import sys
import fire
import base64
from io import BytesIO
import datetime
import cv2
import numpy as np
from PIL import Image
import json
import requests
from pathlib import Path

from metagpt.const import METAGPT_ROOT, DEFAULT_WORKSPACE_ROOT
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team

def upload_to_imgur(image_path: str) -> str:
    """上传图片到imgur并返回URL"""
    try:
        # 读取图片文件
        with open(image_path, 'rb') as image_file:
            # 准备请求头
            headers = {
                'Authorization': 'Client-ID YOUR_IMGUR_CLIENT_ID'  # 需要替换为你的Imgur Client ID
            }
            
            # 准备文件数据
            files = {
                'image': image_file
            }
            
            # 发送POST请求到Imgur API
            response = requests.post(
                'https://api.imgur.com/3/image',
                headers=headers,
                files=files
            )
            
            # 检查响应
            if response.status_code == 200:
                data = response.json()
                return data['data']['link']
            else:
                raise Exception(f"Upload failed with status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to upload image: {str(e)}")
        raise

class UsabilityAction(Action):
    PROMPT_TEMPLATE: str = """
    You are an urban design expert. Please analyze the urban design image from the following URL and evaluate it from a usability perspective (accessibility, usability, user experience).
    
    Image URL: {image_url}
    
    Please focus on:
    1. Accessibility features (ramps, elevators, etc.)
    2. User experience (seating, walkways, etc.)
    3. Overall usability of the space
    
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

    async def run(self, image_url: str):
        prompt = self.PROMPT_TEMPLATE.format(image_url=image_url)
        rsp = await self._aask(prompt)
        return rsp

class UsabilityAgent(Role):
    name: str = "UsabilityAgent"
    profile: str = "UsabilityAgent"

    def __init__(self, image_url: str = "", **kwargs):
        super().__init__(**kwargs)
        self.image_url = image_url
        self._watch([UserRequirement])
        self.set_actions([UsabilityAction])

    async def _act(self) -> Message:
        todo = self.rc.todo
        rsp = await todo.run(self.image_url)
        return Message(content=rsp, role=self.profile, cause_by=type(todo))

class VitalityAction(Action):
    PROMPT_TEMPLATE: str = """
    You are an urban design expert. Please analyze the urban design image from the following URL and evaluate it from a vitality perspective (urban space, landscape, culture).
    
    Image URL: {image_url}
    
    Please focus on:
    1. Urban space utilization
    2. Landscape features
    3. Cultural elements
    
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

    async def run(self, image_url: str):
        prompt = self.PROMPT_TEMPLATE.format(image_url=image_url)
        rsp = await self._aask(prompt)
        return rsp

class VitalityAgent(Role):
    name: str = "VitalityAgent"
    profile: str = "VitalityAgent"

    def __init__(self, image_url: str = "", **kwargs):
        super().__init__(**kwargs)
        self.image_url = image_url
        self._watch([UserRequirement])
        self.set_actions([VitalityAction])

    async def _act(self) -> Message:
        todo = self.rc.todo
        rsp = await todo.run(self.image_url)
        return Message(content=rsp, role=self.profile, cause_by=type(todo))

class SafetyAction(Action):
    PROMPT_TEMPLATE: str = """
    You are an urban design expert. Please analyze the urban design image from the following URL and evaluate it from a safety perspective (pedestrians, cyclists, vehicles).
    
    Image URL: {image_url}
    
    Please focus on:
    1. Pedestrian safety
    2. Cyclist safety
    3. Vehicle safety
    
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

    async def run(self, image_url: str):
        prompt = self.PROMPT_TEMPLATE.format(image_url=image_url)
        rsp = await self._aask(prompt)
        return rsp

class SafetyAgent(Role):
    name: str = "SafetyAgent"
    profile: str = "SafetyAgent"

    def __init__(self, image_url: str = "", **kwargs):
        super().__init__(**kwargs)
        self.image_url = image_url
        self._watch([UserRequirement])
        self.set_actions([SafetyAction])

    async def _act(self) -> Message:
        todo = self.rc.todo
        rsp = await todo.run(self.image_url)
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

async def main(
        idea: str = "",
        image_path: str = "",
        save_path: str = "",
        investment: float = 15.0,
        n_round: int = 1,
        add_human: bool = False,
):
    # 上传图片并获取URL
    try:
        image_url = upload_to_imgur(image_path)
        logger.info(f"Image uploaded successfully, URL: {image_url}")
    except Exception as e:
        logger.error(f"Failed to upload image: {str(e)}")
        raise

    logger.info(idea)
    logger.info(f"Image loaded from: {image_path}")
    logger.info(f"Results will be saved to: {save_path}")

    team = Team()
    team.hire(
        [
            UsabilityAgent(image_url=image_url),
            VitalityAgent(image_url=image_url),
            SafetyAgent(image_url=image_url),
            SummaryAgent(save_path=save_path),
        ]
    )

    team.invest(investment=investment)
    team.run_project(idea)
    await team.run(n_round=n_round)

if __name__ == "__main__":
    save_dir = DEFAULT_WORKSPACE_ROOT / "urban_design"
    os.makedirs(save_dir, exist_ok=True)

    image_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data/2_image_compressed.jpg"
    save_path = str(save_dir / f"2_image_compressed_4o_suggestion-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    idea = f"This is an urban design image. You need to hire 3 evaluation agents (UsabilityAgent, VitalityAgent, SafetyAgent) to give specific evaluation of the image, and 1 summary agent (SummaryAgent) to give a summary of the evaluation results based on the evaluation results of the 3 agents and find the conflicts and unify their suggestions and give a final suggestion for improvement."

    asyncio.run(main(idea=idea, image_path=image_path, save_path=save_path))
