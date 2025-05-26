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

import urllib.request
import time
import requests
import random

from metagpt.const import METAGPT_ROOT, DEFAULT_WORKSPACE_ROOT
from metagpt.roles.di.data_interpreter import DataInterpreter

from metagpt.context import Context
from metagpt.environment import Environment
from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team
from metagpt.tools.tool_recommend import BM25ToolRecommender

from api_payload import i2i_controlnet_payload
from sd_webapi import timestamp, encode_file_to_base64, decode_and_save_base64, call_api, call_img2img_api


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
        # self._watch([UserRequirement])
        self._watch([UserRequirement, GenImageAction])
        self.set_actions([UsabilityAction])

        logger.info(f"UsabilityAgent UserRequirement): {UserRequirement}")

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        msg = self.get_memories(k=1)[0]  # find the most recent messages
        # debug
        # print("\n\n=============== UsabilityAgent msg.content ===============\n\n", msg.content)
        # print("\n\n=============== UsabilityAgent self.rc.history ===============\n\n", self.rc.history)
        # print("\n\n=============== UsabilityAgent self.rc.news ===============\n\n", self.rc.news)
        # raise
        code_text = await todo.run(msg.content, self.image_base64)
        print("\n\n=============== UsabilityAgent code_text ===============\n\n", code_text)
        logger.info(f"UsabilityAgent cause_by: {type(todo)}")
        # raise
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo), send_to="SummaryAgent")
        print()
        # 确保消息被发送到SummaryAgent
        self.publish_message(msg)
        print("\n\n=============== UsabilityAgent msg ===============\n\n", msg)

        logger.info("UsabilityAgent msg", msg)

        logger.info("UsabilityAgent msg", msg)
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
        # self._watch([UserRequirement])
        self._watch([UserRequirement, GenImageAction])
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
        # self._watch([UserRequirement])
        self._watch([UserRequirement, GenImageAction])
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

        logger.info("SafetyAgent msg", msg)
        return msg


