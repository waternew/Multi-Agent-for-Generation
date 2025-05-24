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
    
    Return feedback in JSON format:
    {{
        "agent": "UsabilityAgent",
        "description": "what you see in the image",
        "rating_score": 0-10,
        "reason": "brief explanation",
        "suggestion": "brief improvement suggestion"
    }}
    
    Please return your feedback in valid JSON format without any markdown formatting or additional text.
    """
    name: str = "UsabilityAction"

    async def run(self, content: str, image_base64: str):
        prompt = self.PROMPT_TEMPLATE.format(content=content)
        rsp = await self._aask(prompt=prompt, system_msgs=None, images=[image_base64])
        print("\n\n=============== UsabilityAction rsp ===============\n\n", rsp)
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
        print("\n\n=============== UsabilityAgent code_text ===============\n\n", code_text)
        # raise
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo), send_to="SummaryAgent")
        # 确保消息被发送到SummaryAgent
        self.publish_message(msg)
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
    
    Return feedback in JSON format:
    {{
        "agent": "VitalityAgent",
        "description": "what you see in the image",
        "rating_score": 0-10,
        "reason": "brief explanation",
        "suggestion": "brief improvement suggestion"
    }}
    
    Please return your feedback in valid JSON format without any markdown formatting or additional text.
    """
    name: str = "VitalityAction"

    async def run(self, content: str, image_base64: str):
        prompt = self.PROMPT_TEMPLATE.format(content=content)
        rsp = await self._aask(prompt=prompt, system_msgs=None, images=[image_base64])
        print("\n\n=============== VitalityAction rsp ===============\n\n", rsp)
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
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo), send_to="SummaryAgent")
        # 确保消息被发送到SummaryAgent
        self.publish_message(msg)
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
    
    Return feedback in JSON format:
    {{
        "agent": "SafetyAgent",
        "description": "what you see in the image",
        "rating_score": 0-10,
        "reason": "brief explanation",
        "suggestion": "brief improvement suggestion"
    }}
    
    Please return your feedback in valid JSON format without any markdown formatting or additional text.
    """
    name: str = "SafetyAction"

    async def run(self, content: str, image_base64: str):
        prompt = self.PROMPT_TEMPLATE.format(content=content)
        rsp = await self._aask(prompt=prompt, system_msgs=None, images=[image_base64])
        print("\n\n=============== SafetyAction prompt ===============\n\n", prompt)
        print("\n\n=============== SafetyAction content ===============\n\n", content)
        #  [Message] from User to SummaryAgent: This is an urban design image. You need to hire 3 evaluation agents (UsabilityAgent, VitalityAgent, SafetyAgent) to give specific evaluation of the image, and 1 summary agent (SummaryAgent) to give a summary of the evaluation results based on the evaluation results of the 3 agents and find the conflicts and unify their suggestions and give a final suggestion for improvement.
        print("\n\n=============== SafetyAction rsp ===============\n\n", rsp)
        #  {"agent": "SafetyAgent", "description": "The image shows an urban area plan with several large buildings, green spaces, pathways, and roads.", "rating_score": 7, "reason": "The design includes green spaces and pathways that may accommodate pedestrians and cyclists safely. There seems to be adequate separation between vehicular roads and pedestrian pathways. However, the exact markings and signage are not visible, which are crucial for safety enforcement.", "suggestion": "Include clear demarcations and traffic calming measures for pedestrian crossings and cyclist paths. Add signage and lighting to improve visibility and safety for all users."}
        # raise
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
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo), send_to="SummaryAgent")
        # 确保消息被发送到SummaryAgent
        self.publish_message(msg)
        print("\n\n=============== SafetyAgent msg ===============\n\n", msg)
        return msg


class SummaryAction(Action):
    PROMPT_TEMPLATE: str = """
    You are a summary expert. You will receive evaluation results from 3 evaluation agents in JSON format.
    The input will be a JSON array containing the evaluations from UsabilityAgent, VitalityAgent, and SafetyAgent.

    If any evaluation result indicates that the image was not accessible or analyzable, you should save the error message to the file: {save_path}. And if all evaluations are valid, you should give a comprehensive summary in the JSON format below, and save the summary to the file: {save_path}.
    
    Please analyze the evaluations and provide a comprehensive summary in the following JSON format:
    {{
        "agent": "SummaryAgent",
        "summary": "A brief summary of the key points from all three evaluations",
        "conflicts": "Any conflicts or contradictions found between the evaluations",
        "final_suggestion": "A unified improvement suggestion that addresses all concerns"
    }}
    
    If any evaluation result indicates that the image was not accessible or analyzable, return:
    {{
        "agent": "SummaryAgent",
        "summary_error": "One or more evaluations failed to analyze the image properly"
    }}
    
    Please ensure your response is valid JSON and follows the exact format specified above.
    """
    name: str = "SummaryAction"

    async def run(self, content: str = "", evaluation_str: str = "", save_path: str = ""):
        prompt = self.PROMPT_TEMPLATE.format(content=content, evaluation_str=evaluation_str, save_path=save_path)
        rsp = await self._aask(prompt)
        print("\n\n=============== SummaryAction rsp ===============\n\n", rsp)
        return rsp


class SummaryAgent(Role):
    name: str = "SummaryAgent"
    profile: str = "SummaryAgent"

    def __init__(self, save_path: str = "", **kwargs):
        super().__init__(**kwargs)
        self.save_path = save_path
        # 修改监听设置
        self._watch([UsabilityAction, VitalityAction, SafetyAction])
        self.set_actions([SummaryAction])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        
        # 获取所有评估Agent的消息
        memories = self.get_memories(k=0)
        print("\n\n=============== SummaryAgent memories ===============\n\n", memories)
        print("\n\n=============== SummaryAgent self.get_memories ===============\n\n", self.get_memories)
        # raise
        
        if len(memories) < 3:
            print("\n\n=============== SummaryAgent Not enough memories ===============\n\n")
            return Message(content="Error: Not enough evaluation results received", role=self.profile)
            
        # 提取每个Agent的JSON内容
        evaluation_results = []
        for i, msg in enumerate(memories):
            print(f"\n\n=============== SummaryAgent Processing memory {i} ===============\n\n")
            print(f"Message content: {msg.content}")
            try:
                # 提取JSON部分
                content = msg.content
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content.strip()
                
                print(f"\n\n=============== SummaryAgent Extracted JSON {i} ===============\n\n")
                print(f"JSON string: {json_str}")
                    
                # 解析JSON
                result = json.loads(json_str)
                evaluation_results.append(result)
                print(f"\n\n=============== SummaryAgent Successfully parsed JSON {i} ===============\n\n")
            except Exception as e:
                print(f"\n\n=============== SummaryAgent Error parsing JSON {i} ===============\n\n")
                print(f"Error: {str(e)}")
                logger.error(f"Error parsing JSON from {msg.role}: {str(e)}")
                return Message(content=f"Error parsing evaluation results: {str(e)}", role=self.profile)
        
        # 将评估结果转换为字符串
        evaluation_str = json.dumps(evaluation_results, ensure_ascii=False, indent=2)
        print("\n\n=============== SummaryAgent evaluation_str ===============\n\n", evaluation_str)
        
        # 运行总结Action
        code_text = await todo.run(evaluation_str=evaluation_str, save_path=self.save_path)
        
        finally_msg = Message(content=code_text, role=self.profile, cause_by=type(todo))
        print("\n\n=============== SummaryAgent finally_msg ===============\n\n", finally_msg)
        print("\n\n=============== SummaryAgent finally_msg.content ===============\n\n", finally_msg.content)
        
        # 保存结果
        with open(self.save_path, "w", encoding='utf-8') as f:
            f.write(finally_msg.content)
        return finally_msg



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

    logger.info(idea)
    logger.info(f"Image loaded from: {image_path}")
    logger.info(f"Results will be saved to: {save_path}")

    # 创建团队    
    team = Team()
    team.hire(
        [
            UsabilityAgent(image_base64=image_base64),
            VitalityAgent(image_base64=image_base64),
            SafetyAgent(image_base64=image_base64),
            SummaryAgent(save_path=save_path),
        ]
    )

    # 设置投资和运行项目
    team.invest(investment=investment)
    team.run_project(idea)
    # 运行方式1：直接运行
    await team.run(n_round=n_round)


if __name__ == "__main__":
    save_dir = str(DEFAULT_WORKSPACE_ROOT / "urban_design")
    os.makedirs(save_dir, exist_ok=True)

    image_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data/2_image_compressed.jpg"
    save_path = f"{save_dir}/2_image_compressed_4o_suggestion-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    # image_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data/2_layout_compressed.jpg"
    # save_path = f"{save_dir}/2_layout_compressed_4o_suggestion-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    idea = f"This is an urban design image. You need to hire 3 evaluation agents (UsabilityAgent, VitalityAgent, SafetyAgent) to give specific evaluation of the image, and 1 summary agent (SummaryAgent) to give a summary of the evaluation results based on the evaluation results of the 3 agents and find the conflicts and unify their suggestions and give a final suggestion for improvement."

    asyncio.run(main(idea=idea, image_path=image_path, save_path=save_path))
