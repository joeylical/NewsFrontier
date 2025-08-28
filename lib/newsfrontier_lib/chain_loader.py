"""
Chain Loader for NewsFrontier - Load multi-stage generation chains from database YAML configurations.

This module provides functionality to load and parse YAML-based chain configurations
from the database, convert them into chain objects for the multi-stage generator.
"""

import yaml
import logging
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from .config_service import get_config, ConfigKeys
from .database import get_db_session

logger = logging.getLogger(__name__)


class ChainValidationError(Exception):
    """Exception raised when chain YAML validation fails."""
    pass


class ChainLoader:
    """Loads and validates multi-stage generation chains from database YAML configurations."""
    
    def __init__(self):
        """Initialize the chain loader."""
        self.config = get_config()
        self.supported_stage_types = {
            'question', 'final', 'transform', 'conditional'
        }
        self.required_chain_keys = {'name', 'description', 'stages'}
        self.required_stage_keys = {'name', 'type', 'prompt'}
    
    def load_chain_from_database(self, chain_name: str) -> Optional[Dict[str, Any]]:
        """
        Load a chain configuration from database by name.
        
        Args:
            chain_name: Name of the chain to load (e.g., 'article_summary', 'clustering_detection')
            
        Returns:
            Parsed chain configuration dictionary, or None if not found/invalid
        """
        try:
            # Get chain YAML from database configuration
            config_key = f"chain_{chain_name}_config"
            chain_yaml = self.config.get(config_key)
            
            if not chain_yaml:
                logger.warning(f"Chain configuration not found for '{chain_name}' (key: {config_key})")
                return None
            
            # Parse and validate the YAML
            chain_config = self._parse_and_validate_yaml(chain_yaml, chain_name)
            
            if chain_config:
                logger.info(f"Successfully loaded chain configuration: {chain_name}")
                logger.debug(f"Chain config: {chain_config}")
            
            return chain_config
            
        except Exception as e:
            logger.error(f"Failed to load chain '{chain_name}' from database: {e}")
            return None
    
    def load_all_chains(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all chain configurations from database.
        
        Returns:
            Dictionary mapping chain names to their configurations
        """
        chains = {}
        
        # Legacy global chain types
        legacy_chains = [
            'article_summary',
            'clustering_detection', 
            'event_similarity',
            'simple_clustering',
            'event_naming'
        ]
        
        # Individual prompt chain configurations
        prompt_chains = [
            'prompt_summary_creation',
            'prompt_cluster_detection',
            'prompt_daily_summary_system', 
            'prompt_cover_image_generation'
        ]
        
        # Load legacy chains
        for chain_name in legacy_chains:
            chain_config = self.load_chain_from_database(chain_name)
            if chain_config:
                chains[chain_name] = chain_config
        
        # Load prompt-specific chains
        for prompt_name in prompt_chains:
            chain_config = self.load_prompt_chain_from_database(prompt_name)
            if chain_config:
                chains[prompt_name] = chain_config
        
        logger.info(f"Loaded {len(chains)} chain configurations from database")
        return chains
    
    def load_prompt_chain_from_database(self, prompt_name: str) -> Optional[Dict[str, Any]]:
        """
        Load a prompt-specific chain configuration from database.
        All prompts are now YAML-based by default.
        
        Args:
            prompt_name: Name of the prompt (e.g., 'prompt_summary_creation')
            
        Returns:
            Parsed chain configuration dictionary, or None if not found/invalid
        """
        try:
            # Get chain YAML from database configuration (no multi-stage toggle needed)
            chain_yaml = self.config.get(prompt_name)
            
            if not chain_yaml:
                logger.warning(f"Chain configuration not found for prompt '{prompt_name}'")
                return None
            
            # Parse and validate the YAML
            chain_config = self._parse_and_validate_yaml(chain_yaml, prompt_name)
            
            if chain_config:
                logger.info(f"Successfully loaded prompt chain configuration: {prompt_name}")
                logger.debug(f"Chain config: {chain_config}")
            
            return chain_config
            
        except Exception as e:
            logger.error(f"Failed to load prompt chain '{prompt_name}' from database: {e}")
            return None
    
    def _parse_and_validate_yaml(self, yaml_content: str, chain_name: str) -> Optional[Dict[str, Any]]:
        """
        Parse and validate YAML chain configuration.
        
        Args:
            yaml_content: Raw YAML string from database
            chain_name: Name of the chain for error reporting
            
        Returns:
            Validated chain configuration dictionary
            
        Raises:
            ChainValidationError: If validation fails
        """
        try:
            # Parse YAML
            config = yaml.safe_load(yaml_content)
            
            if not isinstance(config, dict):
                raise ChainValidationError(f"Chain '{chain_name}' must be a YAML object/dictionary")
            
            # Validate chain structure
            self._validate_chain_structure(config, chain_name)
            
            # Validate each stage
            for stage in config['stages']:
                self._validate_stage_structure(stage, chain_name)
            
            # Additional semantic validation
            self._validate_chain_semantics(config, chain_name)
            
            return config
            
        except yaml.YAMLError as e:
            raise ChainValidationError(f"Invalid YAML syntax in chain '{chain_name}': {e}")
        except Exception as e:
            if isinstance(e, ChainValidationError):
                raise
            raise ChainValidationError(f"Validation error in chain '{chain_name}': {e}")
    
    def _validate_chain_structure(self, config: Dict[str, Any], chain_name: str):
        """Validate basic chain structure."""
        # Check required top-level keys
        missing_keys = self.required_chain_keys - set(config.keys())
        if missing_keys:
            raise ChainValidationError(
                f"Chain '{chain_name}' missing required keys: {missing_keys}"
            )
        
        # Validate types
        if not isinstance(config['name'], str):
            raise ChainValidationError(f"Chain '{chain_name}' name must be a string")
        
        if not isinstance(config['description'], str):
            raise ChainValidationError(f"Chain '{chain_name}' description must be a string")
        
        if not isinstance(config['stages'], list):
            raise ChainValidationError(f"Chain '{chain_name}' stages must be a list")
        
        if len(config['stages']) == 0:
            raise ChainValidationError(f"Chain '{chain_name}' must have at least one stage")
    
    def _validate_stage_structure(self, stage: Dict[str, Any], chain_name: str):
        """Validate individual stage structure."""
        if not isinstance(stage, dict):
            raise ChainValidationError(f"Each stage in chain '{chain_name}' must be a dictionary")
        
        # Check required stage keys
        missing_keys = self.required_stage_keys - set(stage.keys())
        if missing_keys:
            raise ChainValidationError(
                f"Stage in chain '{chain_name}' missing required keys: {missing_keys}"
            )
        
        # Validate stage type
        if stage['type'] not in self.supported_stage_types:
            raise ChainValidationError(
                f"Stage type '{stage['type']}' in chain '{chain_name}' not supported. "
                f"Supported types: {self.supported_stage_types}"
            )
        
        # Validate stage-specific requirements
        if stage['type'] == 'question':
            if 'options' not in stage:
                raise ChainValidationError(
                    f"Question stage in chain '{chain_name}' must have 'options' field"
                )
            if not isinstance(stage['options'], list):
                raise ChainValidationError(
                    f"Question stage options in chain '{chain_name}' must be a list"
                )
        
        elif stage['type'] == 'conditional':
            if 'condition' not in stage:
                raise ChainValidationError(
                    f"Conditional stage in chain '{chain_name}' must have 'condition' field"
                )
            if 'next_stage' not in stage:
                raise ChainValidationError(
                    f"Conditional stage in chain '{chain_name}' must have 'next_stage' field"
                )
    
    def _validate_chain_semantics(self, config: Dict[str, Any], chain_name: str):
        """Validate chain semantic consistency."""
        stages = config['stages']
        stage_names = [stage['name'] for stage in stages]
        
        # Check for duplicate stage names
        if len(stage_names) != len(set(stage_names)):
            duplicates = [name for name in stage_names if stage_names.count(name) > 1]
            raise ChainValidationError(
                f"Chain '{chain_name}' has duplicate stage names: {duplicates}"
            )
        
        # Validate stage references in conditional stages
        for stage in stages:
            if stage['type'] == 'conditional' and 'next_stage' in stage:
                next_stage_ref = stage['next_stage']
                if isinstance(next_stage_ref, str):
                    if next_stage_ref not in stage_names:
                        raise ChainValidationError(
                            f"Stage '{stage['name']}' in chain '{chain_name}' references "
                            f"unknown stage '{next_stage_ref}'"
                        )
                elif isinstance(next_stage_ref, dict):
                    # Conditional next stage mapping
                    for condition_value, target_stage in next_stage_ref.items():
                        if target_stage not in stage_names:
                            raise ChainValidationError(
                                f"Stage '{stage['name']}' in chain '{chain_name}' references "
                                f"unknown stage '{target_stage}' for condition '{condition_value}'"
                            )
    
    @staticmethod
    def validate_yaml_syntax(yaml_content: str) -> List[str]:
        """
        Validate YAML syntax and return list of error messages.
        
        Args:
            yaml_content: Raw YAML string to validate
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        if not yaml_content or not yaml_content.strip():
            errors.append("YAML content cannot be empty")
            return errors
        
        try:
            parsed = yaml.safe_load(yaml_content)
            
            # Basic structure validation
            if not isinstance(parsed, dict):
                errors.append("YAML must contain a dictionary/object at root level")
                return errors
            
            # Check for required top-level keys
            required_keys = {'name', 'description', 'stages'}
            missing_keys = required_keys - set(parsed.keys())
            if missing_keys:
                errors.append(f"Missing required keys: {', '.join(missing_keys)}")
            
            # Validate stages structure if present
            if 'stages' in parsed:
                if not isinstance(parsed['stages'], list):
                    errors.append("'stages' must be a list")
                elif len(parsed['stages']) == 0:
                    errors.append("'stages' list cannot be empty")
                else:
                    # Validate each stage
                    for i, stage in enumerate(parsed['stages']):
                        if not isinstance(stage, dict):
                            errors.append(f"Stage {i+1} must be a dictionary")
                        else:
                            stage_errors = ChainLoader._validate_stage_basic(stage, i+1)
                            errors.extend(stage_errors)
            
        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error: {str(e)}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    @staticmethod
    def _validate_stage_basic(stage: Dict[str, Any], stage_num: int) -> List[str]:
        """Basic validation for a single stage."""
        errors = []
        required_keys = {'name', 'type', 'prompt'}
        
        missing_keys = required_keys - set(stage.keys())
        if missing_keys:
            errors.append(f"Stage {stage_num} missing keys: {', '.join(missing_keys)}")
        
        if 'type' in stage:
            valid_types = {'question', 'final', 'transform', 'conditional'}
            if stage['type'] not in valid_types:
                errors.append(
                    f"Stage {stage_num} has invalid type '{stage['type']}'. "
                    f"Valid types: {', '.join(valid_types)}"
                )
        
        return errors


# Global instance for easy access
chain_loader = ChainLoader()


def get_chain_loader() -> ChainLoader:
    """Get the global chain loader instance."""
    return chain_loader


def load_chain(chain_name: str) -> Optional[Dict[str, Any]]:
    """
    Load a chain configuration from database (convenience function).
    
    Args:
        chain_name: Name of the chain to load
        
    Returns:
        Chain configuration dictionary or None if not found
    """
    return chain_loader.load_chain_from_database(chain_name)


def validate_chain_yaml(yaml_content: str) -> List[str]:
    """
    Validate YAML chain configuration (convenience function).
    
    Args:
        yaml_content: YAML string to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    return ChainLoader.validate_yaml_syntax(yaml_content)


def is_prompt_chain_available(prompt_name: str) -> bool:
    """
    Check if a specific prompt has a valid YAML chain configuration.
    
    Args:
        prompt_name: Name of the prompt (e.g., 'prompt_summary_creation')
        
    Returns:
        True if a valid YAML chain configuration exists for this prompt
    """
    chain_loader = get_chain_loader()
    chain_yaml = chain_loader.config.get(prompt_name)
    return bool(chain_yaml and chain_yaml.strip())


def load_prompt_chain(prompt_name: str) -> Optional[Dict[str, Any]]:
    """
    Load a prompt-specific chain configuration (convenience function).
    
    Args:
        prompt_name: Name of the prompt to load chain for
        
    Returns:
        Chain configuration dictionary or None if not found/disabled
    """
    return chain_loader.load_prompt_chain_from_database(prompt_name)