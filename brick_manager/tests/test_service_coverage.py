"""
Comprehensive tests for services to achieve high coverage.
Focus on easily testable service functions.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
import shutil
from services.cache_service import cache_image, is_valid_url
from services.rebrickable_service import RebrickableService


class TestCacheServiceCoverage:
    """Focused tests to increase cache_service coverage."""

    @pytest.mark.unit
    def test_is_valid_url_comprehensive(self):
        """Test URL validation comprehensively."""
        # Valid URLs
        valid_urls = [
            'https://example.com',
            'http://test.com/image.jpg',
            'https://cdn.rebrickable.com/media/parts/elements/123.jpg',
            'ftp://files.example.com/file.txt',
            'https://example.com:8080/path',
            'http://subdomain.example.com/path/to/file.png'
        ]
        
        for url in valid_urls:
            assert is_valid_url(url), f"URL should be valid: {url}"
        
        # Invalid URLs
        invalid_urls = [
            '',
            'not-a-url',
            'just-text',
            'http://',
            'https://',
            '://missing-scheme',
            'file:///local/path'
        ]
        
        for url in invalid_urls:
            assert not is_valid_url(url), f"URL should be invalid: {url}"

    @pytest.mark.unit
    @patch('services.cache_service.requests.get')
    @patch('services.cache_service.os.makedirs')
    @patch('services.cache_service.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_cache_image_success_scenarios(self, mock_file, mock_exists, mock_makedirs, mock_get):
        """Test successful image caching scenarios."""
        # Setup mocks
        mock_exists.return_value = False  # Cache directory doesn't exist
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'fake_image_data'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Test successful caching
        test_url = 'https://example.com/test.jpg'
        with patch('services.cache_service.current_app') as mock_app:
            mock_app.static_folder = '/static'
            result = cache_image(test_url)
            
            # Verify calls were made
            mock_get.assert_called_once()
            mock_makedirs.assert_called_once()
            mock_file.assert_called_once()
            assert result is not None

    @pytest.mark.unit
    @patch('services.cache_service.requests.get')
    def test_cache_image_error_scenarios(self, mock_get):
        """Test cache image error handling."""
        # Test network error
        mock_get.side_effect = Exception("Network error")
        
        test_url = 'https://example.com/test.jpg'
        with patch('services.cache_service.current_app'):
            with patch('services.cache_service.url_for', return_value='/static/default_image.png'):
                result = cache_image(test_url)
                assert result == '/static/default_image.png'  # Should return fallback on error

    @pytest.mark.unit
    @patch('services.cache_service.requests.get')
    def test_cache_image_http_errors(self, mock_get):
        """Test HTTP error handling."""
        # Test 404 error
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response
        
        test_url = 'https://example.com/nonexistent.jpg'
        with patch('services.cache_service.current_app'):
            with patch('services.cache_service.url_for', return_value='/static/default_image.png'):
                result = cache_image(test_url)
                assert result == '/static/default_image.png'

    @pytest.mark.unit
    def test_cache_image_invalid_url(self):
        """Test cache image with invalid URL."""
        with patch('services.cache_service.current_app'):
            with patch('services.cache_service.url_for', return_value='/static/default_image.png'):
                result = cache_image('not-a-valid-url')
                assert result == '/static/default_image.png'

    @pytest.mark.unit
    def test_cache_image_none_url(self):
        """Test cache image with None URL."""
        with patch('services.cache_service.current_app') as mock_app:
            # Mock url_for to avoid Flask context issues
            with patch('services.cache_service.url_for') as mock_url_for:
                mock_url_for.return_value = '/static/default_image.png'
                result = cache_image(None)
                assert result == '/static/default_image.png'
                mock_url_for.assert_called_once()


class TestRebrickableServiceCoverage:
    """Focused tests to increase rebrickable_service coverage."""

    @pytest.mark.unit
    def test_rebrickable_service_constants(self):
        """Test service constants and configuration."""
        assert RebrickableService.BASE_URL == 'https://rebrickable.com/api/v3/lego/'
        assert RebrickableService.DEFAULT_TIMEOUT == 30
        assert RebrickableService.MAX_RETRIES == 3
        assert RebrickableService.INITIAL_RETRY_DELAY == 30

    @pytest.mark.unit
    def test_get_headers_comprehensive(self):
        """Test header generation thoroughly."""
        headers = RebrickableService._get_headers()
        
        assert isinstance(headers, dict)
        assert 'Authorization' in headers
        assert 'Accept' in headers
        assert headers['Accept'] == 'application/json'
        assert 'key ' in headers['Authorization']

    @pytest.mark.unit
    @patch('services.rebrickable_service.requests.get')
    @patch('services.rebrickable_service.time.sleep')
    def test_make_request_retry_logic(self, mock_sleep, mock_get):
        """Test retry logic comprehensively."""
        # First two calls fail, third succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = Exception("500 Error")
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {'success': True}
        mock_response_success.raise_for_status = MagicMock()
        
        mock_get.side_effect = [mock_response_fail, mock_response_fail, mock_response_success]
        
        result = RebrickableService._make_request('test/')
        
        assert result == {'success': True}
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2

    @pytest.mark.unit
    @patch('services.rebrickable_service.requests.get')
    def test_make_request_max_retries_exceeded(self, mock_get):
        """Test when max retries are exceeded."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("500 Error")
        mock_get.return_value = mock_response
        
        result = RebrickableService._make_request('test/')
        
        assert result is None
        assert mock_get.call_count == RebrickableService.MAX_RETRIES

    @pytest.mark.unit
    @patch('services.rebrickable_service.requests.get')
    def test_make_request_timeout(self, mock_get):
        """Test request timeout handling."""
        import requests
        mock_get.side_effect = requests.Timeout("Request timeout")
        
        result = RebrickableService._make_request('test/')
        
        assert result is None

    @pytest.mark.unit
    @patch('services.rebrickable_service.requests.get')
    def test_make_request_connection_error(self, mock_get):
        """Test connection error handling."""
        import requests
        mock_get.side_effect = requests.ConnectionError("Connection failed")
        
        result = RebrickableService._make_request('test/')
        
        assert result is None

    @pytest.mark.unit
    def test_get_all_category_ids_with_data(self):
        """Test category ID retrieval with data."""
        with patch.object(RebrickableService, '_make_request') as mock_request:
            mock_request.return_value = {
                'results': [
                    {'id': 1, 'name': 'Baseplates'},
                    {'id': 2, 'name': 'Bricks'},
                    {'id': 3, 'name': 'Plates'}
                ]
            }
            
            result = RebrickableService.get_all_category_ids()
            
            assert isinstance(result, list)
            assert len(result) == 3
            assert result[0] == (1, 'Baseplates')
            assert result[1] == (2, 'Bricks')
            assert result[2] == (3, 'Plates')

    @pytest.mark.unit
    def test_get_all_category_ids_empty(self):
        """Test category ID retrieval with empty response."""
        with patch.object(RebrickableService, '_make_request') as mock_request:
            mock_request.return_value = {'results': []}
            
            result = RebrickableService.get_all_category_ids()
            
            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.unit
    def test_get_all_category_ids_error(self):
        """Test category ID retrieval with error."""
        with patch.object(RebrickableService, '_make_request') as mock_request:
            mock_request.return_value = None
            
            result = RebrickableService.get_all_category_ids()
            
            assert result == []

    @pytest.mark.unit
    def test_get_part_details_success(self):
        """Test part details retrieval."""
        with patch.object(RebrickableService, '_make_request') as mock_request:
            mock_request.return_value = {
                'part_num': '3001',
                'name': 'Brick 2 x 4',
                'part_cat_id': 1,
                'part_material': 'Plastic'
            }
            
            result = RebrickableService.get_part_details('3001')
            
            assert result['part_num'] == '3001'
            assert result['name'] == 'Brick 2 x 4'
            assert result['part_cat_id'] == 1
            mock_request.assert_called_once_with('parts/3001/')

    @pytest.mark.unit
    def test_get_part_details_error(self):
        """Test part details retrieval with error."""
        with patch.object(RebrickableService, '_make_request') as mock_request:
            mock_request.return_value = None
            
            result = RebrickableService.get_part_details('invalid')
            
            assert result is None

    @pytest.mark.unit
    def test_get_part_image_url_success(self):
        """Test part image URL retrieval."""
        with patch.object(RebrickableService, '_make_request') as mock_request:
            mock_request.return_value = {
                'part_img_url': 'https://cdn.rebrickable.com/media/parts/elements/3001.jpg'
            }
            
            result = RebrickableService.get_part_image_url('3001')
            
            assert result == 'https://cdn.rebrickable.com/media/parts/elements/3001.jpg'

    @pytest.mark.unit
    def test_get_part_image_url_no_image(self):
        """Test part image URL when no image exists."""
        with patch.object(RebrickableService, '_make_request') as mock_request:
            mock_request.return_value = {'part_img_url': None}
            
            result = RebrickableService.get_part_image_url('3001')
            
            assert result is None

    @pytest.mark.unit
    def test_get_part_image_url_error(self):
        """Test part image URL with error."""
        with patch.object(RebrickableService, '_make_request') as mock_request:
            mock_request.return_value = None
            
            result = RebrickableService.get_part_image_url('invalid')
            
            assert result is None

    @pytest.mark.unit
    def test_get_parts_by_category_success(self):
        """Test parts by category retrieval."""
        with patch.object(RebrickableService, '_make_request') as mock_request:
            mock_request.return_value = {
                'results': [
                    {'part_num': '3001', 'name': 'Brick 2 x 4'},
                    {'part_num': '3002', 'name': 'Brick 2 x 3'}
                ],
                'count': 2,
                'next': None,
                'previous': None
            }
            
            result = RebrickableService.get_parts_by_category(1)
            
            assert result['count'] == 2
            assert len(result['results']) == 2
            assert result['results'][0]['part_num'] == '3001'

    @pytest.mark.unit
    def test_get_parts_by_category_with_pagination(self):
        """Test parts by category with pagination."""
        with patch.object(RebrickableService, '_make_request') as mock_request:
            mock_request.return_value = {
                'results': [{'part_num': '3001', 'name': 'Brick 2 x 4'}],
                'count': 1
            }
            
            result = RebrickableService.get_parts_by_category(1, page_size=10, page=2)
            
            assert result is not None
            # Verify correct URL construction with parameters

    @pytest.mark.unit
    def test_get_parts_success(self):
        """Test general parts retrieval."""
        with patch.object(RebrickableService, '_make_request') as mock_request:
            mock_request.return_value = {
                'results': [
                    {'part_num': '3001', 'name': 'Brick 2 x 4'}
                ],
                'count': 1
            }
            
            filters = {'part_cat_id': 1}
            result = RebrickableService.get_parts(filters=filters)
            
            assert result['count'] == 1
            assert len(result['results']) == 1

    @pytest.mark.unit
    def test_get_colors_success(self):
        """Test colors retrieval."""
        with patch.object(RebrickableService, '_make_request') as mock_request:
            mock_request.return_value = {
                'results': [
                    {'id': 0, 'name': 'Black', 'rgb': '05131D'},
                    {'id': 1, 'name': 'Blue', 'rgb': '0055BF'}
                ],
                'count': 2
            }
            
            result = RebrickableService.get_colors()
            
            assert result['count'] == 2
            assert len(result['results']) == 2
            assert result['results'][0]['name'] == 'Black'

    @pytest.mark.unit
    def test_get_part_images_bulk_mixed_results(self):
        """Test bulk image retrieval with mixed results."""
        with patch.object(RebrickableService, 'get_part_image_url') as mock_get_image:
            mock_get_image.side_effect = [
                'https://cdn.rebrickable.com/media/parts/elements/3001.jpg',
                None,  # No image for this part
                'https://cdn.rebrickable.com/media/parts/elements/3003.jpg'
            ]
            
            part_nums = ['3001', '3002', '3003']
            result = RebrickableService.get_part_images_bulk(part_nums)
            
            assert len(result) == 3
            assert result['3001'] == 'https://cdn.rebrickable.com/media/parts/elements/3001.jpg'
            assert result['3002'] is None
            assert result['3003'] == 'https://cdn.rebrickable.com/media/parts/elements/3003.jpg'

    @pytest.mark.unit
    def test_get_part_images_bulk_empty_list(self):
        """Test bulk image retrieval with empty list."""
        result = RebrickableService.get_part_images_bulk([])
        
        assert result == {}


