# Team Handoff

## 项目定位

`case-organizer` 是单患者、本地优先的病情资料整理工具。

它负责：

- 建立固定病例目录
- 接收患者原始资料
- 调用本地解析 / MinerU 解析
- 形成候选病情结构
- 导出标准化结果，供 `ca199-toolbox-v2` 展示

它不负责：

- 多患者管理
- 云端病例平台
- 医疗结论生成
- 医生主界面的展示逻辑

## 当前主接口

后续开发请按这个原则继续：

- `normalized` 是唯一主接口
- 推荐导入文件是：
  `exports/normalized/ca199_toolbox_bundle.json`
- `legacy` 只作为兼容层保留，不再作为后续核心设计前提

## 当前目录职责

```text
output/
  patient001/
    raw/          # 患者原始资料
    workspace/    # 中间处理结果
    exports/
      normalized/ # 主接口
      legacy/     # 兼容层
      printable/
      summaries/
```

## 团队开发顺序建议

后续开发按这个顺序推进：

1. 先稳定 `raw -> workspace -> exports/normalized`
2. 优先保证 `ca199_toolbox_bundle.json` 可持续导出
3. 再增强候选病情结构和 review 体验
4. 最后再考虑是否继续保留或弱化 `legacy`

不要再围绕旧 `legacy` 接口反推主架构。

## 与 ca199-toolbox-v2 的配合方式

最小闭环：

1. 在 `case-organizer` 创建病例并整理资料
2. 导出：
   `exports/normalized/ca199_toolbox_bundle.json`
3. 在 `ca199-toolbox-v2` 导入该文件
4. 查看三 Tab 展示

## 开发入口

### 本地开发

```bash
cd case-organizer
python -m pip install -e ".[dev]"
pytest -q
```

### 启动 Web 向导

```bash
cd case-organizer
python -m case_organizer.cli review ./output/patient001/workspace --host 127.0.0.1 --port 8765
```

### 常用命令

```bash
python -m case_organizer.cli init ./output/patient001
python -m case_organizer.cli scan ./output/patient001
python -m case_organizer.cli review ./output/patient001/workspace
```

## 文档路径

本仓库内建议优先阅读：

- [README.md](../README.md)
- [QUICK_START.md](../QUICK_START.md)
- [output-contract.md](./output-contract.md)
- [TEAM_HANDOFF.md](./TEAM_HANDOFF.md)

如果你在当前本地联合工作区开发，相关上游产品/设计文档还在：

- `/Users/qinxiaoqiang/Downloads/ca199_toolbox/docs/product/2026-04-01-case-organizer-project-spec.md`
- `/Users/qinxiaoqiang/Downloads/ca199_toolbox/docs/product/2026-04-01-case-organizer-patient-wizard-spec.md`
- `/Users/qinxiaoqiang/Downloads/ca199_toolbox/docs/product/2026-04-01-case-organizer-implementation-plan.md`
- `/Users/qinxiaoqiang/Downloads/ca199_toolbox/docs/product/2026-04-01-case-organizer-ca199toolbox-bridge-spec.md`

## 当前仓库状态说明

当前仓库已经包含：

- CLI 主链路
- Web 向导
- MinerU 结果处理
- 标准化导出
- `ca199_toolbox_bundle.json` 单文件主接口

后续如果继续开发，建议在新分支上进行，不直接在 `master` 上混改。
