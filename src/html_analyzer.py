import os
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import logging
from datetime import datetime

class HTMLAnalyzer:
    """Class for analyzing HTML dumps to detect errors, CAPTCHAs, and other patterns."""
    
    def __init__(self, html_dumps_dir: str = 'html_dumps'):
        self.html_dumps_dir = Path(html_dumps_dir)
        if not self.html_dumps_dir.exists():
            logging.warning(f"HTML dumps directory {html_dumps_dir} does not exist")
    
    def analyze_html_dump(self, file_path: str) -> Dict:
        """Analyze a single HTML dump file for error patterns and CAPTCHAs."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
                
                # Check for error messages
                error_message = soup.find('div', class_='error-message')
                if not error_message:
                    error_message = soup.find(text=lambda text: text and 'error' in text.lower())
                
                # Check for CAPTCHAs
                captcha = soup.find('iframe', src=lambda x: x and 'captcha' in x.lower())
                if not captcha:
                    captcha = soup.find(text=lambda text: text and 'captcha' in text.lower())
                
                # Check for rate limiting
                rate_limit = soup.find(text=lambda text: text and ('rate limit' in text.lower() or 
                                                               'too many requests' in text.lower()))
                
                # Check for login status
                logged_in = bool(soup.find('a', href=lambda x: x and 'logout' in x.lower()) or
                                soup.find(text=lambda text: text and 'sign out' in text.lower()))
                
                # Check for rewards page elements
                rewards_page = bool(soup.find('div', id=lambda x: x and 'rewards' in x.lower()) or
                                   soup.find(text=lambda text: text and 'microsoft rewards' in text.lower()))
                
                # Extract points if available
                points_element = soup.find(text=lambda text: text and 'points' in text.lower())
                points = None
                if points_element:
                    # Try to extract numeric points value
                    import re
                    points_match = re.search(r'\d+\s*points', points_element)
                    if points_match:
                        points = int(re.search(r'\d+', points_match.group()).group())
                
                return {
                    'has_error': error_message is not None,
                    'error_text': str(error_message) if error_message else None,
                    'has_captcha': captcha is not None,
                    'rate_limited': rate_limit is not None,
                    'logged_in': logged_in,
                    'on_rewards_page': rewards_page,
                    'points': points
                }
        except Exception as e:
            logging.error(f"Error analyzing HTML dump {file_path}: {e}")
            return {
                'has_error': True,
                'error_text': f"Analysis error: {str(e)}",
                'has_captcha': False,
                'rate_limited': False,
                'logged_in': False,
                'on_rewards_page': False,
                'points': None
            }
    
    def analyze_all_dumps(self) -> List[Dict]:
        """Analyze all HTML dumps in the directory."""
        results = []
        if not self.html_dumps_dir.exists():
            return results
            
        for file_path in self.html_dumps_dir.glob('*.html'):
            try:
                # Extract timestamp and description from filename
                filename = file_path.name
                timestamp_str = filename.split('_')[0] + '_' + filename.split('_')[1]
                description = '_'.join(filename.split('_')[2:]).replace('.html', '')
                
                # Parse timestamp
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                except ValueError:
                    timestamp = None
                
                # Analyze the HTML content
                analysis = self.analyze_html_dump(str(file_path))
                
                # Add metadata
                analysis['file_path'] = str(file_path)
                analysis['timestamp'] = timestamp
                analysis['description'] = description
                
                results.append(analysis)
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {e}")
        
        # Sort by timestamp if available
        results.sort(key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min)
        return results
    
    def get_session_analysis(self, username: Optional[str] = None) -> Dict:
        """Get analysis for a complete session, optionally filtered by username."""
        all_analyses = self.analyze_all_dumps()
        
        # Filter by username if provided
        if username:
            all_analyses = [a for a in all_analyses if username.lower() in a['file_path'].lower()]
        
        if not all_analyses:
            return {
                'total_dumps': 0,
                'error_rate': 0,
                'captcha_rate': 0,
                'rate_limit_count': 0,
                'login_success_rate': 0,
                'rewards_page_success_rate': 0,
                'points_earned': None
            }
        
        # Calculate metrics
        total_dumps = len(all_analyses)
        error_count = sum(1 for a in all_analyses if a['has_error'])
        captcha_count = sum(1 for a in all_analyses if a['has_captcha'])
        rate_limit_count = sum(1 for a in all_analyses if a['rate_limited'])
        login_success_count = sum(1 for a in all_analyses if a['logged_in'])
        rewards_page_count = sum(1 for a in all_analyses if a['on_rewards_page'])
        
        # Find points at the beginning and end to calculate earned points
        points_values = [a['points'] for a in all_analyses if a['points'] is not None]
        initial_points = points_values[0] if points_values else None
        final_points = points_values[-1] if points_values else None
        points_earned = final_points - initial_points if (initial_points is not None and final_points is not None) else None
        
        return {
            'total_dumps': total_dumps,
            'error_rate': error_count / total_dumps if total_dumps > 0 else 0,
            'captcha_rate': captcha_count / total_dumps if total_dumps > 0 else 0,
            'rate_limit_count': rate_limit_count,
            'login_success_rate': login_success_count / total_dumps if total_dumps > 0 else 0,
            'rewards_page_success_rate': rewards_page_count / total_dumps if total_dumps > 0 else 0,
            'points_earned': points_earned,
            'initial_points': initial_points,
            'final_points': final_points
        }

# Example usage
if __name__ == "__main__":
    analyzer = HTMLAnalyzer()
    results = analyzer.analyze_all_dumps()
    print(f"Analyzed {len(results)} HTML dumps")
    
    session_analysis = analyzer.get_session_analysis()
    print(f"Session analysis: {session_analysis}")