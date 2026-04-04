"""
Thinking Blueprint UI Widgets for Blueclaw v1.0
Four-Option interactive mode PyQt5 components
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QSizePolicy, QSpacerItem, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor
from typing import List, Optional, Callable

from .thinking_engine import ThinkingEngine, ThinkingStep, ThinkingOption


class StepWidget(QFrame):
    """Single thinking step visualization component"""
    
    def __init__(self, step: ThinkingStep, parent=None):
        super().__init__(parent)
        self.step = step
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            StepWidget {
                background-color: #2d2d2d;
                border-radius: 8px;
                padding: 8px;
                margin: 4px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        # Step icon
        icon_label = QLabel(self.step.icon)
        icon_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(icon_label)
        
        # Step content
        content_layout = QVBoxLayout()
        
        title = QLabel(f"Step {self.step.step_number}: {self.step.title}")
        title.setStyleSheet("color: #4fc3f7; font-weight: bold;")
        content_layout.addWidget(title)
        
        desc = QLabel(self.step.description)
        desc.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        desc.setWordWrap(True)
        content_layout.addWidget(desc)
        
        layout.addLayout(content_layout, stretch=1)


class OptionButton(QFrame):
    """Single option button in the four-option UI"""
    
    clicked = pyqtSignal(str)  # option_id
    
    def __init__(self, option: ThinkingOption, parent=None):
        super().__init__(parent)
        self.option = option
        self.is_selected = False
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(80)
        self._update_style()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(6)
        
        # Top: label + title
        header = QHBoxLayout()
        
        label = QLabel(f"[{self.option.label}]")
        label.setStyleSheet("""
            color: #4fc3f7;
            font-weight: bold;
            font-size: 14px;
        """)
        header.addWidget(label)
        
        title = QLabel(self.option.title)
        title.setStyleSheet("""
            color: #ffffff;
            font-weight: bold;
            font-size: 13px;
        """)
        header.addWidget(title, stretch=1)
        
        # Confidence percentage
        conf_label = QLabel(f"{self.option.confidence}%")
        conf_label.setStyleSheet(f"""
            color: {self.option.color};
            font-weight: bold;
        """)
        header.addWidget(conf_label)
        
        layout.addLayout(header)
        
        # Description
        desc = QLabel(self.option.description)
        desc.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Confidence bar
        self.conf_bar = QProgressBar()
        self.conf_bar.setMaximum(100)
        self.conf_bar.setValue(self.option.confidence)
        self.conf_bar.setTextVisible(False)
        self.conf_bar.setMaximumHeight(4)
        self.conf_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: #3d3d3d;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {self.option.color};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self.conf_bar)
    
    def _update_style(self):
        """Update style"""
        if self.is_selected:
            self.setStyleSheet(f"""
                OptionButton {{
                    background-color: #1a3a4a;
                    border: 2px solid {self.option.color};
                    border-radius: 10px;
                }}
                OptionButton:hover {{
                    background-color: #2a4a5a;
                }}
            """)
        else:
            self.setStyleSheet("""
                OptionButton {
                    background-color: #2d2d2d;
                    border: 2px solid transparent;
                    border-radius: 10px;
                }
                OptionButton:hover {
                    background-color: #3d3d3d;
                    border: 2px solid #5a5a5a;
                }
            """)
    
    def set_selected(self, selected: bool):
        self.is_selected = selected
        self._update_style()
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.option.option_id)


class ThinkingBlueprintWidget(QWidget):
    """Thinking Blueprint complete panel - includes thinking process and four options"""
    
    option_selected = pyqtSignal(str, object)  # option_id, thinking_result
    execute_clicked = pyqtSignal(str, object)  # option_id, thinking_result
    cancel_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = ThinkingEngine()
        self.current_result = None
        self.option_buttons: List[OptionButton] = []
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #252526;
            }
            QLabel {
                color: #ffffff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # ===== Title Area =====
        title_layout = QHBoxLayout()
        
        self.title_icon = QLabel("*")
        self.title_icon.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(self.title_icon)
        
        self.title_label = QLabel("Thinking Blueprint")
        self.title_label.setStyleSheet("""
            color: #4fc3f7;
            font-size: 16px;
            font-weight: bold;
        """)
        title_layout.addWidget(self.title_label)
        
        title_layout.addStretch()
        
        # Confidence display
        self.confidence_label = QLabel("")
        self.confidence_label.setStyleSheet("""
            color: #4caf50;
            font-size: 12px;
            padding: 4px 10px;
            background-color: #1e3a1e;
            border-radius: 12px;
        """)
        title_layout.addWidget(self.confidence_label)
        
        layout.addLayout(title_layout)
        
        # ===== Thinking Process Area =====
        self.steps_container = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setSpacing(8)
        self.steps_layout.addStretch()
        layout.addWidget(self.steps_container, stretch=1)
        
        # ===== Separator =====
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #3d3d3d;")
        layout.addWidget(line)
        
        # ===== Four Options Area =====
        options_label = QLabel("4-Option Mode - Select an action:")
        options_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        layout.addWidget(options_label)
        
        self.options_grid = QWidget()
        grid_layout = QVBoxLayout(self.options_grid)
        grid_layout.setSpacing(10)
        layout.addWidget(self.options_grid, stretch=2)
        
        # ===== Bottom Buttons =====
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: none;
                padding: 10px 25px;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
        button_layout.addWidget(self.cancel_btn)
        
        self.execute_btn = QPushButton("Execute (A)")
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                padding: 10px 25px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #888888;
            }
        """)
        self.execute_btn.clicked.connect(self._on_execute)
        button_layout.addWidget(self.execute_btn)
        
        layout.addLayout(button_layout)
        
        self.selected_option_id = None
    
    def analyze_input(self, user_input: str):
        """Analyze user input and display thinking process and options"""
        self.current_result = self.engine.analyze(user_input)
        self._display_result()
    
    def set_result(self, result):
        """Directly set analysis result (for external computation)"""
        self.current_result = result
        self._display_result()
    
    def _display_result(self):
        """Display analysis result"""
        if not self.current_result:
            return
        
        result = self.current_result
        
        # Update title
        intent_display = {
            "create": "Create Mode",
            "modify": "Modify Mode",
            "question": "Question Mode",
            "chat": "Chat Mode",
            "execute": "Execute Mode",
            "analyze": "Analyze Mode",
            "unknown": "General Mode"
        }
        self.title_label.setText(
            f"Thinking Blueprint - {intent_display.get(result.intent.value, 'Unknown')}"
        )
        
        # Update confidence
        self.confidence_label.setText(f"Confidence: {result.intent_confidence:.0%}")
        
        # Clear and rebuild thinking steps
        self._clear_steps()
        for step in result.thinking_steps:
            step_widget = StepWidget(step)
            self.steps_layout.insertWidget(self.steps_layout.count() - 1, step_widget)
        
        # Clear and rebuild options
        self._clear_options()
        self.option_buttons = []
        
        grid_layout = QVBoxLayout()
        for option in result.options:
            btn = OptionButton(option)
            btn.clicked.connect(self._on_option_clicked)
            grid_layout.addWidget(btn)
            self.option_buttons.append(btn)
        
        # Replace old layout
        old_layout = self.options_grid.layout()
        if old_layout:
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        self.options_grid.setLayout(grid_layout)
        
        # Default select first option
        if self.option_buttons:
            self._select_option(self.option_buttons[0].option.option_id)
    
    def _clear_steps(self):
        """Clear thinking steps"""
        while self.steps_layout.count() > 1:  # keep stretch
            item = self.steps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _clear_options(self):
        """Clear options"""
        self.option_buttons = []
        self.selected_option_id = None
    
    def _on_option_clicked(self, option_id: str):
        """Option clicked"""
        self._select_option(option_id)
        self.option_selected.emit(option_id, self.current_result)
    
    def _select_option(self, option_id: str):
        """Select specified option"""
        self.selected_option_id = option_id
        
        for btn in self.option_buttons:
            btn.set_selected(btn.option.option_id == option_id)
        
        # Update execute button text
        option = self.current_result.get_option(option_id) if self.current_result else None
        if option:
            self.execute_btn.setText(f"Execute ({option.label})")
            self.execute_btn.setEnabled(True)
        else:
            self.execute_btn.setEnabled(False)
    
    def _on_execute(self):
        """Execute button clicked"""
        if self.selected_option_id and self.current_result:
            self.execute_clicked.emit(self.selected_option_id, self.current_result)
    
    def get_execution_result(self) -> Optional[dict]:
        """Get execution result"""
        if self.selected_option_id and self.current_result:
            return self.engine.execute_option(
                self.current_result, 
                self.selected_option_id
            )
        return None
