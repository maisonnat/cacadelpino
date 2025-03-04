import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class AccountTracker:
    def __init__(self, tracking_dir: str = 'tracking'):
        self.tracking_dir = Path(tracking_dir)
        self.tracking_dir.mkdir(exist_ok=True)
    
    def _get_tracking_file(self, username: str) -> Path:
        """Get the tracking file path for a specific account."""
        return self.tracking_dir / f"{username}_tracking.json"
    
    def load_tracking(self, username: str) -> Dict:
        """Load tracking data for a specific account."""
        tracking_file = self._get_tracking_file(username)
        if tracking_file.exists():
            with open(tracking_file, 'r') as f:
                return json.load(f)
        return {
            'last_activity': None,
            'daily_sets': [],
            'more_activities': [],
            'total_points': 0,
            'last_update': None
        }
    
    def save_tracking(self, username: str, tracking_data: Dict) -> None:
        """Save tracking data for a specific account."""
        tracking_file = self._get_tracking_file(username)
        tracking_data['last_update'] = datetime.now().isoformat()
        with open(tracking_file, 'w') as f:
            json.dump(tracking_data, f, indent=4)
    
    def is_activity_completed(self, username: str, activity_id: str, activity_type: str) -> bool:
        """Check if a specific activity has been completed."""
        tracking_data = self.load_tracking(username)
        if activity_type == 'daily':
            return activity_id in tracking_data['daily_sets']
        elif activity_type == 'more':
            return activity_id in tracking_data['more_activities']
        return False
    
    def mark_activity_completed(self, username: str, activity_id: str, activity_type: str, points: int = 0) -> None:
        """Mark an activity as completed and update points."""
        tracking_data = self.load_tracking(username)
        
        if activity_type == 'daily' and activity_id not in tracking_data['daily_sets']:
            tracking_data['daily_sets'].append(activity_id)
            tracking_data['total_points'] += points
        elif activity_type == 'more' and activity_id not in tracking_data['more_activities']:
            tracking_data['more_activities'].append(activity_id)
            tracking_data['total_points'] += points
        
        tracking_data['last_activity'] = datetime.now().isoformat()
        self.save_tracking(username, tracking_data)
    
    def get_account_summary(self, username: str) -> Dict:
        """Get a summary of account's activities and points."""
        tracking_data = self.load_tracking(username)
        return {
            'total_points': tracking_data['total_points'],
            'daily_sets_completed': len(tracking_data['daily_sets']),
            'more_activities_completed': len(tracking_data['more_activities']),
            'last_activity': tracking_data['last_activity']
        }
    
    def reset_daily_activities(self, username: str) -> None:
        """Reset daily activities for an account."""
        tracking_data = self.load_tracking(username)
        tracking_data['daily_sets'] = []
        self.save_tracking(username, tracking_data)
    
    def should_reset_daily(self, username: str) -> bool:
        """Check if daily activities should be reset based on last update time."""
        tracking_data = self.load_tracking(username)
        if not tracking_data['last_update']:
            return True
        
        last_update = datetime.fromisoformat(tracking_data['last_update'])
        now = datetime.now()
        
        # Reset if last update was on a different day
        return last_update.date() < now.date()