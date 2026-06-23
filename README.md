# Blogger Prediction Aggregator — 使用说明

## 概述

这个系统将一个博主预测JSON（来自某平台API）转换成世界杯主题的静态HTML页面。Python负责数据处理和图片下载，JavaScript负责前端渲染。

## 快速使用

```bash
# 每次用户发来新JSON时，只需两步：
# 1. 把JSON保存到 data/ 目录（或直接传路径）
# 2. 运行：
cd E:/football/blogger_aggregator
python generate_report.py data/2026-06-22.json

# 3. 浏览器打开 output/blogger_report.html
```

## 目录结构

```
E:\football\blogger_aggregator\
├── generate_report.py      ← 主脚本（Python）
├── data\                   ← 原始JSON按日期存储
│   └── 2026-06-22.json     ← 示例数据（10条预测）
├── images\                 ← 下载的博主预测图片
│   ├── 00f010c0eecc.jpg    ← 自动命名（URL的MD5 hash）
│   ├── ...
├── output\
│   └── blogger_report.html ← 最终HTML（浏览器直接打开）
└── README.md               ← 本文档
```

## 数据流程

```
用户提供JSON
    │
    ▼
merge_and_save_json()   ← 保存到 data/日期.json（自动合并去重）
    │
    ▼
load_all_data()         ← 扫描 data/ 下所有JSON
    │
    ▼
process_entry() × N     ← 逐条处理：
    │   ├─ extract_match_from_title()  ← 正则提取队名/编号/时间
    │   ├─ parse_content_html()        ← 解析HTML content为结构化预测
    │   └─ download_image()            ← 下载图片到 images/
    │
    ▼
gen_html()              ← 把数据数组序列化成JSON，嵌入HTML模板
    │                    （只做 2 次 str.replace：__ENTRIES_JSON__ 和 __DATES_JSON__）
    ▼
output/blogger_report.html
```

## 输入JSON格式

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "list": [
      {
        "id": 28746,                          // 唯一ID
        "title": "⚽【博主名】044 世界杯 11:00 约旦VS阿尔及利亚",
        "content": "<p>...预测文字HTML...</p>",  // 文字预测（可为空）
        "img": "https://...jpg",                // 图片预测（可为空）
        "author": {"nickname": "李东评", "avatar": "https://...jpg"},
        "create_date": "2026-06-22",
        "create_time_formatted": "06-22 23:47",
        "buy_num": 11, "read_num": 33,
        "tags": {"2": [{"name": "高胜率"}]}
      }
    ],
    "count": 1818
  }
}
```

## 队名优先AI识别 否则提取正则

```python
# 从title中提取对阵信息
re.findall(r'([一-龥]{2,})\s*(?:[Vv][Ss]\.?|[～~—])\s*([一-龥]{2,})', title)
# 支持的分隔符：vs / VS / vs. / ～ / ~ / —
# 取最后一个"真实"队名对（过滤掉"世界杯""出击"等非队名）
```

## 前后端分工

| 层          | 职责                        |
| ---------- | ------------------------- |
| Python     | JSON解析、图片下载、队名/预测提取、数据序列化 |
| JavaScript | 卡片渲染、日期筛选、弹窗详情、图片灯箱、事件委托  |
| HTML/CSS   | 布局、样式、动画、响应式              |

## 设计特点

- **明亮主题**：浅灰绿背景 + 白卡片 + 世界杯绿色Header
- **信息前置**：所有预测内容直接展示在卡片上，无需点击
- **无框架依赖**：纯静态HTML，浏览器直接打开
- **图片本地化**：远程图片自动下载到 `images/` 目录
- **日期筛选**：顶部下拉框切换日期，纯前端过滤
- **点击弹窗**：点击卡片查看完整详情 + 图片灯箱放大
- **数据合并**：同日期JSON自动合并去重（按ID）

## 常见问题

### 图片下载失败

图片服务器可能有网络限制。脚本会自动回退到远程URL（`download_image` 的 fallback）。

### 某条预测没有显示队名

该博主的标题可能是"合集"格式（如"联赛老鬼"和"星帝足球世界"），标题中没有明确的对阵信息。这是数据源的问题。

### 新增JSON后旧数据还在吗？

在。`load_all_data()` 扫描 `data/` 下**所有**JSON文件，不会覆盖。

### HTML一片空白

打开浏览器控制台（F12→Console），检查JavaScript错误。通常是JSON数据格式问题。

## 未来改进方向

- 按博主分组视图
- 按比赛分组视图（多博主对同一场比赛的预测对比）
- 预测准确率统计
- 移动端App外壳
- 实时推送更新
