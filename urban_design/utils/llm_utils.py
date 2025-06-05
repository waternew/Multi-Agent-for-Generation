import json
from typing import Optional, List, Any, Dict, Union
from metagpt.logs import logger
from metagpt.utils.common import CodeParser

class LLMUtils:
    """LLM调用和重试机制的工具类"""

    @staticmethod
    async def ask_with_retry(
        action_instance,
        prompt: str,
        max_retries: int = 3,
        system_msgs: Optional[List[str]] = None,
        extract_json: bool = True,
        images: Optional[list] = None,
    ) -> str:
        """
        带有重试机制的LLM调用，处理非结构化输出问题

        Args:
            action_instance: 具有_aask方法的Action实例
            prompt: 提示文本
            max_retries: 最大重试次数
            system_msgs: 系统消息
            json_only: 是否只返回JSON
            extract_json: 是否从响应中提取JSON
            images: 图片列表

        Returns:
            如果extract_json为True, 返回提取的JSON字符串；否则返回原始响应
        """
        for attempt in range(max_retries):

            try:
                if images:
                    response = await action_instance._aask(prompt, system_msgs, images=images)
                else:
                    response = await action_instance._aask(prompt, system_msgs)
                logger.info(f"LLMUtils ask_with_retry response (attempt {attempt+1}): {response}")
                
                if not extract_json:
                    return response

                # 尝试提取JSON
                try:
                    # 寻找JSON的开始和结束标记
                    json_start = response.find("{")
                    json_end = response.rfind("}") + 1

                    if json_start >= 0 and json_end > json_start:
                        # 提取可能的JSON部分
                        json_content = response[json_start:json_end]
                        # 验证是否为有效的JSON
                        json.loads(json_content)
                        # 如果验证通过，返回提取的JSON部分
                        return json_content
                    else:
                        raise ValueError("No valid JSON found in response")
                except Exception as e:
                    logger.warning(f"Retry {attempt+1}/{max_retries}: Invalid JSON response: {str(e)}")
                    if attempt == max_retries - 1:  # 如果是最后一次尝试
                        logger.warning(f"Final attempt failed. Returning raw response for manual handling.")
                        return response

                    # 否则继续重试
                    logger.info(f"Retrying LLM call with more explicit instructions...")
                    # 在提示中强调需要有效的JSON
                    prompt = f"""IMPORTANT: Your previous response could not be parsed as valid JSON. 
Please respond ONLY with a properly formatted JSON object and nothing else.

{prompt}

Remember to return ONLY a properly formatted JSON object without any additional text, markdown formatting, or code blocks.
"""
            except Exception as e:
                logger.error(f"LLM call error on attempt {attempt+1}/{max_retries}: {str(e)}")
                if attempt == max_retries - 1:
                    raise

        raise Exception(f"Failed to get valid response after {max_retries} attempts")

    @staticmethod
    def parse_json_safely(json_str: str) -> Dict:
        """
        安全解析JSON字符串，处理各种边缘情况

        Args:
            json_str: JSON字符串

        Returns:
            解析后的字典
        """
        if not json_str:
            return {}

        if isinstance(json_str, dict):
            return json_str

        try:
            return CodeParser.parse_json(json_str)
        except Exception as e:
            # 尝试清理并提取JSON
            try:
                # 查找JSON对象的开始和结束
                start_idx = json_str.find("{")
                end_idx = json_str.rfind("}") + 1

                if start_idx >= 0 and end_idx > start_idx:
                    json_portion = json_str[start_idx:end_idx]
                    return json.loads(json_portion)
                else:
                    logger.error(f"Cannot extract valid JSON: {e}")
                    return {"error": str(e), "raw_text": json_str[:100] + "..."}
            except Exception as e2:
                logger.error(f"JSON parsing failed: {e} -> {e2}")
                return {
                    "error": f"{str(e)} -> {str(e2)}",
                    "raw_text": json_str[:100] + "...",
                } 