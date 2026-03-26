# 需求文档

## 简介

本系统是一个财经智能Agent系统，包含以下核心能力：实时财经资讯采集与整理、A股全市场股价实时获取、基于资讯与行情数据的实时影响分析、以及市场复盘与总结。系统通过Agent架构组织各项能力为独立的Skill模块，支持灵活编排和扩展。

## 术语表

- **Finance_Agent**：财经智能Agent，系统的核心调度模块，负责协调各Skill完成财经信息获取、分析和总结任务
- **News_Skill**：资讯采集技能，负责从多个财经资讯源实时采集和整理财经新闻、公告、研报等信息
- **Quote_Skill**：行情获取技能，负责实时获取A股全市场股票价格及相关行情数据
- **Impact_Skill**：影响分析技能，负责将资讯信息与行情数据关联，生成实时的市场影响分析
- **Review_Skill**：复盘总结技能，负责对指定时间段的市场行情进行复盘分析和总结报告生成
- **News_Source**：资讯数据源，提供财经资讯的外部数据接口（如财经网站API、新闻聚合接口等）
- **Quote_Source**：行情数据源，提供A股实时行情数据的外部接口（如行情API、交易所数据接口等）
- **Skill_Registry**：技能注册中心，负责管理和调度所有已注册的Skill模块
- **News_Item**：单条资讯对象，包含标题、内容、来源、发布时间、关联标签等属性
- **Stock_Quote**：单只股票行情对象，包含股票代码、名称、当前价格、涨跌幅、成交量等属性
- **Impact_Report**：影响分析报告，包含受影响的股票列表、影响方向、影响程度评估和分析依据
- **Review_Report**：复盘总结报告，包含市场概况、板块表现、热点分析和趋势总结
- **User**：系统使用者，通过Agent接口获取财经信息和分析结果的用户

## 需求

### 需求 1：Agent核心调度

**用户故事：** 作为系统使用者，我希望通过一个统一的Agent入口来使用所有财经信息获取和分析能力，以便无需分别调用各个模块。

#### 验收标准

1. THE Finance_Agent SHALL 提供统一的对话式接口，支持User通过自然语言描述需求
2. WHEN User发送请求时，THE Finance_Agent SHALL 解析用户意图并调度对应的Skill执行任务
3. THE Skill_Registry SHALL 维护所有已注册Skill的元信息，包含Skill名称、描述、输入参数和输出格式
4. WHEN 新Skill注册到Skill_Registry时，THE Finance_Agent SHALL 在不修改核心调度代码的前提下识别并调用该Skill
5. THE Finance_Agent SHALL 支持在单次请求中编排多个Skill协同执行（如先获取资讯再进行影响分析）
6. WHEN Skill执行失败时，THE Finance_Agent SHALL 向User返回明确的错误信息，包含失败的Skill名称和错误原因


### 需求 2：实时财经资讯采集

**用户故事：** 作为系统使用者，我希望系统能实时采集各类财经资讯信息，以便我能及时了解市场动态。

#### 验收标准

1. THE News_Skill SHALL 支持从至少3个不同的News_Source采集财经资讯
2. WHEN 触发资讯采集任务时，THE News_Skill SHALL 从所有已配置的News_Source并行采集资讯
3. THE News_Skill SHALL 对每条采集到的News_Item记录标题、内容摘要、来源名称、发布时间和原文链接
4. WHEN 采集到新的News_Item时，THE News_Skill SHALL 自动提取关键词标签（如涉及的行业、公司名称、政策类型等）
5. THE News_Skill SHALL 对采集到的News_Item按发布时间倒序排列并去除重复内容
6. WHEN 某个News_Source连续3次采集失败时，THE News_Skill SHALL 记录告警日志并标记该数据源为不可用
7. THE News_Skill SHALL 支持按关键词、时间范围和资讯类型（新闻、公告、研报）进行资讯筛选查询
8. THE News_Skill SHALL 支持通过配置文件添加和管理News_Source，包含数据源URL、采集频率和认证信息

### 需求 3：A股全市场实时行情获取

**用户故事：** 作为系统使用者，我希望系统能实时获取A股全市场所有股票的价格数据，以便我能掌握市场整体行情。

#### 验收标准

1. THE Quote_Skill SHALL 支持获取沪深两市所有上市股票的实时行情数据
2. THE Quote_Skill SHALL 为每只股票提供Stock_Quote对象，包含股票代码、名称、当前价格、开盘价、最高价、最低价、涨跌额、涨跌幅、成交量和成交额
3. WHEN User请求全市场行情时，THE Quote_Skill SHALL 在30秒内返回全部股票的最新行情数据
4. THE Quote_Skill SHALL 支持按股票代码、名称或板块（主板、创业板、科创板、北交所）筛选行情数据
5. THE Quote_Skill SHALL 支持获取涨幅榜、跌幅榜和成交额排行榜，每个榜单返回前50只股票
6. WHEN Quote_Source返回的数据格式异常时，THE Quote_Skill SHALL 记录错误日志并跳过异常数据，继续处理其余数据
7. THE Quote_Skill SHALL 支持通过配置文件设置Quote_Source的接口地址和认证参数
8. WHILE 交易时段（9:30-11:30, 13:00-15:00）内，THE Quote_Skill SHALL 支持按可配置的时间间隔（默认每5秒）自动刷新行情数据

