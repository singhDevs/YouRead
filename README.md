# YouRead

Turn a YouTube video into a readable Markdown article.

Built for people who prefer reading over watching, who got 100s of youtube tabs opened but none watched — technical talks, podcasts, discussions. It goes beyond summaries; the goal is an article detailed enough that you usually don't need to watch the video.


## Quick Start

```bash
pip install youread
youread config set --provider openai --set-api-key
youread run "https://youtube.com/watch?v=VIDEO_ID"
```

## Install

Requires Python 3.10+.

```bash
pip install youread
```

## Configure

YouRead supports OpenAI and Gemini. Defaults:

```yaml
llm:
  provider: openai
  model: gpt-5
  max_tokens: 8000
  temperature: 0.3
output:
  directory: ./output
processing:
  remove_sponsors: true
```

```bash
# set provider + model
youread config set --provider openai --model gpt-5

# set API key (secure prompt, no echo)
youread config set --set-api-key

# view current config
youread config show

# check if active provider has a key
youread config check
```

Provider/model pairs are validated at save time — `--provider gemini --model gpt-5` is rejected immediately.

## Usage

```bash
youread run "https://youtube.com/watch?v=VIDEO_ID"

# with options
youread run "URL" --mode detailed
youread run "URL" --prompt "Focus on code examples"
youread run "URL" --model gemini-2.5-flash
youread run "URL" --no-sponsorblock
```

| Flag | What it does |
|------|-------------|
| `--mode summary\|standard\|detailed` | Article depth (default: standard) |
| `--prompt "..."` | Custom instructions appended to the system prompt |
| `--model <name>` | Override configured model for one run |
| `--no-sponsorblock` | Skip sponsor segment removal |

Output goes to the configured directory (`./output` by default). After generation, YouRead asks whether to open the file.

## Supported Providers

| Provider | Example Model | Env variable |
|----------|---------------|-------------|
| OpenAI | `gpt-5` | `OPENAI_API_KEY` |
| Gemini | `gemini-2.5-flash` | `GEMINI_API_KEY` |

## Troubleshooting

**`No API key found`** — `youread config check` then `youread config set --set-api-key`.

**`Provider mismatch`** — You paired `--provider gemini` with `--model gpt-5`. Use matching pairs: `openai` + `gpt-5`, `gemini` + `gemini-2.5-flash`.

**`No transcript available`** — Video has no accessible captions.
