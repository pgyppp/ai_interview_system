import plotly.graph_objects as go
import os
import random
from datetime import datetime

def generate_interactive_single_radar_chart(
    data: dict,
    output_dir: str = "output",
    tag: str = "",
    filename_html: str = "radar_chart.html",
    filename_png: str = "radar_chart.png",
    save_png: bool = True # PDF报告需要PNG图像
) -> str:
    """
    生成单用户的交互式雷达图。

    Args:
        data (dict): 包含雷达图数据的字典。
        output_dir (str): 输出目录。
        tag (str): 文件名标签。
        filename_html (str): HTML 文件名。
        filename_png (str): PNG 文件名。
        save_png (bool): 是否同时保存 PNG。

    Returns:
        str: HTML 文件路径。
    """
    labels = list(data.keys())
    values = list(data.values())

    # 归一化到 0-1 范围（用于绘图）
    normalized_values = [v / 10.0 for v in values]
    normalized_values += normalized_values[:1]  # 闭合图形
    labels += labels[:1]

    # 设置随机颜色
    color_pool = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#9C27B0", "#FF9800",
        "#3F51B5", "#00BCD4", "#8BC34A", "#FF5722", "#9E9E9E"
    ]
    line_color = random.choice(color_pool)

    # 将 hex 转换为 rgba 格式（支持透明度）
    try:
        r, g, b = int(line_color[1:3], 16), int(line_color[3:5], 16), int(line_color[5:7], 16)
    except ValueError:
        # 如果不是标准 hex，使用默认颜色（Material Blue）
        r, g, b = 63, 81, 181
    fill_color = f"rgba({r}, {g}, {b}, 0.6)"

    # 创建图形
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=normalized_values,
        theta=labels,
        fill='toself',
        name="能力评估",
        line=dict(color=line_color, width=3),
        fillcolor=fill_color,
        hovertemplate="<b>%{theta}</b><br>评分: %{r:.2f} / 1.0<br>原始分: %{customdata.value}<extra></extra>",
        customdata=[{"value": v} for v in values]  # 使用二维数组存储自定义数据
    ))

    # 更新布局
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],  # 确保范围从 0 到 1
                tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                ticktext=["0", "2", "4", "6", "8", "10"],
                showline=True,  # 显示径向轴的外框线
                gridcolor="#ccc",  # 设置网格线颜色
                linewidth=2,  # 增加外框线宽度
                linecolor="#333",  # 设置外框线颜色
                layer="above traces"  # 确保外框线在轨迹之上
            ),
            angularaxis=dict(
                direction="clockwise",
                linewidth=2,  # 增加角度轴线宽
                showline=True,
                linecolor="#ccc",
                layer="below traces"  # 确保角度轴线在轨迹之下
            )
        ),
        showlegend=False,
        title=dict(text="个人能力雷达图", x=0.5, font=dict(size=20)),
        template="plotly_white",
        margin=dict(t=80, b=40)
    )

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 保存为 HTML
    file_path_html = os.path.join(output_dir, filename_html)
    if tag:
        name, ext = os.path.splitext(filename_html)
        file_path_html = os.path.join(output_dir, f"{name}_{tag}{ext}")
    fig.write_html(file_path_html)

    # 同时保存为 PNG
    if save_png:
        png_tag = tag or datetime.now().strftime("%Y%m%d_%H%M%S")
        png_name, png_ext = os.path.splitext(filename_png)
        file_path_png = os.path.join(output_dir, f"{png_name}_{png_tag}{png_ext}")
        fig.write_image(file_path_png, engine="kaleido", format="png", width=1000, height=1000)

    return os.path.abspath(file_path_png), os.path.abspath(file_path_html)


if __name__ == "__main__":
    sample_data = {
        "肢体语言": 7.0,
        "表情管理": 7.0,
        "语速": 5.0,
        "流畅度": 4.0,
        "专业知识": 6.0,
        "逻辑性": 5.0
    }

    chart_path = generate_interactive_single_radar_chart(
        data=sample_data,
        output_dir="output_chart",
        tag="single_user",
        filename_html="radar_chart.html",
        filename_png="radar_chart.png"
    )
    print(f"✅ 交互式雷达图已生成: {chart_path}")
      