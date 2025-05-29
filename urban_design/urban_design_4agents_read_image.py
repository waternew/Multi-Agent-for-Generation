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

import re
from utils.execution_logger import ExecutionLogger

# 创建基础目录结构
save_dir = str(DEFAULT_WORKSPACE_ROOT / "urban_design")
os.makedirs(save_dir, exist_ok=True)

# 使用同一个时间戳创建结果目录
timestamp_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
result_dir = os.path.join(save_dir, timestamp_str)
os.makedirs(result_dir, exist_ok=True)

# 创建子目录
logs_dir = os.path.join(result_dir, "logs")
suggestions_dir = os.path.join(result_dir, "suggestions")
gen_image_path = os.path.join(result_dir, "sd_api_out")

os.makedirs(logs_dir, exist_ok=True)
os.makedirs(suggestions_dir, exist_ok=True)
os.makedirs(gen_image_path, exist_ok=True)

# 初始化日志记录器
execution_logger = ExecutionLogger(result_dir=result_dir)

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
        return rsp


class UsabilityAgent(Role):
    name: str = "UsabilityAgent"
    profile: str = "UsabilityAgent"

    def __init__(self, image_base64: str = "", **kwargs):
        super().__init__(**kwargs)
        self.image_base64 = image_base64
        self._watch([UserRequirement, GenImageAction])
        self.set_actions([UsabilityAction])
        self.last_msg = None

        execution_logger.log_action(
            agent=self.name,
            action="Initialize",
            description="UsabilityAgent initialized with UserRequirement and GenImageAction",
            status="success"
        )

    async def _act(self) -> Message:
        execution_logger.log_action(
            agent=self.name,
            action="StartAction",
            description=f"Starting {self.rc.todo.name}",
            status="in_progress"
        )

        todo = self.rc.todo
        msg = self.get_memories(k=1)[0]  # find the most recent messages
        
        if msg.role == "GenImageAgent":
            self.image_base64 = msg.content
            execution_logger.log_action(
                agent=self.name,
                action="UpdateImage",
                description="Updated image_base64 from GenImageAgent message",
                received_message={
                    "role": msg.role,
                    "content_length": len(msg.content),
                    "image_info": "New image received from GenImageAgent"
                },
                status="success"
            )

        execution_logger.log_action(
            agent=self.name,
            action="ProcessMessage",
            description="Processing current message",
            received_message={
                "role": msg.role,
                "content": msg.content[:100] + "...",
                "message_type": "Initial request" if msg.role == "user" else "Generated image"
            },
            status="in_progress"
        )

        code_text = await todo.run(msg.content, self.image_base64)
        
        # 解析评估结果
        try:
            evaluation_result = json.loads(code_text)
            execution_logger.log_action(
                agent=self.name,
                action="GenerateResponse",
                description=f"Generated evaluation response",
                additional_data={
                    "evaluation": {
                        "agent": evaluation_result.get("agent"),
                        "rating_score": evaluation_result.get("rating_score"),
                        "reason": evaluation_result.get("reason"),
                        "suggestion": evaluation_result.get("suggestion")
                    }
                },
                status="success"
            )
        except json.JSONDecodeError:
            execution_logger.log_action(
                agent=self.name,
                action="GenerateResponse",
                description=f"Generated response for {type(todo)}",
                status="success"
            )

        msg = Message(content=code_text, role=self.profile, cause_by=type(todo), send_to="SummaryAgent")
        self.publish_message(msg)
        
        execution_logger.log_action(
            agent=self.name,
            action="SendMessage",
            description="Sending evaluation to SummaryAgent",
            sent_message={
                "role": self.profile,
                "content": code_text,
                "send_to": "SummaryAgent",
                "message_type": "Evaluation result"
            },
            status="success"
        )

        self.last_msg = msg
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
        # print("\n\n=============== VitalityAction rsp ===============\n\n", rsp)
        return rsp


