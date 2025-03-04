import argparse
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from src.html_analyzer import HTMLAnalyzer
from src.metrics_collector import MetricsCollector
from src.account_tracker import AccountTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/monitor.log"),
        logging.StreamHandler()
    ]
)

class PerformanceMonitor:
    """Main class for monitoring and analyzing account performance."""
    
    def __init__(self, credentials_file: str = 'credenciales.txt'):
        self.credentials_file = credentials_file
        self.html_analyzer = HTMLAnalyzer()
        self.metrics_collector = MetricsCollector()
        self.account_tracker = AccountTracker()
        self.accounts = self._load_accounts()
        
    def _load_accounts(self) -> List[str]:
        """Load account usernames from credentials file."""
        accounts = []
        try:
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        username, _ = line.strip().split(':')
                        accounts.append(username)
            logging.info(f"Loaded {len(accounts)} accounts from credentials file")
            return accounts
        except Exception as e:
            logging.error(f"Error loading accounts: {e}")
            return []
    
    def analyze_html_dumps(self, username: Optional[str] = None) -> Dict:
        """Analyze HTML dumps for a specific account or all accounts."""
        logging.info(f"Analyzing HTML dumps for {'all accounts' if username is None else username}")
        return self.html_analyzer.get_session_analysis(username)
    
    def register_accounts(self) -> None:
        """Register all accounts in the metrics database."""
        for username in self.accounts:
            self.metrics_collector.register_account(username)
        logging.info(f"Registered {len(self.accounts)} accounts in metrics database")
    
    def generate_account_report(self, username: str) -> Dict:
        """Generate a comprehensive report for a specific account."""
        logging.info(f"Generating report for account: {username}")
        
        # Get metrics from different sources
        metrics_stats = self.metrics_collector.get_account_stats(username)
        html_analysis = self.html_analyzer.get_session_analysis(username)
        tracking_summary = self.account_tracker.get_account_summary(username)
        
        # Combine all data
        report = {
            'username': username,
            'metrics': metrics_stats,
            'html_analysis': html_analysis,
            'tracking': tracking_summary,
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def generate_system_report(self) -> Dict:
        """Generate a system-wide report with aggregated statistics."""
        logging.info("Generating system-wide report")
        
        # Get all accounts summary
        accounts_summary = self.metrics_collector.get_all_accounts_summary()
        
        # Get error patterns
        error_patterns = self.metrics_collector.get_error_patterns()
        
        # Get HTML analysis for all accounts
        html_analysis = self.html_analyzer.get_session_analysis()
        
        # Calculate aggregate statistics
        total_points = sum(acc.get('total_points', 0) for acc in accounts_summary)
        total_sessions = sum(acc.get('total_sessions', 0) for acc in accounts_summary)
        successful_sessions = sum(acc.get('successful_sessions', 0) for acc in accounts_summary)
        success_rate = successful_sessions / total_sessions if total_sessions > 0 else 0
        
        # Identify problematic accounts (high error rates)
        problematic_accounts = []
        for acc in accounts_summary:
            if acc.get('session_success_rate', 1.0) < 0.7:  # Less than 70% success rate
                problematic_accounts.append({
                    'username': acc.get('username'),
                    'success_rate': acc.get('session_success_rate', 0),
                    'total_errors': acc.get('total_errors', 0)
                })
        
        return {
            'total_accounts': len(accounts_summary),
            'total_points': total_points,
            'total_sessions': total_sessions,
            'successful_sessions': successful_sessions,
            'overall_success_rate': success_rate,
            'problematic_accounts': problematic_accounts,
            'error_patterns': error_patterns,
            'html_analysis': html_analysis,
            'generated_at': datetime.now().isoformat()
        }
    
    def print_report(self, report: Dict, detailed: bool = False) -> None:
        """Print a report in a readable format."""
        if 'username' in report:  # Account report
            print(f"\n===== ACCOUNT REPORT: {report['username']} =====")
            print(f"Generated at: {report['generated_at']}\n")
            
            # Print metrics
            metrics = report.get('metrics', {})
            print("METRICS:")
            print(f"  Total logins: {metrics.get('total_logins', 0)}")
            print(f"  Successful logins: {metrics.get('successful_logins', 0)}")
            print(f"  Success rate: {metrics.get('success_rate', 0):.2%}")
            print(f"  Total points: {metrics.get('total_points', 0)}")
            print(f"  Last points: {metrics.get('last_points', 0)}")
            
            # Print tracking info
            tracking = report.get('tracking', {})
            print("\nTRACKING:")
            print(f"  Total points: {tracking.get('total_points', 0)}")
            print(f"  Daily sets completed: {tracking.get('daily_sets_completed', 0)}")
            print(f"  More activities completed: {tracking.get('more_activities_completed', 0)}")
            print(f"  Last activity: {tracking.get('last_activity', 'Never')}")
            
            # Print HTML analysis
            html = report.get('html_analysis', {})
            print("\nHTML ANALYSIS:")
            print(f"  Total dumps: {html.get('total_dumps', 0)}")
            print(f"  Error rate: {html.get('error_rate', 0):.2%}")
            print(f"  Captcha rate: {html.get('captcha_rate', 0):.2%}")
            print(f"  Rate limit count: {html.get('rate_limit_count', 0)}")
            print(f"  Login success rate: {html.get('login_success_rate', 0):.2%}")
            print(f"  Points earned: {html.get('points_earned', 'Unknown')}")
            
            # Print recent errors if detailed
            if detailed and 'recent_errors' in metrics:
                print("\nRECENT ERRORS:")
                for error in metrics['recent_errors']:
                    print(f"  [{error['timestamp']}] {error['error_type']}: {error['error_message']}")
        
        else:  # System report
            print("\n===== SYSTEM-WIDE REPORT =====")
            print(f"Generated at: {report['generated_at']}\n")
            
            print("OVERALL STATISTICS:")
            print(f"  Total accounts: {report.get('total_accounts', 0)}")
            print(f"  Total points: {report.get('total_points', 0)}")
            print(f"  Total sessions: {report.get('total_sessions', 0)}")
            print(f"  Successful sessions: {report.get('successful_sessions', 0)}")
            print(f"  Overall success rate: {report.get('overall_success_rate', 0):.2%}")
            
            # Print problematic accounts
            problematic = report.get('problematic_accounts', [])
            if problematic:
                print("\nPROBLEMATIC ACCOUNTS:")
                for acc in problematic:
                    print(f"  {acc['username']}: {acc['success_rate']:.2%} success rate, {acc['total_errors']} errors")
            
            # Print error patterns if detailed
            if detailed and 'error_patterns' in report:
                patterns = report['error_patterns']
                
                print("\nERROR TYPES:")
                for error_type, count in patterns.get('error_types', {}).items():
                    print(f"  {error_type}: {count}")
                
                print("\nACCOUNTS WITH MOST ERRORS:")
                for username, count in patterns.get('accounts_with_most_errors', {}).items():
                    print(f"  {username}: {count} errors")
                
                print("\nERRORS BY HOUR:")
                for hour, count in patterns.get('errors_by_hour', {}).items():
                    print(f"  {hour}:00 - {int(hour)+1}:00: {count} errors")
            
            # Print HTML analysis
            html = report.get('html_analysis', {})
            print("\nHTML ANALYSIS:")
            print(f"  Total dumps: {html.get('total_dumps', 0)}")
            print(f"  Error rate: {html.get('error_rate', 0):.2%}")
            print(f"  Captcha rate: {html.get('captcha_rate', 0):.2%}")
            print(f"  Rate limit count: {html.get('rate_limit_count', 0)}")

def main():
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Microsoft Rewards Performance Monitor')
    parser.add_argument('--account', '-a', help='Analyze a specific account')
    parser.add_argument('--html', action='store_true', help='Analyze HTML dumps')
    parser.add_argument('--metrics', action='store_true', help='Show metrics')
    parser.add_argument('--detailed', '-d', action='store_true', help='Show detailed report')
    parser.add_argument('--register', action='store_true', help='Register all accounts in metrics database')
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = PerformanceMonitor()
    
    # Register accounts if requested
    if args.register:
        monitor.register_accounts()
        return
    
    # Analyze HTML dumps if requested
    if args.html:
        analysis = monitor.analyze_html_dumps(args.account)
        print(f"HTML Analysis: {analysis}")
        return
    
    # Generate and print report
    if args.account:
        report = monitor.generate_account_report(args.account)
    else:
        report = monitor.generate_system_report()
    
    monitor.print_report(report, args.detailed)

if __name__ == "__main__":
    main()