# ArchSight AIOS Contract Audit（产品内置适配）

本目录记录 ContractLens 对 ArchSight AIOS `aios-contract-audit` 工作流的产品内适配。

接入原则：

- 增强现有合同审核引擎，不新建独立服务或上传入口。
- 只基于合同原文输出，不把缺失资料直接认定为违约事实。
- 每条 AI 风险必须提供页码、条款或原文短摘，并进行原文反查。
- 输出“建议复核 / 需核验”与人工复核岗位，不输出最终法律意见。
- 对明显不适用的贷款、担保、电子合同规则先按合同类型过滤。

上游来源：https://github.com/ArchSightLabs/archsight-aios

参考 Skill：`skills/aios-contract-audit/SKILL.md`

许可证：Apache-2.0。ArchSight AIOS 名称仅用于说明上游来源，不表示官方认证或背书。
