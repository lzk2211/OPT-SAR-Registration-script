import os
import pandas as pd

def extract_offset_from_filename(filename):
    """
    从文件名中提取坐标偏移值
    例如：从 'tile_0_0_points.csv' 提取 (0, 0)
    """
    parts = filename.split('_')
    offset_x = int(parts[1])
    offset_y = int(parts[2])
    return offset_x, offset_y

def process_csv_files(input_folder, output_file):
    all_data = []

    for filename in os.listdir(input_folder):
        if filename.endswith('.csv'):
            filepath = os.path.join(input_folder, filename)
            
            # 提取偏移值
            offset_x, offset_y = extract_offset_from_filename(filename)
            
            # 加载CSV文件
            df = pd.read_csv(filepath, skiprows=3)
            
            # 修改坐标值
            df['LeftX'] += offset_x
            df['LeftY'] += offset_y
            df['RightX'] += offset_x
            df['RightY'] += offset_y
            
            # 添加到总数据中
            all_data.append(df)

    # 合并所有数据并保存到一个CSV文件中
    result = pd.concat(all_data, ignore_index=True)
    result.to_csv(output_file, index=False)
    print(f"所有CSV文件已合并到 {output_file}")

# 使用示例
input_folder = r'C:\Users\liukunkun\Desktop\OPT-SAR-Registration-script\Dataset_Label_Test2\Label2'  # 替换为你的文件夹路径
output_file = 'tile_all_points.csv'     # 输出文件名
process_csv_files(input_folder, output_file)
