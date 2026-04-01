# Case Organizer

[English](README.md) | [中文](README_CN.md)

`case-organizer` 是一个本地优先的单患者病情整理工具。

它的目标不是直接展示病情，而是把患者和家属手里的图片、PDF、Word、Excel、Markdown 等材料整理成：

- 可校对的候选病情结构
- 可导出的标准化文件
- 可供 `ca199_toolbox` 展示的病程数据

## 产品边界

- 只支持 `1 人 1 用`
- 一个病例目录只对应一个患者
- 不支持多患者列表和混合管理
- 所有数据默认本地处理

## 推荐目录结构

默认病例目录根路径：

```text
./output/
```

每个患者一个目录，例如：

```text
output/
  patient001/
    raw/
      01_基本资料/
      02_诊断报告书/
      03_影像报告/
      04_病理与基因/
      05_检验检查/
        01_肿瘤标志物/
        02_血常规/
        03_肝肾功能/
        04_凝血/
        05_炎症指标/
        06_体液检查_尿便常规/
        07_其他检验/
      06_处方与用药/
      07_个人病情记录/
      08_手术与住院资料/
      99_待分类/
    workspace/
    exports/
      normalized/
      legacy/
      printable/
      summaries/
```

目录职责：

- `raw/`：患者放原始资料
- `workspace/`：系统中间结果和候选结构
- `exports/`：标准化输出、兼容输出和打印输出

## 支持的输入类型

- 图片：`jpg`, `jpeg`, `png`, `webp`
- 文档：`pdf`, `doc`, `docx`
- 表格：`xls`, `xlsx`, `csv`
- 文本：`txt`, `md`

## 功能

1. 初始化标准病例目录
2. 按分类上传和整理文件
3. 调用 MinerU 或本地读取能力提取内容
4. 生成候选病情结构
5. 本地 Web 向导页校对结果
6. 导出：
   - `normalized/`
   - `legacy/`
   - `printable/`
   - `summaries/`

## 启动方式

### CLI

```bash
cd case-organizer
python -m case_organizer.cli init ./output/patient001
python -m case_organizer.cli scan ./output/patient001
python -m case_organizer.cli review ./output/patient001/workspace
```

### Web 向导

```bash
cd case-organizer
python -m case_organizer.cli review ./output/patient001/workspace --host 127.0.0.1 --port 8765
```

然后在浏览器中打开：

```text
http://127.0.0.1:8765
```

## 与 ca199_toolbox 的关系

- `case-organizer` 负责整理输入
- `ca199_toolbox` 负责展示输出

数据衔接分两层：

- `exports/normalized/`：长期主接口
- `exports/legacy/`：旧版 `ca199_toolbox` 兼容接口

## 测试

```bash
cd case-organizer
pytest -q
```
