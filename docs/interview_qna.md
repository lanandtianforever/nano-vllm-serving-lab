# 面试问题合集

这个文件专门用于面试准备。回答必须贴合当前项目真实情况：Mac + LM Studio 的结果是黑盒 serving baseline，scheduler 部分是受控模拟实验，不能把它们包装成生产级 vLLM 优化结果。

## 项目定位

### Q1：这个项目会不会太 toy？

建议回答：

这个项目里确实有一个轻量 simulator，但我不会把它说成生产级推理引擎。它的作用是把 LLM Serving 里的几个核心 trade-off 隔离出来观察，比如 prefill/decode 干扰、tail latency、chunked prefill、prefix cache reuse 和 goodput。项目不是只停留在 toy simulator：前面有 MacBook Air M5 + LM Studio 的真实流式 API 黑盒测量，后面会对齐 vLLM 的 benchmark、prefix caching、chunked prefill 等真实工程设计，并尝试提交小 PR。我的定位是“用最小实验场理解生产推理框架中的问题”，而不是宣称自己重写了 vLLM。

### Q2：一句话介绍这个项目？

建议回答：

我先用 MacBook Air M5 + LM Studio 搭建本地 LLM Serving 黑盒基线，测 TTFT、TPOT、E2E latency 和 tail latency；再基于 nano-vLLM 思路构建轻量 scheduler 实验框架，研究 prefill/decode 调度、KV cache 和 prefix cache 对推理服务质量的影响。

### Q3：这个项目最安全的简历表述是什么？

建议回答：

可以写“围绕 LLM Serving 的 benchmark、scheduler、KV cache 和 tail latency 做实验分析”，不要写“深度优化 vLLM 内核”或“显著提升 vLLM 性能”。当前安全表述是：我实现了本地 serving benchmark client，构建了 FCFS / decode-priority 等调度实验框架，并用实验分析并发、上下文长度、输出长度对 TTFT、TPOT 和 E2E latency 的影响。

### Q4：哪些话现在不能说？

建议回答：

现在不能说我优化了 vLLM 生产性能，不能说我实现了 PagedAttention，不能说我写了 CUDA/Triton kernel，也不能说我测了真实 GPU vLLM throughput。当前 Mac 本地实验是 LM Studio / MLX 黑盒结果，scheduler 部分是 simulator 结果。

## 本地 Serving 基线

### Q5：为什么用 LM Studio + Mac，而不是直接用 vLLM？

建议回答：

Mac 本地实验只是第一层 baseline，目的是练 serving benchmark 的基本能力：怎么记录 request start、first token、finish time，怎么计算 TTFT、TPOT、E2E latency，怎么观察并发压力。它不用于证明 vLLM 性能。真正对齐 vLLM 的部分，会通过阅读 vLLM benchmark、prefix caching、chunked prefill 相关设计，并提交小 PR 来完成。

### Q6：Day 2 并发实验说明了什么？

建议回答：

我用 `qwen/qwen3-8b` 在 MacBook Air M5 + LM Studio 上跑了 concurrency 1、2、4、8，每档 10 个请求，错误数为 0。结果里 E2E latency 从 concurrency 1 的约 5.57s 上升到 concurrency 8 的约 16.26s；chunk-level TPOT 从约 0.041s 上升到约 0.119s。这个说明本地 serving stack 在并发升高时出现明显压力，尤其 decode 阶段和排队效应会影响用户体验。

### Q7：为什么要让本地请求绕过系统代理？

建议回答：

我机器上设置了 HTTP/HTTPS 代理。一开始 LM Studio server 没启动时，localhost 请求返回了代理的 `502 Bad Gateway`，这会干扰实验诊断。后来我在 client 里用空的 `ProxyHandler` 绕过系统代理，确保 `127.0.0.1:1234` 的 benchmark 流量直接打到本地 LM Studio。

### Q8：Day 3 上下文实验说明了什么？

建议回答：

我跑了 context label 1024、2048、4096、8192，每档 5 个请求，错误数为 0。从 1024 到 4096，平均 TTFT 从约 0.61s 增加到约 3.20s，符合长 prompt 增加 prefill 压力的直觉。8192 这一行要谨慎解释，因为为了避免超过 LM Studio context window，我把 prompt cap 到约 2926 words，所以它是“高上下文本地基线点”，不是严格的 8192 tokenizer token 测量。

### Q9：为什么原始 8192 prompt 会失败？

建议回答：

原始 prompt 大约 3712 个英文词，但 word count 不等于 tokenizer token count。经过 tokenizer 展开后，LM Studio 报错说 prompt 需要保留的 token 数超过加载模型的 context length。这个点反而很有价值，因为它说明做 serving benchmark 时必须区分配置 label、词数估算和真实 tokenizer token 长度。

### Q10：Day 4 输出长度实验说明了什么？

建议回答：

