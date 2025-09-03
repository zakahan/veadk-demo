from datetime import datetime
from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀", log_level="ERROR")

@mcp.tool
def calculate_date_difference(date1: str, date2: str) -> int:
    """
    计算两个日期之间的天数差异

    参数:
        date1: 第一个日期，格式为"YYYY-MM-DD"
        date2: 第二个日期，格式为"YYYY-MM-DD"

    返回:
        两个日期之间的天数差异（绝对值）

    异常:
        ValueError: 当输入的日期格式不正确时抛出
    """
    # 解析日期字符串为datetime对象
    try:
        d1 = datetime.strptime(date1, "%Y-%m-%d")
        d2 = datetime.strptime(date2, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"日期格式错误，请使用YYYY-MM-DD格式: {e}")

    # 计算日期差并返回绝对值
    delta = d2 - d1
    return abs(delta.days)


if __name__ == "__main__":
    mcp.run()