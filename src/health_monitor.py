import logging
from datetime import datetime
from typing import Dict

class HealthMonitor:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.metrics = {
                'localization_success': 0,
                'localization_failures': 0,
                'rate_limit_events': 0,
                'evasion_success': 0,
                'proxy_failures': 0
            }
            cls._instance.start_time = datetime.now()
        return cls._instance

    def track_rate_limit_event(self):
        if not hasattr(self, 'metrics'):
            self.metrics = {'rate_limit_events': 0}
        if 'rate_limit_events' not in self.metrics:
            self.metrics['rate_limit_events'] = 0
        self.metrics['rate_limit_events'] += 1

    def record_success(self, metric_type: str):
        if metric_type + '_success' in self.metrics:
            self.metrics[metric_type + '_success'] += 1

    def record_failure(self, metric_type: str):
        if metric_type + '_failures' in self.metrics:
            self.metrics[metric_type + '_failures'] += 1

    def check_vitals(self) -> Dict:
        total_requests = self.metrics['localization_success'] + self.metrics['localization_failures']
        
        return {
            'success_rate': self.metrics['localization_success'] / total_requests if total_requests > 0 else 0,
            'rate_limit_frequency': self.metrics['rate_limit_events'] / ((datetime.now() - self.start_time).total_seconds() / 3600),
            'evasion_effectiveness': self.metrics['evasion_success'] / (self.metrics['evasion_success'] + self.metrics['proxy_failures']) if (self.metrics['evasion_success'] + self.metrics['proxy_failures']) > 0 else 0,
            'uptime': (datetime.now() - self.start_time).total_seconds()
        }

    def generate_report(self) -> str:
        vitals = self.check_vitals()
        return f"""
        System Health Report:
        ---------------------
        Localization Success Rate: {vitals['success_rate']:.2%}
        Rate Limit Events/Hour: {vitals['rate_limit_frequency']:.2f}
        Evasion Effectiveness: {vitals['evasion_effectiveness']:.2%}
        System Uptime: {vitals['uptime']:.2f} seconds
        """

# Initialize logger for monitoring
logger = logging.getLogger('health_monitor')
logger.setLevel(logging.INFO)