class TestConfigCoverage:
    """Test configuration module for high coverage."""
    
    @pytest.mark.unit
    def test_config_import(self):
        """Test that config can be imported."""
        from config import Config
        assert hasattr(Config, 'REBRICKABLE_TOKEN')
        assert hasattr(Config, 'SECRET_KEY')
        assert hasattr(Config, 'SQLALCHEMY_DATABASE_URI')


class TestServiceIntegration:
    """Integration tests for service interactions."""
    
    @pytest.mark.integration
    def test_cache_and_rebrickable_integration(self):
        """Test cache service with rebrickable URLs."""
        with patch('services.cache_service.requests.get') as mock_get:
            with patch('services.cache_service.current_app'):
                with patch('services.cache_service.url_for') as mock_url_for:
                    mock_url_for.return_value = '/static/default_image.png'
                    
                    # Test with rebrickable-like URL
                    test_url = 'https://cdn.rebrickable.com/media/parts/elements/3001.jpg'
                    
                    # Setup successful response
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.content = b'fake_image_data'
                    mock_response.raise_for_status = MagicMock()
                    mock_get.return_value = mock_response
                    
                    with patch('services.cache_service.os.makedirs'):
                        with patch('services.cache_service.os.path.exists', return_value=True):
                            with patch('builtins.open', mock_open()):
                                result = cache_image(test_url)
                                assert result is not None