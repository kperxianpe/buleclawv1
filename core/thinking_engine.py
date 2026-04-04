#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
thinking_engine.py - Blueclaw v1.0 Thinking Blueprint Engine

Core engine for intent recognition, thinking steps generation,
and four-option interactive mode.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
import re


class IntentType(Enum):
    """User intent types"""
    CREATE = "create"           # Create/generate something
    MODIFY = "modify"           # Modify/change something
    QUESTION = "question"       # Ask a question
    CHAT = "chat"               # Casual conversation
    EXECUTE = "execute"         # Execute a command
    ANALYZE = "analyze"         # Analyze something
    UNKNOWN = "unknown"         # Unknown intent


@dataclass
class ThinkingStep:
    """Single thinking step"""
    step_number: int
    icon: str
    title: str
    description: str
    status: str = "pending"  # pending, active, completed


@dataclass
class ThinkingOption:
    """Four-option UI option"""
    option_id: str  # A, B, C, D
    label: str      # A, B, C, D
    icon: str
    title: str
    description: str
    confidence: int  # 0-100
    color: str       # CSS color
    action: str      # Action identifier
    params: Dict = field(default_factory=dict)


@dataclass
class ThinkingResult:
    """Complete thinking result"""
    intent: IntentType
    intent_confidence: float
    thinking_steps: List[ThinkingStep]
    options: List[ThinkingOption]
    context: Dict = field(default_factory=dict)
    
    def get_option(self, option_id: str) -> Optional[ThinkingOption]:
        """Get option by ID"""
        for opt in self.options:
            if opt.option_id == option_id:
                return opt
        return None


