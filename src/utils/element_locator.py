class LocationStrategy:
    @staticmethod
    def find_element(page, identifier):
        raise NotImplementedError

class CSSLocationStrategy(LocationStrategy):
    @staticmethod
    def find_element(page, identifier):
        return page.query_selector(identifier)

class XPathLocationStrategy(LocationStrategy):
    @staticmethod
    def find_element(page, identifier):
        return page.query_selector(f'xpath={identifier}')

class TextLocationStrategy(LocationStrategy):
    @staticmethod
    def find_element(page, identifier):
        return page.query_selector(f'text="{identifier}"')
import logging
from thefuzz import fuzz

logger = logging.getLogger(__name__)

class ElementLocator:
    def __init__(self, strategies=None):
        self.strategies = strategies or [
            CSSLocationStrategy(),
            XPathLocationStrategy(),
            TextLocationStrategy()
        ]
    
    async def find(self, page, selector, metrics=None):
        try:
            if 'parent' in selector and 'child' in selector:
                parent = await page.query_selector(selector['parent'])
                if parent:
                    element = await parent.query_selector(selector['child'])
                    if element:
                        return element
            elif 'text' in selector:
                elements = await page.query_selector_all('*')
                for element in elements:
                    text = await element.inner_text()
                    if selector['text'] in text:
                        return element
            return None
        except Exception as e:
            logging.error(f"Element detection failed: {str(e)}")
            return None
        """Enhanced element location with multiple fallback strategies and metadata collection"""
        strategies = [
            self._hierarchical_search,
            self._fuzzy_text_match,
            self._css_xpath_hybrid,
            self._accessibility_tree
        ]

        for strategy in strategies:
            element = await strategy(page, identifier, metadata)
            if element:
                self._record_success(metadata, strategy.__name__)
                return element
        
        self._handle_missing_element(metadata)
        return None

    async def _hierarchical_search(self, page, identifier, metadata):
        try:
            parent = await page.query_selector(identifier.get('parent', 'body'))
            if not parent:
                return None
            return await parent.query_selector(identifier['child'])
        except Exception as e:
            logger.error(f"Hierarchical search failed: {str(e)}")
            return None
        if 'parent' in identifier and 'child' in identifier:
            parent = await page.query_selector(identifier['parent'])
            if parent:
                return await parent.query_selector(identifier['child'])
        return None

    async def _fuzzy_text_match(self, page, identifier, metadata):
        if 'text' in identifier:
            elements = await page.query_selector_all('*')
            for element in elements:
                text = await element.text_content()
                if text and fuzz.partial_ratio(text, identifier['text']) > 85:
                    return element
        return None

    async def _css_xpath_hybrid(self, page, identifier, metadata):
        selectors = []
        if 'css' in identifier:
            selectors.append(identifier['css'])
        if 'xpath' in identifier:
            selectors.append(f'xpath={identifier["xpath"]}')
        
        for selector in selectors:
            element = await page.query_selector(selector)
            if element:
                return element
        return None

    def _record_success(self, metadata, strategy_name):
        metadata['last_success_strategy'] = strategy_name
        metadata['success_count'] = metadata.get('success_count', 0) + 1

    async def _accessibility_tree(self, page, identifier, metadata):
        if 'aria_label' in identifier:
            return await page.query_selector(f'[aria-label="{identifier["aria_label"]}"]')
        return None

    def _handle_missing_element(self, metadata):
        logger.error(f"Element detection failed. Metadata: {metadata}")
        if 'failure_count' in metadata:
            metadata['failure_count'] += 1
        else:
            metadata['failure_count'] = 1
    
    def _collect_metadata(self, element, metadata):
        if metadata:
            metadata['html'] = element.inner_html()
            metadata['attributes'] = element.evaluate('el => el.attributes')
            metadata['position'] = element.bounding_box()