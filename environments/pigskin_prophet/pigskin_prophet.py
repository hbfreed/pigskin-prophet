import subprocess
from pathlib import Path
from datasets import load_dataset
from tools.exa_tool import search_web_exa
# from tools.brave_search_tool import search_web_brave as search_web_exa
# from tools.scratchpad_tool import read_scratchpad, write_scratchpad, search_scratchpad
import verifiers as vf

system_prompt = """You are an expert NFL analyst tasked with predicting games against the spread.

## Your Task
For each NFL game, you must:
1. Predict which team will cover the spread (if Bills are -7, they must win by 8+ to cover)
2. Allocate between 1-5 units per game based on confidence (you have exactly 50 units per week)
3. Provide clear reasoning for your picks

## Resources Available
- **Web Search**: You have EXACTLY 3 searches PER GAME via search_web_exa(). Use strategically for:
  - Current injury reports and inactive lists
  - Recent team performance and trends
  - Weather forecasts for outdoor games
  - Relevant team/player news
  
WARNING: You are limited to 3 searches per game. With 16 games, that's 48 searches total maximum.
Plan your searches carefully - you cannot exceed this limit!

## Output Format
For each game, provide your pick using these XML tags:

Required tags:
- <pick>TEAM_ABBREVIATION</pick> - The team you think will cover (e.g., "BUF", "SEA", "GB")
- <units>NUMBER</units> - Your confidence level from 1-5 units
- <reasoning>Your analysis here</reasoning> - Brief explanation of your pick

Optional tag:
- <think>Your thought process</think> - Work through your analysis (you may use this to reason)

Example:
```
<think>Bills are -7 at home. They've been dominant, but Ravens have strong defense...</think>
<pick>SEA</pick>
<units>4</units>
<reasoning>Seattle at home with extra rest against injured opponent</reasoning>
```

## Constraints
- You MUST pick every game (no sitting out)
- You MUST use exactly 50 units total per week
- Each game gets 1-5 units (higher units = higher confidence)
- Spreads shown are consensus lines from major sportsbooks

## Strategy Tips
- The spread is designed to be hard to beat - 52-53% long-term is excellent
- Manage information gathering efficiently with your limited searches
- Consider: injuries, rest, travel, weather, divisional dynamics, recent form

Remember: Going 9-7 (56%) against the spread is outstanding. Focus on finding edges through smart research and pattern recognition."""


from datetime import datetime, date, time
from zoneinfo import ZoneInfo