class ThinkingEngine:
    """
    Thinking Blueprint Engine
    
    Analyzes user input and generates:
    1. Intent recognition with confidence
    2. Thinking process steps
    3. Four options with confidence scores
    """
    
    # Intent detection keywords
    INTENT_KEYWORDS = {
        IntentType.CREATE: [
            "create", "make", "build", "generate", "write", "design",
            "create", "create", "generate", "write", "develop"
        ],
        IntentType.MODIFY: [
            "modify", "change", "update", "edit", "fix", "improve",
            "modify", "change", "update", "adjust"
        ],
        IntentType.QUESTION: [
            "what", "how", "why", "when", "where", "who",
            "what", "how", "why", "is", "can", "do"
        ],
        IntentType.CHAT: [
            "hello", "hi", "hey", "thanks", "bye",
            "hello", "hi", "talk", "chat", "joke"
        ],
        IntentType.EXECUTE: [
            "run", "execute", "start", "launch", "open",
            "run", "execute", "open", "start", "call"
        ],
        IntentType.ANALYZE: [
            "analyze", "check", "review", "inspect", "examine",
            "analyze", "check", "view", "inspect", "evaluate"
        ]
    }
    
    def __init__(self):
        self.history: List[Dict] = []
    
    def analyze(self, user_input: str) -> ThinkingResult:
        """
        Main analysis method
        
        Args:
            user_input: User's input text
            
        Returns:
            ThinkingResult with intent, steps, and options
        """
        # 1. Recognize intent
        intent, confidence = self._recognize_intent(user_input)
        
        # 2. Generate thinking steps
        steps = self._generate_thinking_steps(intent, user_input)
        
        # 3. Generate four options
        options = self._generate_options(intent, user_input)
        
        # 4. Build context
        context = {
            "original_input": user_input,
            "timestamp": self._get_timestamp(),
            "history_count": len(self.history)
        }
        
        # Save to history
        result = ThinkingResult(
            intent=intent,
            intent_confidence=confidence,
            thinking_steps=steps,
            options=options,
            context=context
        )
        
        self.history.append({
            "input": user_input,
            "intent": intent.value,
            "confidence": confidence
        })
        
        return result
    
    def _recognize_intent(self, text: str) -> Tuple[IntentType, float]:
        """
        Recognize user intent with confidence score
        
        Args:
            text: User input text
            
        Returns:
            Tuple of (intent_type, confidence)
        """
        text_lower = text.lower()
        scores = {intent: 0 for intent in IntentType}
        
        # Keyword matching
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[intent] += 1
        
        # Pattern matching
        if re.search(r"^what\s+(is|are|does)", text_lower):
            scores[IntentType.QUESTION] += 2
        
        if re.search(r"\?$", text):
            scores[IntentType.QUESTION] += 1
        
        if re.search(r"(create|make|build)\s+(a|an|the)", text_lower):
            scores[IntentType.CREATE] += 2
        
        # Find highest score
        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]
        
        # Calculate confidence
        total_score = sum(scores.values())
        if total_score == 0:
            confidence = 0.3
        else:
            confidence = min(0.95, max_score / total_score * 0.8 + 0.2)
        
        return max_intent, confidence
    
    def _generate_thinking_steps(
        self, 
        intent: IntentType, 
        user_input: str
    ) -> List[ThinkingStep]:
        """Generate thinking steps based on intent"""
        
        # Base steps for all intents
        steps = [
            ThinkingStep(
                step_number=1,
                icon="[?]",
                title="Intent Analysis",
                description=f"Recognized user intent: {intent.value}"
            ),
            ThinkingStep(
                step_number=2,
                icon="[~]",
                title="Context Analysis",
                description="Analyzing conversation history..."
            ),
            ThinkingStep(
                step_number=3,
                icon="[!]",
                title="Generate Options",
                description=f"Generating 4 options based on intent '{intent.value}'..."
            )
        ]
        
        # Add intent-specific steps
        if intent == IntentType.CREATE:
            steps.insert(2, ThinkingStep(
                step_number=2,
                icon="[*]",
                title="Requirements Analysis",
                description="Extracting creation requirements from input..."
            ))
        elif intent == IntentType.QUESTION:
            steps.insert(2, ThinkingStep(
                step_number=2,
                icon="[@]",
                title="Question Analysis",
                description="Determining question type and scope..."
            ))
        elif intent == IntentType.EXECUTE:
            steps.insert(2, ThinkingStep(
                step_number=2,
                icon="[>]",
                title="Command Analysis",
                description="Parsing command structure and parameters..."
            ))
        
        # Renumber steps
        for i, step in enumerate(steps):
            step.step_number = i + 1
        
        return steps
    
    def _generate_options(
        self, 
        intent: IntentType, 
        user_input: str,
        context: Dict = None
    ) -> List[ThinkingOption]:
        """Generate four options based on intent"""
        
        option_templates = {
            IntentType.CREATE: [
                ("A", "[*]", "Quick Template", 
                 "Use pre-built template for rapid creation", 90,
                 "#4caf50", "quick_template"),
                ("B", "[+]", "Custom Creation", 
                 "Build from scratch with full customization", 85,
                 "#2196f3", "custom_create"),
                ("C", "[@]", "View Examples", 
                 "See similar examples first", 70,
                 "#ff9800", "view_examples"),
                ("D", "[?]", "AI Recommendation", 
                 "Let AI suggest the best approach", 75,
                 "#9c27b0", "ai_recommend")
            ],
            IntentType.QUESTION: [
                ("A", "[@]", "Quick Answer", 
                 "Give a concise direct answer", 95,
                 "#4caf50", "quick_answer"),
                ("B", "[+]", "Detailed Explanation", 
                 "Provide comprehensive explanation", 85,
                 "#2196f3", "detailed_explain"),
                ("C", "[~]", "Search Online", 
                 "Search for latest information", 75,
                 "#ff9800", "search_online"),
                ("D", "[*]", "Related Resources", 
                 "Show related learning resources", 70,
                 "#9c27b0", "show_resources")
            ],
            IntentType.CHAT: [
                ("A", "[:)]", "Continue Chat", 
                 "Continue conversation", 90,
                 "#4caf50", "chat"),
                ("B", "[*]", "Tell Joke", 
                 "Tell a joke", 70,
                 "#ff9800", "joke"),
                ("C", "[+]", "Start Task", 
                 "Switch to task mode", 85,
                 "#2196f3", "start_task"),
                ("D", "[?]", "Show Capabilities", 
                 "Learn what I can do", 75,
                 "#9c27b0", "capabilities")
            ],
            IntentType.EXECUTE: [
                ("A", "[>]", "Execute Now", 
                 "Execute command immediately", 80,
                 "#4caf50", "execute"),
                ("B", "[?]", "Ask Parameters", 
                 "Ask for more information", 85,
                 "#2196f3", "ask_params"),
                ("C", "[@]", "Show Help", 
                 "View usage help", 70,
                 "#ff9800", "show_help"),
                ("D", "[~]", "Preview First", 
                 "Preview before execution", 75,
                 "#9c27b0", "preview")
            ],
            IntentType.MODIFY: [
                ("A", "[+]", "Quick Modify", 
                 "Make simple changes", 85,
                 "#4caf50", "quick_modify"),
                ("B", "[*]", "Advanced Edit", 
                 "Detailed modification options", 80,
                 "#2196f3", "advanced_edit"),
                ("C", "[@]", "Show Current", 
                 "View current state first", 75,
                 "#ff9800", "show_current"),
                ("D", "[?]", "Suggest Changes", 
                 "AI suggests modifications", 78,
                 "#9c27b0", "suggest")
            ],
            IntentType.ANALYZE: [
                ("A", "[@]", "Quick Analysis", 
                 "Fast summary analysis", 88,
                 "#4caf50", "quick_analyze"),
                ("B", "[+]", "Deep Analysis", 
                 "Comprehensive detailed analysis", 82,
                 "#2196f3", "deep_analyze"),
                ("C", "[*]", "Visual Report", 
                 "Generate visual analysis report", 75,
                 "#ff9800", "visual_report"),
                ("D", "[?]", "Compare Options", 
                 "Compare different approaches", 70,
                 "#9c27b0", "compare")
            ],
            IntentType.UNKNOWN: [
                ("A", "[>]", "Execute Directly", 
                 "Execute command directly", 80,
                 "#4caf50", "execute"),
                ("B", "[?]", "Ask Details", 
                 "Ask for more information", 85,
                 "#2196f3", "ask_details"),
                ("C", "[@]", "Show Help", 
                 "View help documentation", 70,
                 "#ff9800", "show_help"),
                ("D", "[~]", "Try Best Guess", 
                 "Attempt with best interpretation", 60,
                 "#9c27b0", "best_guess")
            ]
        }
        
        templates = option_templates.get(intent, option_templates[IntentType.UNKNOWN])
        
        options = []
        for opt_id, icon, title, desc, conf, color, action in templates:
            options.append(ThinkingOption(
                option_id=opt_id,
                label=opt_id,
                icon=icon,
                title=title,
                description=desc,
                confidence=conf,
                color=color,
                action=action
            ))
        
        return options
    
    def execute_option(self, thinking_result: ThinkingResult, 
                       option_id: str) -> Dict:
        """
        Execute selected option
        
        Args:
            thinking_result: The thinking result
            option_id: Selected option ID (A, B, C, D)
            
        Returns:
            Execution result dictionary
        """
        option = thinking_result.get_option(option_id)
        if not option:
            return {
                "success": False,
                "error": f"Option {option_id} not found",
                "action": "error"
            }
        
        return {
            "success": True,
            "action": option.action,
            "option_id": option_id,
            "intent": thinking_result.intent.value,
            "confidence": option.confidence / 100.0,
            "params": option.params
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# Global engine instance
_engine = None

def get_thinking_engine() -> ThinkingEngine:
    """Get or create global thinking engine instance"""
    global _engine
    if _engine is None:
        _engine = ThinkingEngine()
    return _engine
