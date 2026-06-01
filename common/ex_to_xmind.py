import xmind
import openpyxl
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def validate_file_path(file_path):
    """验证文件路径合法性"""
    if not isinstance(file_path, str) or not file_path.strip():
        raise ValueError("文件路径不能为空")
    if not os.path.isabs(file_path):
        raise ValueError("请提供绝对路径")
    if any(char in file_path for char in ['<', '>', ':', '"', '|', '?', '*']):
        raise ValueError("文件路径包含非法字符")

def load_excel(file_path):
    """加载Excel文件"""
    try:
        validate_file_path(file_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel文件不存在: {file_path}")
        wb = openpyxl.load_workbook(file_path)
        logging.info(f"成功加载Excel文件: {file_path}")
        return wb.active
    except Exception as e:
        logging.error(f"加载Excel失败: {e}")
        raise

def create_xmind_topics(sheet, root_topic):
    """根据Excel内容创建XMind主题结构"""
    try:
        # 遍历Excel行生成节点（跳过表头，min_row=2）
        has_data = False
        for row in sheet.iter_rows(min_row=2, values_only=True):
            for cell in row:
                if cell is None or str(cell).strip() == "":
                    break
                sub_topic = parent_topic.addSubTopic()
                sub_topic.setTitle(str(cell))
                parent_topic = sub_topic
                has_data = True
        if not has_data:
            logging.warning("Excel表格中无有效数据，XMind文件将为空")
    except Exception as e:
        logging.error(f"创建XMind主题失败: {e}")
        raise

def save_xmind(xmind_wb, output_path):
    """保存XMind文件"""
    try:
        validate_file_path(output_path)
        xmind_wb.save(output_path)
        logging.info(f"XMind文件已保存至: {output_path}")
    except Exception as e:
        logging.error(f"保存XMind文件失败: {e}")
        raise

def create_xmind_structure(sheet, output_path):
    """根据Excel内容创建XMind结构"""
    try:
        # 创建XMind工作簿
        xmind_wb = xmind.load(output_path)
        sheet1 = xmind_wb.getPrimarySheet()
        root_topic = sheet1.getRootTopic()
        root_topic.setTitle("Excel转XMind结果")

        # 构建主题结构
        create_xmind_topics(sheet, root_topic)

        # 保存XMind
        save_xmind(xmind_wb, output_path)
    except Exception as e:
        logging.error(f"创建XMind结构失败: {e}")
        raise

def main(excel_path, xmind_output_path):
    """主函数"""
    try:
        logging.info("开始处理Excel文件...")
        sheet = load_excel(excel_path)
        logging.info("Excel文件加载成功，开始转换为XMind...")
        create_xmind_structure(sheet, xmind_output_path)
        logging.info("转换完成！")
    except Exception as e:
        logging.critical(f"程序执行失败: {e}")

# 示例调用
if __name__ == "__main__":
    excel_file = "/Users/alloyx/Desktop/法币中台.xlsx"
    xmind_file = "/Users/alloyx/Desktop/法币中台.xmind"
    main(excel_file, xmind_file)