我换了长输出 prompt，让模型尽量生成到 API 的 `max_tokens` 上限。128、256、512 档平均输出 chunks 分别约 124、251、501，说明 prompt 起效了。E2E latency 从 128 档约 5.01s 增加到 256 档约 9.94s，再到 512 档约 24.54s；而 TTFT 基本稳定。这符合推理过程的直觉：prompt 固定时，长输出主要增加 decode step 数量，所以主要拉长 E2E latency。

### Q11：Day 4 有一条 error，怎么解释？

建议回答：

64 档有 1 条 LM Studio error，它在生成 62 个 chunks 后返回非空错误。我在 summary 里把它计入 Errors，但把 error row 从 latency 和 throughput 均值里排除了。面试里我会主动说明这一点，因为生产 benchmark 里成功请求指标和错误率应该分开记录。

### Q12：`output_tokens` 是真实 token 数吗？

建议回答：

现在还不是。当前 client 统计的是 streaming response 里非空 content chunk 数，我在精确表述时会叫它 output chunks。它能用于 chunk-level TPOT 和趋势分析，但不是 tokenizer-accurate token count。后续改进是接入模型 tokenizer，补充真实 prompt tokens 和 output tokens。

## 指标与实验设计

### Q13：TTFT 怎么算？

建议回答：

TTFT = `first_token_time - arrival_time`。在我的 client 里，`arrival_time` 是发送 HTTP 请求前记录的时间，`first_token_time` 是收到第一个带内容的 streaming chunk 时记录的时间。

### Q14：TPOT 怎么算？

建议回答：

当前 TPOT = `(finish_time - first_token_time) / (output_chunks - 1)`。因为目前统计的是 streaming chunks，不是 tokenizer tokens，所以更准确地说是 chunk-level TPOT。概念上对应 token-level TPOT，但绝对数值要谨慎解释。

### Q15：为什么看 P95/P99，不只看平均 latency？

建议回答：

LLM Serving 是面向用户体验和 SLO 的服务，平均值会掩盖少数很慢的请求。并发、长 prompt、排队都会让一部分请求明显变慢，所以 P95/P99 更能反映服务质量和线上风险。

### Q16：为什么要把 error 单独统计？

建议回答：

如果把失败请求混进成功请求 latency 均值，会让结果很难解释。生产 benchmark 通常要同时报告成功请求的 latency 分布和错误率。我的 Day 4 summary 就是这样处理的：错误数单独列出，latency/throughput 均值只基于无错误行。

## 推理系统基础

### Q17：prefill 和 decode 有什么区别？

建议回答：

prefill 是处理输入 prompt，建立初始 KV cache，主要影响 TTFT，尤其长上下文时很明显。decode 是自回归生成，每一步生成下一个 token，主要影响 TPOT、ITL 和长输出下的 E2E latency。

### Q18：为什么长上下文主要影响 TTFT？

建议回答：

因为第一个输出 token 之前，系统必须先处理完整 prompt 并填充 KV cache。prompt 越长，prefill 工作越多，所以 TTFT 往往会增加。

### Q19：为什么长输出主要影响 E2E？

建议回答：

在 prefill 完成后，模型需要一步一步 decode。输出越长，decode step 越多，所以 E2E latency 会增长。我的 Day 4 实验也支持这个现象：TTFT 基本稳定，但 E2E 随 `max_tokens` 增长明显增加。

### Q20：什么是 KV cache？

建议回答：

KV cache 缓存历史 token 的 key/value 张量，让模型在 decode 时不用每一步都重新计算完整历史。它提升 decode 效率，但会消耗显存，消耗量和活跃序列数量、上下文长度、batch size 等有关。

### Q21：什么是 prefix caching？

建议回答：

prefix caching 是复用共享 prompt 前缀的 KV cache，比如相同 system prompt、RAG 文档、tool schema 或代码上下文。它主要减少重复 prefill 计算，但不能消除后续新生成 token 的 decode 成本。

### Q22：prefix caching 什么时候收益不明显？

建议回答：

当请求之间没有共享 prefix、共享 prefix 很短、decode 阶段占主导，或者 cache 命中率很低时，prefix caching 收益会有限。有时调度和 cache 管理还会带来额外开销。

## Scheduler 实验

### Q23：当前 scheduler simulator 模拟了什么？

建议回答：

当前 simulator 模拟 request arrival、简化状态、prefill cost、decode cost、FCFS、decode-priority 和请求级 summary metrics。它足够用于理解调度 trade-off，但还没有模拟完整 vLLM batching、PagedAttention、真实 KV block allocator 或 CUDA 执行。

### Q24：decode-priority 想解决什么问题？

建议回答：

decode-priority 想避免正在交互式生成的请求被长 prefill 阻塞。它优先调度已经进入 decode 的请求，让输出更连续。但代价是 waiting prefill 的请求，尤其长 prompt 请求，TTFT 可能变差。

### Q25：chunked prefill 的 trade-off 是什么？

建议回答：

chunked prefill 把长 prompt 的 prefill 拆成多个小块，方便在块之间插入 decode 工作。如果 chunk 太大，还是会阻塞 decode；如果 chunk 太小，调度开销增加，硬件利用率可能下降。合适的 chunk size 取决于模型、硬件、prompt 分布和请求到达率。

