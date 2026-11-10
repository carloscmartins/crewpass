# Arena.ai programming and coding rankings (accessed 2026-11-06)

## Is there a distinct Code Arena / coding leaderboard, and what does it measure?

### Takeaway
Yes. Arena's dedicated coding destination is Code Arena, whose main board is **WebDev** (`https://arena.ai/leaderboard/code/webdev`). It ranks human preferences between generated, runnable web applications; this is not a pass-rate benchmark of arbitrary software-engineering tasks. Arena also has a separate **Coding** category under Text Arena (`https://arena.ai/leaderboard/text/coding`), which should be read as a distinct board, not as a synonym for WebDev.

### Cited Findings
- Arena's Code navigation exposes WebDev and Image-to-WebDev boards; the current WebDev URL is `https://arena.ai/leaderboard/code/webdev`, and Image-to-WebDev is `https://arena.ai/leaderboard/code/image-to-webdev`. The Arena landing/leaderboard pages describe WebDev as front-end development with multi-step reasoning/tool use, and Image-to-WebDev as website generation from images/screenshots — [Arena Code leaderboard](https://arena.ai/leaderboard/code), [Arena WebDev](https://arena.ai/leaderboard/code/webdev), [Arena Image-to-WebDev](https://arena.ai/leaderboard/code/image-to-webdev). (Accessed 2026-11-06.)
- Arena's official 2025 Code Arena description says users submit a task; two models build apps in the controlled environment; users inspect rendered results and vote pairwise. Votes assess functionality, usability, fidelity, design, taste, and aesthetics. The platform logs model version, latency, and environment — [The Next Stage of AI Coding Evaluation Is Here](https://arena.ai/blog/code-arena). (Accessed 2026-11-06.)
- The WebDev leaderboard's displayed **Arena Score** is a relative rating derived from head-to-head preferences, not a percentage/pass rate; Arena's FAQ identifies Bradley–Terry as the standard aggregation method — [Arena FAQ](https://arena.ai/faq), [BenchLeader: Arena WebDev](https://www.benchleader.com/benchmarks/lmarena_webdev). (Accessed 2026-11-06.)
- Arena's official Code Arena launch article explicitly says the rebuilt WebDev V2 board starts with a fresh dataset and does not merge/retrofit WebDev Legacy results — [The Next Stage of AI Coding Evaluation Is Here](https://arena.ai/blog/code-arena). (Accessed 2026-11-06.)
- Arena separately exposes `Text Arena > Coding` at `https://arena.ai/leaderboard/text/coding`. Epoch AI describes it as pairwise human preference for website-producing prompts, using a standardized standalone React component in TypeScript with Tailwind; some outputs are normalized by GPT-4.1-mini and run in a Linux sandbox — [Arena Text Coding leaderboard](https://arena.ai/leaderboard/text/coding), [Epoch AI: Text Arena (Coding)](https://epoch.ai/benchmarks/webdev-arena). (Accessed 2026-11-06.)
- Arena FAQ says its standard blind battle votes are aggregated using a Bradley–Terry rating system (described as Elo-like), not a fixed pass/fail task suite — [Arena FAQ](https://arena.ai/faq). (Accessed 2026-11-06.)
- The official leaderboard changelog documents the current WebDev segmentation: Fullstack and Frontend, with HTML and React technology views; it states that HTML represents standalone HTML/CSS/JS within one document and React represents multi-file applications with components, routing, state, and cross-file consistency. The changelog says the Fullstack board went live July 28, 2026 — [Arena leaderboard changelog](https://arena.ai/company/leaderboard-changelog). (Accessed 2026-11-06.)

### Inferences
- “Code Arena” is the Arena product/leaderboard family; “WebDev” is the most prominent all-model coding ranking within it. It is misleading to say Arena has a single generic software-engineering coding leaderboard: its boards exercise different task formats and populations.
- The Text Arena Coding category overlaps conceptually with web generation (Epoch's prompt description is React/TypeScript/Tailwind), but is a distinct Arena board and score series. Its board score must not be combined with WebDev scores.

### Gaps
- Direct requests to the live WebDev and Text Coding pages were blocked by Arena's Cloudflare challenge in this research environment. The exact ranked snapshots below are cross-checked against Arena's official changelog and official leaderboard dataset references, with contemporaneous mirrors used for the rows and vote counts.

## What were the top 10 entries, scores/uncertainty, and update date?

### Takeaway
The latest WebDev snapshot located for this report is dated **2026-10-28** (Arena’s page/search index has also exposed the page date as Oct. 27, one day earlier). Claude Opus 5.5 (Max) leads WebDev at 1810; GPT-6 Astra (Max) is second at 1773. The official Arena changelog records Gemini 4 Carbon's addition to Code Arena: WebDev on Oct. 28. For Text Arena Coding, the latest available source snapshot is also dated Oct. 28 and has Gemini 4 Carbon (High) first at 1573.

### Cited Findings
- Arena changelog: Gemini 4 Carbon (High) was added to Code Arena: WebDev and Text Arena on Oct. 28; GPT-6.1 Terra (Max) was added to WebDev Oct. 27 — [Arena leaderboard changelog](https://arena.ai/company/leaderboard-changelog). The official Arena leaderboard dataset announcement says `webdev` has `latest` and `full` splits and a publish-date field — [Arena Leaderboard Dataset](https://arena.ai/blog/arena-leaderboard-dataset). (Accessed 2026-11-06.)
- Arena's WebDev page has been indexed with the displayed date Oct. 27, 2026, 952,039 total votes and 153 models. A contemporaneous daily snapshot source describes the board as published Oct. 28, 2026. This is a one-day page-date/snapshot-date discrepancy; treat Oct. 28 as the dataset publication date and note that the Arena UI/index also displayed Oct. 27 — [Arena WebDev leaderboard](https://arena.ai/leaderboard/code/webdev), [What Is the Latest? Arena board snapshots](https://whatisthelatest.ai/leaderboards), [Arena changelog](https://arena.ai/company/leaderboard-changelog). (Accessed 2026-11-06.)
- The 2026-10-28 WebDev top ten, with Arena scores rounded as displayed, 95% score CI half-width, and model battle count:

| Rank | Model configuration | Score | 95% CI (±) | Votes |
|---:|---|---:|---:|---:|
| 1 | Claude Opus 5.5 (Max) | 1810 | 13 | 3,473 |
| 2 | GPT-6 Astra (Max) | 1773 | 10 | 7,210 |
| 3 | Claude Sonnet 5.5 (xHigh) | 1770 | 11 | 4,469 |
| 4 | Gemini 4 Carbon (High) | 1768 | 15* | 2,230 |
| 5 | GPT-6.1 Sol (Max) | 1751 | 11 | 4,092 |
| 6 | Claude Fable 5.1 (Max) | 1746 | 9 | 8,614 |
| 7 | Muse Wonder Full (Max) | 1725 | 14 | 2,248 |
| 8 | Claude Sonnet 5.5 (High) | 1711 | 9 | 6,371 |
| 9 | Kimi K3.1 Pro (Max) | 1695 | 13* | 2,671 |
| 10 | Claude Opus 5 (Max) | 1691 | 6 | 19,641 |

  `*` Preliminary in the mirrored source. These are the WebDev rows, not the Text Arena Coding rows — [PandaSi Arena coding leaderboard](https://pandasi.ai/leaderboard/code), [What Is the Latest? Oct. 28 Arena snapshot](https://whatisthelatest.ai/leaderboards), and the official [Arena WebDev board](https://arena.ai/leaderboard/code/webdev). The listed WebDev snapshot dates to Oct. 28; PandaSi's page was updated Nov. 6. (Accessed 2026-11-06.)
- On Text Arena Coding, the Oct. 28 snapshot's top 10 are: (1) Gemini 4 Carbon (High), 1573; (2) Claude Opus 4.7 (High), 1551; (3) Claude Opus 5.5 (High), 1551; (4) Claude Fable 5 (High), 1550; (5) Gemini 4 Argon (High), 1550; (6) Claude Opus 4.6 (High), 1548; (7) Claude Opus 4.6, 1546; (8) Claude Opus 4.7, 1546; (9) Muse Wonder (Max), 1545; (10) Muse Spark 1.2 (xHigh), 1543 — [BenchLeader Arena Coding snapshot](https://www.benchleader.com/benchmarks/lmarena_text_coding). Scores are Arena scores, not accuracy percentages. BenchLeader labels this as Text Arena coding prompts, data published Oct. 28; its page states data as of Nov. 6. (Accessed 2026-11-06.)
- Arena says rank spread communicates the plausible best-to-worst rank from confidence interval overlap; it assigns a unique raw rank even when uncertainty ranges overlap. The current ranking-method article explains how these spreads should be read — [Arena's Ranking Method](https://arena.ai/blog/ranking-method). The help page defines the ± score value as confidence interval and “Votes” as comparison count — [Arena Help: How to see AI rankings](https://help.arena.ai/articles/7011479247-how-to-see-ai-rankings-in-arena-leaderboards-2-0-wip). (Accessed 2026-11-06.)

### Inferences
- The WebDev leader's raw score is 37 points above #2, and their displayed ± intervals do not overlap in the Oct. 28 snapshot; among the remaining first-four rows, Carbon and Sonnet are only 2 points apart and have overlapping uncertainty intervals. Do not treat the numbered ranks as certainty-equivalent distinctions.
- Carbon was a young, explicitly preliminary entry (2,230 votes and ±15) versus Claude Opus 5 (Max)'s 19,641 votes and ±6. This makes uncertainty and evidence volume material to any recommendation.

### Gaps
- We did not recover a primary-source, machine-readable export of every Oct. 28 Text Coding row or its confidence intervals directly from the blocked live page. The top-ten scores above are sourced to a dated secondary snapshot; a current official Text Coding table may have refreshed since Oct. 28.
- Rank spread for each WebDev top-ten row is omitted because the snapshot mirror used for CI/vote counts does not expose that column consistently. Arena's own guide defines the field and the official UI/search index showed it on older WebDev snapshots.

## Which categories best represent day-to-day software engineering, and what are the limitations for OpenCode recommendations?

### Takeaway
Of Arena's categories, **Fullstack** is the closest proxy for end-to-end application-building; **React** is the closest for structured multi-file frontend development. For a general software-engineering / OpenCode choice, neither WebDev nor Text Coding alone is representative of repository maintenance, tests, CLI workflows, backend systems, or coding-agent task completion. Use the scores as preference evidence and a shortlist signal, then compare the exact available model/configuration on the user's own tasks.

### Cited Findings
- Arena introduced Fullstack capabilities with databases, authentication, third-party APIs, persistent data, bash/web search, and Vercel deployment. Its own description frames the board as extending the earlier frontend prototyping setup to real end-to-end app building — [Build, Deploy, and Evaluate with Fullstack Code Arena](https://arena.ai/blog/fullstack-code-arena). (Accessed 2026-11-06.)
- Arena's official changelog distinguishes HTML document generation from multi-file React applications, including components, routing, state coordination, and consistency across files; WebDev also has Frontend and Fullstack views and seven intent/domain categories — [Arena leaderboard changelog](https://arena.ai/company/leaderboard-changelog), [New Categories for Web Development in Code Arena](https://arena.ai/blog/new-categories-code-arena). (Accessed 2026-11-06.)
- The Text Coding leaderboard is a preference score on coding prompts. The Oct. 28 leaderboard's top model, Gemini 4 Carbon, has a 95% CI of 1555–1591 (±18, preliminary), while Claude Opus 4.7 High is 1545–1557 (±6) and Claude Opus 5.5 High is 1539–1563 (±12) — [Arena Coding snapshot, per-model score/CI](https://www.aitntnews.com/arena/text/coding/), [BenchLeader Arena Coding, as of Nov. 6](https://www.benchleader.com/benchmarks/lmarena_text_coding). A separate Arena/ModelCap capture reports Carbon as preliminary at 1573 and confirms overlapping top score intervals — [ModelCap Arena Coding](https://modelcap.ai/benchmarks/arena-coding). (Accessed 2026-11-06.)
- Arena FAQ explains that only votes while identities are anonymous count toward public rankings, and that codenamed variants can be provider test versions; names enter the public board according to provider release/policy. This makes board configuration labels important — [Arena FAQ](https://arena.ai/faq). (Accessed 2026-11-06.)
- Arena's rank spread and CI guidance, and its warning that the rank is a statistical estimate, are in its method/help materials — [Arena's Ranking Method](https://arena.ai/blog/ranking-method), [Arena Help: leaderboard rankings](https://help.arena.ai/articles/7011479247-how-to-see-ai-rankings-in-arena-leaderboards-2-0-wip). (Accessed 2026-11-06.)
- Arena's own rebuilt Code Arena article emphasizes that results are preference judgments on rendered apps, with functionality/usability/fidelity considered, rather than conventional static test-suite correctness. The task is web-app-specific and the voter judges the complete artifact — [The Next Stage of AI Coding Evaluation Is Here](https://arena.ai/blog/code-arena). Epoch's description gives the standardized React/TypeScript/Tailwind prompt for the separate Text Coding dataset — [Epoch AI methodology](https://epoch.ai/benchmarks/webdev-arena). (Accessed 2026-11-06.)
- For an independent example of why a coding-task success metric differs from Arena preference, Arena's official help describes its non-pairwise Agent Arena as using real sessions and task outcome/satisfaction/steerability signals, not the ordinary Bradley–Terry battle metric — [Arena Agent Mode help](https://help.arena.ai/articles/5432423882-how-to-use-agent-mode). (Accessed 2026-11-06.)

### Inferences
- If selecting one Arena slice for day-to-day software work, choose Fullstack for end-to-end app workflows; React for multi-file frontend. This is a task-fit inference, not Arena's claim that those boards validate general software engineering.
- Rankings describe the tested model variant and effort/configuration (e.g., Max, High, xHigh), not a provider family in the abstract. An OpenCode provider/model alias, backend serving snapshot, reasoning effort, system prompt, and tools may not match Arena's evaluated configuration. Confirm model ID/configuration and run a small task suite with the actual OpenCode setup.
- A human preference vote can reward a more attractive, clearer, more complete first-render result without establishing maintainability, security, correctness under hidden tests, or success on an existing repository. Use a task-success benchmark such as SWE-bench/Terminal-Bench as an additional lens when relevant; neither can simply be substituted for the other.
- Sample size is model-specific, not just the board's headline total. New/preliminary entries and smaller-category slices can have wider CIs; when score intervals/rank spreads overlap, describe the models as statistically unresolved rather than asserting a reliable ordering.
- A high Arena rank does not by itself make a model selectable in OpenCode: availability, account access, exact provider identifier, price, latency, context/output limits, and licensing remain separate checks.

### Gaps
- Arena does not publish a universal “best for day-to-day software engineering” category or guarantee that WebDev/Fullstack ordering transfers to work in arbitrary existing repositories. The recommendation is therefore an evidence-informed mapping, not a verified transfer result.
- Public sources do not establish that Arena's API/provider serving version, system prompt, reasoning budget, and tool environment exactly match every OpenCode model alias or user deployment. Validate the exact configuration locally before recommending a winner.
