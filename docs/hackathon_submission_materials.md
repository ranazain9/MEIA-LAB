# MEIA-LAB Hackathon Submission Materials
*AMD Developer Act 2 Hackathon Submission*

This document contains two core parts:
1. **30-Second Demo Video Script** (optimized for a fast-paced, high-impact product walkthrough).
2. **Hackathon Submission Slides & Presenter Script** (Intro, Problem, Solution, AMD Technology, Product Demo, and Market Business Model).

---

## Part 1: 30-Second Demo Video Script

**Format**: Fast-paced, high energy, voiceover (VO) coordinated with UI screen recordings.

| Time (s) | Visual (On Screen) | Voiceover (VO) Script |
| :--- | :--- | :--- |
| **0:00 - 0:05** | **Screen**: The MEIA-LAB "Source Ingestion" processing page. Ticker set to `AMD`. The cursor drags and drops `sample.wav` and `slides.pdf` into the upload cards. Clicking **Run Analysis**. <br><br> *Micro-animation*: The pipeline steps light up one-by-one (Ingest $\rightarrow$ ASR $\rightarrow$ Vision $\rightarrow$ Filing). | *"This is MEIA-LAB, the multi-agent earnings call intelligence platform. With just a stock ticker, audio file, and presentation deck, we start verification."* |
| **0:05 - 0:12** | **Screen**: Fast transition to the main **Dashboard Page**. The dashboard populates with high-fidelity visual cards. The cursor points to the **Consistency Score (92%)**, **Claims Verified (47/54)**, and **Risk Flags (3)**. <br><br> *Micro-animation*: The agent activity logs scroll dynamically (ASR Agent transcribing, Vision Agent parsing PDF OCR, Filing Agent pulling EDGAR). | *"Our Whisper-powered ASR and layout-aware Vision agents immediately process the data, generating a unified dashboard that highlights inconsistency, risk flags, and consensus alignment."* |
| **0:12 - 0:20** | **Screen**: The user clicks the **Claims tab**. The UI scrolls through claims. Zoom in on verified and unsupported claims. <br><br> *Claim 1*: "Gross margin expanded to 54%" (Status: **Verified**, Confidence: 91%, Source: Earnings Transcript, Location: L. 204). <br> *Claim 2*: "Embedded segment operating income flat" (Status: **Unsupported**, Confidence: 48%, Snippet shows a 3% decline on 10-Q p. 24). | *"Dive into individual management claims. MEIA-LAB cross-examines verbal commentary against SEC filings. See what is verified, what needs review, and what is flat-out unsupported by official disclosures."* |
| **0:20 - 0:30** | **Screen**: The user clicks the **Evidence Room** and **Analyst Brief** tabs. Highlight the citations panel linking claims directly to SEC 10-Q paragraphs (e.g., *10-Q p. 12 - Data Center revenue*). <br><br> *End Screen*: MEIA-LAB logo appears. Subtitle: *"Financial Truth, Verified on AMD GPUs."* | *"Review the audit trail in our Evidence Room with source-level citations. Generate complete, risk-aware analyst briefs instantly. Cut research time by 90% and invest with certainty. MEIA-LAB—powered by AMD."* |

---

## Part 2: Hackathon Submission Slides & Presenter Script

### Slide 1: Title Slide (Intro)
* **Slide Title**: MEIA-LAB: Multi-Agent Earnings Call Intelligence & Alignment
* **Subtitle**: Cross-Examining Corporate Disclosures in Real-Time
* **Visuals**: Modern, dark-mode dashboard mockups showing agents (ASR, Vision, SEC Filing) interacting; logos for AMD, ROCm, and Hugging Face.
* **Key Bullet Points**:
  * AI-powered earnings call audio and presentation verification.
  * Multi-agent execution optimized for AMD Developer Cloud GPUs.
  * Direct alignment checks against live SEC EDGAR filings.
* **Presenter Script**:
  > *"Hello, we are the team behind MEIA-LAB. Today, we are excited to present our submission for the AMD Developer Act 2 Hackathon. MEIA-LAB is an end-to-end earnings-call intelligence platform designed to eliminate financial misinformation and save analysts hundreds of hours by automatically verifying earnings-call statements against official disclosures in real-time."*

---

### Slide 2: The Problem
* **Slide Title**: The Earnings Verification Crisis
* **Visuals**: A cluttered desk showing overlapping PDF pages of 10-Qs, transcripts, and presentation slides. A graph showing the growing volume of quarterly corporate communications.
* **Key Bullet Points**:
  * **Hype vs. Fact**: Management teams often use optimistic or qualified language in calls that doesn't match the cold numbers in SEC filings.
  * **Cognitive Overload**: A single quarterly earnings event requires reading 100+ pages of SEC filings, listening to 45 minutes of audio, and parsing slide decks.
  * **Error-Prone Auditing**: Cross-referencing statements manually is slow and leads to missed discrepancies (such as inventory surges or guidance mismatches).
