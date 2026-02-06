import struct
import sys
import zlib

def get_png_dimensions(png_file):
    """获取PNG图片的尺寸"""
    try:
        with open(png_file, 'rb') as f:
            # 验证PNG文件签名
            signature = f.read(8)
            if signature != b'\x89PNG\r\n\x1a\n':
                print("不是有效的PNG文件")
                return None
            
            # 查找IHDR块
            while True:
                chunk_length_data = f.read(4)
                if not chunk_length_data:
                    break
                
                chunk_length = struct.unpack('>I', chunk_length_data)[0]
                chunk_type = f.read(4)
                
                if chunk_type == b'IHDR':
                    # IHDR块包含：宽度(4), 高度(4), 位深(1), 颜色类型(1), 
                    # 压缩方法(1), 过滤方法(1), 隔行扫描方法(1)
                    width_data = f.read(4)
                    height_data = f.read(4)
                    
                    width = struct.unpack('>I', width_data)[0]
                    height = struct.unpack('>I', height_data)[0]
                    
                    print(f"PNG尺寸: {width} x {height} 像素")
                    return width, height
                else:
                    # 跳过这个块的数据和CRC
                    f.read(chunk_length + 4)
                    
    except Exception as e:
        print(f"错误: {e}")
        return None

def modify_png_dimensions(input_file, output_file, new_width=None, new_height=None, 
                          keep_aspect_ratio=False, scale_factor=None):
    """
    修改PNG图片的尺寸（仅修改元数据，不重新采样像素）
    
    警告：这不会改变实际的像素数据，可能导致图片显示异常！
    如果要真正改变图片尺寸，需要重新采样像素。
    
    参数:
        input_file: 输入PNG文件
        output_file: 输出PNG文件
        new_width: 新的宽度（像素）
        new_height: 新的高度（像素）
        keep_aspect_ratio: 是否保持宽高比（当只指定一个尺寸时）
        scale_factor: 缩放因子（例如0.5表示缩小一半）
    """
    try:
        with open(input_file, 'rb') as f:
            png_data = f.read()
        
        # 验证PNG签名
        if png_data[:8] != b'\x89PNG\r\n\x1a\n':
            raise ValueError("不是有效的PNG文件")
        
        # 查找IHDR块
        pos = 8  # 跳过签名
        ihdr_pos = -1
        width_pos = -1
        height_pos = -1
        original_width = 0
        original_height = 0
        
        while pos < len(png_data):
            if pos + 8 > len(png_data):
                break
                
            chunk_length = struct.unpack('>I', png_data[pos:pos+4])[0]
            chunk_type = png_data[pos+4:pos+8]
            
            if chunk_type == b'IHDR':
                ihdr_pos = pos
                width_pos = pos + 8  # 类型之后
                height_pos = width_pos + 4
                
                original_width = struct.unpack('>I', png_data[width_pos:width_pos+4])[0]
                original_height = struct.unpack('>I', png_data[height_pos:height_pos+4])[0]
                break
            
            # 移动到下一个块
            pos += 12 + chunk_length  # 长度+类型+数据+CRC
        
        if ihdr_pos == -1:
            raise ValueError("找不到IHDR块")
        
        print(f"原始尺寸: {original_width} x {original_height} 像素")
        
        # 计算新的尺寸
        if scale_factor is not None:
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
        else:
            if new_width is None and new_height is None:
                raise ValueError("必须指定新的宽度或高度，或缩放因子")
            
            if new_width is not None and new_height is not None:
                # 两个尺寸都指定了
                pass
            elif new_width is not None and new_height is None:
                # 只指定了宽度，计算高度
                if keep_aspect_ratio:
                    new_height = int(original_height * (new_width / original_width))
                else:
                    new_height = original_height
            elif new_height is not None and new_width is None:
                # 只指定了高度，计算宽度
                if keep_aspect_ratio:
                    new_width = int(original_width * (new_height / original_height))
                else:
                    new_width = original_width
        
        # 确保新尺寸为正整数
        new_width = max(1, int(new_width))
        new_height = max(1, int(new_height))
        
        print(f"新尺寸: {new_width} x {new_height} 像素")
        
        # 警告用户这不会改变像素数据
        print("\n警告: 这只是修改元数据，不会重新采样像素数据！")
        print("图片内容不会改变，但显示时会被拉伸/压缩。")
        print("要真正改变图片尺寸，请使用图片编辑软件。")
        
        confirm = input("确定要修改吗？(y/N): ").lower()
        if confirm != 'y':
            print("操作已取消")
            return
        
        # 创建新的PNG数据，替换尺寸
        new_png_data = bytearray(png_data)
        
        # 替换宽度
        new_width_bytes = struct.pack('>I', new_width)
        for i in range(4):
            new_png_data[width_pos + i] = new_width_bytes[i]
        
        # 替换高度
        new_height_bytes = struct.pack('>I', new_height)
        for i in range(4):
            new_png_data[height_pos + i] = new_height_bytes[i]
        
        # 重新计算IHDR块的CRC
        ihdr_start = width_pos - 4  # 块类型开始
        ihdr_end = height_pos + 4 + 5  # 高度之后还有5个字节（位深、颜色类型等）
        
        # CRC计算：块类型 + 数据
        crc_data = png_data[ihdr_start:ihdr_end]
        crc_value = zlib.crc32(crc_data) & 0xffffffff
        
        # 替换CRC（紧接在IHDR数据之后）
        crc_pos = ihdr_end
        new_crc_bytes = struct.pack('>I', crc_value)
        for i in range(4):
            new_png_data[crc_pos + i] = new_crc_bytes[i]
        
        # 写入新文件
        with open(output_file, 'wb') as f:
            f.write(new_png_data)
        
        print(f"\n成功修改尺寸！")
        print(f"已保存为: {output_file}")
        print(f"注意: 像素数据未改变，显示时尺寸为 {new_width}x{new_height}")
        
    except Exception as e:
        print(f"错误: {e}")