class VitalityAgent(Role):
    name: str = "VitalityAgent"
    profile: str = "VitalityAgent"

    def __init__(self, image_base64: str = "", **kwargs):
        super().__init__(**kwargs)
        self.image_base64 = image_base64
        self._watch([UserRequirement, GenImageAction])
        self.set_actions([VitalityAction])
        self.last_msg = None

        execution_logger.log_action(
            agent=self.name,
            action="Initialize",
            description="VitalityAgent initialized with UserRequirement and GenImageAction",
            status="success"
        )

    async def _act(self) -> Message:
        execution_logger.log_action(
            agent=self.name,
            action="StartAction",
            description=f"Starting {self.rc.todo.name}",
            status="in_progress"
        )

        todo = self.rc.todo
        msg = self.get_memories(k=1)[0]  # find the most recent messages

        if msg.role == "GenImageAgent":
            self.image_base64 = msg.content
            execution_logger.log_action(
                agent=self.name,
                action="UpdateImage",
                description="Updated image_base64 from GenImageAgent message",
                received_message={
                    "role": msg.role,
                    "content_length": len(msg.content),
                    "image_info": "New image received from GenImageAgent"
                },
                status="success"
            )

        execution_logger.log_action(
            agent=self.name,
            action="ProcessMessage",
            description="Processing current message",
            received_message={
                "role": msg.role,
                "content": msg.content[:100] + "...",
                "message_type": "Initial request" if msg.role == "user" else "Generated image"
            },
            status="in_progress"
        )

        code_text = await todo.run(msg.content, self.image_base64)
        
        # 解析评估结果
        try:
            evaluation_result = json.loads(code_text)
            execution_logger.log_action(
                agent=self.name,
                action="GenerateResponse",
                description=f"Generated evaluation response",
                additional_data={
                    "evaluation": {
                        "agent": evaluation_result.get("agent"),
                        "rating_score": evaluation_result.get("rating_score"),
                        "reason": evaluation_result.get("reason"),
                        "suggestion": evaluation_result.get("suggestion")
                    }
                },
                status="success"
            )
        except json.JSONDecodeError:
            execution_logger.log_action(
                agent=self.name,
                action="GenerateResponse",
                description=f"Generated response for {type(todo)}",
                status="success"
            )

        msg = Message(content=code_text, role=self.profile, cause_by=type(todo), send_to="SummaryAgent")
        self.publish_message(msg)
        
        execution_logger.log_action(
            agent=self.name,
            action="SendMessage",
            description="Sending evaluation to SummaryAgent",
            sent_message={
                "role": self.profile,
                "content": code_text,
                "send_to": "SummaryAgent",
                "message_type": "Evaluation result"
            },
            status="success"
        )

        self.last_msg = msg
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
        return rsp


class SafetyAgent(Role):
    name: str = "SafetyAgent"
    profile: str = "SafetyAgent"

    def __init__(self, image_base64: str = "", **kwargs):
        super().__init__(**kwargs)
        self.image_base64 = image_base64
        self._watch([UserRequirement, GenImageAction])
        self.set_actions([SafetyAction])
        self.last_msg = None

        execution_logger.log_action(
            agent=self.name,
            action="Initialize",
            description="SafetyAgent initialized with UserRequirement and GenImageAction",
            status="success"
        )

    async def _act(self) -> Message:
        execution_logger.log_action(
            agent=self.name,
            action="StartAction",
            description=f"Starting {self.rc.todo.name}",
            status="in_progress"
        )

        todo = self.rc.todo
        msg = self.get_memories(k=1)[0]  # find the most recent messages

        # 检查消息来源和内容
        if msg.role == "GenImageAgent":
            self.image_base64 = msg.content
            execution_logger.log_action(
                agent=self.name,
                action="UpdateImage",
                description="Updated image_base64 from GenImageAgent message",
                received_message={
                    "role": msg.role,
                    "content_length": len(msg.content),
                    "image_info": "New image received from GenImageAgent"
                },
                status="success"
            )

        execution_logger.log_action(
            agent=self.name,
            action="ProcessMessage",
            description="Processing current message",
            received_message={
                "role": msg.role,
                "content": msg.content[:100] + "...",
                "message_type": "Initial request" if msg.role == "user" else "Generated image",
                "image_available": bool(self.image_base64) # check
            },
            status="in_progress"
        )

        code_text = await todo.run(msg.content, self.image_base64)
        
        # 解析评估结果
        try:
            evaluation_result = json.loads(code_text)
            execution_logger.log_action(
                agent=self.name,
                action="GenerateResponse",
                description=f"Generated evaluation response",
                additional_data={
                    "evaluation": {
                        "agent": evaluation_result.get("agent"),
                        "rating_score": evaluation_result.get("rating_score"),
                        "reason": evaluation_result.get("reason"),
                        "suggestion": evaluation_result.get("suggestion")
                    }
                },
                status="success"
            )
        except json.JSONDecodeError:
            execution_logger.log_action(
                agent=self.name,
                action="GenerateResponse",
                description=f"Generated response for {type(todo)}",
                status="success"
            )

        msg = Message(content=code_text, role=self.profile, cause_by=type(todo), send_to="SummaryAgent")
        self.publish_message(msg)
        
        execution_logger.log_action(
            agent=self.name,
            action="SendMessage",
            description="Sending evaluation to SummaryAgent",
            sent_message={
                "role": self.profile,
                "content": code_text,
                "send_to": "SummaryAgent",
                "message_type": "Evaluation result"
            },
            status="success"
        )

        self.last_msg = msg
        return msg


