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

from api_payload import i2i_controlnet_payload, t2i_controlnet_payload, i2i_payload
from sd_webapi import timestamp, encode_file_to_base64, decode_and_save_base64, call_api, call_img2img_api, call_txt2img_api

import re
from utils.execution_logger import ExecutionLogger
from utils.llm_utils import LLMUtils

# from scripts.read_shp import read_shapefile
from scripts.cityengine_processor import CityEngineProcessor
# from scripts.render_obj_blender import render_multiple_objs, read_mtl_colors


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


def encode_image(image_path: Path | str) -> str:
    """Encodes image to base64."""    
    with open(image_path, "rb") as img_file:
        b64code = b64encode(img_file.read()).decode('utf-8')
        return b64code


def process_image_for_webui(image_path: str, resize: bool = True, max_size: int = 512) -> str:
    """
    处理图片用于WebUI，可以选择是否缩放
    
    Args:
        image_path (str): 图片路径
        resize (bool): 是否缩放图片
        max_size (int): 缩放后的最大尺寸（宽或高的最大值）
    
    Returns:
        str: base64编码的图片
    """
    from PIL import Image
    import io
    
    try:
        # 读取图片
        with Image.open(image_path) as img:
            print(f"📸 原始图片尺寸: {img.size}")
            
            if resize:
                # 计算等比例缩放
                width, height = img.size
                print(f"📐 原始宽高比: {width}:{height} = {width/height:.3f}")
                
                # 等比例缩放：保持宽高比，最长边不超过max_size
                if width > height:
                    # 横向图片，以宽度为基准
                    new_width = max_size
                    new_height = int(height * max_size / width)
                else:
                    # 纵向图片，以高度为基准
                    new_height = max_size
                    new_width = int(width * max_size / height)
                
                print(f"📏 缩放后尺寸: {new_width}x{new_height}")
                print(f"📐 缩放后宽高比: {new_width}:{new_height} = {new_width/new_height:.3f}")
                
                # 缩放图片，使用高质量的重采样方法
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 转换为RGB模式（确保兼容性）
                if img_resized.mode != 'RGB':
                    img_resized = img_resized.convert('RGB')
                
                # 保存到内存
                buffer = io.BytesIO()
                img_resized.save(buffer, format='PNG', optimize=True)
                buffer.seek(0)
                
                # 编码为base64
                b64code = b64encode(buffer.getvalue()).decode('utf-8')
                print(f"✅ 图片处理完成，base64长度: {len(b64code)}")
                
            else:
                # 不缩放，直接编码
                print("📸 不进行缩放，直接编码原图")
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                b64code = b64encode(buffer.getvalue()).decode('utf-8')
                print(f"✅ 图片处理完成，base64长度: {len(b64code)}")
            
            return b64code
            
    except Exception as e:
        print(f"❌ 图片处理失败: {e}")
        # 如果处理失败，回退到原始方法
        print("🔄 回退到原始encode_image方法")
        return encode_image(image_path)


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
        "reason": "brief explanation (no more than 240 characters)",
        "suggestion": "brief improvement suggestion (no more than 240 characters)"
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
        "reason": "brief explanation (no more than 240 characters)",
        "suggestion": "brief improvement suggestion (no more than 240 characters)"
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
        "reason": "brief explanation (no more than 240 characters)",
        "suggestion": "brief improvement suggestion (no more than 240 characters)"
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
    You are a summary expert. You will receive evaluation results, which will be 
    a JSON array containing the evaluations from UsabilityAgent, VitalityAgent, 
    and SafetyAgent:

    {evaluations}

    Your task is to:
    1. Extract the 'suggestion' field from each agent's evaluation
    2. Analyze these suggestions to identify any conflicts or contradictions between them
    3. Provide a unified final suggestion that addresses all concerns

    IMPORTANT: You must return ONLY ONE JSON object in the following format:
    {{
        "agent": "SummaryAgent",
        "conflicts": "Describe any conflicts or contradictions between the three agents' suggestions. If there are no conflicts, state that the suggestions are complementary. (no more than 300 characters)",
        "final_suggestion": "A unified final improvement suggestion that addresses all concerns from the three agents. (no more than 300 characters)"
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

            # 将评估结果格式化为易读的字符串
            evaluations_str = "\n".join([
                f"- {eval['agent']}: {eval['suggestion']}"
                for eval in simplified_evaluations
            ])

            prompt = self.PROMPT_TEMPLATE.format(evaluations=evaluations_str)

            print("\n\n=============== SummaryAction prompt ===============\n\n", prompt)

            rsp = await self._aask(prompt=prompt)

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
        except json.JSONDecodeError as e:
            return json.dumps({
                "agent": "SummaryAgent",
                "summary_error": f"Failed to parse evaluations: {str(e)}"
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
        

        print("\n\n=============== SummaryAction self.evaluations ===============\n\n", self.evaluations)

        print("\n\n=============== SummaryAction json.dumps(self.evaluations, ensure_ascii=False) ===============\n\n", json.dumps(self.evaluations, ensure_ascii=False))
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


def render_with_blender(obj_paths, output_image, blender_path="D:/aaa/blender/blender-3.0.0-windows-x64/blender-3.0.0-windows-x64/blender.exe"):
    """
    通过子进程调用Blender进行渲染
    Args:
        obj_paths (list): OBJ文件路径列表
        output_image (str): 输出图片路径
        blender_path (str): Blender可执行文件路径
    """
    import subprocess
    import tempfile
    import os

    # 路径全部用正斜杠，防止转义问题
    current_dir = os.path.abspath(os.path.dirname(__file__)).replace('\\', '/')
    obj_paths = [p.replace('\\', '/') for p in obj_paths]
    output_image = output_image.replace('\\', '/')

    # 创建临时Python脚本，用于调用Blender
    script_content = f'''
import bpy
import os
import sys

print("=== Blender脚本开始执行 ===")
print("当前工作目录:", os.getcwd())

# 添加当前目录到Python路径
sys.path.append(r"{current_dir}")
print("添加路径到sys.path:", r"{current_dir}")

try:
    from scripts.render_obj_blender import render_multiple_objs
    print("✅ 成功导入render_multiple_objs")
except Exception as e:
    print("❌ 导入render_multiple_objs失败:", e)
    import traceback
    traceback.print_exc()
    raise

obj_paths = {obj_paths}
output_image = r"{output_image}"

print("参数设置:")
print("  - obj_paths:", obj_paths)
print("  - output_image:", output_image)

for obj_path in obj_paths:
    if not os.path.exists(obj_path):
        print("❌ 错误: 输入文件不存在:", obj_path)
        raise Exception("输入文件不存在: " + obj_path)
    else:
        print("✅ 文件存在:", obj_path)

output_dir = os.path.dirname(output_image)
if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print("✅ 创建输出目录:", output_dir)

print("=== 开始渲染 ===")
print("输入文件:")
for i, obj_path in enumerate(obj_paths):
    print(f"  {{i+1}}. {{obj_path}}")
print("输出文件:", output_image)
print("=" * 30)

try:
    render_multiple_objs(obj_paths, output_image)
    print("✅ 渲染完成")
    if os.path.exists(output_image):
        file_size = os.path.getsize(output_image)
        print("✅ 输出文件已生成:", output_image, f"({{file_size}} 字节)")
    else:
        print("❌ 输出文件未生成:", output_image)
except Exception as e:
    print("❌ 渲染过程中出错:", e)
    import traceback
    traceback.print_exc()
    raise

print("=== Blender脚本执行完成 ===")
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(script_content)
        temp_script_path = f.name

    print(f"📝 临时脚本文件: {temp_script_path}")

    try:
        cmd = [
            blender_path,
            "--background",
            "--python", temp_script_path
        ]
        print(f"🚀 执行Blender命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        print(f"📊 Blender执行结果:")
        print(f"   - 返回码: {result.returncode}")
        print(f"   - 标准输出长度: {len(result.stdout)}")
        print(f"   - 错误输出长度: {len(result.stderr)}")
        if result.returncode == 0:
            print("✅ Blender渲染成功")
            if result.stdout:
                print("📄 Blender输出:")
                print(result.stdout)
            if result.stderr:
                print("⚠️ Blender警告/错误:")
                print(result.stderr)
        else:
            print("❌ Blender渲染失败")
            if result.stderr:
                print("📄 Blender错误:")
                print(result.stderr)
            if result.stdout:
                print("📄 Blender输出:")
                print(result.stdout)
            raise Exception("Blender渲染失败")
        if os.path.exists(output_image):
            file_size = os.path.getsize(output_image)
            print(f"✅ 最终检查: 输出文件存在 {output_image} ({file_size} 字节)")
        else:
            print(f"❌ 最终检查: 输出文件不存在 {output_image}")
    finally:
        if os.path.exists(temp_script_path):
            print("🗑️ 清理临时脚本文件")
            os.unlink(temp_script_path)


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
    time.sleep(1)


    # ==== 定量评估分支 ====
    print("\n\n=============== 定量评估分支 ===============\n\n")

    # # 读取shp文件
    # shp_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data_shp/site01_utm_final/site01_utm_final.shp"
    # rpk_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/data/shangye.rpk"
    # obj_output_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images"

    # print("🏙️ CityEngine SDK Python处理器")
    # print("=" * 50)

    # processor = CityEngineProcessor()

    # # 动态参数
    # setback_dis = random.uniform(7,20)
    # street_jiao = random.uniform(30,70)
    # street_jiao_1 = random.uniform(30,70)
    # Far = random.uniform(5,12)
    # BD_set_dis_min = random.uniform(30,70)
    # BD_set_dis_max = random.uniform(BD_set_dis_min,100)
    # BD_kuandu = random.uniform(30,100)
    # BD_kaikou = random.uniform(0.8,1.0)
    # BD_gaocen_kaundu = random.uniform(30,100)
    # BD_gaocen_shengdu = random.uniform(30,100)
    # BD_gaocen_site = random.uniform(10,2000)
    # BD_gaocen_kaundu = random.uniform(30,100)
    # gao_per = random.uniform(0.4,0.7)
    # zhong_per = random.uniform(0,1-gao_per)
    # di_per = 1 - gao_per - zhong_per
    # BD_dicen_chang = random.uniform(80,300)
    # BD_dicen_kuan = random.uniform(80,300)

    # # 使用简化的属性（只保留必要的）todo
    # attributes = {
    #     'height': 30.0,  # 对应CGA中的 attr height = 30
    #     'Mode': 'Visualization',

    #     'setback_dis': setback_dis,
    #     'street_jiao': street_jiao,
    #     'street_jiao_1': street_jiao_1,
    #     'Far': Far,
    #     'BD_set_dis_min': BD_set_dis_min,
    #     'BD_set_dis_max': BD_set_dis_max,
    #     'BD_kuandu': BD_kuandu,
    #     'BD_kaikou': BD_kaikou,
    #     'BD_gaocen_kaundu': BD_gaocen_kaundu,
    #     'BD_gaocen_shengdu': BD_gaocen_shengdu,
    #     'BD_gaocen_site': BD_gaocen_site,
    #     'BD_gaocen_kaundu': BD_gaocen_kaundu,
    #     'gao_per': gao_per,
    #     'zhong_per': zhong_per,
    #     'di_per': di_per,
    #     'BD_dicen_chang': BD_dicen_chang,
    #     'BD_dicen_kuan': BD_dicen_kuan,
    # }

    # ## 生成3D模型
    # processor.process_files(shp_path, rpk_path, obj_output_path, attributes)

    # ## 渲染布局图片
    # gen_obj_path = f"{obj_output_path}/generated_0.obj"
    # obj_paths = [gen_obj_path]

    # layout_output_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/layout_render_0.png"

    # render_with_blender(obj_paths, layout_output_path) 
    
    ## 生成初始图片

    # 读取布局图片并缩放
    # layout_image_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/layout_render_0.png"
    layout_image_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/control_img/topview4.png"
    ip_image_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/control_img/ip2.png"
    
    # 使用新的图片处理函数，缩放图片以避免WebUI内存溢出
    print("🖼️ 处理layout图片用于WebUI...")
    # layout_image_base64 = process_image_for_webui(layout_image_path, resize=True, max_size=512)
    layout_image_base64 = encode_image(layout_image_path)
    ip_image_base64 = encode_image(ip_image_path)

    webui_server_url = 'http://127.0.0.1:7860'

    gen_initial_image_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/"
    os.makedirs(gen_initial_image_path, exist_ok=True)
    
    prompt = "block,block scale,outdoor,urban planning,master plan design,architectural site plan,residential area,mixed-use development,square,abundant space,diverse open spaces,children's playground,greening,public parks,trees,bird's-eye view,abundant landscape,square,children's facilities,paving,water features,high detail,vibrant urban environment,3D visualization,top-down view,"
    negative_prompt = "ng_deepnegative_v1_75t,(badhandv4:1.2),EasyNegative,(worst quality:2),fence,enclosure,wall,interior design"
    random_seed = random.randint(1,1000000)

    # 对于1920x1080的图片，等比例缩放到512x288 (512 * 1080/1920)
    # 但为了更好的效果，我们使用512x512的正方形
    img = cv2.imread(layout_image_path)
    target_width = img.shape[1]//2#1600#480#2404
    target_height = img.shape[0]//2#870#270#1886
    
    print(f"🎨 设置生成图片尺寸: {target_width}x{target_height}")
    
    # 使用更小的图片尺寸，避免VAE内存溢出
    payload_t2i = t2i_controlnet_payload(height=target_height, width=target_width,prompt=prompt, negative_prompt=negative_prompt, seg_img=layout_image_base64, ip_img=ip_image_base64, random_seed=random_seed)
    
    # 添加重试机制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🔄 尝试调用WebUI API (第{attempt + 1}次)")
            response = call_txt2img_api(webui_server_url, **payload_t2i)
            print("✅ WebUI API调用成功")
            break
        except Exception as e:
            print(f"❌ WebUI API调用失败 (第{attempt + 1}次): {e}")
            if attempt < max_retries - 1:
                print("⏳ 等待5秒后重试...")
                time.sleep(5)
            else:
                print("❌ 所有重试都失败了，跳过图片生成")
                raise e

    for index, image in enumerate(response.get('images')):
        save_path = os.path.join(gen_initial_image_path, f'i2i_img-{timestamp()}-{index}.png')
        decode_and_save_base64(image, save_path)

    raise


    # ==== 定性评估分支 ====
    print("\n\n=============== 定性评估分支 ===============\n\n")

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
            max_rounds=3  # 设置最大轮次
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