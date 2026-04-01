from __future__ import annotations

RAW_CATEGORY_GROUPS = [
    {
        "key": "01_基本资料",
        "label": "基本资料",
        "examples": ["身份证明", "病历主页", "基本病史"],
    },
    {
        "key": "02_诊断报告书",
        "label": "诊断报告书",
        "examples": ["门诊诊断书", "复诊结论", "随访诊断"],
    },
    {
        "key": "03_影像报告",
        "label": "影像报告",
        "examples": ["CT", "MR", "PET-CT", "超声"],
    },
    {
        "key": "04_病理与基因",
        "label": "病理与基因",
        "examples": ["病理报告", "免疫组化", "基因检测"],
    },
    {
        "key": "05_检验检查",
        "label": "检验检查",
        "children": [
            "01_肿瘤标志物",
            "02_血常规",
            "03_肝肾功能",
            "04_凝血",
            "05_炎症指标",
            "06_体液检查_尿便常规",
            "07_其他检验",
        ],
    },
    {
        "key": "06_处方与用药",
        "label": "处方与用药",
        "examples": ["门诊处方", "出院带药", "治疗方案"],
    },
    {
        "key": "07_个人病情记录",
        "label": "个人病情记录",
        "examples": ["患者自述", "家属整理", "微信记录"],
    },
    {
        "key": "08_手术与住院资料",
        "label": "手术与住院资料",
        "examples": ["手术记录", "出院小结", "住院病程"],
    },
    {
        "key": "99_待分类",
        "label": "待分类",
        "examples": ["暂时不清楚归类的资料"],
    },
]

EXPORT_GROUPS = ["normalized", "legacy", "printable", "summaries"]