def resize_png_with_resampling(input_file, output_file, new_width=None, new_height=None,
                              keep_aspect_ratio=True, scale_factor=None):
    """
    真正重新采样像素来改变PNG尺寸（使用PIL库）
    需要安装Pillow: pip install Pillow
    """
    try:
        from PIL import Image
        
        # 打开图片
        img = Image.open(input_file)
        original_width, original_height = img.size
        
        print(f"原始尺寸: {original_width} x {original_height} 像素")
        
        # 计算新的尺寸
        if scale_factor is not None:
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
        else:
            if new_width is None and new_height is None:
                raise ValueError("必须指定新的宽度或高度，或缩放因子")
            
            if new_width is not None and new_height is not None:
                # 两个尺寸都指定了
                pass
            elif new_width is not None and new_height is None:
                # 只指定了宽度
                if keep_aspect_ratio:
                    ratio = new_width / original_width
                    new_height = int(original_height * ratio)
                else:
                    new_height = original_height
            elif new_height is not None and new_width is None:
                # 只指定了高度
                if keep_aspect_ratio:
                    ratio = new_height / original_height
                    new_width = int(original_width * ratio)
                else:
                    new_width = original_width
        
        # 确保新尺寸为正整数
        new_width = max(1, int(new_width))
        new_height = max(1, int(new_height))
        
        print(f"新尺寸: {new_width} x {new_height} 像素")
        
        # 重新采样
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 保存图片
        resized_img.save(output_file, 'PNG')
        
        print(f"\n成功重新采样并保存！")
        print(f"已保存为: {output_file}")
        print(f"这是真正的尺寸修改，像素已重新采样。")
        
    except ImportError:
        print("错误: 需要Pillow库。请运行: pip install Pillow")
    except Exception as e:
        print(f"错误: {e}")

def main():
    """主函数，提供命令行界面"""
    if len(sys.argv) < 2:
        print("PNG尺寸修改工具")
        print("=" * 50)
        print("用法:")
        print("  1. 查看尺寸: python png_size.py view <PNG文件>")
        print("  2. 修改元数据尺寸（不重采样，仅改头信息）:")
        print("     python png_size.py meta <输入文件> <输出文件> <宽度> <高度>")
        print("     python png_size.py meta input.png output.png 800 600")
        print("  3. 修改并重采样（需要Pillow）:")
        print("     python png_size.py resize <输入文件> <输出文件> <宽度> <高度>")
        print("     python png_size.py resize input.png output.png 800 600")
        print("\n选项:")
        print("  -a: 保持宽高比（只指定一个尺寸时有效）")
        print("  -s <缩放因子>: 按比例缩放（例如0.5）")
        print("\n示例:")
        print("  python png_size.py view image.png")
        print("  python png_size.py meta in.png out.png 1024 768")
        print("  python png_size.py resize in.png out.png 1024 768")
        print("  python png_size.py resize in.png out.png -s 0.5")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'view' and len(sys.argv) >= 3:
        png_file = sys.argv[2]
        get_png_dimensions(png_file)
    
    elif command == 'meta' and len(sys.argv) >= 6:
        input_file = sys.argv[2]
        output_file = sys.argv[3]
        
        # 解析参数
        keep_aspect = '-a' in sys.argv
        scale_factor = None
        
        if '-s' in sys.argv:
            s_index = sys.argv.index('-s')
            if s_index + 1 < len(sys.argv):
                try:
                    scale_factor = float(sys.argv[s_index + 1])
                except ValueError:
                    print("错误: 缩放因子必须是数字")
                    return
        
        # 解析宽度和高度
        args = [arg for arg in sys.argv[4:] if not arg.startswith('-')]
        
        if scale_factor is not None:
            modify_png_dimensions(input_file, output_file, scale_factor=scale_factor)
        elif len(args) >= 2:
            try:
                new_width = int(args[0]) if args[0].lower() != 'none' else None
                new_height = int(args[1]) if args[1].lower() != 'none' else None
                modify_png_dimensions(input_file, output_file, new_width, new_height, keep_aspect)
            except ValueError:
                print("错误: 宽度和高度必须是整数")
        else:
            print("错误: 需要指定宽度和高度，或缩放因子")
    
    elif command == 'resize' and len(sys.argv) >= 5:
        input_file = sys.argv[2]
        output_file = sys.argv[3]
        
        # 解析参数
        keep_aspect = '-a' in sys.argv
        scale_factor = None
        
        if '-s' in sys.argv:
            s_index = sys.argv.index('-s')
            if s_index + 1 < len(sys.argv):
                try:
                    scale_factor = float(sys.argv[s_index + 1])
                except ValueError:
                    print("错误: 缩放因子必须是数字")
                    return
        
        # 解析宽度和高度
        args = [arg for arg in sys.argv[4:] if not arg.startswith('-')]
        
        if scale_factor is not None:
            resize_png_with_resampling(input_file, output_file, scale_factor=scale_factor)
        elif len(args) >= 2:
            try:
                new_width = int(args[0]) if args[0].lower() != 'none' else None
                new_height = int(args[1]) if args[1].lower() != 'none' else None
                resize_png_with_resampling(input_file, output_file, new_width, new_height, keep_aspect)
            except ValueError:
                print("错误: 宽度和高度必须是整数")
        else:
            print("错误: 需要指定宽度和高度，或缩放因子")
    
    else:
        print("无效的命令或参数")

if __name__ == "__main__":
    main()