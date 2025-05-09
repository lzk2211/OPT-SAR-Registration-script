from PIL import Image, ImageDraw
import os

def draw_grid_on_image(image_path, output_path):
    img = Image.open(image_path)
    width, height = img.size

    if width != height:
        raise ValueError("输入图片必须是正方形！")

    draw = ImageDraw.Draw(img)
    grid_size = width // 3

    # 画竖线（两条）
    for i in range(1, 3):
        x = i * grid_size
        draw.line([(x, 0), (x, height)], fill="pink", width=2)

    # 画横线（两条）
    for i in range(1, 3):
        y = i * grid_size
        draw.line([(0, y), (width, y)], fill="pink", width=2)

    img.save(output_path)
    print(f"已保存带九宫格的图片至：{output_path}")

# 示例用法
draw_grid_on_image("./SAR2/SAR2.png", "./SAR2/tile_all.png")
