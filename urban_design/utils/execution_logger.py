import json
import os
from datetime import datetime
from loguru import logger
import sys
import logging
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler

class ExecutionLogger:
    """执行日志记录器，用于记录agent的执行过程"""
    
    def __init__(self, result_dir: str, max_log_size: int = 10 * 1024 * 1024, backup_count: int = 5):
        self.result_dir = result_dir
        self.logs_dir = os.path.join(result_dir, "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # 创建带时间戳的日志文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.logs_dir, f"execution_{timestamp}.jsonl")
        
        # 设置日志记录器
        self.logger = self._setup_logger()
        
        # 记录初始化信息
        self.log_action(
            agent="System",
            action="Initialize",
            description="ExecutionLogger initialized",
            status="success"
        )
        
    def _setup_logger(self):
        """设置日志记录器"""
        try:
            logger = logging.getLogger("ExecutionLogger")
            logger.setLevel(logging.INFO)
            
            # 创建文件处理器
            file_handler = RotatingFileHandler(
                self.log_file,
                maxBytes=self.max_log_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            
            # 设置JSON格式
            class JsonFormatter(logging.Formatter):
                def format(self, record):
                    if isinstance(record.msg, dict):
                        return json.dumps(record.msg, ensure_ascii=False)
                    return json.dumps({"message": str(record.msg)}, ensure_ascii=False)
            
            file_handler.setFormatter(JsonFormatter())
            logger.addHandler(file_handler)
            
            return logger
        except Exception as e:
            print(f"Error setting up logger: {str(e)}")
            return None
            
    def _truncate_description(self, description: str, max_length: int = 1000) -> str:
        """截断过长的描述"""
        if len(description) > max_length:
            return description[:max_length] + "..."
        return description
        
    def log_action(
        self,
        agent: str,
        action: str,
        description: str,
        status: str = "success",
        received_message: dict = None,
        sent_message: dict = None,
        additional_data: dict = None
    ):
        """记录动作"""
        try:
            # 构建日志条目
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "action": action,
                "description": self._truncate_description(description),
                "status": status
            }
            
            if received_message:
                log_entry["received_message"] = received_message
            if sent_message:
                log_entry["sent_message"] = sent_message
            if additional_data:
                log_entry["additional_data"] = additional_data
                
            # 记录日志
            if self.logger:
                self.logger.info(log_entry)
            else:
                # 如果logger未初始化，直接写入文件
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                    
        except Exception as e:
            print(f"Error logging action: {str(e)}")
            # 尝试直接写入文件
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        "timestamp": datetime.now().isoformat(),
                        "agent": "System",
                        "action": "Error",
                        "description": f"Failed to log action: {str(e)}",
                        "status": "error"
                    }, ensure_ascii=False) + '\n')
            except:
                pass

# 创建全局日志记录器实例
# execution_logger = ExecutionLogger() 