class SummaryAction(Action):
    PROMPT_TEMPLATE: str = """
    You are a summary expert. You will receive evaluation results, which will be a JSON array containing the evaluations from UsabilityAgent, VitalityAgent, and SafetyAgent.

    Your task is to:
    1. Extract the 'suggestion' field from each agent's evaluation
    2. Analyze these suggestions to identify any conflicts or contradictions between them
    3. Provide a unified final suggestion that addresses all concerns

    IMPORTANT: You must return ONLY ONE JSON object in the following format:
    {{
        "agent": "SummaryAgent",
        "conflicts": "Describe any conflicts or contradictions between the three agents' suggestions. If there are no conflicts, state that the suggestions are complementary.",
        "final_suggestion": "A unified final improvement suggestion that addresses all concerns from the three agents"
    }}

    DO NOT return an array of evaluations. DO NOT include any other text or markdown formatting.
    Your response must be a single JSON object that follows the exact format above.
    """
    name: str = "SummaryAction"

    async def run(self, content: str = "", save_path: str = ""):
        # 确保输入是有效的JSON
        try:
            evaluations = json.loads(content)

            print("\n\n=============== SummaryAction evaluations ===============\n\n", evaluations)

            # 提取每个 agent 的 suggestion
            simplified_evaluations = []
            for eval in evaluations:
                if isinstance(eval, dict) and "suggestion" in eval:
                    simplified_evaluations.append({
                        "agent": eval.get("agent", "Unknown"),
                        "suggestion": eval.get("suggestion", "")
                    })

            print("\n\n=============== SummaryAction simplified_evaluations ===============\n\n", simplified_evaluations)

            # 验证评估结果
            if not isinstance(simplified_evaluations, list) or len(simplified_evaluations) < 3:
                return json.dumps({
                    "agent": "SummaryAgent",
                    "summary_error": f"Invalid evaluations format. Expected list of 3 evaluations, got {type(simplified_evaluations)}"
                })
        except json.JSONDecodeError as e:
            return json.dumps({
                "agent": "SummaryAgent",
                "summary_error": f"Failed to parse evaluations: {str(e)}"
            })

        prompt = self.PROMPT_TEMPLATE.format(content=simplified_evaluations)

        print("\n\n=============== SummaryAction prompt ===============\n\n", prompt)

        rsp = await self._aask(prompt)

        print("\n\n=============== SummaryAction rsp ===============\n\n", rsp)
        
        # 验证响应格式
        try:
            summary = json.loads(rsp)
            
            # 确保返回的是单个对象而不是数组
            if isinstance(summary, list):
                if len(summary) > 0 and isinstance(summary[0], dict):
                    summary = summary[0]
                else:
                    return json.dumps({
                        "agent": "SummaryAgent",
                        "summary_error": "Invalid response format: received array instead of object"
                    })

            print("\n\n=============== SummaryAction summary ===============\n\n", summary)

            # 验证返回的对象格式是否正确
            if not isinstance(summary, dict) or "agent" not in summary or "conflicts" not in summary or "final_suggestion" not in summary:
                return json.dumps({
                    "agent": "SummaryAgent",
                    "summary_error": "Invalid summary format: missing required fields"
                })

            return json.dumps(summary)
        except json.JSONDecodeError:
            return json.dumps({
                "agent": "SummaryAgent",
                "summary_error": "Failed to generate valid JSON summary"
            })


