"""
Multi-stage generation framework for NewsFrontier.

This module provides a lightweight alternative to LangChain for conditional,
multi-step LLM processing with predefined question sets and enumerated responses.
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class StageType(Enum):
    """Types of processing stages"""
    QUESTION = "question"        # Ask a question and branch based on response
    FINAL = "final"             # Final processing stage
    TRANSFORM = "transform"      # Data transformation stage


@dataclass
class StageConfig:
    """Configuration for a single processing stage"""
    id: str
    stage_type: StageType
    prompt_template: str
    
    # For QUESTION stages
    expected_responses: Optional[Dict[str, str]] = None  # response -> next_stage_id
    response_extractor: Optional[str] = None  # regex pattern to extract response
    
    # For FINAL stages  
    is_final: bool = False
    
    # For TRANSFORM stages
    transformer: Optional[Callable] = None
    
    # General options
    temperature: float = 0.3
    max_tokens: int = 500
    model_preference: str = "summary"  # "summary" or "analysis"
    
    # Validation
    required_variables: List[str] = field(default_factory=list)


@dataclass
class ChainConfig:
    """Configuration for a complete processing chain"""
    name: str
    description: str
    initial_stage: str
    stages: Dict[str, StageConfig]
    
    def validate(self) -> bool:
        """Validate the chain configuration"""
        if self.initial_stage not in self.stages:
            raise ValueError(f"Initial stage '{self.initial_stage}' not found in stages")
        
        # Check all referenced stages exist
        for stage in self.stages.values():
            if stage.expected_responses:
                for next_stage in stage.expected_responses.values():
                    if next_stage not in self.stages:
                        raise ValueError(f"Referenced stage '{next_stage}' not found")
        
        # Check at least one final stage exists
        final_stages = [s for s in self.stages.values() if s.is_final]
        if not final_stages:
            raise ValueError("Chain must have at least one final stage")
            
        return True


class MultiStageGenerator:
    """
    Multi-stage content generator using conditional prompting.
    
    Supports predefined question sets with enumerated responses for 
    branching logic, enabling complex processing flows with smaller models.
    """
    
    def __init__(self, llm_client, config_service=None):
        """
        Initialize the multi-stage generator.
        
        Args:
            llm_client: Enhanced LLM client for making requests
            config_service: Configuration service for model settings
        """
        self.llm_client = llm_client
        self.config_service = config_service
        self.chains: Dict[str, ChainConfig] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def register_chain(self, chain_config: ChainConfig) -> None:
        """Register a new processing chain"""
        chain_config.validate()
        self.chains[chain_config.name] = chain_config
        self.logger.info(f"Registered processing chain: {chain_config.name}")
        
    def execute_chain(self, chain_name: str, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complete processing chain.
        
        Args:
            chain_name: Name of the chain to execute
            initial_data: Initial data to process
            
        Returns:
            Result dict with final output and execution metadata
        """
        if chain_name not in self.chains:
            raise ValueError(f"Chain '{chain_name}' not found")
            
        chain = self.chains[chain_name]
        current_stage = chain.initial_stage
        context = initial_data.copy()
        execution_log = []
        
        self.logger.info(f"Starting chain execution: {chain_name}")
        
        try:
            while current_stage:
                stage_config = chain.stages[current_stage]
                self.logger.debug(f"Executing stage: {current_stage}")
                
                # Execute current stage
                stage_result = self._execute_stage(stage_config, context)
                
                # Log execution
                execution_log.append({
                    "stage": current_stage,
                    "stage_type": stage_config.stage_type.value,
                    "result": stage_result
                })
                
                # Update context with result
                if isinstance(stage_result, dict):
                    context.update(stage_result)
                else:
                    context["stage_result"] = stage_result
                
                # Determine next stage
                if stage_config.is_final:
                    self.logger.info(f"Chain completed at final stage: {current_stage}")
                    break
                    
                current_stage = self._get_next_stage(stage_config, stage_result, context)
                
                if not current_stage:
                    self.logger.warning("Chain execution stopped - no next stage determined")
                    break
                    
        except Exception as e:
            self.logger.error(f"Chain execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_log": execution_log,
                "context": context
            }
            
        return {
            "success": True,
            "result": context.get("stage_result", context),
            "execution_log": execution_log,
            "final_stage": current_stage,
            "context": context
        }
        
    def _execute_stage(self, stage_config: StageConfig, context: Dict[str, Any]) -> Any:
        """Execute a single stage"""
        try:
            if stage_config.stage_type == StageType.QUESTION:
                return self._execute_question_stage(stage_config, context)
            elif stage_config.stage_type == StageType.FINAL:
                return self._execute_final_stage(stage_config, context)
            elif stage_config.stage_type == StageType.TRANSFORM:
                return self._execute_transform_stage(stage_config, context)
            else:
                raise ValueError(f"Unknown stage type: {stage_config.stage_type}")
                
        except Exception as e:
            self.logger.error(f"Stage execution failed: {e}")
            raise
            
    def _execute_question_stage(self, stage_config: StageConfig, context: Dict[str, Any]) -> str:
        """Execute a question stage that branches based on response"""
        # Validate required variables
        self._validate_required_variables(stage_config, context)
        
        # Format prompt
        prompt = stage_config.prompt_template.format(**context)
        
        # Make LLM request
        if stage_config.model_preference == "analysis":
            response = self.llm_client.create_analysis_completion(
                prompt=prompt,
                temperature=stage_config.temperature,
                max_tokens=stage_config.max_tokens
            )
        else:
            response = self.llm_client.create_summary_completion(
                prompt=prompt,
                temperature=stage_config.temperature,
                max_tokens=stage_config.max_tokens
            )
            
        if not response:
            raise RuntimeError("LLM request failed - no response received")
            
        # Extract structured response if needed
        if stage_config.response_extractor:
            match = re.search(stage_config.response_extractor, response, re.IGNORECASE)
            if match:
                response = match.group(1).strip()
            else:
                self.logger.warning(f"Failed to extract response using pattern: {stage_config.response_extractor}")
                
        self.logger.debug(f"Question stage response: {response}")
        return response.strip()
        
    def _execute_final_stage(self, stage_config: StageConfig, context: Dict[str, Any]) -> str:
        """Execute a final processing stage"""
        # Validate required variables
        self._validate_required_variables(stage_config, context)
        
        # Format prompt
        prompt = stage_config.prompt_template.format(**context)
        
        # Make LLM request
        if stage_config.model_preference == "analysis":
            response = self.llm_client.create_analysis_completion(
                prompt=prompt,
                temperature=stage_config.temperature,
                max_tokens=stage_config.max_tokens
            )
        else:
            response = self.llm_client.create_summary_completion(
                prompt=prompt,
                temperature=stage_config.temperature,
                max_tokens=stage_config.max_tokens
            )
            
        if not response:
            raise RuntimeError("LLM request failed - no response received")
            
        self.logger.debug(f"Final stage completed with {len(response)} characters")
        return response.strip()
        
    def _execute_transform_stage(self, stage_config: StageConfig, context: Dict[str, Any]) -> Any:
        """Execute a data transformation stage"""
        if not stage_config.transformer:
            raise ValueError("Transform stage missing transformer function")
            
        return stage_config.transformer(context)
        
    def _get_next_stage(self, stage_config: StageConfig, stage_result: Any, context: Dict[str, Any]) -> Optional[str]:
        """Determine the next stage based on current stage result"""
        if not stage_config.expected_responses:
            return None
            
        # Try exact match first
        response_text = str(stage_result).strip().lower()
        
        for expected_response, next_stage in stage_config.expected_responses.items():
            if expected_response.lower() == response_text:
                self.logger.debug(f"Exact match: '{response_text}' -> {next_stage}")
                return next_stage
                
        # Try partial match
        for expected_response, next_stage in stage_config.expected_responses.items():
            if expected_response.lower() in response_text:
                self.logger.debug(f"Partial match: '{expected_response}' in '{response_text}' -> {next_stage}")
                return next_stage
                
        # Try reverse partial match
        for expected_response, next_stage in stage_config.expected_responses.items():
            if response_text in expected_response.lower():
                self.logger.debug(f"Reverse partial match: '{response_text}' in '{expected_response}' -> {next_stage}")
                return next_stage
        
        # Default fallback if configured
        if "default" in stage_config.expected_responses:
            default_stage = stage_config.expected_responses["default"]
            self.logger.warning(f"No match found for '{response_text}', using default: {default_stage}")
            return default_stage
            
        self.logger.error(f"No matching response found for: '{response_text}'. Expected one of: {list(stage_config.expected_responses.keys())}")
        return None
        
    def _validate_required_variables(self, stage_config: StageConfig, context: Dict[str, Any]) -> None:
        """Validate that all required variables are present in context"""
        missing_vars = [var for var in stage_config.required_variables if var not in context]
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")