### 需求 4：实时影响分析

**用户故事：** 作为系统使用者，我希望系统能根据最新资讯自动分析对股票市场的影响，以便我能快速判断资讯的投资价值。

#### 验收标准

1. WHEN 新的News_Item被采集到时，THE Impact_Skill SHALL 分析该资讯对相关股票的潜在影响
2. THE Impact_Skill SHALL 生成Impact_Report，包含受影响的股票列表、影响方向（利好/利空/中性）、影响程度评估（高/中/低）和分析依据文本
3. THE Impact_Skill SHALL 通过News_Item中的关键词标签与Stock_Quote中的股票名称和行业进行关联匹配
4. WHEN 生成Impact_Report时，THE Impact_Skill SHALL 同时引用触发分析的News_Item和关联股票的当前Stock_Quote数据
5. THE Impact_Skill SHALL 支持按影响方向和影响程度筛选查询历史Impact_Report
6. IF News_Item中未能识别出任何关联股票，THEN THE Impact_Skill SHALL 将该资讯标记为"无直接关联"并记录到日志中

### 需求 5：市场复盘与总结

**用户故事：** 作为系统使用者，我希望系统能对市场进行复盘分析和总结，以便我能回顾和理解市场走势。

#### 验收标准

1. WHEN User请求市场复盘时，THE Review_Skill SHALL 生成指定日期的Review_Report
2. THE Review_Skill SHALL 在Review_Report中包含以下内容：大盘指数表现（上证指数、深证成指、创业板指）、各行业板块涨跌排名、当日涨停和跌停股票统计、成交额与前一交易日对比
3. THE Review_Skill SHALL 在Review_Report中包含当日热点事件总结，关联当日采集的高影响度News_Item
4. THE Review_Skill SHALL 在Review_Report中包含市场情绪分析，基于涨跌家数比、涨停跌停比和成交量变化进行判断
5. WHEN User请求周度或月度复盘时，THE Review_Skill SHALL 生成对应时间跨度的汇总Review_Report
6. THE Review_Skill SHALL 支持将Review_Report导出为Markdown格式的文本
7. THE Review_Skill SHALL 在Review_Report中提供趋势总结，基于近期行情数据描述市场运行趋势

### 需求 6：数据存储与缓存

**用户故事：** 作为系统运维人员，我希望系统的资讯和行情数据能持久化存储，以便支持历史查询和复盘分析。

#### 验收标准

1. THE News_Skill SHALL 将采集到的News_Item持久化存储到数据库
2. THE Quote_Skill SHALL 将获取到的Stock_Quote数据持久化存储到数据库，保留每个交易日的收盘行情快照
3. THE Impact_Skill SHALL 将生成的Impact_Report持久化存储到数据库
4. THE Review_Skill SHALL 将生成的Review_Report持久化存储到数据库
5. WHEN 系统重启时，THE Finance_Agent SHALL 从数据库加载已有数据并恢复运行状态
6. THE Quote_Skill SHALL 使用内存缓存存储最新一次获取的全市场行情数据，减少对Quote_Source的重复请求
7. WHILE 缓存中的行情数据存在时间超过可配置的过期时间（默认10秒）时，THE Quote_Skill SHALL 标记缓存为过期并在下次请求时重新获取数据

### 需求 7：系统配置与日志

**用户故事：** 作为系统运维人员，我希望能方便地配置系统参数和查看运行日志，以便管理和排查问题。

#### 验收标准

1. THE Finance_Agent SHALL 支持通过YAML配置文件设置所有可配置参数，包含各Skill的数据源配置、采集频率和缓存策略
2. THE Finance_Agent SHALL 记录结构化日志，包含每次Skill调用的输入参数、执行耗时和返回状态
3. IF 系统启动时配置文件格式不正确，THEN THE Finance_Agent SHALL 输出明确的配置错误信息并终止启动
4. THE Finance_Agent SHALL 支持通过配置文件设置日志级别（DEBUG/INFO/WARNING/ERROR）
5. THE Finance_Agent SHALL 提供健康检查接口，返回各Skill的运行状态和各数据源的连接状态

### 需求 8：资讯数据解析

**用户故事：** 作为开发人员，我希望系统能正确解析各种格式的资讯数据，以便统一处理来自不同数据源的信息。

#### 验收标准

1. THE News_Skill SHALL 支持解析JSON格式和HTML格式的资讯数据，将其转换为统一的News_Item对象
2. THE News_Skill SHALL 提供格式化输出功能，将News_Item对象转换为可读的文本格式
3. 对于所有有效的News_Item对象，解析后格式化再解析 SHALL 产生等价的News_Item对象（往返一致性）
4. WHEN 资讯数据格式不符合预期时，THE News_Skill SHALL 返回描述性的解析错误信息，包含错误位置和原因
