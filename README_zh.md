# MM-CoT 论文补充代码

项目仓库：[whu-totemdb/MM-CoT](https://github.com/whu-totemdb/MM-CoT)。

本目录是可独立上传 GitHub 的整理版，对应论文 **MM-CoT: LLM-Guided Coordination of Vector, Graph, and Relational Operations for Scholarly Knowledge Graph Analytics**。主 README 使用英文，便于审稿和公开使用。

## 保留内容

- MM-CoT：向量检索、图操作和关系操作的迭代推理控制器。
- Graph-CoT、Text RAG、Graph RAG、Base LLM 四种对比方法。
- 原始研究提示词和 few-shot 示例，移除 MCP 专用部分及 LangChain 模板依赖。
- 五个学科的全部可用 QA，共 746 条；问题、答案、编号保持原样，增加模板编号用于追溯。
- 统一命令行、批量实验、逐题保存、答案评估，以及少量验证重构行为的离线回归测试。

排除了 MCP/MCPO 服务、FRP、临时测试、占位脚本、日志、缓存、历史实验结果和重复的领域批处理代码。原工作目录的文件未改动。

## 使用方法

在本目录创建 Python 3.10+ 环境，执行：

```bash
python -m pip install -e .
```

复制 `.env.example` 为 `.env`，填写模型和数据库配置。配置文件不会被 Git 跟踪。先使用 `mmcot inspect-data` 检查数据，再按 [英文说明](README.md) 运行单题、批量实验和评估。

原项目中的密钥、私网地址和本机路径没有进入本发布目录。原始文件仍包含密钥，因此上传时应只使用此目录或配套 ZIP 的内容；原有密钥建议撤销或轮换。

## 与论文复现有关的实际限制

1. 实际 QA 数量为 Biology、Chemistry、ComputerScience、MaterialsScience 各 150 条，Medicine 146 条，总计 746 条。Medicine 的模板 10、12 各 8 条。不能据此推定历史实验的评分分母。
2. 当前目录未提供完整 SciSciNet 数据库、向量、数据导入流程、确定的依赖锁定文件或逐题评分选择信息。发布版提供数据库接口契约，运行数据库方法仍需准备数据。
3. 中间结果保存在 Python 内存；表上的过滤、聚合和排序由 PostgreSQL 执行，列表上的操作在 Python 执行，Join 把已有记录交给 PostgreSQL 完成匹配。并非全部中间结果始终保留在数据库内。
4. 重构修复了参数解析、升序排序、空结果和 API 失败处理、零样本模板选择等问题，并收紧了停止和评分规则。这些变化可能影响结果，不能将新跑分直接当作论文原表格的复现。
5. 已完成离线验证，未连接真实数据库或调用付费模型验证端到端效果。具体检查见 [验证记录](docs/validation.md)。

## 上传方式

将本目录内容作为新 GitHub 仓库的根目录，不要将整个原始工作目录一起上传。作者和公开发表信息尚未提供，未擅自添加开源许可证或虚构论文引用信息；可由作者在发布时补充。

详细对应关系见 [代码迁移说明](docs/migration.md)，运行条件见 [数据库说明](docs/database.md)，实验差异见 [复现说明](docs/reproducibility.md)。
