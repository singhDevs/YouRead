# YouRead

A **CLI** tool that converts YouTube videos into comprehensive, readable markdown articles.

## Problem

- Watching 15-45 minute YouTube videos daily is time-consuming
- Existing tools produce shallow summaries (max 2,500 words) optimized for SEO
- No tool focuses on complete knowledge retention over content repurposing

## Solution

**YouRead** extracts transcripts from YouTube videos and uses LLM API to generate comprehensive articles that replace the need to watch the video entirely.

## Prerequisites

- Python 3.10+
- LLM API key

## Setup

1. Clone the repository

2. Create and activate virtual environment:
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your LLM API key
   ```


## Documentation
- [Quality Metrics](doc/QUALITY_METRICS.md) — How article quality is measured

## License
Personal project — not yet licensed for distribution.