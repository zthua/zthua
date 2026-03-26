# 实施计划：财经智能Agent系统

## 概述

基于Agent + Skill插件化架构，按自底向上的方式实现：先建立数据模型和基础设施（配置、数据库、日志），再实现各Skill模块，最后实现核心调度器并完成集成。使用Python 3.8+，SQLite持久化，asyncio异步，pytest + hypothesis测试。

## 任务

- [ ] 1. 搭建项目结构与基础数据模型
  - [-] 1.1 创建项目目录结构和基础文件
    - 创建 `finance_agent/` 包目录，包含 `__init__.py`、`models.py`、`config.py`、`database.py`、`logger.py`
    - 创建 `finance_agent/skills/` 子包，包含 `__init__.py`、`base.py`、`registry.py`
    - 创建 `tests/` 目录和 `conftest.py`
    - 创建 `config.yaml` 示例配置文件
    - _需求: 7.1_

  - [~] 1.2 实现核心数据模型（models.py）
    - 实现所有 dataclass：NewsItem、NewsType、StockQuote、BoardType、ImpactReport、AffectedStock、ImpactDirection、ImpactSeverity、ReviewReport、ReviewType、IndexPerformance、SectorRanking、TurnoverComparison、MarketSentiment
    - 实现错误类型：SkillError、ParseError
    - 实现辅助类型：Intent、ExecutionPlan、SkillResult、SkillInfo、ValidationResult、AgentResponse、HealthStatus
    - _需求: 2.3, 3.2, 4.2, 5.2_

  - [ ]* 1.3 编写数据模型属性测试
    - **Property 6: 采集资讯字段完整性** — 验证任意NewsItem必填字段非空
    - **验证需求: 2.3**
    - **Property 10: Stock_Quote字段完整性** — 验证任意StockQuote必填字段存在且数值有效
    - **验证需求: 3.2**

- [ ] 2. 实现配置管理与日志系统
  - [~] 2.1 实现YAML配置解析（config.py）
    - 实现 AgentConfig、SkillConfig、SourceConfig 数据类
    - 实现 `load_config(path: str) -> AgentConfig` 函数，解析YAML配置文件
    - 实现 `dump_config(config: AgentConfig) -> str` 函数，序列化为YAML
    - 配置文件格式不正确时输出明确错误信息并抛出异常
    - _需求: 7.1, 7.3_

  - [ ]* 2.2 编写配置解析属性测试
    - **Property 21: YAML配置解析往返一致性** — 任意有效AgentConfig序列化为YAML后再解析应等价
    - **验证需求: 7.1**

  - [~] 2.3 实现结构化日志系统（logger.py）
    - 实现结构化日志记录器，支持记录Skill调用的输入参数、执行耗时和返回状态
    - 支持通过配置文件设置日志级别（DEBUG/INFO/WARNING/ERROR）
    - _需求: 7.2, 7.4_

  - [ ]* 2.4 编写日志系统属性测试
    - **Property 22: 结构化日志完整性** — 任意Skill调用生成的日志应包含输入参数、执行耗时和返回状态
    - **验证需求: 7.2**

- [ ] 3. 实现数据库层
  - [~] 3.1 实现SQLite数据库管理（database.py）
    - 实现数据库初始化，创建所有表和索引（news_items、stock_quotes、impact_reports、review_reports）
    - 实现 NewsItem、StockQuote、ImpactReport、ReviewReport 的 CRUD 操作
    - 实现按条件查询方法（按时间、类型、关键词等）
    - _需求: 6.1, 6.2, 6.3, 6.4_

  - [ ]* 3.2 编写数据持久化属性测试
    - **Property 19: 数据对象持久化往返一致性** — 任意有效数据对象存储后读取应与原始对象等价
    - **验证需求: 6.1, 6.2, 6.3, 6.4**

- [~] 4. 检查点 - 确保基础设施测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [ ] 5. 实现Skill基类与注册中心
  - [~] 5.1 实现BaseSkill抽象基类（skills/base.py）
    - 实现 BaseSkill ABC，定义 name、description、input_schema、output_schema 抽象属性
    - 实现 execute、validate_params 抽象方法
    - _需求: 1.3, 1.4_

  - [~] 5.2 实现Skill_Registry（skills/registry.py）
    - 实现 register、unregister、get_skill、list_skills 方法
    - 实现 resolve_skills 方法，根据Intent解析执行计划
    - _需求: 1.3, 1.4_

  - [ ]* 5.3 编写Skill注册属性测试
    - **Property 2: 新Skill注册后可被发现和调用** — 任意BaseSkill实现注册后应能被发现并调用
    - **验证需求: 1.4**

