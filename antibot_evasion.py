import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

import re
import logging
from typing import Dict, List, Optional
from playwright.async_api import Page, Browser, BrowserContext
import random
import json
import time
from human_behavior import HumanBehavior
from config import RATE_LIMIT_CONFIG, FINGERPRINT_CONFIG

class AntiBotEvasion:
    class CircuitBreaker:
        def __init__(self, threshold=3, reset_timeout=300):
            self.threshold = threshold
            self.reset_timeout = reset_timeout
            self.failure_count = 0
            self.last_failure_time = 0
            self.state = 'CLOSED'

        def record_failure(self):
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.threshold:
                self.state = 'OPEN'

        def should_block(self):
            if self.state == 'OPEN' and \
               (time.time() - self.last_failure_time) > self.reset_timeout:
                self.state = 'HALF-OPEN'
                return False
            return self.state == 'OPEN'

    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.2365.66",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0"
        ]
        
        self.languages = ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR", "nl-NL", "pl-PL", "ru-RU"]
        self.platforms = ["Windows", "MacIntel", "Linux x86_64", "Win32", "Win64"]
        
        # Enhanced rate limiting configuration
        self.request_delay = random.uniform(3, 8)  # Increased random delay between requests
        self.max_retries = RATE_LIMIT_CONFIG.get('max_retries', 3)
        self.retry_delay = RATE_LIMIT_CONFIG.get('base_retry_delay', 5)
        self.max_delay = RATE_LIMIT_CONFIG.get('max_retry_delay', 60)
        self.jitter_range = RATE_LIMIT_CONFIG.get('jitter_range', (0.8, 1.2))
        
        # Session management
        self.session_requests = 0
        self.session_start_time = None
        self.requests_per_session = 30
        self.session_duration = 7200
        self.max_retries = 7
        self.base_delay = 60
        
        # Usa consistentemente el valor inicial para jitter_range
        self.jitter_range = RATE_LIMIT_CONFIG.get('jitter_range', (0.8, 1.2))
    
    async def setup_browser_context(self, browser: Browser) -> BrowserContext:
        """Configura un contexto de navegador con evasión de detección."""
        context = await browser.new_context()
        await self._setup_fingerprint_evasion(context)
        return context
    
    async def _setup_fingerprint_evasion(self, context: BrowserContext) -> None:
        """Configura técnicas de evasión de fingerprinting."""
        await context.add_init_script("""
(function() {
    // Ocultar webdriver
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // Simular plugins sin redefinir la propiedad
    const mockPlugins = [
        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
        { name: 'Chrome PDF Viewer', filename: 'chrome-pdf-viewer' },
        { name: 'Native Client', filename: 'native-client' }
    ];

    // Modificar propiedades de navigator de manera segura
    if (Navigator.prototype) {
        const originalGetProperty = Object.getOwnPropertyDescriptor(Navigator.prototype, 'platform');
        if (originalGetProperty && originalGetProperty.configurable) {
            Object.defineProperty(Navigator.prototype, 'platform', {
                get: function() { return originalGetProperty.get.call(this); }
            });
        }
    }

    // Modificar canvas fingerprint de manera segura
    if (HTMLCanvasElement.prototype) {
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type) {
            const context = originalGetContext.apply(this, arguments);
            if (context && type === '2d') {
                const originalFillText = context.fillText;
                context.fillText = function() {
                    if (arguments.length > 0) {
                        const args = Array.from(arguments);
                        args[0] = String(args[0]) + String.fromCharCode(0x200b + Math.random() * 10);
                        return originalFillText.apply(this, args);
                    }
                    return originalFillText.apply(this, arguments);
                };
            }
            return context;
        };
    }

    // Modificar WebGL fingerprint de manera segura
    if (WebGLRenderingContext && WebGLRenderingContext.prototype) {
        const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(param) {
            if (param === 37445) return 'Intel Inc.';
            if (param === 37446) return 'Intel Iris OpenGL Engine';
            return originalGetParameter.apply(this, arguments);
        };
    }

    // Randomizar propiedades de hardware de manera segura
    try {
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => Math.floor(Math.random() * 8) + 4
        });

        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => Math.floor(Math.random() * 8) + 4
        });
    } catch (e) {}

    // Simular plugins comunes de manera segura
    try {
        if (window.chrome === undefined) {
            Object.defineProperty(window, 'chrome', {
                value: { runtime: {} },
                writable: true
            });
        }
    } catch (e) {}

    // Randomizar resolución de pantalla de manera segura
    try {
        const screenResolutions = [
            {width: 1920, height: 1080},
            {width: 1366, height: 768},
            {width: 1536, height: 864},
            {width: 1440, height: 900},
            {width: 1280, height: 720}
        ];
        const selectedResolution = screenResolutions[Math.floor(Math.random() * screenResolutions.length)];

        if (window.screen && Object.getOwnPropertyDescriptor(window, 'screen').configurable) {
            Object.defineProperty(window, 'screen', {
                value: new Proxy(window.screen, {
                    get: function(target, property) {
                        if (property === 'width') return selectedResolution.width;
                        if (property === 'height') return selectedResolution.height;
                        if (property === 'availWidth') return selectedResolution.width;
                        if (property === 'availHeight') return selectedResolution.height;
                        if (property === 'colorDepth') return 24;
                        if (property === 'pixelDepth') return 24;
                        return target[property];
                    }
                })
            });
        }
    } catch (e) {}
})();
""")
    
    async def apply_stealth_techniques(self, page: Page) -> None:
        """Aplica técnicas de sigilo adicionales a la página."""
        # Simular eventos de ratón aleatorios
        await self._simulate_mouse_movement(page)
        
        # Simular eventos de teclado ocasionales
        await self._simulate_keyboard_events(page)
        
        # Modificar propiedades de la página
        await page.evaluate('''
            // Modificar el objeto screen
            Object.defineProperty(window, 'screen', {
                value: new Proxy(window.screen, {
                    get: function(target, property) {
                        if (property === 'width') return 1920;
                        if (property === 'height') return 1080;
                        if (property === 'colorDepth') return 24;
                        return target[property];
                    }
                })
            });

            // Usar un enfoque más seguro para simular plugins sin redefinir la propiedad
            try {
                if (!Object.getOwnPropertyDescriptor(Navigator.prototype, 'plugins') ||
                    Object.getOwnPropertyDescriptor(Navigator.prototype, 'plugins').configurable) {
                    const pluginData = {
                        0: {type: 'application/x-google-chrome-pdf'},
                        description: 'Portable Document Format',
                        filename: 'internal-pdf-viewer',
                        length: 1,
                        name: 'Chrome PDF Plugin'
                    };
                    window.chrome = window.chrome || {};
                    window.chrome.runtime = window.chrome.runtime || {};
                }
            } catch (e) {
                console.log('Plugin modification skipped');
            }
        ''')
    
    async def _simulate_mouse_movement(self, page: Page) -> None:
        """Simula movimientos naturales del ratón."""
        await HumanBehavior.move_mouse_naturally(
            page,
            random.randint(100, 800),
            random.randint(100, 600)
        )
    
    async def _simulate_keyboard_events(self, page: Page) -> None:
        """Simula eventos de teclado ocasionales."""
        if random.random() < 0.1:  # 10% de probabilidad
            await page.keyboard.press('Tab')
            await HumanBehavior.random_delay(100, 300)
    
    async def handle_rate_limit(self, page: Page, attempt: int = 1) -> bool:
        # Initialize circuit breaker if not exists
        if not hasattr(self, 'circuit_breaker'):
            self.circuit_breaker = self.CircuitBreaker(
                threshold=3,
                reset_timeout=300
            )

        if self.circuit_breaker.should_block():
            logging.warning("Circuit breaker open - blocking request")
            return True

        try:
            """Enhanced rate limit handling with sophisticated backoff and session management."""
            # Initialize session if not started
            if not self.session_start_time:
                self.session_start_time = time.time()
                self.session_requests = 0
            
            # Check session limits
            current_time = time.time()
            session_age = current_time - self.session_start_time
            
            if session_age >= self.session_duration or self.session_requests >= self.requests_per_session:
                logging.info("Session limits reached, starting new session")
                await self._rotate_session(page)
                return True
            
            # Enhanced rate limit detection with HTML structure analysis
            rate_limit_indicators = [
                re.compile(r'<body[^>]*>\s*Too Many Requests\s*</body>', re.IGNORECASE),
                'text="Rate limit exceeded"',
                'text="Please try again later"',
                'text="429"',
                'text="Service Unavailable"',
                'text="Access Denied"',
                'text="IP blocked"'
            ]
            
            # Check page content and headers
            content = await page.content()
            try:
                response = await page.request.get(page.url)
                headers = response.headers if response else {}
                status_code = response.status if response else None
            except Exception as e:
                logging.warning(f"Error getting response headers: {e}")
                headers = {}
                status_code = None
            
            is_rate_limited = any(
                (isinstance(indicator, re.Pattern) and indicator.search(content)) or 
                (isinstance(indicator, str) and indicator in content)
                for indicator in rate_limit_indicators
            ) or \
            'retry-after' in headers or \
            status_code in [429, 503]
            
            if is_rate_limited:
                logging.warning(f"Rate limit detected (attempt {attempt}/{self.max_retries}")
                self.circuit_breaker.record_failure()
                from src.health_monitor import HealthMonitor
                HealthMonitor().track_rate_limit_event()  # Update metrics
                
                # Enhanced backoff with exponential factor and random variance
                base_delay = min(self.max_delay, (2.5 ** attempt) * self.retry_delay)
                jitter = random.uniform(0.7, 1.5)
                final_delay = base_delay * jitter
                
                # Parse Retry-After from headers with fallback
                try:
                    if headers.get('retry-after'):
                        final_delay = max(final_delay, float(headers['retry-after']) * 1.3)  # Add buffer to header value
                except Exception as e:
                    logging.warning(f"Error parsing Retry-After header: {e}")
            
                # Implement progressive session rotation
                if attempt > 3:
                    await self._rotate_session(page)
                elif attempt > 1:
                    await self._rotate_browser_fingerprint(page, full_rotation=True)
                
                logging.info(f"Implementing backoff strategy: waiting {final_delay:.2f} seconds")
                await HumanBehavior.random_delay(int(final_delay * 1000), int(final_delay * 1200))
                
                # Enhanced browser fingerprint rotation
                await self._rotate_browser_fingerprint(page, full_rotation=True)
                
                self.session_requests += 1
                return True
            
            self.session_requests += 1
            return False
            
        except (TimeoutError, playwright.async_api.Error) as e:
            logging.error(f"Error de red o tiempo de espera: {str(e)}")
            return True
        except Exception as e:
            logging.error(f"Error inesperado: {str(e)}")
            return True
    
    async def apply_rate_limit_delay(self):
        """Applies an intelligent delay between requests based on session state."""
        if self.session_requests > 0:
            # Progressive delay increase as session ages
            session_age = time.time() - self.session_start_time
            session_factor = min(2.0, 1.0 + (session_age / self.session_duration))
            base_delay = self.request_delay * session_factor
            
            # Add jitter to avoid detection patterns
            jitter = random.uniform(self.jitter_range[0], self.jitter_range[1])
            final_delay = base_delay * jitter
            
            await HumanBehavior.random_delay(int(final_delay * 1000), int(final_delay * 1500))
        else:
            # Standard delay for first request in session
            await HumanBehavior.random_delay(int(self.request_delay * 1000), int(self.request_delay * 1500))
    
    async def _rotate_session(self, page: Page):
        """Rotates session parameters and fingerprint."""
        self.session_start_time = time.time()
        self.session_requests = 0
        await self._rotate_browser_fingerprint(page)
        await HumanBehavior.random_delay(5000, 10000)  # Additional delay after rotation
    
    async def _rotate_browser_fingerprint(self, page: Page):
        """Rotates browser fingerprint parameters."""
        new_user_agent = random.choice(self.user_agents)
        new_language = random.choice(self.languages)
        new_platform = random.choice(self.platforms)
        
        await page.set_extra_http_headers({
            'User-Agent': new_user_agent,
            'Accept-Language': new_language,
            'Sec-CH-UA-Platform': f'"{new_platform}"',
            'Sec-CH-UA': '" Not A;Brand";v="99", "Chromium";v="99"'
        })
        
        # Update viewport and other parameters
        await page.set_viewport_size({
            'width': random.randint(1024, 1920),
            'height': random.randint(768, 1080)
        })
        
        logging.info("Rotated browser fingerprint parameters")