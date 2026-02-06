import struct
import sys

def insert_string_to_png(input_file, output_file, text_to_insert):
    """
    将字符串插入到PNG文件的末尾（在IEND块之后）
    
    参数:
        input_file: 输入的PNG文件名
        output_file: 输出的PNG文件名
        text_to_insert: 要插入的字符串
    """
    try:
        # 读取原始PNG文件
        with open(input_file, 'rb') as f:
            png_data = f.read()
        
        # 查找IEND块的位置（PNG文件以IEND块结束）
        # IEND块的签名字节：00 00 00 00 49 45 4E 44 AE 42 60 82
        iend_signature = b'\x00\x00\x00\x00IEND\xaeB`\x82'
        iend_position = png_data.rfind(iend_signature)
        
        if iend_position == -1:
            raise ValueError("无效的PNG文件：找不到IEND块")
        
        # IEND块结束的位置（起始位置 + 12字节）
        iend_end = iend_position + 12
        
        # 创建要插入的数据（包含长度前缀以便读取）
        text_bytes = text_to_insert.encode('utf-8')
        data_to_insert = struct.pack('>I', len(text_bytes)) + text_bytes
        
        # 在IEND块之后插入数据
        new_png_data = (
            png_data[:iend_end] + 
            data_to_insert + 
            png_data[iend_end:]
        )
        
        # 写入新的PNG文件
        with open(output_file, 'wb') as f:
            f.write(new_png_data)
        
        print(f"成功将字符串插入到 {input_file}")
        print(f"已保存为 {output_file}")
        print(f"插入的字符串: {text_to_insert}")
        print(f"插入位置: IEND块之后（偏移量 {iend_end}）")
        
    except Exception as e:
        print(f"错误: {e}")

def extract_string_from_png(png_file):
    """
    从PNG文件末尾提取插入的字符串
    
    参数:
        png_file: PNG文件名
    """
    try:
        with open(png_file, 'rb') as f:
            png_data = f.read()
        
        # 查找IEND块
        iend_signature = b'\x00\x00\x00\x00IEND\xaeB`\x82'
        iend_position = png_data.rfind(iend_signature)
        
        if iend_position == -1:
            raise ValueError("无效的PNG文件：找不到IEND块")
        
        iend_end = iend_position + 12
        
        # 检查IEND之后是否有数据
        if len(png_data) <= iend_end:
            print("PNG文件末尾没有插入的数据")
            return None
        
        # 读取插入的数据
        # 前4字节是数据长度（大端序）
        data_after_iend = png_data[iend_end:]
        
        if len(data_after_iend) < 4:
            print("插入的数据格式错误")
            return None
        
        # 读取长度
        text_length = struct.unpack('>I', data_after_iend[:4])[0]
        
        # 读取字符串
        text_data = data_after_iend[4:4+text_length]
        
        if len(text_data) != text_length:
            print("数据损坏：长度不匹配")
            return None
        
        # 解码字符串
        extracted_text = text_data.decode('utf-8')
        print(f"提取到的字符串: {extracted_text}")
        return extracted_text
        
    except Exception as e:
        print(f"错误: {e}")
        return None

def main():
    """主函数，提供命令行界面"""
    if len(sys.argv) < 2:
        print("PNG文件字符串插入工具")
        print("用法:")
        print("  插入字符串: python png_insert.py insert <输入文件> <输出文件> <要插入的字符串>")
        print("  提取字符串: python png_insert.py extract <PNG文件>")
        print("  示例:")
        print("    python png_insert.py insert input.png output.png \"这是一个秘密消息\"")
        print("    python png_insert.py extract output.png")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'insert' and len(sys.argv) >= 5:
        input_file = sys.argv[2]
        output_file = sys.argv[3]
        # 合并剩余参数作为要插入的字符串
        text_to_insert = ' '.join(sys.argv[4:])
        insert_string_to_png(input_file, output_file, text_to_insert)
    
    elif command == 'extract' and len(sys.argv) >= 3:
        png_file = sys.argv[2]
        extract_string_from_png(png_file)
    
    else:
        print("无效的命令或参数")
        print("使用 'insert' 或 'extract' 命令")

if __name__ == "__main__":
    main()