## vLLM 开源贡献

### Q26：vLLM PR 和这个项目怎么结合？

建议回答：

我会先从小而可 review 的 PR 切入，比如 benchmark 示例、prefix caching 文档、chunked prefill 说明、错误信息或测试。这和项目是对齐的，因为推理优化首先要能设计 workload、理解指标、解释 benchmark 结果。除非我真的合并了 core 相关改动并做了验证，否则不会说自己优化了 vLLM core。

### Q27：如果 PR 只是文档，有意义吗？

建议回答：

有意义，但要看内容。如果只是 typo，价值有限；但如果是围绕 prefix caching、chunked prefill、benchmark sweep、SLO/goodput 这些真实推理系统概念补充说明或示例，就能体现我读懂了生产项目的设计，并能把复杂概念写清楚。当然简历里必须诚实写成文档或 benchmark 贡献，不能包装成核心性能优化。

## Day 5 文档整理

### Q28：为什么要单独写 local serving baseline 文档？

建议回答：

因为本地实验不是项目主线，但它是后续 scheduler 实验的指标基础。单独写文档可以把实验环境、命令、结果、解释和限制说清楚，避免面试时把 Mac + LM Studio 的黑盒结果误讲成 vLLM 性能结果。

### Q29：这三组本地实验和后续推理优化有什么关系？

建议回答：

并发实验让我观察 serving stack 在并发下的排队和 decode 压力；上下文实验对应 prefill/TTFT；输出长度实验对应 decode/E2E。后续做 scheduler、chunked prefill、prefix-aware scheduling 时，仍然会围绕这些指标来判断策略是否真的改善了 serving quality。

## Day 6 图表解释

### Q30：为什么要把实验结果画成图，而不是只放表格？

建议回答：

表格适合精确查数，图更适合展示趋势。面试时我更需要快速说明“并发升高后 E2E/TPOT 变差”“上下文变长后 TTFT 上升”“输出变长后 E2E 上升”这三条主线。图表能让面试官一眼看到趋势，再回到表格查具体数值。

### Q31：为什么并发图和输出长度图要分成上下两个面板？

建议回答：

因为 E2E latency 通常是几秒到几十秒，而 TPOT 是几十毫秒级。如果放在同一个 y 轴上，TPOT 曲线会被压在底部，看不出变化。分成上下两个面板后，既能保留同一个 x 轴，也能分别观察 E2E 和 TPOT 的趋势。

### Q32：context sweep 图里为什么用 prompt words 作为 x 轴，而不是 context label？

建议回答：

因为这组实验里我已经发现 context label、word count 和真实 tokenizer token length 不是一回事。用平均 prompt words 作为 x 轴，比直接用 1024/2048/4096/8192 label 更诚实。下一步如果接入 tokenizer，就应该把 x 轴换成真实 prompt tokens。

### Q33：图表最容易被追问的风险是什么？

建议回答：

最大的风险是把 Mac + LM Studio 的黑盒趋势讲成 vLLM 或 GPU 内核结论。所以我会明确说：这些图只说明本地 serving baseline 的趋势，用来建立指标和现象直觉；后续白盒 scheduler 实验和 vLLM PR 才是和推理框架更直接相关的部分。

## Day 7 第一周总结

### Q34：第一周你到底完成了什么？

建议回答：

第一周我把本地 serving baseline 做成了一个可复现实验层：实现了 streaming benchmark client，修复了 localhost 代理污染问题，跑了并发、上下文长度、输出长度三组实验，保存了 raw JSONL、summary 和 SVG 图表，并写了正式的 local baseline report。这个阶段的重点不是优化，而是建立可靠的指标体系和实验叙事。

### Q35：第一周成果和“推理优化”有什么关系？

建议回答：

推理优化不能只说“更快”，必须先知道怎么定义和观测“快”。第一周我围绕 TTFT、TPOT、E2E、P95/P99、错误率建立了指标基础。并发实验对应 serving pressure，长上下文实验对应 prefill/TTFT，长输出实验对应 decode/E2E。这些会成为后续 scheduler、chunked prefill、prefix-aware scheduling 的评价标准。

### Q36：为什么 README 里要主动写 limitations？

建议回答：

因为这个项目很容易被误解成“我在 Mac 上测了 vLLM 性能”。主动写 limitations 可以防止过度包装：本地 baseline 不是 vLLM benchmark，`output_tokens` 目前是 streaming chunks，prompt length 是 word count，不是 tokenizer tokens。这样反而更可信，也能体现 benchmark 意识。

### Q37：Week 2 准备怎么做？

建议回答：

Week 2 会从本地测量切到 vLLM 对齐：先读 vLLM contribution docs 和 benchmark sweep 文档，再读 prefix caching、chunked prefill 相关设计，找一个小而可 review 的 PR 切口，比如 benchmark 示例、prefix caching 文档、错误信息或测试。同时继续把自己的 scheduler lab 往 chunked prefill 和 prefix-aware scheduling 扩展。
