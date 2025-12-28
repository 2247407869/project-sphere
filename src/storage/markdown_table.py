import os
import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class MarkdownTableEngine:
    """
    极简 Markdown 表格存储引擎：直接读写 Obsidian 中的 Markdown 表格。
    支持：读取、追加行、动态增加列。
    """
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def _get_full_path(self, relative_path: str) -> str:
        # 允许传入全路径或相对 Obsidian 库的路径
        if os.path.isabs(relative_path):
            return relative_path
        return os.path.join(self.base_dir, relative_path)

    def read_table(self, file_path: str) -> Optional[Dict]:
        """
        从文件中提取第一个 Markdown 表格及其结构。
        返回: { "headers": [], "rows": [[]], "raw_content": str, "start_line": int, "end_line": int }
        """
        full_path = self._get_full_path(file_path)
        if not os.path.exists(full_path):
            return None

        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        table_data = {"headers": [], "rows": [], "start_index": -1, "end_index": -1}
        
        # 寻找表格特征行: | col1 | col2 |
        # 以及对齐行: | :--- | :--- |
        found_header = False
        found_separator = False

        for i, line in enumerate(lines):
            line_strip = line.strip()
            if "|" in line_strip and "-|-" not in line_strip and not found_header:
                # 可能是表头
                parts = [p.strip() for p in line_strip.split("|")[1:-1]]
                if parts:
                    table_data["headers"] = parts
                    table_data["start_index"] = i
                    found_header = True
                continue
            
            if found_header and not found_separator:
                if re.match(r"\|\s*[:\-]+\s*\|", line_strip):
                    found_separator = True
                    continue
                else:
                    # 如果表头下面不是隔离带，重置
                    found_header = False
                    table_data["headers"] = []
                    table_data["start_index"] = -1
                    continue
            
            if found_separator:
                if "|" in line_strip:
                    parts = [p.strip() for p in line_strip.split("|")[1:-1]]
                    table_data["rows"].append(parts)
                    table_data["end_index"] = i
                else:
                    break # 表格结束

        return table_data if found_separator else None

    def append_row(self, file_path: str, row_data: Dict[str, str]):
        """
        向表格追加一行。如果字段不存在，自动忽略或初始化。
        """
        table = self.read_table(file_path)
        full_path = self._get_full_path(file_path)

        if not table:
            # 如果表格不存在，创建一个新表格
            headers = list(row_data.keys())
            new_table = f"\n| {' | '.join(headers)} |\n"
            new_table += f"| {' | '.join([':---' for _ in headers])} |\n"
            new_table += f"| {' | '.join([str(row_data.get(h, '')) for h in headers])} |\n"
            
            with open(full_path, "a", encoding="utf-8") as f:
                f.write(new_table)
            return True

        # 构造新行
        new_row_parts = []
        for h in table["headers"]:
            new_row_parts.append(str(row_data.get(h, "")))
        
        new_row_line = f"| {' | '.join(new_row_parts)} |\n"
        
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # 在表格结束处插入
        lines.insert(table["end_index"] + 1, new_row_line)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True

    def add_column(self, file_path: str, col_name: str, fill_values: List[str] = None):
        """
        为现有表格动态增加一列，并回填值。
        """
        table = self.read_table(file_path)
        if not table:
            return False

        full_path = self._get_full_path(file_path)
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 1. 更新表头行
        h_idx = table["start_index"]
        lines[h_idx] = lines[h_idx].strip()[:-1] + f" {col_name} |\n"
        
        # 2. 更新隔离带行
        s_idx = h_idx + 1
        lines[s_idx] = lines[s_idx].strip()[:-1] + f" :--- |\n"
        
        # 3. 更新现有行
        for i, row_idx in enumerate(range(s_idx + 1, table["end_index"] + 1)):
            val = fill_values[i] if fill_values and i < len(fill_values) else ""
            lines[row_idx] = lines[row_idx].strip()[:-1] + f" {val} |\n"

        with open(full_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True

if __name__ == "__main__":
    # 单元测试路径逻辑
    logging.basicConfig(level=logging.INFO)
    test_path = "test_table.md"
    engine = MarkdownTableEngine(os.getcwd())
    
    # 初始化
    engine.append_row(test_path, {"物品": "鸡蛋", "数量": "20"})
    engine.append_row(test_path, {"物品": "面包", "数量": "2"})
    
    # 动态加列
    engine.add_column(test_path, "单位", ["枚", "袋"])
    
    print("测试表已生成: test_table.md")