- [ ] 6. 实现News_Skill（资讯采集技能）
  - [~] 6.1 实现News_Skill核心逻辑（skills/news_skill.py）
    - 实现 NewsSkill 继承 BaseSkill
    - 实现 fetch_all_sources 并行采集，使用 asyncio.gather
    - 实现 fetch_from_source 单源采集，含超时和错误处理
    - 实现 extract_keywords 关键词提取
    - 实现 deduplicate 去重（基于标题和来源）和按发布时间倒序排序
    - 实现 query_news 按关键词、时间范围、资讯类型筛选
    - 实现数据源健康追踪：连续3次失败标记为不可用并记录告警日志
    - _需求: 2.1, 2.2, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [~] 6.2 实现资讯数据解析器（skills/news_parser.py）
    - 实现 parse_json 解析JSON格式资讯
    - 实现 parse_html 解析HTML格式资讯
    - 实现 format_news_item 格式化输出
    - 实现 parse_formatted_text 从格式化文本解析回NewsItem
    - 格式不正确时返回包含错误位置和原因的ParseError
    - _需求: 8.1, 8.2, 8.3, 8.4_

  - [ ]* 6.3 编写News_Skill属性测试
    - **Property 5: 多源并行采集覆盖所有数据源** — 任意数量数据源都应被调用一次
    - **验证需求: 2.2**
    - **Property 7: 资讯关键词自动提取** — 包含行业/公司信息的资讯提取关键词应非空
    - **验证需求: 2.4**
    - **Property 8: 资讯去重与排序** — 去重后无重复项且按发布时间倒序
    - **验证需求: 2.5**
    - **Property 9: 资讯筛选结果一致性** — 返回的资讯都满足筛选条件
    - **验证需求: 2.7**

  - [ ]* 6.4 编写资讯解析属性测试
    - **Property 24: 资讯数据解析有效性** — 有效JSON/HTML解析后产生字段完整的NewsItem
    - **验证需求: 8.1**
    - **Property 25: NewsItem格式化往返一致性** — 格式化后再解析应等价
    - **验证需求: 8.3**
    - **Property 26: 解析错误信息描述性** — 格式不正确的输入返回包含位置和原因的错误
    - **验证需求: 8.4**

  - [ ]* 6.5 编写News_Skill单元测试
    - 测试从至少3个数据源采集资讯（需求2.1）
    - 测试数据源连续3次失败后标记为不可用（需求2.6）
    - 测试已知JSON和HTML格式的解析（需求8.1）
    - _需求: 2.1, 2.6, 8.1_

- [ ] 7. 实现Quote_Skill（行情获取技能）
  - [~] 7.1 实现Quote_Skill核心逻辑（skills/quote_skill.py）
    - 实现 QuoteSkill 继承 BaseSkill
    - 实现 fetch_all_quotes 获取全市场行情
    - 实现 filter_quotes 按股票代码、名称、板块筛选
    - 实现 get_ranking 获取涨幅榜、跌幅榜、成交额排行榜（前50）
    - 实现内存缓存：get_cached_quotes、update_cache、is_cache_expired（可配置TTL，默认10秒）
    - 实现 is_trading_hours 交易时段判断（9:30-11:30, 13:00-15:00）
    - 异常数据跳过并记录错误日志
    - _需求: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 6.6, 6.7_

  - [ ]* 7.2 编写Quote_Skill属性测试
    - **Property 11: 行情筛选结果一致性** — 返回的StockQuote都满足筛选条件
    - **验证需求: 3.4**
    - **Property 12: 排行榜正确排序与长度限制** — 按对应指标排序且不超过50条
    - **验证需求: 3.5**
    - **Property 20: 行情缓存读写一致性** — 更新缓存后立即读取应返回相同数据
    - **验证需求: 6.6**

  - [ ]* 7.3 编写Quote_Skill单元测试
    - 测试缓存过期后标记为过期状态（需求6.7）
    - 测试Quote_Source返回异常数据时跳过并继续处理（需求3.6）
    - _需求: 3.6, 6.7_

