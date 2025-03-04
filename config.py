URL = "https://rewards.bing.com/"
SELECTORS = {
    "username_field": "#i0116",
    "password_field": "#i0118",
    "next_button": "#idSIButton9",
    "sign_in_button": "#idSIButton9",
    "stay_signed_in_no": 'button:has-text("No")',
    "stay_signed_in_yes": 'button:has-text("Sí")',
    "daily_set_cards": "#daily-sets mee-card",
    "more_activities_cards": "#more-activities mee-card",
    "activity_title": "h3.c-heading, h3.ng-binding",
    "activity_icon": ".mee-icon",
    "points_10": 'span.c-heading.pointsString:has-text("10"), span.pointLink:has-text("10 points"), .mee-icon-AddMedium, [data-points="10"]',
    "points_50": 'span.c-heading.pointsString:has-text("50"), span.pointLink:has-text("50 points"), [data-points="50"]',
    "points_5": 'span.c-heading.pointsString:has-text("5"), span.pointLink:has-text("5 points"), [data-points="5"]',
    "close_popup": 'button.c-glyph.glyph-cancel[aria-label="Close"]'
}

DELAY_RANGES = {
    "short": (1000, 3000),
    "medium": (2500, 5000),
    "long": (5000, 10000),
    "very_long": (15000, 30000)
}

CREDENTIALS_FILE = "credenciales.txt"

RATE_LIMIT_CONFIG = {
    'max_retries': 7,
    'base_retry_delay': 5,
    'max_retry_delay': 60,
    'jitter_range': (0.8, 1.2)
}

FINGERPRINT_CONFIG = {
    'user_agents': [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ],
    'webgl_vendors': ['Intel Inc.', 'Google Inc.', 'NVIDIA Corporation'],
    'webgl_renderers': ['Intel Iris', 'ANGLE', 'NVIDIA GeForce'],
    'screen_resolutions': [(1920, 1080), (1366, 768), (1536, 864)]
}