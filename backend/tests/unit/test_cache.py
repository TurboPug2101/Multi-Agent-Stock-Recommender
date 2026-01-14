"""
Unit tests for Cache utility.
"""

import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from common.cache import Cache


@pytest.mark.unit
class TestCache:
    """Test cache functionality."""
    
    def test_cache_key_generation(self):
        """Test cache key generation with various inputs."""
        cache = Cache()
        
        # Test basic key generation
        key1 = cache.generate_key('scouting', top_n=10)
        assert key1 == 'scouting_top_n_10'
        
        # Test with multiple parameters
        key2 = cache.generate_key('sentiment', symbol='RELIANCE.NS', company_name='Reliance')
        assert 'sentiment' in key2
        assert 'RELIANCE_NS' in key2  # Dots replaced with underscores
        assert 'Reliance' in key2
        
        # Test with special characters
        key3 = cache.generate_key('test', value='test value')
        assert ' ' not in key3  # Spaces removed
    
    def test_cache_get_set_and_ttl(self, isolated_cache):
        """Test cache get, set, and TTL expiration."""
        cache = isolated_cache
        
        # Set a value
        cache.set('test_key', {'data': 'test_value'})
        
        # Get should return the value
        result = cache.get('test_key')
        assert result == {'data': 'test_value'}
        
        # Test TTL expiration
        with freeze_time(datetime.now() + timedelta(hours=4)):
            # After 4 hours (exceeds 3-hour TTL), should return None
            result = cache.get('test_key')
            assert result is None
            # Key should be deleted
            assert 'test_key' not in cache._cache
