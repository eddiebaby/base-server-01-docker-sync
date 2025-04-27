"""
Market Data Validation Module

This module provides validation filters for market data using the Pipe and Filter architectural pattern.
It implements both synchronous and asynchronous validation methods for market data coming from
the MarketDataCollector.

:TechnologyVersion: Python 3.10+
:ArchitecturalPattern: PipeAndFilter
"""

import asyncio
import datetime
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TypeVar, Generic

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T')
MarketDataType = Dict[str, Any]  # Type for market data records

@dataclass
class ValidationResult:
    """Class for storing validation results with detailed error messages."""
    is_valid: bool
    errors: List[Dict[str, Any]] = None
    warnings: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize empty lists if None provided."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    def add_error(self, filter_name: str, field: str, message: str, data: Any = None):
        """Add a validation error with detailed information."""
        self.errors.append({
            'filter': filter_name,
            'field': field,
            'message': message,
            'data': data
        })
        self.is_valid = False
    
    def add_warning(self, filter_name: str, field: str, message: str, data: Any = None):
        """Add a validation warning with detailed information."""
        self.warnings.append({
            'filter': filter_name,
            'field': field,
            'message': message,
            'data': data
        })
    
    def merge(self, other: 'ValidationResult'):
        """Merge another ValidationResult into this one."""
        self.is_valid = self.is_valid and other.is_valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        return self


class ValidationFilter(ABC, Generic[T]):
    """Abstract base class for validation filters."""
    
    @abstractmethod
    def validate(self, data: T) -> ValidationResult:
        """Validate data synchronously."""
        pass
    
    @abstractmethod
    async def validate_async(self, data: T) -> ValidationResult:
        """Validate data asynchronously."""
        pass


class SchemaValidator(ValidationFilter[MarketDataType]):
    """Filter for validating schema (required fields and data types)."""
    
    def __init__(self, schema: Dict[str, Dict[str, Any]]):
        """
        Initialize with schema definition.
        
        Args:
            schema: Dictionary where keys are field names and values are dictionaries
                   containing 'required' (boolean) and 'type' (type object)
        """
        self.schema = schema
    
    def validate(self, data: MarketDataType) -> ValidationResult:
        """
        Validate data against the schema synchronously.
        
        Args:
            data: Market data record to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        result = ValidationResult(is_valid=True)
        
        # Check required fields and types
        for field, field_schema in self.schema.items():
            # Check if field exists when required
            if field_schema.get('required', False) and field not in data:
                result.add_error('SchemaValidator', field, f"Required field '{field}' is missing")
                continue
                
            # Skip type checking if field is not present (and not required)
            if field not in data:
                continue
                
            # Check type if specified
            expected_type = field_schema.get('type')
            if expected_type and not isinstance(data[field], expected_type):
                actual_type = type(data[field]).__name__
                expected_type_name = expected_type.__name__
                result.add_error(
                    'SchemaValidator', 
                    field, 
                    f"Field '{field}' has incorrect type. Expected {expected_type_name}, got {actual_type}", 
                    data[field]
                )
        
        return result
    
    async def validate_async(self, data: MarketDataType) -> ValidationResult:
        """
        Validate data against the schema asynchronously.
        
        Args:
            data: Market data record to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        # Schema validation is CPU-bound, so we delegate to sync version
        return await asyncio.to_thread(self.validate, data)


