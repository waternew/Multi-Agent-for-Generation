def t2i_controlnet_payload(height, width, prompt, negative_prompt, seg_img, random_seed, max_size=256):
    if height > max_size or width > max_size:
        if height > width:
            width = int(width * (max_size / height))
            height = max_size
        else:
            height = int(height * (max_size / width))
            width = max_size

    payload = {
        "alwayson_scripts": {
            "ControlNet": {
                "args": [
                    # { 
                    #     # 线图
                    #     "advanced_weighting": None,
                    #     "batch_images": "",
                    #     "control_mode": "ControlNet is more important",
                    #     "enabled": True,
                    #     "guidance_end": 0.68,
                    #     "guidance_start": 0,
                    #     "hr_option": "Both",
                    #     "image": {
                    #         "image": line_img,
                    #         # "mask": "base64image placeholder"
                    #     },
                    #     "inpaint_crop_input_image": True,
                    #     "input_mode": "simple",
                    #     "ipadapter_input": None,
                    #     "is_ui": True,
                    #     "loopback": False,
                    #     "low_vram": False,
                    #     "model": "control_v11p_sd15_lineart_fp16 [5c23b17d]",
                    #     "module": "lineart_standard (from white bg & black line)",
                    #     "output_dir": "",
                    #     "pixel_perfect": False,
                    #     "processor_res": 512,
                    #     "resize_mode": "Crop and Resize",
                    #     "save_detected_map": True,
                    #     "threshold_a": 0.5,
                    #     "threshold_b": 0.5,
                    #     "weight": 0.65
                    # }
                    {
                        # 分割图
                        "advanced_weighting": None,
                        "batch_images": "",
                        "control_mode": "ControlNet is more important",
                        "enabled": True,
                        "guidance_end": 0.73,
                        "guidance_start": 0,
                        "hr_option": "Both",
                        "image": {
                            "image": seg_img,
                            # "mask": "base64image placeholder"
                        },
                        "inpaint_crop_input_image": False,
                        "input_mode": "simple",
                        "ipadapter_input": None,
                        "is_ui": True,
                        "loopback": False,
                        "low_vram": False,
                        "model": "control_v11p_sd15_seg_fp16 [ab613144]",
                        "module": "seg_ofcoco",
                        "output_dir": "",
                        "pixel_perfect": False,
                        "processor_res": 512,
                        "resize_mode": "Crop and Resize",
                        "save_detected_map": True,
                        "threshold_a": 0.5,
                        "threshold_b": 0.5,
                        "weight": 0.85
                    }
                ]
            },
            "Sampler": {
                "args": [
                    20,
                    "DPM++ 2M",
                    "Automatic"
                ]
            },
            "Seed": {
                "args": [
                    random_seed,
                    False,
                    -1,
                    0,
                    0,
                    0
                ]
            },
        },

        "denoising_strength": 0.7,          
        "disable_extra_networks": False,
        "do_not_save_grid": False,
        "do_not_save_samples": False,
        "hr_negative_prompt": negative_prompt,
        "hr_prompt": prompt,
        "hr_resize_x": 0,
        "hr_resize_y": 0,
        "hr_scheduler": "Automatic",
        "hr_second_pass_steps": 0,
        "hr_upscaler": "Latent",

        "negative_prompt": negative_prompt,
        "prompt": prompt,

        "restore_faces": False,
        "s_churn": 0.0,
        "s_min_uncond": 0.0,
        "s_noise": 1.0,
        "s_tmax": None,
        "s_tmin": 0.0,
        "sampler_name": "DPM++ 2M",         # 采样方法
        "scheduler": "Automatic",
        "script_args": [],                  # lora 模型参数配置
        "script_name": None,
        "seed_enable_extras": True,
        "seed_resize_from_h": -1,
        "seed_resize_from_w": -1,
        "styles": [],
        "subseed": -1,                      
        "subseed_strength": 0,              
        "tiling": False,


        # 换模型
        "override_settings": {
            'sd_model_checkpoint': "LandscapeBING_v1.0.safetensors [0bbe3f1aa3]"
        },            
        "override_settings_restore_afterwards": False,

        "width": width,                     # 生成图像宽度
        "height": height,                   # 生成图像高度
        "seed": random_seed,                # 随机种子
        "steps": 20,                        # 生成步数 20

        "batch_size": 1,                    # 每次生成的张数
        "n_iter": 1,                        # 生成批次

        "cfg_scale": 7,                     # 关键词相关性

        "enable_hr": True,                  # 开启高清hr
        "hr_scale": 1.5,                    # 高清级别
    }
    return payload


