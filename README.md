# Pigskin Prophet

**A benchmark for evaluating AI model reasoning and research capabilities using NFL sports analysis tasks**

## Overview

Pigskin Prophet is a [Verifiers](https://github.com/willccbb/verifiers) benchmark that evaluates how well AI models can gather information, analyze data, and make reasoned assessments. Using NFL games as a complex, real-world domain, it tests models' abilities to research, synthesize information, and maintain knowledge over time.

## Purpose

This is an **evaluation benchmark**, not a prediction system. It measures:
- Information gathering strategies
- Research efficiency with limited resources
- Knowledge synthesis from multiple sources
- Persistent memory management
- Reasoning under uncertainty

## Key Features

### Active Research Capabilities
- Models get **limited web searches** to gather information
- Must strategically allocate research resources
- Tests information prioritization and search query formulation

### Persistent Knowledge Base
- Each model maintains a scratchpad across evaluation rounds
- Tests long-term knowledge management
- Evaluates ability to update beliefs with new information

### Multi-Week Evaluation
- Continuous assessment across multiple weeks
- Tests adaptation and learning from past assessments
- Measures consistency and improvement over time

## Benchmark Components

1. **Data Collection**: Provides consistent NFL odds data as evaluation inputs
2. **Research Tools**: Limited web search budget via Exa API
3. **Scratchpad System**: 20k token persistent storage for each model
4. **Scoring Framework**: Evaluates reasoning quality and resource efficiency

## How It Works

1. **Setup Phase**: Models receive:
   - Current week's NFL game data
   - Access to their persistent scratchpad
   - Limited search budget for research

2. **Research Phase**: Models can:
   - Query web for contextual information
   - Update their knowledge base
   - Strategize resource allocation

3. **Analysis Phase**: Models produce:
   - Assessments for each game
   - Reasoning explanations
   - Confidence indicators

4. **Evaluation**: Scoring based on:
   - Reasoning quality
   - Information usage efficiency
   - Consistency with available data
   - Resource management

## Installation

```bash
# Install dependencies
uv pip install python-dotenv requests exa-py tiktoken

# Set up API keys in .env file
ODDS_API_KEY=your_odds_api_key
EXA_API_KEY=your_exa_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Project Structure

```
pigskin-prophet/
├── pull_lines.py           # Fetches NFL data for consistent inputs
├── tools/
│   ├── exa_tool.py         # Web search tool (limited queries)
│   └── scratchpad_tool.py  # Persistent storage (20k tokens)
├── environments/
│   └── vf_nfl_picker/      # Verifiers environment
└── data/
    └── week_*/             # Weekly NFL data snapshots
```

## Research Focus

This benchmark is designed to study:
- **Information Gathering**: How models prioritize and search for information
- **Knowledge Management**: How models organize and update persistent knowledge
- **Resource Allocation**: How models budget limited research resources
- **Reasoning Patterns**: How models synthesize multiple information sources
- **Uncertainty Handling**: How models reason with incomplete information

## Usage

### For Researchers
Use this benchmark to evaluate:
- Multi-tool agent architectures
- Information retrieval strategies
- Long-term memory systems
- Reasoning under constraints

### For Model Developers
Test your models on:
- Complex real-world reasoning tasks
- Resource-constrained decision making
- Multi-round evaluation scenarios
- Information synthesis challenges

## Limitations

- This is a **benchmark tool**, not a prediction system
- Evaluates reasoning processes, not prediction accuracy
- Focuses on information gathering and synthesis capabilities
- Uses sports domain as a complex but bounded test environment

## Contributing

This benchmark is part of ongoing research into AI model evaluation. We welcome contributions for:
- Improved evaluation metrics
- Additional research tools
- Enhanced scoring rubrics
- Extended test domains

## Ethics Note

This system is designed for AI research and benchmarking purposes only. It evaluates how models process and analyze information, not their ability to predict real-world outcomes.

---

*Part of the [Verifiers](https://github.com/willccbb/verifiers) ecosystem for rigorous AI evaluation*