import verifiers as vf
import os
import json
from glob import glob
from datetime import datetime

from tools.exa_tool import search_web_exa
from tools.scratchpad_tool import read_scratchpad, write_scratchpad


system_prompt = """You are an expert NFL analyst tasked with predicting games against the spread.

## Your Task
For each NFL game, you must:
1. Predict which team will cover the spread (if Bills are -7, they must win by 8+ to cover)
2. Allocate between 1-5 units per game based on confidence (you have exactly 50 units per week)
3. Provide clear reasoning for your picks

## Resources Available
- **Web Search**: 3 searches per game via search_web_exa(). Use strategically for:
  - Current injury reports and inactive lists
  - Recent team performance and trends
  - Weather forecasts for outdoor games
  - Relevant team/player news
- **Scratchpad**: Persistent notes across weeks via read_scratchpad() and write_scratchpad()
  - Build knowledge about teams, patterns, and lessons learned
  - Update with insights that will help future weeks
  - You have 20,000 tokens of storage

## Constraints
- You MUST pick every game (no sitting out)
- You MUST use exactly 50 units total per week
- Each game gets 1-5 units (higher units = higher confidence)
- Spreads shown are consensus lines from major sportsbooks

## Strategy Tips
- The spread is designed to be hard to beat - 52-53% long-term is excellent
- Manage information gathering efficiently with your limited searches
- Your scratchpad persists all season - invest in building useful knowledge
- Consider: injuries, rest, travel, weather, divisional dynamics, recent form

Remember: Going 9-7 (56%) against the spread is outstanding. Focus on finding edges through smart research and pattern recognition."""

def fetch_spreads(week_number, day=None):
    """
    Fetch spreads from saved JSON files instead of API.
    
    Args:
        week_number: NFL week number (1-18)
        day: Optional day filter ('thursday', 'sunday', 'monday', etc.)
    
    Returns:
        List of game dictionaries with spreads
    """
    # Look for saved files in the week directory
    week_dir = f"data/week_{week_number}"
    
    if not os.path.exists(week_dir):
        raise FileNotFoundError(f"No data found for week {week_number}. Run pull_lines.py first!")
    
    # Build file pattern based on day filter
    if day:
        pattern = f"nfl_lines_week_{week_number}_{day}_*.json"
    else:
        pattern = f"nfl_lines_week_{week_number}_*.json"
    
    # Find matching files
    files = glob(os.path.join(week_dir, pattern))
    
    if not files:
        if day:
            raise FileNotFoundError(f"No {day} data found for week {week_number}")
        else:
            raise FileNotFoundError(f"No data found for week {week_number}")
    
    # Get the most recent file (based on timestamp in filename)
    latest_file = sorted(files)[-1]
    
    # Load the JSON data
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    # Return just the games array
    games = data['games']
    
    print(f"Loaded {len(games)} games from {os.path.basename(latest_file)}")
    
    return games
class NFLPickerEnvironment(vf.ToolEnvironment):
    def __init__(self, week_number=None, day=None, season=2025):
        super().__init__()
        
        # Register tools
        self.register_tool("search_web_exa", self.search_with_budget)  # Wrap to track usage
        self.register_tool("read_scratchpad", read_scratchpad)
        self.register_tool("write_scratchpad", write_scratchpad)
        
        self.week_number = week_number
        self.day = day
        self.season = season
        self.searches_used = {}  # Track per game
        self.games = []  # Store games from reset

    def search_with_budget(self, query, **kwargs):
        """Wrapper to enforce search budget."""
        total_allowed = len(self.games) * 3
        total_used = sum(self.searches_used.values())
        
        if total_used >= total_allowed:
            return {"error": f"Search budget exhausted ({total_allowed} searches for {len(self.games)} games)"}
        
        # Track usage (you'd need game context here - simplified for now)
        result = search_web_exa(query, **kwargs)
        # Increment counter
        return result

    def reset(self):
        ''' Called at the start of evaluation.'''

        games = fetch_spreads(self.week_number, self.day)

        return {
            "games": games,
            "week": self.week_number,
            "units_available": 50,
            "searches_per_game": 3
        }
    
    def step(self, action):
        """Validate and save predictions."""
        predictions = action  # Expecting dict of predictions
        
        # Validate all games picked
        if len(predictions) != len(self.games):
            return None, 0, False, False, {"error": "Must pick every game"}
        
        # Validate units
        total_units = sum(p.get('units', 0) for p in predictions.values())
        if total_units != 50:
            return None, 0, False, False, {"error": f"Must use exactly 50 units (used {total_units})"}
        
        # Save predictions
        output_dir = f"predictions/week_{self.week_number}"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/predictions_{self.day or 'all'}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "week": self.week_number,
                "day": self.day,
                "predictions": predictions,
                "timestamp": timestamp
            }, f, indent=2)
        
        done = True
        return None, 0, done, False, {"predictions_saved": filename}