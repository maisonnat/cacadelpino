import pytest
from src.security.anti_detection import AntiDetectionSystem
from src.health_monitor import HealthMonitor
from src.utils.element_locator import ElementLocator
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_rate_limit_handling():
    # Test setup
    monitor = HealthMonitor()
    
    # Simulate rate limit responses
    for attempt in range(1, 6):
        # Should trigger circuit breaker after 3 attempts
        if attempt > 3:
            # Verify circuit breaker activates
            assert monitor.metrics['rate_limit_events'] >= 3
        else:
            # Verify backoff strategy
            monitor.track_rate_limit_event()
            assert monitor.metrics['rate_limit_events'] == attempt
    
    # Verify final metrics
    assert monitor.metrics['rate_limit_events'] == 3
    assert monitor.check_vitals()['evasion_effectiveness'] > 0.7

@pytest.mark.asyncio
async def test_element_localization_strategies():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content('<div id="container"><div class="target-element">Búsqueda</div></div>')
        locator = ElementLocator()
        monitor = HealthMonitor()
        
        # Test hierarchical search
        element = await locator.find(page, {
            'parent': '#container',
            'child': '.target-element'
        }, monitor.metrics)
        assert element is not None
        assert monitor.check_vitals()['success_rate'] == 1.0
        
        # Test fuzzy text matching
        element = await locator.find(page, {
            'text': 'Búsqueda'
        }, monitor.metrics)
        assert element is not None
        assert monitor.check_vitals()['success_rate'] == 1.0

@pytest.mark.asyncio
async def test_evasion_techniques():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        anti_detection = AntiDetectionSystem({
            'fingerprint': {
                'user_agents': ['Test Agent'],
                'screen_resolutions': [(1024, 768)]
            }
        })
        
        # Test fingerprint rotation
        page = await context.new_page()
        await anti_detection.rotate_fingerprint(page)
        user_agent = await page.evaluate('navigator.userAgent')
        assert 'Test Agent' in user_agent or 'HeadlessChrome' in user_agent
        
        # Test WebGL fingerprint spoofing
        page = await context.new_page()
        webgl_vendor = await page.evaluate('WebGLRenderingContext.prototype.getParameter(37445)')
        assert webgl_vendor in ['Intel Inc.', 'Google Inc.', 'NVIDIA Corporation']