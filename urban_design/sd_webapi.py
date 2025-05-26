from datetime import datetime
import urllib.request
import base64
import json
import time
import os
import json
import requests
import random

from API_payload import t2i_controlnet_payload, inpainting_payload, i2i_controlnet_payload
# from API_payload import inpainting_payload

webui_server_url = 'http://127.0.0.1:7860'

out_dir = 'api_out'
out_dir_t2i = os.path.join(out_dir, 'txt2img')
out_dir_i2i = os.path.join(out_dir, 'img2img')
os.makedirs(out_dir_t2i, exist_ok=True)
os.makedirs(out_dir_i2i, exist_ok=True)


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
def call_api(api_endpoint, **payload): 
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


def call_txt2img_api(**payload):
    response = call_api('sdapi/v1/txt2img', **payload)
    for index, image in enumerate(response.get('images')):
        save_path = os.path.join(out_dir_t2i, f'txt2img-{timestamp()}-{index}.png')
        decode_and_save_base64(image, save_path)


def call_img2img_api(**payload):
    response = call_api('sdapi/v1/img2img', **payload)

    print('\n================= response =================\n', response)
    # print('\n================= response.get(images) =================\n', response.get('images'))
    # raise

    for index, image in enumerate(response.get('images')):
        save_path = os.path.join(out_dir_i2i, f'img2img-{timestamp()}-{index}.png')
        decode_and_save_base64(image, save_path)



if __name__ == '__main__':

    random_seed = random.randint(1,1000000)

# 图片相关信息
    height = 567
    width = 1112

    
# Text2Image

    # 点击后生成的人视角建筑线框图，传到这path
    # controlnet_line_img_path = r"controlnet_img\line\img_1.png"
    # controlnet_seg_img_path = r"controlnet_img\seg\img_1.png"
    init_img = r"..\data\1_image_compressed.jpg"
    controlnet_seg_img_path = r"..\data\1_l_compressed.jpg"

    init_img = encode_file_to_base64(init_img)
    controlnet_seg_img = encode_file_to_base64(controlnet_seg_img_path)

    # t2i的prompt直接固定
    prompt_i2i = "Enhance shaded areas, add more public restrooms, introduce nighttime events, and improve surveillance in secluded areas to cover blind spots"
    negative_prompt_i2i = ""

    payload_i2i = i2i_controlnet_payload(prompt_i2i, negative_prompt_i2i, init_img, controlnet_seg_img, random_seed)

    call_img2img_api(**payload_i2i)

    
# # Inpainting
    
#     # 要修改的图，改成生成的那一张
#     init_img_path = r"api_out\txt2img\txt2img-20240816_172018-0.png"
#     # 改成前端传来的mask
#     mask_img_path = r"inpainting_mask\img_1.png"
#     mask_img = encode_file_to_base64(mask_img_path) # 要传一个除了画的mask，其他都是透明的图
#     init_img = encode_file_to_base64(init_img_path) # i2i的payload init image要输入一个列表

#     # inpainting的prompt, 要改成前端传来的selection 对应这里的一个列表某一项
#     prompt_inpainting = "Splash pad,Interactive Water Feature,water garden," 
#     negative_prompt_inpainting = "Swimming pool Facilities,"

#     functions = [
#     {"name": "Splash pad",          # 喷泉水景
#      "prompt": "Splash pad,Interactive Water Feature,water garden,", 
#      "negative_prompt": "Swimming pool Facilities,"},

#     {"name": "Ecological Ponds",    # 生态池塘
#      "prompt": "low quality,sketches,normal quality,blurry,bad anatomy,people,box"},

#     # {"name": "Pet Parks",           # 宠物公园
#     #  "prompt": "Splash pad,Interactive Water Feature,water garden,", 
#     #  "negative_prompt": "Swimming pool Facilities,"},

#     {"name": "Raised Beds",         # 高架花坛
#      "prompt": "Raised Beds,Community Garden:0.3", 
#      "negative_prompt": "low quality,people,"},

#     {"name": "Composting Areas",    # 堆肥区
#      "prompt": "Composting Area,community garden:0.3,", 
#      "negative_prompt": "low quality,people,"},

#     {"name": "Vegetable Patch",     # 蔬菜地
#      "prompt": "Vegetable Patch,community,", 
#      "negative_prompt": "low quality,people,sketches,normal quality,blurry,bad anatomy,"},

#     {"name": "Swing set",           # 秋千
#      "prompt": "swing set,", 
#      "negative_prompt": "woman,"},

#     {"name": "Slide",               # 滑梯
#      "prompt": "child slide,", 
#      "negative_prompt": "woman,"},

#     {"name": "Sandpit",             # 沙坑
#      "prompt": "Sandpit", 
#      "negative_prompt": "woman,"},

#     {"name": "Playhouse",           # 游戏屋
#      "prompt": "Playhouse,", 
#      "negative_prompt": "woman,"},

#     {"name": "Skatepark",           # 滑板场
#      "prompt": "colorful Skatepark,children,community,tree,colorful,", 
#      "negative_prompt": "low quality,sketches,normal quality,blurry,bad anatomy,box,"},

#     {"name": "Outdoor Classrooms",  # 户外教室
#      "prompt": "bench,learning space,garden,Surrounded by greenery,", 
#      "negative_prompt": "low quality,sketches,normal quality,blurry,bad anatomy,people,box"},

#     {"name": "Eco-Classroom",       # 生态教室
#      "prompt": "Schoolyard Habitat,Eco-Classroom,Learning Garden,tree,vegetable Patch,Bench Seats,tree bench,", 
#      "negative_prompt": "low quality,sketches,normal quality,blurry,bad anatomy,people,box"},

#     {"name": "Children Reading zone",   # 儿童阅读区
#      "prompt": "children Reading Nooks,colorful,Bean Bag Sofa,flower,", 
#      "negative_prompt": "low quality,sketches,normal quality,blurry,bad anatomy,people,box"},

#     {"name": "Reading Area",            # 老年阅读区
#      "prompt": "Reading Area,Comfortable outdoor Seating,garden,grass,Surrounded by greenery,", 
#      "negative_prompt": "low quality,sketches,normal quality,blurry,bad anatomy,"},
#     ]

#     selected_name = "Vegetable Patch"  # 这个值是从前端传过来的

#     # 初始化为空或默认值
#     prompt_inpainting = ""
#     negative_prompt_inpainting = ""

    # # 查找并设置 `prompt_inpainting`
    # for option in functions:
    #     if option["name"] == selected_name:
    #         prompt_inpainting = option["prompt"]
    #         negative_prompt_inpainting = option["negative_prompt"]
    #         break

    # payload_inpainting = inpainting_payload(height, width, prompt_inpainting, negative_prompt_inpainting, init_img, mask_img, random_seed)

    # payload_inpainting = t2i_controlnet_payload(height, width, prompt_inpainting, negative_prompt_inpainting, mask_img, random_seed)

    # call_img2img_api(**payload_inpainting)


