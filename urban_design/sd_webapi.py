from datetime import datetime
import urllib.request
import base64
import json
import time
import os
import json
import requests
import random

from api_payload import i2i_controlnet_payload

def timestamp():
    return datetime.fromtimestamp(time.time()).strftime("%Y%m%d_%H%M%S")

# 把文件转成Base64字符串，方便通过api传图
def encode_file_to_base64(path):
    with open(path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')

# 把api传回的文件转为二进制 并保存
def decode_and_save_base64(base64_str, save_path):
    with open(save_path, "wb") as file:
        file.write(base64.b64decode(base64_str))

# api_endpoint API端点，**payload 任意数量的关键字参数，作为请求的数据负载。
def call_api(webui_server_url, api_endpoint, **payload): 
    data = json.dumps(payload).encode('utf-8')
    # 创建请求对象 用来发送HTTP请求
    request = urllib.request.Request(
        f'{webui_server_url}/{api_endpoint}',
        headers={'Content-Type': 'application/json'},
        data=data,
    )
    # 发送请求并获取响应
    response = urllib.request.urlopen(request)
    return json.loads(response.read().decode('utf-8'))

def call_img2img_api(webui_server_url, **payload):
    response = call_api(webui_server_url, 'sdapi/v1/img2img', **payload)

    # print('\n================= response =================\n', response)
    # print('\n================= response.get(images) =================\n', response.get('images'))
    # raise

    return response


if __name__ == '__main__':

    webui_server_url = 'http://127.0.0.1:7860'

    out_i2i_dir = r"..\workspace\sd_api_out"
    os.makedirs(out_i2i_dir, exist_ok=True)

    random_seed = random.randint(1,1000000)

    # 图片相关信息
    init_img = r"..\data\1_image_comp.jpg"
    controlnet_seg_img_path = r"..\data\1_layout_comp.jpg"

    init_img = encode_file_to_base64(init_img)
    controlnet_seg_img = encode_file_to_base64(controlnet_seg_img_path)

    prompt_i2i = "Enhance shaded areas, add more public restrooms, introduce nighttime events, and improve surveillance in secluded areas to cover blind spots"
    negative_prompt_i2i = ""

    payload_i2i = i2i_controlnet_payload(prompt_i2i, negative_prompt_i2i, init_img, controlnet_seg_img, random_seed)

    response = call_img2img_api(**payload_i2i)
    for index, image in enumerate(response.get('images')):
        save_path = os.path.join(out_i2i_dir, f'img2img-{timestamp()}-{index}.png')
        decode_and_save_base64(image, save_path)