def i2i_controlnet_payload(prompt, negative_prompt, init_img, seg_img, random_seed, max_size=256):
    payload = {
        # 1.基础参数
        "init_images": [init_img],  # 这里是你要输入的init image
        "negative_prompt": negative_prompt,
        "prompt": prompt,
        "hr_negative_prompt": negative_prompt,
        "hr_prompt": prompt,

        # 模型设置
        "override_settings": {
            # 'sd_model_checkpoint': "anything-v5"  # 确保使用 SD1.5 模型
            # 'sd_model_checkpoint': "AD_老王SD1.5_ARCH_入门版"
            'sd_model_checkpoint': "老王SDXL生图模型_XL入门"
        },
        "override_settings_restore_afterwards": True,

        # 2.controlnet参数
        "alwayson_scripts": {        
            "ControlNet": {
                "args": [
                    { 
                        # ControlNet配置
                        "advanced_weighting": None,
                        "batch_images": "",
                        "control_mode": "Balanced",
                        "enabled": True,
                        "guidance_end": 0.68,
                        "guidance_start": 0,
                        "hr_option": "Both",
                        "image": {
                            "image": seg_img,
                        },
                        "inpaint_crop_input_image": True,
                        "input_mode": "simple",
                        "ipadapter_input": None,
                        "is_ui": True,
                        "loopback": False,
                        "low_vram": False,
                        # "model": "control_v11p_sd15_seg_fp16 [ab613144]",  # SD1.5 的 ControlNet 模型
                        # "model": "ip-adapter_sd15",
                        # "model": "ip-adapter_sdxl_vit-h",
                        # "model": "diffusion_pytorch_model",
                        "model": "sdxl_segmentation_ade20k_controlnet",
                        "module": "none",  # 使用分割模块seg_ofcoco
                        "output_dir": "",

                        "pixel_perfect": False,
                        "processor_res": 512,
                        "resize_mode": "Crop and Resize",
                        "save_detected_map": True,
                        "threshold_a": 0.5,
                        "threshold_b": 0.5,
                        "weight": 0.6
                    }
                ]
            },
        },

        # 3.生成参数
        "denoising_strength": 0.5,
        "disable_extra_networks": False,
        "do_not_save_grid": False,
        "do_not_save_samples": False,
        "hr_resize_x": max_size,
        "hr_resize_y": max_size,
        "hr_scheduler": "Automatic",
        "hr_second_pass_steps": 20,
        "hr_upscaler": "Latent",

        # 4.其他参数
        "include_init_images": False,
        "send_images": True,
        "save_images": False,
    }
    return payload


def inpainting_payload(height, width, prompt, negative_prompt, init_img, mask_img, random_seed):
    payload = {
        "alwayson_scripts": {
            "Sampler": {
                "args": [
                    20,
                    "DPM++ 2M",
                    "Automatic"
                ]
            },
            "Seed": {
                "args": [
                    random_seed,
                    False,
                    -1,
                    0,
                    0,
                    0
                ]
            },
            "Soft Inpainting": {
                "args": [
                    True,       # Soft inpainting
                    1,          # Schedule bias
                    0.5,        # Preservation strength
                    4,          # Transition contrast boost
                    0,          # Mask influence
                    0.5,        # Difference threshold
                    2           # Difference contrast
                ]
            },
        },

        "denoising_strength": 0.75,
        "disable_extra_networks": False,
        "do_not_save_grid": False,
        "do_not_save_samples": False,
        "image_cfg_scale": 1.5,

        # inpainting mode
        "init_images": [init_img],
        "initial_noise_multiplier": 1,      # 初始噪声强度，1标准
        "inpaint_full_res": 0,              # 1表示在全分辨率下修补，0表示在缩小的分辨率下修补后再放大回原size
        "inpaint_full_res_padding": 32,     # 仅蒙版区域下边缘预留像素
        "inpainting_fill": 1,               # inpainting方式，0空白填充 1原版（临近像素） 2潜空间噪声 3空白潜空间
        "inpainting_mask_invert": 0,        # mask 黑白反转与否，0不转，1黑白反转，默认api接受的是 白mask透明底！ 透明！！！

        # inpainting mask
        "mask": mask_img,
        "mask_blur": 4,                     # 蒙版边缘模糊
        "mask_blur_x": 4,
        "mask_blur_y": 4,
        "mask_round": False,                # mask是否倒角

        "negative_prompt": negative_prompt,
        "prompt": prompt,

        "resize_mode": 0,
        "restore_faces": False,
        "s_churn": 0,
        "s_min_uncond": 0,
        "s_noise": 1,
        "s_tmax": None,
        "s_tmin": 0,
        "sampler_name": "DPM++ 2M",
        "scheduler": "Automatic",
        "script_args": [],
        "script_name": None,
        "seed_enable_extras": True,
        "seed_resize_from_h": -1,
        "seed_resize_from_w": -1,
        "styles": [],
        "subseed": -1,
        "subseed_strength": 0,
        "tiling": False,


        # # 换模型
        # "override_settings": {
        #     'sd_model_checkpoint': "LandscapeBING_v1.0.safetensors [0bbe3f1aa3]"
        # },            
        # "override_settings_restore_afterwards": False,

        "width": width,                     # 生成图像宽度
        "height": height,                   # 生成图像高度
        "seed": random_seed,                # 随机种子
        "steps": 20,                        # 生成步数

        "batch_size": 1,                    # 每次生成的张数
        "n_iter": 1,                        # 生成批次

        "cfg_scale": 7,                     # 关键词相关性
    }
    return payload