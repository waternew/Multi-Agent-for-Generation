import cv2
from PIL import Image


class compress_image:

    def __init__(self, image_path: str):
        self.image_path = image_path
        self.image_name = image_path.split("/")[-1]

    def compress_image(self, compress_ratio: float = 0.25, show_image: bool = False):
        image = cv2.imread(self.image_path)
        height, width, channels = image.shape
        new_height = int(height * compress_ratio)
        new_width = int(width * compress_ratio)
        # image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        image = cv2.resize(image, (256, 256), interpolation=cv2.INTER_AREA)

        # 将图片转换为JPEG格式
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        image.save(self.image_path.replace(".png", "_compr.jpg"))

        # if show_image:
        #     cv2.imshow(self.image_name, image)
        #     cv2.waitKey(0)
        #     cv2.destroyAllWindows()


if __name__ == "__main__":
    compress_image = compress_image("E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data/2_image.png")
    # compress_image = compress_image("E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data/2_layout.png")
    compress_image.compress_image(compress_ratio=0.25, show_image=True)