class SummaryAgent(Role):
    name: str = "SummaryAgent"
    profile: str = "SummaryAgent"

    def __init__(self, suggestions_dir: str = "", **kwargs):
        super().__init__(**kwargs)
        self.suggestions_dir = suggestions_dir
        self.current_round = 1
        self._watch([UsabilityAction, VitalityAction, SafetyAction])
        self.set_actions([SummaryAction])
        self.last_msg = None
        self.evaluations = []  # 存储所有评估结果

        execution_logger.log_action(
            agent=self.name,
            action="Initialize",
            description="SummaryAgent initialized with UsabilityAction, VitalityAction, and SafetyAction",
            status="success"
        )

    async def _act(self) -> Message:
        execution_logger.log_action(
            agent=self.name,
            action="StartAction",
            description=f"Starting {self.rc.todo.name} for round {self.current_round}",
            status="in_progress"
        )

        todo = self.rc.todo
        memories = self.get_memories(k=3)  # 获取最近3条消息，确保获取所有评估结果

        # 收集所有评估结果
        for msg in memories:
            if msg.role in ["UsabilityAgent", "VitalityAgent", "SafetyAgent"]:
                try:
                    evaluation = json.loads(msg.content)
                    self.evaluations.append(evaluation)
                    execution_logger.log_action(
                        agent=self.name,
                        action="CollectEvaluation",
                        description=f"Collected evaluation from {msg.role}",
                        received_message={
                            "role": msg.role,
                            "content": evaluation,
                            "message_type": "Evaluation result"
                        },
                        status="success"
                    )
                except json.JSONDecodeError as e:
                    execution_logger.log_action(
                        agent=self.name,
                        action="CollectEvaluation",
                        description=f"Failed to parse evaluation from {msg.role}",
                        received_message={
                            "role": msg.role,
                            "content": msg.content[:100] + "...",
                            "error": str(e)
                        },
                        status="error"
                    )

        # 检查是否收集到所有评估结果
        if len(self.evaluations) < 3:
            error_msg = f"Missing evaluations. Expected 3, got {len(self.evaluations)}"
            execution_logger.log_action(
                agent=self.name,
                action="CheckEvaluations",
                description=error_msg,
                status="error"
            )
            return Message(
                content=json.dumps({
                    "agent": "SummaryAgent",
                    "summary_error": error_msg
                }),
                role=self.profile,
                cause_by=type(todo)
            )

        # 为当前轮次创建建议文件路径
        current_suggestion_path = os.path.join(self.suggestions_dir, f"round_{self.current_round}.txt")
        

        # print("\n\n=============== SummaryAction self.evaluations ===============\n\n", self.evaluations)

        # print("\n\n=============== SummaryAction json.dumps(self.evaluations, ensure_ascii=False) ===============\n\n", json.dumps(self.evaluations, ensure_ascii=False))
        # raise

        # 生成总结
        code_text = await todo.run(
            content=json.dumps(self.evaluations, ensure_ascii=False),
            # evaluation_str=json.dumps(self.evaluations, ensure_ascii=False),
            save_path=current_suggestion_path
        )

        # raise

        print("\n\n=============== SummaryAction code_text ===============\n\n", code_text)


        # 解析生成的总结
        try:
            summary_result = json.loads(code_text)
            print("\n\n=============== SummaryAction summary_result ===============\n\n", summary_result)
            # raise
            # 检查 summary_result 的类型
            if isinstance(summary_result, list):
                # 如果是列表，取第一个元素
                summary_result = summary_result[0] if summary_result else {}
            
            # 确保 summary_result 是字典类型
            if not isinstance(summary_result, dict):
                raise ValueError(f"Unexpected summary result type: {type(summary_result)}")
                
            execution_logger.log_action(
                agent=self.name,
                action="GenerateSummary",
                description="Generated summary of all evaluations",
                additional_data={
                    "summary": {
                        "agent": summary_result.get("agent", "SummaryAgent"),
                        "conflicts": summary_result.get("conflicts", ""),
                        "final_suggestion": summary_result.get("final_suggestion", "")
                    }
                },
                status="success"
            )
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            error_msg = f"Failed to process summary result: {str(e)}"
            execution_logger.log_action(
                agent=self.name,
                action="GenerateSummary",
                description=error_msg,
                additional_data={"raw_response": code_text},
                status="error"
            )
            summary_result = {
                "agent": "SummaryAgent",
                "summary_error": error_msg
            }
            code_text = json.dumps(summary_result)

        summary_msg = Message(content=code_text, role=self.profile, cause_by=type(todo), send_to="GenImageAgent")
        self.publish_message(summary_msg)
        
        execution_logger.log_action(
            agent=self.name,
            action="SendMessage",
            description="Sending summary to GenImageAgent",
            sent_message={
                "role": self.profile,
                "content": code_text,
                "send_to": "GenImageAgent",
                "message_type": "Summary with final suggestion"
            },
            status="success"
        )

        # 保存结果
        with open(current_suggestion_path, "w", encoding='utf-8') as f:
            f.write(summary_msg.content)
            
        execution_logger.log_action(
            agent=self.name,
            action="SaveResult",
            description="Saved summary result to file",
            additional_data={"save_path": current_suggestion_path},
            status="success"
        )

        self.current_round += 1
        self.last_msg = summary_msg
        return summary_msg


