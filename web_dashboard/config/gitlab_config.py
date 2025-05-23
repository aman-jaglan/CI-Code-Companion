"""
GitLab Integration Configuration for CI Code Companion Dashboard
"""

import os
import logging
import re
from typing import Dict, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

class GitLabConfig:
    def __init__(self):
        # Log all environment variables (excluding secrets)
        logger.debug("Environment variables:")
        for key in os.environ:
            if 'SECRET' not in key and 'PASSWORD' not in key:
                logger.debug(f"{key}: {os.environ[key]}")
        
        self.app_id = os.getenv('GITLAB_APP_ID')
        self.app_secret = os.getenv('GITLAB_APP_SECRET')
        self.redirect_uri = os.getenv('GITLAB_REDIRECT_URI', 'http://localhost:5001/gitlab/callback')
        self.scope = 'api read_registry write_registry'
        
        # Log detailed configuration status
        logger.info("GitLab Configuration Status:")
        logger.info(f"App ID present: {'Yes' if self.app_id else 'No'}")
        if self.app_id:
            logger.info(f"App ID length: {len(self.app_id)}")
        logger.info(f"App Secret present: {'Yes' if self.app_secret else 'No'}")
        if self.app_secret:
            logger.info(f"App Secret length: {len(self.app_secret)}")
        logger.info(f"Redirect URI: {self.redirect_uri}")
        logger.info(f"Configured scopes: {self.scope}")
        
        # Validate credentials
        if not self.app_id:
            logger.error("GITLAB_APP_ID environment variable is not set")
        
        if not self.app_secret:
            logger.error("GITLAB_APP_SECRET environment variable is not set")
        elif len(self.app_secret) < 32:
            logger.error("Invalid GitLab Application Secret format")
            self.app_secret = None
    
    @property
    def is_configured(self) -> bool:
        """Check if GitLab integration is configured."""
        is_config = bool(self.app_id and self.app_secret)
        logger.info(f"GitLab configuration status: {'Configured' if is_config else 'Not configured'}")
        return is_config
    
    def get_oauth_url(self) -> str:
        """Get GitLab OAuth URL for authorization."""
        if not self.is_configured:
            logger.error("Attempting to get OAuth URL without proper configuration")
            return None
            
        # Ensure all parameters are properly encoded
        encoded_redirect_uri = quote(self.redirect_uri, safe='')
        encoded_scope = quote(self.scope, safe='')
        
        url = (
            f"https://gitlab.com/oauth/authorize"
            f"?client_id={self.app_id}"
            f"&redirect_uri={encoded_redirect_uri}"
            f"&response_type=code"
            f"&scope={encoded_scope}"
        )
        logger.debug(f"Generated OAuth URL: {url}")
        return url
    
    def to_dict(self) -> Dict[str, str]:
        """Convert config to dictionary."""
        return {
            'app_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope
        } 