class RangeValidator(ValidationFilter[MarketDataType]):
    """Filter for validating value ranges."""
    
    def __init__(self, ranges: Dict[str, Dict[str, Any]]):
        """
        Initialize with range definitions.
        
        Args:
            ranges: Dictionary where keys are field names and values are dictionaries 
                   with 'min' and/or 'max' values
        """
        self.ranges = ranges
    
    def validate(self, data: MarketDataType) -> ValidationResult:
        """
        Validate that numeric values are within specified ranges.
        
        Args:
            data: Market data record to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        result = ValidationResult(is_valid=True)
        
        for field, range_def in self.ranges.items():
            if field not in data:
                continue
                
            value = data[field]
            
            # Skip non-numeric values
            if not isinstance(value, (int, float)):
                continue
                
            # Check minimum
            if 'min' in range_def and value < range_def['min']:
                result.add_error(
                    'RangeValidator', 
                    field, 
                    f"Value {value} is less than minimum {range_def['min']}", 
                    value
                )
                
            # Check maximum
            if 'max' in range_def and value > range_def['max']:
                result.add_error(
                    'RangeValidator', 
                    field, 
                    f"Value {value} is greater than maximum {range_def['max']}", 
                    value
                )
        
        return result
    
    async def validate_async(self, data: MarketDataType) -> ValidationResult:
        """Validate ranges asynchronously."""
        # Range validation is CPU-bound, so we delegate to sync version
        return await asyncio.to_thread(self.validate, data)


class ConsistencyValidator(ValidationFilter[MarketDataType]):
    """Filter for validating data consistency (e.g., high >= low)."""
    
    def __init__(self, rules: List[Dict[str, Any]]):
        """
        Initialize with consistency rules.
        
        Args:
            rules: List of rule dictionaries, each containing field names and comparison operators
        """
        self.rules = rules
    
    def validate(self, data: MarketDataType) -> ValidationResult:
        """
        Validate that data is internally consistent.
        
        Args:
            data: Market data record to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        result = ValidationResult(is_valid=True)
        
        for rule in self.rules:
            rule_type = rule.get('type')
            
            if rule_type == 'comparison':
                # Fields to compare
                field1 = rule.get('field1')
                field2 = rule.get('field2')
                
                # Skip if fields don't exist
                if field1 not in data or field2 not in data:
                    continue
                
                value1 = data[field1]
                value2 = data[field2]
                
                # Skip if values are not comparable
                if not isinstance(value1, (int, float)) or not isinstance(value2, (int, float)):
                    continue
                
                # Check the comparison
                operator = rule.get('operator')
                if operator == 'gte' and value1 < value2:
                    result.add_error(
                        'ConsistencyValidator', 
                        f"{field1}_{field2}", 
                        f"{field1} ({value1}) must be greater than or equal to {field2} ({value2})",
                        {'field1': value1, 'field2': value2}
                    )
                elif operator == 'lte' and value1 > value2:
                    result.add_error(
                        'ConsistencyValidator', 
                        f"{field1}_{field2}", 
                        f"{field1} ({value1}) must be less than or equal to {field2} ({value2})",
                        {'field1': value1, 'field2': value2}
                    )
                elif operator == 'between' and (value1 < rule.get('min') or value1 > rule.get('max')):
                    result.add_error(
                        'ConsistencyValidator', 
                        field1, 
                        f"{field1} ({value1}) must be between {rule.get('min')} and {rule.get('max')}",
                        {'value': value1, 'min': rule.get('min'), 'max': rule.get('max')}
                    )
            
            elif rule_type == 'ohlc_check':
                # Traditional high >= low and open/close within high/low bounds check
                high = data.get('high')
                low = data.get('low')
                open_price = data.get('open')
                close = data.get('close')
                
                if all(x is not None for x in [high, low, open_price, close]):
                    if high < low:
                        result.add_error(
                            'ConsistencyValidator', 
                            'high_low', 
                            f"High ({high}) must be greater than or equal to Low ({low})",
                            {'high': high, 'low': low}
                        )
                    
                    if open_price > high:
                        result.add_error(
                            'ConsistencyValidator', 
                            'open_high', 
                            f"Open ({open_price}) must be less than or equal to High ({high})",
                            {'open': open_price, 'high': high}
                        )
                    
                    if open_price < low:
                        result.add_error(
                            'ConsistencyValidator', 
                            'open_low', 
                            f"Open ({open_price}) must be greater than or equal to Low ({low})",
                            {'open': open_price, 'low': low}
                        )
                    
                    if close > high:
                        result.add_error(
                            'ConsistencyValidator', 
                            'close_high', 
                            f"Close ({close}) must be less than or equal to High ({high})",
                            {'close': close, 'high': high}
                        )
                    
                    if close < low:
                        result.add_error(
                            'ConsistencyValidator', 
                            'close_low', 
                            f"Close ({close}) must be greater than or equal to Low ({low})",
                            {'close': close, 'low': low}
                        )
        
        return result
    
    async def validate_async(self, data: MarketDataType) -> ValidationResult:
        """Validate consistency asynchronously."""
        # Consistency validation is CPU-bound, so we delegate to sync version
        return await asyncio.to_thread(self.validate, data)


