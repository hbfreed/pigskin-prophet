import requests
import json
import os
import argparse
from datetime import datetime, timedelta
from statistics import median
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

load_dotenv()

API_KEY = os.getenv('ODDS_API_KEY')
BASE_URL = 'https://api.the-odds-api.com/v4'

def get_current_nfl_week():
    season_start = datetime(2025, 9, 4, tzinfo=ZoneInfo('America/Los_Angeles'))  # 2025 NFL season starts Sept 4, 2025
    current_date = datetime.now(ZoneInfo('America/Los_Angeles'))
    
    if current_date < season_start:
        return 1
    
    days_since_start = (current_date - season_start).days
    week = (days_since_start // 7) + 1
    
    return min(week, 18)

def get_week_boundaries():
    """Get the start and end datetime for the current NFL week (Thursday to Wednesday)"""
    current_date = datetime.now(ZoneInfo('America/Los_Angeles'))
    season_start = datetime(2025, 9, 4, tzinfo=ZoneInfo('America/Los_Angeles'))  # First Thursday
    
    # If we're before season start, return week 1 boundaries
    if current_date < season_start:
        week_start = season_start
        week_end = season_start + timedelta(days=6, hours=23, minutes=59)
        return week_start, week_end
    
    # Calculate current week number
    days_since_start = (current_date - season_start).days
    current_week = (days_since_start // 7)
    
    # Calculate this week's Thursday
    week_start = season_start + timedelta(weeks=current_week)
    week_end = week_start + timedelta(days=6, hours=23, minutes=59)
    
    return week_start, week_end

def fetch_nfl_odds():
    sport = 'americanfootball_nfl'
    
    odds_url = f'{BASE_URL}/sports/{sport}/odds'
    params = {
        'apiKey': API_KEY,
        'regions': 'us',
        'markets': 'spreads,totals',
        'oddsFormat': 'american',
    }
    
    response = requests.get(odds_url, params=params)
    
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        print(response.text)
        return None
    
    print(f"API Usage - Remaining: {response.headers.get('x-requests-remaining', 'N/A')}")
    print(f"API Usage - Used: {response.headers.get('x-requests-used', 'N/A')}")
    
    return response.json()

def filter_current_week_games(games, week_start, week_end):
    """Filter games to only include those in the current NFL week"""
    current_week_games = []
    
    for game in games:
        # Parse the commence_time from ISO format
        game_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
        # Convert to Pacific time for comparison
        game_time_pacific = game_time.astimezone(ZoneInfo('America/Los_Angeles'))
        
        # Check if game is within current week boundaries
        if week_start <= game_time_pacific <= week_end:
            current_week_games.append(game)
    
    return current_week_games

def process_game_lines(game):
    game_info = {
        'game_id': game['id'],
        'home_team': game['home_team'],
        'away_team': game['away_team'],
        'game_time': game['commence_time'],
        'bookmaker_count': len(game.get('bookmakers', [])),
        'spreads': {
            'home': [],
            'away': []
        },
        'totals': []
    }
    
    for bookmaker in game.get('bookmakers', []):
        for market in bookmaker.get('markets', []):
            if market['key'] == 'spreads':
                for outcome in market['outcomes']:
                    if outcome['name'] == game['home_team']:
                        game_info['spreads']['home'].append({
                            'bookmaker': bookmaker['title'],
                            'spread': outcome['point'],
                            'price': outcome['price']
                        })
                    else:
                        game_info['spreads']['away'].append({
                            'bookmaker': bookmaker['title'],
                            'spread': outcome['point'],
                            'price': outcome['price']
                        })
            
            elif market['key'] == 'totals':
                for outcome in market['outcomes']:
                    if outcome['name'] == 'Over':
                        game_info['totals'].append({
                            'bookmaker': bookmaker['title'],
                            'total': outcome['point'],
                            'over_price': outcome['price']
                        })
    
    # Calculate median spreads and format for model consumption
    if game_info['spreads']['home']:
        home_spreads = [s['spread'] for s in game_info['spreads']['home']]
        game_info['home_spread'] = median(home_spreads)
    else:
        game_info['home_spread'] = None
    
    if game_info['spreads']['away']:
        away_spreads = [s['spread'] for s in game_info['spreads']['away']]
        game_info['away_spread'] = median(away_spreads)
    else:
        game_info['away_spread'] = None
    
    if game_info['totals']:
        total_lines = [t['total'] for t in game_info['totals']]
        game_info['total'] = median(total_lines)
    else:
        game_info['total'] = None
    
    # Remove detailed spreads/totals arrays for cleaner output
    del game_info['spreads']
    del game_info['totals']
    
    return game_info

def filter_by_day(games, day_filter):
    """Filter games to only include those on a specific day of the week"""
    if not day_filter:
        return games
    
    day_filter = day_filter.lower()
    filtered_games = []
    
    for game in games:
        game_dt = datetime.fromisoformat(game['game_time'].replace('Z', '+00:00'))
        game_pacific = game_dt.astimezone(ZoneInfo('America/Los_Angeles'))
        game_day = game_pacific.strftime('%A').lower()
        
        if game_day == day_filter:
            filtered_games.append(game)
    
    return filtered_games

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Pull NFL betting lines for the current week')
    parser.add_argument('--day', type=str, 
                       choices=['thursday', 'friday', 'saturday', 'sunday', 'monday', 'tuesday', 'wednesday'],
                       help='Filter games to a specific day of the week')
    args = parser.parse_args()
    
    print("Fetching NFL odds data...")
    odds_data = fetch_nfl_odds()
    
    if not odds_data:
        print("Failed to fetch odds data")
        return
    
    current_week = get_current_nfl_week()
    week_start, week_end = get_week_boundaries()
    
    print(f"\nFiltering for Week {current_week} games")
    if args.day:
        print(f"Day filter: {args.day.capitalize()}")
    print(f"Week boundaries: {week_start.strftime('%Y-%m-%d %H:%M %Z')} to {week_end.strftime('%Y-%m-%d %H:%M %Z')}")
    
    # Filter to only current week's games
    current_week_games = filter_current_week_games(odds_data, week_start, week_end)
    
    print(f"Found {len(current_week_games)} games in Week {current_week}")
    
    processed_games = []
    for game in current_week_games:
        processed_game = process_game_lines(game)
        processed_games.append(processed_game)
    
    # Filter by day if specified
    if args.day:
        processed_games = filter_by_day(processed_games, args.day)
        print(f"Found {len(processed_games)} games on {args.day.capitalize()}")
    
    # Sort games by game time
    processed_games.sort(key=lambda x: x['game_time'])
    
    # Create directory structure for organized storage
    week_dir = f"data/week_{current_week}"
    os.makedirs(week_dir, exist_ok=True)
    
    # Adjust filename based on day filter
    if args.day:
        filename = f"nfl_lines_week_{current_week}_{args.day}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    else:
        filename = f"nfl_lines_week_{current_week}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Full path with directory
    filepath = os.path.join(week_dir, filename)
    
    output = {
        'meta': {
            'pull_timestamp': datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),
            'week': current_week,
            'season': 2025,
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'day_filter': args.day if args.day else 'all',
            'games_count': len(processed_games)
        },
        'games': processed_games
    }
    
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nData saved to {filepath}")
    print(f"Week: {current_week}")
    if args.day:
        print(f"Day: {args.day.capitalize()}")
    print(f"Games found: {len(processed_games)}")
    
    for game in processed_games:
        game_dt = datetime.fromisoformat(game['game_time'].replace('Z', '+00:00'))
        game_pacific = game_dt.astimezone(ZoneInfo('America/Los_Angeles'))
        
        print(f"\n{game['away_team']} @ {game['home_team']}")
        print(f"  Time: {game_pacific.strftime('%a %b %d, %I:%M %p PT')}")
        if game['home_spread'] is not None:
            print(f"  Spread: {game['home_team']} {game['home_spread']:+.1f}")
        if game['total'] is not None:
            print(f"  Total: {game['total']:.1f}")

if __name__ == "__main__":
    main()