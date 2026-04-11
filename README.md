# Qinyang Li 李亲洋

**AI-Native Industry Researcher × Data-Driven Analyst**

Beijing Jiaotong University × Rochester Institute of Technology (Dual Degree, 2024–2028)  
Information Management & Information Systems

📧 liqinyang7211@gmail.com · 📞 +86 15251987211

---

## 🧠 Who I Am

I'm an undergraduate deeply invested in using **AI to transform industry research workflows**. I spend significant time and resources each month on AI tools — not as a novelty, but as my default working method. From day one of every project, I reach for LLMs, automation pipelines, and programmatic data collection before manual approaches.

My background sits at the intersection of **industry research**, **quantitative analysis**, and **AI-powered automation** — I've done primary research at Roland Berger for Huawei, built quant models at Guosheng Securities, and independently developed AI-driven tools for content analysis and data collection.

---

## 🔥 AI-Native Workflow

I don't just "use" AI — I build systems around it:

- **LLM-integrated research pipelines**: Built a multi-stage LLM scoring system that automates content discovery, relevance filtering, and creator evaluation on social platforms (see Xiaohongshu Evaluator below)
- **n8n automation flows**: Designed automated information monitoring workflows for real-time industry signal tracking
- **AI-assisted writing & analysis**: Use Claude, DeepSeek, and GPT daily for research synthesis, framework construction, and multilingual report drafting
- **Programmatic data collection → AI analysis**: Python scrapers feeding into LLM-powered structuring and insight extraction — applied this at Roland Berger to process 3,000+ developer feedbacks into quantified tech maturity metrics

---

## 🏢 Industry Research Experience

### [Roland Berger — Huawei iOS AI Ecosystem Insight Project](https://github.com/Leon-S-7211/Leon-S-7211/tree/main/RB%E5%AE%9E%E4%B9%A0%E6%88%90%E6%9E%9C)
**Cross-Platform AI Assessment** · Jan 2026 – Mar 2026

- Led a multi-dimensional competitive analysis of Apple Core ML/SiriKit vs. Google Android vs. HarmonyOS across network, compression, toolchain, and privacy dimensions using Porter's Five Forces and SWOT.
- Built Python scrapers to collect and structure 3,000+ developer feedbacks, 100+ technical docs, and 200+ competitor data points; quantified tech maturity (78% adaptation rate) and user value (+22% experience score).
- Delivered a 15,000-word panoramic industry report combining quantitative metrics with qualitative insights, directly informing HarmonyOS AI strategy prioritization.

### Guosheng Securities — Quantitative Research Institute, Fixed Income
**Quantitative Strategy Analyst** · Sep 2025 – Jan 2026

- Validated 26 REITs factors with Pandas/NumPy backtesting; identified 2 high-IC core factors for investment decisions.
- Used Bloomberg Terminal + BQL to research equity-bond constant-allocation ETFs (iShares focus); findings published in external research reports.
- Built analytical frameworks for bond ETFs covering AUM evolution, volatility drivers, investor holding periods, and holder structure; delivered 2 systematic reports.
- Assessed 175 bond issuers (SOEs to micro-enterprises) with standardized quantitative credit evaluation.

### State Grid Credit Company — Data Products & Operations
**Data Analyst** · Jul 2025 – Sep 2025

- Cleaned 100K+ enterprise power/credit records via SQL; built a logistic regression credit model (AUC = 0.86) using WOE binning, entropy weighting, and IV-based feature selection.
- Processed financial data for 412 Jiangsu manufacturers to support a power-finance fusion assessment model.

---

## 🚀 Projects

### [Startup Daily Digest — n8n AI Pipeline](https://github.com/Leon-S-7211/Leon-S-7211/tree/main/n8n自动搜寻初创公司新闻)
> **Problem:** Tracking startup product launches and funding rounds across fragmented Chinese tech media is time-consuming and easy to miss. As someone genuinely interested in industry research, I needed a system that delivers a curated daily briefing — not raw noise.

`n8n` `RSS` `DeepSeek API` `Structured Output` `Multi-source Aggregation`

- **8+ source aggregation:** Pulls RSS feeds from 36Kr, IT之家, 爱范儿, 少数派, 钛媒体, 营销新榜, 管理智库, Jôle and more — covering VC/PE deals, product launches, and market signals across sectors.
- **LLM-powered filtering & structuring:** Merged feed is routed through a multi-stage DeepSeek pipeline that filters relevance, extracts structured fields (company name, sector, event type, funding stage/amount, lead investors), and discards noise.
- **Daily output:** Generates a concise, structured daily digest ready for review — effectively a mini industry research briefing assembled automatically each morning.
- **Why it matters for industry research:** This is how I stay current on market dynamics across sectors. Instead of spending 1–2 hours scrolling feeds, I get a structured overview in minutes and can go deep on what matters.

### Douyin-to-Text: Finance Creator Knowledge Base
> **Problem:** Top financial analysts and macro commentators on Douyin produce deep, thesis-quality content — but it lives in video form, impossible to search, annotate, or reference in research. I built a fully local pipeline to convert their output into a searchable document library at zero cost.

`Python` `Playwright` `OBS WebSocket` `faster-whisper` `python-docx`

- **Research motivation:** Systematically studying how experienced investors frame sector theses, analyze business models, and interpret policy signals — building my own analytical depth through structured review of expert reasoning.
- **Full pipeline:** Playwright auto-navigates creator pages → OBS records via WebSocket → faster-whisper transcribes locally (Chinese-optimized, medium model) → formatted Word docs with creator/date metadata → auto cleanup.
- **Anti-fragile design:** Uses screen recording instead of direct download to bypass Douyin's frequently updated anti-scraping — ensuring the pipeline doesn't break when the platform changes.
- **Batch tracking:** JSON config manages a watchlist of finance creators; new creators can be added in seconds.

### Xiaohongshu Intelligent Content Evaluator
> **Problem:** Xiaohongshu hosts a mix of high-signal industry posts and low-quality noise. Manually filtering for relevant business/AI content daily is a time sink. I built an LLM-powered multi-stage scoring system to surface what matters.

`Python` `Playwright` `DeepSeek API` `LLM Multi-stage Scoring`

- **Three-stage AI pipeline:** (1) LLM batch screens all visible card titles in one API call → (2) relevant posts are opened; full text + comments extracted and scored for depth, specificity, and actionability → (3) high-scoring posts trigger author profile evaluation for credibility.
- **Robust scraping:** Reverse-engineered and validated all key DOM selectors (`section.note-item`, `#noteContainer`, `.comments-el`, author link disambiguation) — tested stable across multiple consecutive runs.
- **Efficiency-first:** Minimizes LLM API calls by front-loading a cheap batch filter before expensive per-post analysis — mirrors how a good research analyst triages information.

---

## 🛠 Technical Skills

| Category | Details |
|----------|---------|
| **Programming** | Python (Pandas, NumPy, Scikit-Learn), SQL, JavaScript |
| **AI Tools** | Claude, DeepSeek, GPT-4, faster-whisper, LLM API integration |
| **Automation** | n8n workflows, Playwright browser automation, OBS WebSocket |
| **Finance** | Bloomberg Terminal, BQL, iFinD, factor backtesting |
| **Data** | WOE/IV, logistic regression, feature engineering, AUC evaluation |
| **Languages** | Chinese (native), English (fluent — read/write/research) |

---

## 🏆 Honors & Activities

- 2024 BJTU Outstanding League Member (Top 2%) · Professional Skills Excellence Award (Top 4%)
- **Way To AGI** Campus Ambassador
- **RIT Student Board of Directors** Co-Vice Chair
