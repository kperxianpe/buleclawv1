"""
Blueclaw v1.0 - Core Modules
"""

from .thinking_engine import (
    IntentType,
    ThinkingStep,
    ThinkingOption,
    ThinkingResult,
    ThinkingEngine
)

try:
    from .thinking_widgets import (
        StepWidget,
        OptionButton,
        ThinkingBlueprintWidget
    )
    WIDGETS_AVAILABLE = True
except ImportError:
    WIDGETS_AVAILABLE = False

__all__ = [
    'IntentType',
    'ThinkingStep',
    'ThinkingOption',
    'ThinkingResult',
    'ThinkingEngine',
    'StepWidget',
    'OptionButton',
    'ThinkingBlueprintWidget',
    'WIDGETS_AVAILABLE'
]
