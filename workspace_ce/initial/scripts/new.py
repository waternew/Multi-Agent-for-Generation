# -*- coding: utf-8 -*-
'''
Created on Jun 19, 2025

@author: 12407
'''

import os
from scripting import *

def main():
    
    try:
        # 获取当前脚本所在目录（自动识别）
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print("📁 当前脚本目录:", script_dir)
        
        # 切换到该目录（可选）
        os.chdir(script_dir)

        # 获取 CityEngine 实例
        ce = CE()
        
        # 切换为俯视图（可选）
        ce.setViewTop()

        # 导出图像
        output_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/layout_img1.png"
        
        ce.exportImage(
            filename=output_path,
            width=1920,
            height=1080,
            format="png",
            openFolder=True  # 自动打开文件夹
        )

        print("✅ 图像已成功导出")

    except Exception as e:
        print("❌ 发生错误:", str(e))
        
if __name__ == '__main__':
    main()