class SummaryAction(Action):
    PROMPT_TEMPLATE: str = """
    You are a summary expert. You will receive evaluation results from 3 evaluation agents in JSON format.
    The input will be a JSON array containing the evaluations from UsabilityAgent, VitalityAgent, and SafetyAgent.

    If any evaluation result indicates that the image was not accessible or analyzable, you should save the error message to the file: {save_path}. And if all evaluations are valid, you should give a comprehensive summary in the JSON format below, and save the summary to the file: {save_path}.

    What evaluations you receive from UsabilityAgent, VitalityAgent, and SafetyAgent will be like this:
    {{
        "agent": "UsabilityAgent",
        "description": "what you see in the image",
        "rating_score": 0-10,
        "reason": "brief explanation",
        "suggestion": "brief improvement suggestion"
    }}
    
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

        logger.info(f"SummaryAgent UsabilityAction, VitalityAction, SafetyAction): {UsabilityAction, VitalityAction, SafetyAction}")

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo
        
        # 获取所有评估Agent的消息
        memories = self.get_memories(k=0)
        print("\n\n=============== SummaryAgent memories ===============\n\n", memories)
        print("\n\n=============== SummaryAgent self.get_memories ===============\n\n", self.get_memories)
        # raise
                    
        # # 提取每个Agent的JSON内容
        # evaluation_results = []
        # for i, msg in enumerate(memories):
        #     print(f"\n\n=============== SummaryAgent Processing memory {i} ===============\n\n")
        #     print(f"Message content: {msg.content}")
        #     try:
        #         # 提取JSON部分
        #         content = msg.content
        #         if "```json" in content:
        #             json_str = content.split("```json")[1].split("```")[0].strip()
        #         elif "```" in content:
        #             json_str = content.split("```")[1].split("```")[0].strip()
        #         else:
        #             json_str = content.strip()
                
        #         print(f"\n\n=============== SummaryAgent Extracted JSON {i} ===============\n\n")
        #         print(f"JSON string: {json_str}")
                    
        #         # 解析JSON
        #         result = json.loads(json_str)
        #         evaluation_results.append(result)
        #         print(f"\n\n=============== SummaryAgent Successfully parsed JSON {i} ===============\n\n")
        #     except Exception as e:
        #         print(f"\n\n=============== SummaryAgent Error parsing JSON {i} ===============\n\n")
        #         print(f"Error: {str(e)}")
        #         logger.error(f"Error parsing JSON from {msg.role}: {str(e)}")
        
        # # 将评估结果转换为字符串
        # evaluation_str = json.dumps(evaluation_results, ensure_ascii=False, indent=2)
        # print("\n\n=============== SummaryAgent evaluation_str ===============\n\n", evaluation_str)
        
        # 运行总结Action
        code_text = await todo.run(content=memories, save_path=self.save_path)
        
        summary_msg = Message(content=code_text, role=self.profile, cause_by=type(todo), send_to="GenImageAgent")
        self.publish_message(summary_msg)
        print("\n\n=============== SummaryAgent summary_msg ===============\n\n", summary_msg)
        print("\n\n=============== SummaryAgent summary_msg.content ===============\n\n", summary_msg.content)

        # raise
        
        # 保存结果
        with open(self.save_path, "w", encoding='utf-8') as f:
            f.write(summary_msg.content)

        logger.info("SummaryAgent summary_msg", summary_msg)
        return summary_msg


class GenImageAction(Action):
    PROMPT_TEMPLATE: str = """
    You are an urban design expert. You will receive a image in base64 format, a suggestion from SummaryAgent, and a layout image in base64 format.
    Please use call_img2img_api function to generate a new image based on them.
    """
    name: str = "GenImageAction"

    async def run(self, content: str, image_base64: str, layout_base64: str, gen_image_path: str):
        
        webui_server_url = 'http://127.0.0.1:7860'
        out_i2i_dir = r"E:\\HKUST\\202505_Agent_Urban_Design\\MetaGPT\\workspace\\urban_design\\sd_api_out"
        os.makedirs(out_i2i_dir, exist_ok=True)

        random_seed = random.randint(1,1000000)

        prompt_i2i = content
        negative_prompt_i2i = ""
        print("\n\n=============== GenImageAction prompt_i2i ===============\n\n", prompt_i2i)
        # raise

        # 第一次的图片、后面的图片？

        payload_i2i = i2i_controlnet_payload(prompt_i2i, negative_prompt_i2i, image_base64, layout_base64, random_seed)    
        print("\n\n=============== GenImageAction payload_i2i ===============\n\n", payload_i2i)

        response = call_img2img_api(webui_server_url, **payload_i2i)

        for index, image in enumerate(response.get('images')):
            save_path = os.path.join(out_i2i_dir, f'img2img-{timestamp()}-{index}.png')
            decode_and_save_base64(image, save_path)

        print("\n\n=============== GenImageAction response ===============\n\n", response)
        return response
    
    
class GenImageAgent(Role):
    name: str = "GenImageAgent"
    profile: str = "GenImageAgent"

    def __init__(self, image_base64: str = "", layout_base64: str = "", gen_image_path: str = "", **kwargs):
        super().__init__(**kwargs)
        self.image_base64 = image_base64
        self.layout_base64 = layout_base64
        self.gen_image_path = gen_image_path
        self._watch([SummaryAction])
        self.set_actions([GenImageAction])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        msg = self.get_memories(k=1)[0]  # find the most recent messages
        print("\n\n=============== GenImageAgent self.get_memories ===============\n\n", msg)
        # raise
        gen_image = await todo.run(content=msg.content, image_base64=self.image_base64, layout_base64=self.layout_base64, gen_image_path=self.gen_image_path)

        gen_msg = Message(content=gen_image, role=self.profile, cause_by=type(todo), send_to=(UsabilityAgent, VitalityAgent, SafetyAgent))
        self.publish_message(gen_msg)

        print("\n\n=============== GenImageAgent type(gen_image) ===============\n\n", type(gen_image))
        print("\n\n=============== GenImageAgent gen_msg ===============\n\n", gen_msg)

        logger.info("GenImageAgent gen_msg", type(gen_msg))
        return gen_msg




def encode_image(image_path: Path | str) -> str:
    """Encodes image to base64."""    
    with open(image_path, "rb") as img_file:
        b64code = b64encode(img_file.read()).decode('utf-8')
        return b64code


async def main(
        description: str = "",
        init_image_path: str = "",
        layout_path: str = "",
        suggestion_path: str = "",
        gen_image_path: str = "",
):
    # 读取并转换图片
    init_image_base64 = encode_image(init_image_path)
    layout_base64 = encode_image(layout_path)

    logger.info(description)
    logger.info(f"Image loaded from: {init_image_path}")
    logger.info(f"Layout loaded from: {layout_path}")
    logger.info(f"Results will be saved to: {suggestion_path}")
    logger.info(f"Gen image will be saved to: {gen_image_path}")

    context = Context(config_file="config/config2.yaml")
    env = Environment(context=context)

    usability_agent = UsabilityAgent(image_base64=init_image_base64)
    vitality_agent = VitalityAgent(image_base64=init_image_base64)
    safety_agent = SafetyAgent(image_base64=init_image_base64)
    summary_agent = SummaryAgent(save_path=suggestion_path)
    gen_image_agent = GenImageAgent(image_base64=init_image_base64, layout_base64=layout_base64, gen_image_path=gen_image_path)

    env.add_roles([usability_agent, vitality_agent, safety_agent, summary_agent, gen_image_agent])
    logger.info("agents added to environment")

    # content = {"description": description, "image_base64": image_base64}
    content = {"description": description}
    content_json = json.dumps(content)

    env.publish_message(
        Message(
            content=content_json, send_to=(usability_agent, vitality_agent, safety_agent), sent_from=UserRequirement
        )
    )

    logger.info("environment start running...")
    run_count = 0
    while not env.is_idle:
        run_count += 1
        logger.info(f"environment running #{run_count}")
        await env.run()

    logger.info(f"environment finished, run_count: {run_count}")
    
    logger.info("getting env")
    print("================= main env =================", env)
    
    # return final_result

if __name__ == "__main__":
    save_dir = str(DEFAULT_WORKSPACE_ROOT / "urban_design")
    os.makedirs(save_dir, exist_ok=True)

    description = "This is an urban design image. Hire 3 evaluation agents (UsabilityAgent, VitalityAgent, SafetyAgent) to give specific evaluation of the image, and 1 summary agent (SummaryAgent) to give a summary of the evaluation results based on the evaluation results of the 3 agents and find the conflicts and unify their suggestions and give a final suggestion for improvement."

    init_image_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data/1_image_comp.jpg"
    layout_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data/1_layout_comp.jpg"
    suggestion_path = f"{save_dir}/1_image_comp-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    gen_image_path = f"{save_dir}/1_image_comp_gen_image-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    # image_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data/2_l_compressed.jpg"
    # save_path = f"{save_dir}/2_l_compressed_4o_suggestion-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    result = asyncio.run(main(description=description, init_image_path=init_image_path, layout_path=layout_path, suggestion_path=suggestion_path, gen_image_path=gen_image_path))
    print("\n\n=============== Result ===============\n\n", json.dumps(result, ensure_ascii=False))