class GenImageAction(Action):
    PROMPT_TEMPLATE: str = """
    You are an urban design expert. You will receive a image in base64 format, a suggestion from SummaryAgent, and a layout image in base64 format.
    Please use call_img2img_api function to generate a new image based on them.
    """
    name: str = "GenImageAction"

    async def run(self, content: str, image_base64: str, layout_base64: str, gen_image_path: str):
        
        webui_server_url = 'http://127.0.0.1:7860'
        os.makedirs(gen_image_path, exist_ok=True)

        random_seed = random.randint(1,1000000)

        prompt_i2i = content
        negative_prompt_i2i = ""
        # print("\n\n=============== GenImageAction prompt_i2i ===============\n\n", prompt_i2i)
        # raise

        # 第一次的图片、后面的图片？

        payload_i2i = i2i_controlnet_payload(prompt_i2i, negative_prompt_i2i, image_base64, layout_base64, random_seed, max_size=256)    
        # print("\n\n=============== GenImageAction payload_i2i ===============\n\n", payload_i2i)

        response = call_img2img_api(webui_server_url, **payload_i2i)

        for index, image in enumerate(response.get('images')):
            save_path = os.path.join(gen_image_path, f'img2img-{timestamp()}-{index}.png')
            decode_and_save_base64(image, save_path)

        # print("\n\n=============== GenImageAction response ===============\n\n", response)
        return response
    
    
