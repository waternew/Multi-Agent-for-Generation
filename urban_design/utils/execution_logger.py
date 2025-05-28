import json
import os
from datetime import datetime
from loguru import logger
import sys
import logging
from typing import Dict, Any, Optional

class ExecutionLogger:
    """执行日志记录器，用于记录agent的执行过程"""
    
    def __init__(self, result_dir: str = None, max_description_length: int = 200):
        self.result_dir = result_dir
        self.log_dir = os.path.join(result_dir, "logs") if result_dir else "../../workspace/logs/execution"
        self.current_log_file = None
        self.max_description_length = max_description_length
        self._setup_logger()
        
    def _setup_logger(self):
        """设置日志记录器"""
        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 创建当前日志文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log_file = os.path.join(self.log_dir, f"execution_{timestamp}.jsonl")
        
        # 配置loguru
        logger.remove()  # 移除默认处理器
        
        # 添加控制台输出
        logger.add(sys.stdout, 
                  format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                  level="INFO")
        
        # 添加文件输出
        logger.add(self.current_log_file,
                  format="{message}",
                  level="INFO",
                  mode="a")
        
        # 设置agent日志记录器
        self.agent_logger = logging.getLogger("agent")
        self.agent_logger.setLevel(logging.INFO)
        
        # 为agent日志添加文件处理器
        agent_log_file = os.path.join(self.log_dir, f"agent_{timestamp}.log")
        agent_file_handler = logging.FileHandler(agent_log_file, encoding='utf-8')
        agent_file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
        ))
        self.agent_logger.addHandler(agent_file_handler)
        
        # 为agent日志添加控制台处理器
        agent_console_handler = logging.StreamHandler()
        agent_console_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
        ))
        self.agent_logger.addHandler(agent_console_handler)
    
    def _truncate_description(self, description: str) -> str:
        """截断描述文本，保留完整句子"""
        if len(description) <= self.max_description_length:
            return description
            
        # 找到最后一个完整句子的位置
        last_period = description[:self.max_description_length].rfind('.')
        if last_period == -1:
            last_period = self.max_description_length
            
        return description[:last_period + 1] + "..."
    
    def log_action(
        self, 
        agent: str, 
        action: str, 
        description: str, 
        status: str = "success",
        received_message: Optional[Dict[str, Any]] = None,
        sent_message: Optional[Dict[str, Any]] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """记录agent的动作
        
        Args:
            agent: agent名称
            action: 动作名称
            description: 动作描述
            status: 执行状态（success/failed等）
            received_message: 接收到的消息详情
            sent_message: 发送的消息详情
            additional_data: 额外的数据
        """
        # 截断描述文本
        truncated_description = self._truncate_description(description)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "description": truncated_description,
            "status": status,
            "received_message": received_message,
            "sent_message": sent_message,
            "additional_data": additional_data
        }
        
        # 将日志条目写入文件
        with open(self.current_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        # 使用agent_logger记录
        self.agent_logger.info(
            f"Agent: {agent} | Action: {action} | Status: {status} | Description: {truncated_description}"
        )
        
        # 记录详细信息
        if received_message:
            self.agent_logger.debug(f"Received message: {json.dumps(received_message, ensure_ascii=False)}")
        if sent_message:
            self.agent_logger.debug(f"Sent message: {json.dumps(sent_message, ensure_ascii=False)}")
        if additional_data:
            self.agent_logger.debug(f"Additional data: {json.dumps(additional_data, ensure_ascii=False)}")

# 创建全局日志记录器实例
# execution_logger = ExecutionLogger() 