def get_current_week(
    now: datetime | None = None,
    season_start_date: date = date(2025, 9, 4),  # Opening Thursday (local)
    tz: str = "America/Los_Angeles",
) -> int:
    """
    NFL weeks roll over at LOCAL Thursday 00:00, i.e., [Thu 00:00 ... next Wed 23:59].
    Returns an integer in [1, 18]. If called before the season start, returns 1.
    """
    tzinfo = ZoneInfo(tz)

    # Resolve "now" in the target timezone
    if now is None:
        now = datetime.now(tzinfo)
    else:
        now = now.astimezone(tzinfo) if now.tzinfo else now.replace(tzinfo=tzinfo)

    # Anchor week boundaries at local midnight on the opening Thursday
    season_start = datetime.combine(season_start_date, time.min, tzinfo)

    if now < season_start:
        return 1

    # Use DATE arithmetic so DST/hour differences can't skew the count
    days_since_start = (now.date() - season_start.date()).days
    week = 1 + (days_since_start // 7)

    return min(max(week, 1), 18)


def make_dataset(week=None):
    """Load NFL lines dataset for specified week, pulling if necessary"""
    if week is None:
        week = get_current_week()
    
    # Look for most recent JSON file in the week directory
    data_dir = Path(f"data/week_{week}")
    
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    
    # Find the most recent JSON file
    json_files = list(data_dir.glob("*.json"))
    
    if not json_files:
        # No data exists, pull it using pull_lines.py
        print(f"No data found for week {week}, pulling lines...")
        result = subprocess.run(
            ["python3", "pull_lines.py"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent  # Project root
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to pull lines: {result.stderr}")
        
        # Try to find the file again
        json_files = list(data_dir.glob("*.json"))
        if not json_files:
            raise RuntimeError(f"No JSON files found after pulling lines for week {week}")
    
    # Get the most recent file
    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
    
    # Load using HuggingFace datasets
    dataset = load_dataset('json', data_files=str(latest_file), split='train')
    
    # Extract just the games from the dataset structure
    # The dataset has 'meta' and 'games' fields, we only want games
    games = dataset['games'][0]  # games is a list column, get first (only) row
    
    # Transform games into question/answer format for verifiers
    formatted_games = []
    for game in games:
        # Create a question about who will win against the spread
        question = f"Who will cover the spread in {game['away_team']} @ {game['home_team']}? The spread is {game['home_team']} {game['home_spread']:+.1f}."
        
        # For now, we don't have actual answers, so we'll use placeholder
        # In reality, you'd fill this in after games are played
        answer = "TBD"  # This would be filled with actual winner after game
        
        formatted_games.append({
            "question": question,
            "answer": answer,
            "game_id": game['game_id'],
            "home_team": game['home_team'],
            "away_team": game['away_team'],
            "home_spread": game['home_spread'],
            "away_spread": game['away_spread'],
            "total": game['total'],
            "game_time": game['game_time']
        })
    
    # Convert to a dataset with required format
    from datasets import Dataset
    games_dataset = Dataset.from_list(formatted_games)
    
    return games_dataset

def load_environment(**kwargs) -> vf.Environment:
    dataset = make_dataset()
    
    # Get current week and date for the prompt
    from datetime import datetime
    from zoneinfo import ZoneInfo
    
    current_week = get_current_week()
    current_date = datetime.now(ZoneInfo('America/Los_Angeles'))
    
    # Format date as "Sunday September 7th, 2025"
    day_name = current_date.strftime("%A")
    month_name = current_date.strftime("%B")
    day = current_date.day
    year = current_date.year
    
    # Add ordinal suffix to day
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    
    formatted_date = f"{day_name} {month_name} {day}{suffix}, {year}"
    
    # Update system prompt with current context
    contextualized_prompt = f"""## Current Context
Today is {formatted_date}
This is Week {current_week} of the 2025 NFL season

{system_prompt}"""
    
    # Use built-in XML parser with fields for pick, units, and reasoning
    parser = vf.XMLParser(
        fields=["think", "pick", "units", "reasoning"],
        answer_field="pick"  # The main answer is the team pick
    )

    def binary_correct(parser, completion, answer):
        """Binary scoring: 1.0 if correct, 0.0 if wrong"""
        # For now, since games haven't been played, we can't score correctness
        # Just return 0 - this will be updated once we have actual results
        if answer == "" or answer == "TBD":
            return 0.0
        
        response = parser.parse_answer(completion) or ''
        # When we have real answers:
        return 1.0 if response.strip().upper() == answer.strip().upper() else 0.0
    
    def weighted_correct(parser, completion, answer):
        """Weighted scoring: correctness * units wagered"""
        # For now, since games haven't been played, we can't score correctness
        if answer == "" or answer == "TBD":
            return 0.0
        
        # Parse the full completion to get both pick and units
        parsed = parser.parse(completion)
        
        # Get the pick (answer)
        pick = getattr(parsed, 'pick', None)
        if not pick:
            return 0.0
        
        # Get the units wagered (1-5)
        units_str = getattr(parsed, 'units', None)
        if not units_str:
            return 0.0
        
        try:
            units = int(units_str)
            # Validate units are in valid range
            if units < 1 or units > 5:
                return 0.0
        except (ValueError, TypeError):
            return 0.0
        
        # Check if pick is correct
        is_correct = pick.strip().upper() == answer.strip().upper()
        
        # Return weighted score: +units if correct, -units if wrong
        # Normalize to 0-1 range by dividing by max units (5)
        if is_correct:
            return units / 5.0
        else:
            return -units / 5.0  # Negative score for wrong picks

    # For now, only use format scoring since we don't have answers yet
    # When games are played, update weights to score correctness
    rubric = vf.Rubric(
            funcs=[binary_correct, weighted_correct],
            weights=[0.0, 0.0]  # Only score formatting for now
    )

    return vf.ToolEnv(
            dataset=dataset,
            system_prompt=contextualized_prompt,
            tools=[search_web_exa],
            parser=parser,
            rubric=rubric,
            **kwargs
    )