class DuplicateDetector(ValidationFilter[List[MarketDataType]]):
    """Filter for detecting duplicate data records."""
    
    def __init__(self, key_fields: List[str]):
        """
        Initialize with fields that should be unique.
        
        Args:
            key_fields: List of field names that should form a unique key
        """
        self.key_fields = key_fields
    
    def _make_key(self, record: MarketDataType) -> tuple:
        """Create a tuple key from specified fields for duplicate detection."""
        return tuple(record.get(field) for field in self.key_fields)
    
    def validate(self, data: List[MarketDataType]) -> ValidationResult:
        """
        Validate that there are no duplicate records based on key fields.
        
        Args:
            data: List of market data records to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        result = ValidationResult(is_valid=True)
        
        seen_keys = set()
        duplicates = []
        
        for i, record in enumerate(data):
            key = self._make_key(record)
            
            # Skip records with None values in key fields
            if None in key:
                continue
                
            if key in seen_keys:
                duplicates.append((i, record))
            else:
                seen_keys.add(key)
        
        # Add errors for duplicates
        for i, record in duplicates:
            key_values = {field: record.get(field) for field in self.key_fields}
            result.add_error(
                'DuplicateDetector', 
                ','.join(self.key_fields), 
                f"Duplicate record found at index {i} with key values: {key_values}",
                key_values
            )
        
        return result
    
    async def validate_async(self, data: List[MarketDataType]) -> ValidationResult:
        """Validate for duplicates asynchronously."""
        # Duplicate detection can be CPU-bound for large datasets, so delegate to sync version
        return await asyncio.to_thread(self.validate, data)


class MarketDataValidator:
    """
    Main validator class that implements the Pipe and Filter pattern for market data validation.
    Takes market data from MarketDataCollector and applies various validation filters.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the validator with configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_filters()
        
    def _init_filters(self):
        """Initialize validation filters based on configuration."""
        # Schema validation
        schema = {
            'symbol': {'required': True, 'type': str},
            'date': {'required': True, 'type': (str, datetime.datetime, datetime.date)},
            'open': {'required': True, 'type': (float, int)},
            'high': {'required': True, 'type': (float, int)},
            'low': {'required': True, 'type': (float, int)},
            'close': {'required': True, 'type': (float, int)},
            'volume': {'required': True, 'type': (float, int)},
            # Optional fields
            'adj_close': {'required': False, 'type': (float, int)},
            'timestamp': {'required': False, 'type': (float, int, str, datetime.datetime)},
        }
        self.schema_validator = SchemaValidator(schema)
        
        # Range validation
        ranges = {
            'open': {'min': 0},
            'high': {'min': 0},
            'low': {'min': 0},
            'close': {'min': 0},
            'volume': {'min': 0},
            'adj_close': {'min': 0},
        }
        self.range_validator = RangeValidator(ranges)
        
        # Consistency validation
        consistency_rules = [
            {'type': 'ohlc_check'}  # Built-in OHLC checks
        ]
        self.consistency_validator = ConsistencyValidator(consistency_rules)
        
        # Duplicate detector
        key_fields = ['symbol', 'date']
        self.duplicate_detector = DuplicateDetector(key_fields)
    
    def validate_record(self, record: MarketDataType) -> ValidationResult:
        """
        Validate a single market data record synchronously.
        
        Args:
            record: Market data record to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        # Start with a valid result
        result = ValidationResult(is_valid=True)
        
        # Apply filters in sequence
        result.merge(self.schema_validator.validate(record))
        result.merge(self.range_validator.validate(record))
        result.merge(self.consistency_validator.validate(record))
        
        return result
    
    async def validate_record_async(self, record: MarketDataType) -> ValidationResult:
        """
        Validate a single market data record asynchronously.
        
        Args:
            record: Market data record to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        # Start with a valid result
        result = ValidationResult(is_valid=True)
        
        # Apply filters in sequence
        schema_result = await self.schema_validator.validate_async(record)
        result.merge(schema_result)
        
        # Short-circuit if schema validation fails
        if not result.is_valid:
            return result
        
        # Continue validation if schema is valid
        range_result = await self.range_validator.validate_async(record)
        result.merge(range_result)
        
        consistency_result = await self.consistency_validator.validate_async(record)
        result.merge(consistency_result)
        
        return result
    
    def validate_records(self, records: List[MarketDataType]) -> Dict[str, Any]:
        """
        Validate multiple market data records synchronously.
        
        Args:
            records: List of market data records to validate
            
        Returns:
            Dictionary with overall validation results and per-record results
        """
        overall_result = ValidationResult(is_valid=True)
        record_results = []
        
        # Validate each record
        for i, record in enumerate(records):
            record_result = self.validate_record(record)
            record_results.append(record_result)
            
            # Update overall validity
            if not record_result.is_valid:
                overall_result.is_valid = False
        
        # Check for duplicates across all records
        duplicate_result = self.duplicate_detector.validate(records)
        overall_result.merge(duplicate_result)
        
        return {
            'is_valid': overall_result.is_valid,
            'record_results': record_results,
            'duplicate_errors': duplicate_result.errors,
            'warnings': overall_result.warnings
        }
    
    async def validate_records_async(self, records: List[MarketDataType]) -> Dict[str, Any]:
        """
        Validate multiple market data records asynchronously.
        
        Args:
            records: List of market data records to validate
            
        Returns:
            Dictionary with overall validation results and per-record results
        """
        overall_result = ValidationResult(is_valid=True)
        
        # Validate each record concurrently
        validation_tasks = [self.validate_record_async(record) for record in records]
        record_results = await asyncio.gather(*validation_tasks)
        
        # Process results
        for record_result in record_results:
            if not record_result.is_valid:
                overall_result.is_valid = False
        
        # Check for duplicates across all records
        duplicate_result = await self.duplicate_detector.validate_async(records)
        overall_result.merge(duplicate_result)
        
        return {
            'is_valid': overall_result.is_valid,
            'record_results': record_results,
            'duplicate_errors': duplicate_result.errors,
            'warnings': overall_result.warnings
        }