# Utility functions for creating common stage patterns

def create_binary_question_stage(stage_id: str, prompt: str, yes_stage: str, no_stage: str, 
                                 required_vars: List[str] = None) -> StageConfig:
    """Create a simple yes/no question stage"""
    return StageConfig(
        id=stage_id,
        stage_type=StageType.QUESTION,
        prompt_template=prompt + "\n\n请回答：是 或 否",
        expected_responses={
            "是": yes_stage,
            "yes": yes_stage,
            "y": yes_stage,
            "否": no_stage,
            "no": no_stage,
            "n": no_stage
        },
        required_variables=required_vars or [],
        temperature=0.1  # Low temperature for consistent responses
    )


def create_category_question_stage(stage_id: str, prompt: str, categories: Dict[str, str],
                                  required_vars: List[str] = None) -> StageConfig:
    """Create a categorization question stage"""
    # Build response mapping
    responses = {}
    for category, next_stage in categories.items():
        responses[category.lower()] = next_stage
    
    # Add default if not provided
    if "default" not in responses and "其他" not in responses:
        responses["default"] = list(categories.values())[0]  # Use first category as default
    
    return StageConfig(
        id=stage_id,
        stage_type=StageType.QUESTION,
        prompt_template=prompt,
        expected_responses=responses,
        required_variables=required_vars or [],
        temperature=0.2
    )


def create_final_generation_stage(stage_id: str, prompt: str, required_vars: List[str] = None,
                                 model_preference: str = "summary", temperature: float = 0.7) -> StageConfig:
    """Create a final content generation stage"""
    return StageConfig(
        id=stage_id,
        stage_type=StageType.FINAL,
        prompt_template=prompt,
        is_final=True,
        required_variables=required_vars or [],
        model_preference=model_preference,
        temperature=temperature,
        max_tokens=1000
    )