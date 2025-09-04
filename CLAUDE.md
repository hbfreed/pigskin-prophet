# Pigskin Prophet

NFL betting lines analysis and prediction system.

## Quick Start

```bash
# Install dependencies
uv pip install python-dotenv requests exa-py

# Pull current week's lines
python3 pull_lines.py

# Pull specific day's games
python3 pull_lines.py --day sunday
```

## Key Files

- `pull_lines.py` - Fetches NFL betting lines from The Odds API
- `tools/exa_tool.py` - Web search tool for research via Exa API
- `tools/scratchpad_tool.py` - Persistent notes storage for models (20k token limit)
- `data/` - JSON files organized by week
- `.env` - API keys (gitignored)

## API Keys Required

In `.env`:
- `ODDS_API_KEY` - The Odds API for betting lines
- `EXA_API_KEY` - Exa for web search
- `OPENROUTER_API_KEY` - OpenRouter for model inference

## Pull Lines Script

Fetches median betting lines across bookmakers. Outputs JSON with:
- Game metadata (teams, time, ID)
- Median spreads and totals
- Filtered by week (Thursday-Wednesday) and optionally by day

## Exa Tool

Cost-optimized web search using keyword search ($2.50/1k) with full text retrieval. 
Hard-coded to 5 results max to prevent cheating.

## Scratchpad Tool

Simple persistent storage for models to track insights across weeks.
- 20k token limit per model
- Append or replace modes
- Stored in `scratchpads/{season}/{model_name}.json`

## Notes

- 2025 NFL season starts Sept 4
- Uses Pacific Time for all calculations
- Median values provide stable betting lines
- Dependencies: `python-dotenv requests exa-py tiktoken`