import verifiers as vf
import os
from openai import OpenAI
from pathlib import Path
from environments.pigskin_prophet.tools.scratchpad_tool import set_current_model
from datetime import datetime
from zoneinfo import ZoneInfo

def get_current_nfl_week():
    season_start = datetime(2025, 9, 4, tzinfo=ZoneInfo('America/Los_Angeles'))  # 2025 NFL season starts Sept 4, 2025
    current_date = datetime.now(ZoneInfo('America/Los_Angeles'))

    if current_date < season_start:
        return 1

    days_since_start = (current_date - season_start).days
    week = (days_since_start // 7) + 1

    return min(week, 18)

def main():
    # Get current NFL week
    current_week = get_current_nfl_week()
    print(f"Current NFL Week: {current_week}")

    # Connect to vLLM server
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    # List of models to evaluate
    models = [
        #"openai/gpt-5",
        #"openai/gpt-oss-120b",
        #"anthropic/claude-sonnet-4",
        #"google/gemini-2.5-flash",
        #"google/gemini-2.5-pro",
        # "deepseek/deepseek-chat-v3.1", #sadly, openrouter can't handle deepseek's tool calling or something
        #"moonshotai/kimi-k2-0905",
        "z-ai/glm-4.5",
        "qwen/qwen3-235b-a22b-thinking-2507",
    ]

    for model_name in models:
        print(f"\n{'='*60}")
        print(f"Evaluating model: {model_name}")
        print(f"{'='*60}")

        # Set the current model for scratchpad isolation
        set_current_model(model_name)

        # Load environment fresh for each model
        env = vf.load_environment("pigskin-prophet")

        # Run evaluation with rate limit considerations
        results = env.evaluate(
            client,
            model_name,
            num_examples=len(env.dataset),
            rollouts_per_example=1,
            max_concurrent=5,
        )

        # Save results with model-specific filename
        ds = env.make_dataset(results)
        safe_model_name = model_name.replace("/", "_").replace(":", "_")
        out = Path(f"runs/week{current_week}/{safe_model_name}_week{current_week}.jsonl")
        out.parent.mkdir(parents=True, exist_ok=True)
        ds.to_json(str(out))
        print(f"Saved rollouts to {out}")

if __name__ == "__main__":
    main()