* **Presenter Script**:
  > *"Every quarter, public companies present their financial health through earnings calls and presentation decks. However, finding the truth within the corporate noise is a massive challenge. Analysts have to manually read through hundreds of pages of SEC filings to check if management's verbal statements align with official disclosures. This process is slow, tedious, and highly error-prone, which often leads to missed risk flags and costly investment mistakes."*

---

### Slide 3: The Solution
* **Slide Title**: MEIA-LAB: Automated Multi-Agent Verification
* **Visuals**: High-level block diagram showing the flow of raw data (audio, slides, filings) into the Orchestrator, which distributes tasks to specialized agents (ASR, Vision, Filing) and outputs a verified dashboard.
* **Key Bullet Points**:
  * **Whisper ASR Agent**: Fast, high-accuracy speech transcription and speaker identification.
  * **Vision Agent**: Slide-deck OCR and semantic layout analysis.
  * **SEC Filing Agent**: Real-time extraction of official 10-Q/8-K financial tables via SEC EDGAR.
  * **AI Orchestrator**: Merges findings, scores claim consistency, and drafts interactive briefs.
* **Presenter Script**:
  > *"MEIA-LAB solves this by deploying a team of specialized AI agents. Our ASR agent transcribes the call audio; our Vision agent extracts text and figures from presentation slides; and our Filing agent automatically pulls the company's latest filings from SEC EDGAR. Finally, our Orchestrator cross-references all the data to verify management's claims and flag discrepancies in seconds, reducing research time from hours to under a minute."*

---

### Slide 4: Technology & AMD GPU Acceleration
* **Slide Title**: Powered by AMD GPU Hardware
* **Visuals**: Schematic showing local API/frontend routing heavy workloads to AMD GPUs. Benchmarks indicating performance speedups on GPU execution vs CPU execution.
* **Key Bullet Points**:
  * **High-Performance Whisper Inference**: Running Hugging Face Transformers models with ROCm on AMD GPUs for near-instant transcription.
  * **Accelerated Embedding Generation**: High-throughput vector embeddings for RAG-based SEC filing search.
  * **Flexible Deployment**: Seamless CPU-fallback for local development, with automatic GPU routing for enterprise batch workloads.
* **Presenter Script**:
  > *"Under the hood, MEIA-LAB is built to leverage AMD GPU hardware. By running our Whisper-based transcription and embedding models on AMD GPU resources using Hugging Face and ROCm, we achieve massive speedups. Long earnings call audio files are transcribed in seconds, and semantic searches across thousands of SEC filing pages run instantly. Our hybrid setup allows developers to run the light API locally while routing heavy processing workloads to AMD Developer Cloud GPUs."*

---

### Slide 5: Demo & Key Features
* **Slide Title**: Live Platform Demo & Key Features
* **Visuals**: Screenshots or embedding of the web dashboard. Callout bubbles pointing to key features:
  * **Consistency Score (92%)**: Summary of slide-to-audio-to-filing agreement.
  * **Verified Claims Panel**: Explaining how a claim is mapped directly to a source (e.g., *Gross margin verified at 54%*).
  * **Evidence Room**: Clickable citations detailing exact page numbers and transcript lines.
  * **Risk Monitor**: Highlights key warning signs (e.g., *Revenue Guidance Gap of $200M*).
* **Presenter Script**:
  > *"Let's look at the platform in action. After ingestion, the user lands on our unified dashboard. Instantly, we see a Consistency Score of 92% and three active risk flags. In the Claims tab, we can see exactly which statements are verified, and which are unsupported. For example, our system flagged an unsupported claim regarding the embedded segment's operating income, showing a 3% decline in the filing despite management's optimistic verbal comments. Every single claim links directly to its source citation in the Evidence Room."*

---

### Slide 6: Market Opportunity & Business Model
* **Slide Title**: Market Potential & Business Outlook
* **Visuals**: Chart showing addressable market segments (Hedge Funds, Equity Research, Compliance Teams, Investor Relations). Pricing table.
* **Key Bullet Points**:
  * **Primary Target Audience**: Hedge funds, institutional asset managers, buy-side/sell-side equity research firms, corporate compliance teams.
  * **Business Model**: 
    * *SaaS Tier*: Standard subscription for individual analysts accessing standard models.
    * *Enterprise Tier*: Private, secure deployments utilizing dedicated AMD GPUs for zero-data-leak processing of proprietary files.
  * **Value Proposition**: Saves time, prevents regulatory and financial compliance errors, and discovers alpha before the market adjusts.
* **Presenter Script**:
  > *"The market opportunity for MEIA-LAB is substantial. Our target customers include hedge funds, equity research desks, and corporate audit teams who pay millions annually for data feeds. We will operate on a SaaS model with standard subscriptions for analysts, and a premium Enterprise tier. The Enterprise tier is particularly compelling: it offers dedicated private instances running on secure AMD GPU clouds, ensuring zero data leakage for sensitive, pre-earnings information. MEIA-LAB makes institutional-grade corporate auditing fast, accessible, and flawless."*
