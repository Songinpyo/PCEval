"""
Evaluation package for Arduino-LLM project.

This package provides evaluation metrics for hardware designs and code generation.
"""

from .hardware_metrics import (
    check_duplicate_connections,
    check_endpoint_conflicts,
    check_unused_components,
    compare_with_reference,
    check_direct_connections,
    evaluate_hardware_design
)
from .code_metrics import (
    calculate_codebleu
)

__all__ = [
    'check_duplicate_connections',
    'check_endpoint_conflicts',
    'check_unused_components',
    'compare_with_reference',
    'check_direct_connections',
    'evaluate_hardware_design',
    'calculate_codebleu'
]