class GenImageAgent(Role):
    name: str = "GenImageAgent"
    profile: str = "GenImageAgent"

    def __init__(self, image_base64: str = "", layout_base64: str = "", gen_image_path: str = "", max_rounds: int = 3, **kwargs):
        super().__init__(**kwargs)
        self.image_base64 = image_base64
        self.layout_base64 = layout_base64
        self.gen_image_path = gen_image_path
        self.max_rounds = max_rounds
        self.current_round = 1  
        self._watch([SummaryAction])
        self.set_actions([GenImageAction])
        self.last_msg = None
        self.last_image_base64 = ""  
        self.last_image_path = ""    

        execution_logger.log_action(
            agent=self.name,
            action="Initialize",
            description=f"GenImageAgent initialized with max_rounds={max_rounds}",
            status="success"
        )

    async def _act(self) -> Message:
        execution_logger.log_action(
            agent=self.name,
            action="StartAction",
            description=f"Starting round {self.current_round}/{self.max_rounds}",
            status="in_progress"
        )

        todo = self.rc.todo
        msg = self.get_memories(k=1)[0]

        execution_logger.log_action(
            agent=self.name,
            action="ProcessMessage",
            description="Processing message from SummaryAgent",
            received_message={
                "role": msg.role,
                "content": msg.content,
                "message_type": "Summary with final suggestion"
            },
            status="in_progress"
        )

        final_suggestion = extract_final_suggestion(msg.content)
        execution_logger.log_action(
            agent=self.name,
            action="ExtractSuggestion",
            description="Extracted final suggestion",
            additional_data={"final_suggestion": final_suggestion},
            status="success"
        )

        gen_image = await todo.run(content=final_suggestion, image_base64=self.image_base64, layout_base64=self.layout_base64, gen_image_path=self.gen_image_path)

        # 记录生成的图片信息
        if isinstance(gen_image, dict) and 'images' in gen_image:
            new_image_base64 = gen_image['images'][0]
            image_info = {
                "image_count": len(gen_image['images']),
                "image_length": len(new_image_base64),
                "save_path": self.gen_image_path
            }
        else:
            new_image_base64 = gen_image
            image_info = {
                "image_length": len(new_image_base64),
                "save_path": self.gen_image_path
            }

        execution_logger.log_action(
            agent=self.name,
            action="GenerateImage",
            description="Generated new image",
            additional_data={"image_info": image_info},
            status="success"
        )

        gen_msg = Message(content=new_image_base64, role=self.profile, cause_by=type(todo), send_to=(UsabilityAgent, VitalityAgent, SafetyAgent))
        self.publish_message(gen_msg)

        execution_logger.log_action(
            agent=self.name,
            action="SendMessage",
            description="Sending generated image to evaluation agents",
            sent_message={
                "role": self.profile,
                "content_length": len(new_image_base64),
                "send_to": ["UsabilityAgent", "VitalityAgent", "SafetyAgent"],
                "message_type": "Generated image",
                "image_info": image_info
            },
            status="success"
        )

        self.current_round += 1
        if self.current_round > self.max_rounds:
            execution_logger.log_action(
                agent=self.name,
                action="Terminate",
                description="Maximum rounds reached, sending termination message",
                status="success"
            )
            gen_msg = Message(content="TERMINATE", role=self.profile, cause_by=type(todo), send_to=())
            self.publish_message(gen_msg)
            return gen_msg
        
        self.last_msg = gen_msg
        self.last_image_base64 = new_image_base64
        self.last_image_path = self.gen_image_path
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
        suggestions_dir: str = "",
        gen_image_path: str = "",
        max_rounds: int = 2,
):
    # 读取并转换图片
    init_image_base64 = encode_image(init_image_path)
    layout_base64 = encode_image(layout_path)

    logger.info(f"Description: {description}")
    logger.info(f"Image loaded from: {init_image_path}")
    logger.info(f"Layout loaded from: {layout_path}")
    logger.info(f"Results will be saved to: {suggestions_dir}")
    logger.info(f"Gen image will be saved to: {gen_image_path}")
    logger.info(f"Maximum rounds: {max_rounds}")

    # 记录初始状态
    execution_logger.log_action(
        agent="System",
        action="Initialize",
        description="Starting urban design evaluation process",
        additional_data={
            "description": description,
            "init_image_path": init_image_path,
            "layout_path": layout_path,
            "max_rounds": max_rounds
        },
        status="success"
    )

    context = Context(config_file="config/config2.yaml")
    env = Environment(context=context)

    usability_agent = UsabilityAgent(image_base64=init_image_base64)
    vitality_agent = VitalityAgent(image_base64=init_image_base64)
    safety_agent = SafetyAgent(image_base64=init_image_base64)
    summary_agent = SummaryAgent(suggestions_dir=suggestions_dir)
    gen_image_agent = GenImageAgent(
        image_base64=init_image_base64,
        layout_base64=layout_base64,
        gen_image_path=gen_image_path,
        max_rounds=max_rounds,
    )

    env.add_roles([usability_agent, vitality_agent, safety_agent, summary_agent, gen_image_agent])
    logger.info("All agents added to environment")

    content = {"description": description}
    content_json = json.dumps(content)

    env.publish_message(
        Message(
            content=content_json, send_to=(usability_agent, vitality_agent, safety_agent), sent_from=UserRequirement
        )
    )

    logger.info("Environment starting to run...")
    run_count = 0
    history = []
    while not env.is_idle:
        run_count += 1
        logger.info(f"Environment running iteration #{run_count}")
        await env.run()

        if gen_image_agent.current_round > max_rounds:
            logger.info("Maximum rounds reached, stopping environment")
            break

    logger.info(f"Environment finished, total iterations: {run_count}")
    
    logger.info("Getting environment state")
    logger.debug(f"Environment state: {env}")
    
    # 循环外保存
    with open("E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace/urban_design/process_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
        logger.info("Process history saved to file")

    return history

def extract_final_suggestion(summary_json_str):
    """
    从 SummaryAgent 的消息中提取 final_suggestion 字段
    输入格式示例：
    {
        "role": "SummaryAgent",
        "content": "{\"agent\": \"SummaryAgent\", \"conflicts\": \"...\", \"final_suggestion\": \"...\"}",
        "message_type": "Summary with final suggestion"
    }
    """
    try:
        # 解析 JSON 字符串
        content_json = json.loads(summary_json_str)

        print("\n\n=============== content_json ===============\n\n", content_json)
        
        # 提取 final_suggestion
        if "final_suggestion" in content_json:
            return content_json["final_suggestion"]
        else:
            print("未找到 final_suggestion 字段")
            return ""
            
    except json.JSONDecodeError as e:
        print(f"解析 JSON 失败: {e}")
        return ""
    except Exception as e:
        print(f"提取 final_suggestion 时发生错误: {e}")
        return ""


if __name__ == "__main__":
    save_dir = str(DEFAULT_WORKSPACE_ROOT / "urban_design")
    os.makedirs(save_dir, exist_ok=True)

    # 使用同一个时间戳创建结果目录
    timestamp_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    result_dir = os.path.join(save_dir, timestamp_str)
    os.makedirs(result_dir, exist_ok=True)

    # 创建子目录
    logs_dir = os.path.join(result_dir, "logs")
    suggestions_dir = os.path.join(result_dir, "suggestions")
    gen_image_path = os.path.join(result_dir, "sd_api_out")
    
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(suggestions_dir, exist_ok=True)
    os.makedirs(gen_image_path, exist_ok=True)

    # 初始化日志记录器
    execution_logger = ExecutionLogger(result_dir=result_dir)

    # 启动可视化服务器
    import subprocess
    import sys
    import time
    
    # 启动可视化服务器
    server_process = subprocess.Popen(
        [sys.executable, os.path.join(os.path.dirname(__file__), "utils/visualization_server.py")],
        env={**os.environ, "LOG_DIR": logs_dir}
    )
    
    # 等待服务器启动
    time.sleep(2)

    description = "This is an urban design image. Hire 3 evaluation agents (UsabilityAgent, VitalityAgent, SafetyAgent) to give specific evaluation of the image, and 1 summary agent (SummaryAgent) to give a summary of the evaluation results based on the evaluation results of the 3 agents and find the conflicts and unify their suggestions and give a final suggestion for improvement."

    init_image_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data/1_image_comp.jpg"
    layout_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data/1_layout_comp.jpg"

    try:
        result = asyncio.run(main(
            description=description, 
            init_image_path=init_image_path, 
            layout_path=layout_path, 
            suggestions_dir=suggestions_dir, 
            gen_image_path=gen_image_path,
            max_rounds=2  # 设置最大轮次
        ))
        print("\n\n=============== Result ===============\n\n", json.dumps(result, ensure_ascii=False))
        
        # 程序运行完成后，等待用户输入
        print("\n程序运行完成！可视化服务器仍在运行。")
        print("您可以在浏览器中查看日志：http://localhost:8002/urban_design/utils/visualization.html")
        print("按 Ctrl+C 可以关闭服务器和程序。")
        
        # 保持服务器运行，直到用户按 Ctrl+C
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在关闭服务器...")
    finally:
        # 关闭可视化服务器
        server_process.terminate()
        server_process.wait()
        print("服务器已关闭。")