- [~] 8. 检查点 - 确保News_Skill和Quote_Skill测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [ ] 9. 实现Impact_Skill（影响分析技能）
  - [~] 9.1 实现Impact_Skill核心逻辑（skills/impact_skill.py）
    - 实现 ImpactSkill 继承 BaseSkill
    - 实现 analyze_impact 分析资讯对股票的影响，生成ImpactReport
    - 实现 match_stocks 通过关键词标签与股票名称/行业关联匹配
    - 实现 query_reports 按影响方向和影响程度筛选历史报告
    - 无法关联任何股票时标记为"无直接关联"并记录日志
    - _需求: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 9.2 编写Impact_Skill属性测试
    - **Property 13: 影响分析报告完整性** — ImpactReport包含所有必要字段和引用
    - **验证需求: 4.2, 4.4**
    - **Property 14: 关键词与股票关联匹配正确性** — 匹配结果中股票与关键词存在关联
    - **验证需求: 4.3**
    - **Property 15: 影响报告筛选结果一致性** — 返回的报告满足筛选条件
    - **验证需求: 4.5**

  - [ ]* 9.3 编写Impact_Skill单元测试
    - 测试资讯无法关联任何股票时标记为"无直接关联"（需求4.6）
    - _需求: 4.6_

- [ ] 10. 实现Review_Skill（复盘总结技能）
  - [~] 10.1 实现Review_Skill核心逻辑（skills/review_skill.py）
    - 实现 ReviewSkill 继承 BaseSkill
    - 实现 generate_daily_review 生成日度复盘报告
    - 实现 generate_weekly_review 和 generate_monthly_review 生成周度/月度报告
    - 实现 export_markdown 导出Markdown格式
    - 报告包含：大盘指数表现、板块涨跌排名、涨跌停统计、成交额对比、热点事件、市场情绪、趋势总结
    - _需求: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [ ]* 10.2 编写Review_Skill属性测试
    - **Property 16: 复盘报告内容完整性** — ReviewReport包含所有必要内容板块
    - **验证需求: 5.2, 5.3, 5.4, 5.7**
    - **Property 17: 周度/月度复盘报告时间跨度正确性** — 起止日期覆盖请求的完整时间范围
    - **验证需求: 5.5**
    - **Property 18: 复盘报告Markdown导出完整性** — Markdown包含所有关键信息
    - **验证需求: 5.6**

- [~] 11. 检查点 - 确保Impact_Skill和Review_Skill测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [ ] 12. 实现Finance_Agent核心调度器
  - [~] 12.1 实现Finance_Agent（agent.py）
    - 实现 FinanceAgent 类，初始化时加载配置、创建数据库、注册所有Skill
    - 实现 handle_request 处理用户自然语言请求
    - 实现 parse_intent 意图解析（识别资讯查询、行情查询、影响分析、复盘总结等意图）
    - 实现 execute_plan 按编排计划执行多Skill（支持串行和并行）
    - 实现 health_check 健康检查接口
    - Skill执行失败时返回包含Skill名称和错误原因的错误信息
    - 系统重启时从数据库加载已有数据并恢复运行状态
    - _需求: 1.1, 1.2, 1.5, 1.6, 6.5, 7.5_

  - [ ]* 12.2 编写Finance_Agent属性测试
    - **Property 1: 意图解析正确调度Skill** — 已知意图类型应调度到正确的Skill
    - **验证需求: 1.2**
    - **Property 3: 多Skill编排执行完整性** — 执行计划中所有Skill都被执行且结果完整
    - **验证需求: 1.5**
    - **Property 4: Skill失败错误信息完整性** — 错误信息包含Skill名称和错误原因
    - **验证需求: 1.6**
    - **Property 23: 健康检查覆盖所有组件** — 健康检查包含所有Skill和数据源状态
    - **验证需求: 7.5**

  - [ ]* 12.3 编写Finance_Agent单元测试
    - 测试配置文件格式不正确时输出错误信息并终止启动（需求7.3）
    - 测试日志级别配置生效（需求7.4）
    - _需求: 7.3, 7.4_

- [ ] 13. 集成与端到端连接
  - [~] 13.1 连接所有组件并实现入口模块（main.py）
    - 创建应用入口，初始化FinanceAgent并启动
    - 连接所有Skill到Registry
    - 实现命令行交互接口
    - _需求: 1.1, 1.4_

  - [ ]* 13.2 编写集成测试
    - 测试完整流程：请求 → 意图解析 → Skill调度 → 返回结果
    - 测试多Skill编排执行的端到端流程
    - _需求: 1.2, 1.5_

- [~] 14. 最终检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请向用户确认。

## 备注

- 标记 `*` 的子任务为可选任务，可跳过以加快MVP进度
- 每个任务引用了具体的需求编号以确保可追溯性
- 检查点任务确保增量验证
- 属性测试验证通用正确性属性（使用hypothesis），单元测试验证具体示例和边界情况（使用pytest）
