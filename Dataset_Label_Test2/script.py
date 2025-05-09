from PIL import Image
import os

def split_image_to_9(image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    img = Image.open(image_path)
    width, height = img.size

    if width != height:
        raise ValueError("输入图片必须是正方形！")

    grid_size = width // 3

    for i in range(3):  # 行
        for j in range(3):  # 列
            left = j * grid_size
            upper = i * grid_size
            right = left + grid_size
            lower = upper + grid_size

            cropped_img = img.crop((left, upper, right, lower))

            filename = f"tile_{left}_{upper}.png"  # 用左上角坐标命名
            cropped_img.save(os.path.join(output_dir, filename))

    print(f"保存完成，图片输出在：{output_dir}")

# 示例用法
split_image_to_9("./SAR2/SAR2.png", "SAR2")
