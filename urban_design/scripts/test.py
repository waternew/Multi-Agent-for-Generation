from safetensors import safe_open

tensors = {}
with safe_open(r"E:\HKUST\202505_Agent_Urban_Design\StableDiffusionWebUI\sd-webui-aki-v4.10\sd-webui-aki-v4.10\models\Stable-diffusion\老王SDXL生图模型_XL入门.safetensors", framework='pt') as f:
    for k in f.keys():
        tensors[k] = f.get_tensor(k)
print(tensors)