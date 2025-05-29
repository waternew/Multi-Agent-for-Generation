import os
import json
import asyncio
import websockets
from pathlib import Path
from datetime import datetime
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class LogFileHandler(FileSystemEventHandler):
    def __init__(self, server):
        self.server = server
        self.last_position = {}
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            asyncio.run_coroutine_threadsafe(
                self.server.send_file_updates(event.src_path),
                self.server.loop
            )

class VisualizationServer:
    def __init__(self, log_dir: str = None, port: int = 8081):
        # 如果没有指定日志目录，则使用默认目录
        if log_dir is None:
            # 获取当前时间戳
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            # 构建默认日志目录路径
            workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../workspace"))
            result_dir = os.path.join(workspace_root, "urban_design", timestamp_str)
            self.log_dir = os.path.join(result_dir, "logs")
        else:
            self.log_dir = log_dir
            
        self.port = port
        self.clients = set()
        self.loop = None
        self.file_handler = LogFileHandler(self)
        self.observer = Observer()
        
        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)
        print(f"\n[Server] Monitoring log directory: {self.log_dir}")
        print(f"[Server] Log directory exists: {os.path.exists(self.log_dir)}")
        print(f"[Server] Log directory contents: {os.listdir(self.log_dir) if os.path.exists(self.log_dir) else 'Directory not found'}\n")
        
    async def register(self, websocket):
        self.clients.add(websocket)
        try:
            # 发送初始数据
            await self.send_initial_data(websocket)
            # 保持连接
            await websocket.wait_closed()
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
        except Exception as e:
            print(f"Error in client connection: {str(e)}")
        finally:
            self.clients.remove(websocket)
            
    async def send_initial_data(self, websocket):
        """发送初始日志数据"""
        try:
            # 获取最新的日志文件
            log_files = list(Path(self.log_dir).glob("execution_*.jsonl"))
            print(f"\n[Server] Looking for log files in: {self.log_dir}")
            print(f"[Server] Found log files: {log_files}")
            
            if not log_files:
                print("[Server] No log files found!")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "No log files found",
                    "timestamp": datetime.now().isoformat()
                }))
                return
                
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            print(f"[Server] Using latest log file: {latest_log}")
            print(f"[Server] File exists: {os.path.exists(latest_log)}")
            print(f"[Server] File size: {os.path.getsize(latest_log)} bytes")
            
            # 记录文件位置
            self.file_handler.last_position[latest_log] = 0
            
            # 读取并发送日志内容
            with open(latest_log, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"[Server] File content length: {len(content)}")
                print(f"[Server] First 100 characters: {content[:100]}")
                
                for line in content.splitlines():
                    if line.strip():
                        try:
                            log_entry = json.loads(line.strip())
                            await websocket.send(json.dumps({
                                "type": "log_entry",
                                "data": log_entry,
                                "timestamp": datetime.now().isoformat()
                            }))
                        except json.JSONDecodeError as e:
                            print(f"[Server] Error decoding log entry: {line.strip()}")
                            print(f"[Server] Error details: {str(e)}")
                            
        except Exception as e:
            print(f"[Server] Error in send_initial_data: {str(e)}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }))
            
    async def send_file_updates(self, file_path):
        """发送文件更新"""
        try:
            current_position = self.file_handler.last_position.get(file_path, 0)
            print(f"\n[Server] Processing file updates for: {file_path}")
            print(f"[Server] Current position: {current_position}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                f.seek(current_position)
                new_lines = f.readlines()
                self.file_handler.last_position[file_path] = f.tell()
                
                print(f"[Server] Read {len(new_lines)} new lines")
                
                for line in new_lines:
                    if line.strip():
                        try:
                            log_entry = json.loads(line.strip())
                            await self.broadcast(json.dumps({
                                "type": "log_entry",
                                "data": log_entry,
                                "timestamp": datetime.now().isoformat()
                            }))
                        except json.JSONDecodeError as e:
                            print(f"[Server] Error decoding log entry: {line.strip()}")
                            print(f"[Server] Error details: {str(e)}")
                            
        except Exception as e:
            print(f"[Server] Error in send_file_updates: {str(e)}")
            
    async def broadcast(self, message):
        """广播消息给所有连接的客户端"""
        if self.clients:
            print(f"\n[Server] Broadcasting to {len(self.clients)} clients")
            disconnected_clients = set()
            for client in self.clients:
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    print("[Server] Client disconnected")
                    disconnected_clients.add(client)
                except Exception as e:
                    print(f"[Server] Error broadcasting to client: {str(e)}")
                    disconnected_clients.add(client)
                    
            # 移除断开的客户端
            self.clients -= disconnected_clients
            if disconnected_clients:
                print(f"[Server] Removed {len(disconnected_clients)} disconnected clients")
            
    async def start(self):
        """启动WebSocket服务器"""
        self.loop = asyncio.get_running_loop()
        
        # 启动文件监控
        self.observer.schedule(self.file_handler, self.log_dir, recursive=False)
        self.observer.start()
        print(f"\n[Server] Started file monitoring in: {self.log_dir}")
        
        try:
            async with websockets.serve(self.register, "localhost", self.port):
                print(f"[Server] Visualization server started on ws://localhost:{self.port}")
                print(f"[Server] Monitoring log directory: {self.log_dir}")
                await asyncio.Future()  # 保持服务器运行
        except Exception as e:
            print(f"[Server] Error starting server: {str(e)}")
        finally:
            self.observer.stop()
            self.observer.join()
            
    def run(self):
        """运行服务器"""
        try:
            print("\n[Server] Starting visualization server...")
            asyncio.run(self.start())
        except KeyboardInterrupt:
            print("\n[Server] Shutting down server...")
        except Exception as e:
            print(f"[Server] Error running server: {str(e)}")

if __name__ == "__main__":
    # 从环境变量中获取日志目录
    log_dir = os.environ.get("LOG_DIR")
    if log_dir is None:
        # 如果没有设置环境变量，使用默认目录
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../workspace"))
        result_dir = os.path.join(workspace_root, "urban_design", timestamp_str)
        log_dir = os.path.join(result_dir, "logs")
    
    print(f"\n[Server] Using log directory: {log_dir}")
    print(f"[Server] Log directory exists: {os.path.exists(log_dir)}")
    print(f"[Server] Log directory contents: {os.listdir(log_dir) if os.path.exists(log_dir) else 'Directory not found'}\n")
    
    # 创建服务器实例
    server = VisualizationServer(log_dir, port=8081)
    server.run() 