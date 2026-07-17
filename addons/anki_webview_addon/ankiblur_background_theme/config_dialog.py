# AnkiBlur configuration dialog (moved verbatim from __init__.py).

from aqt import mw
from aqt.qt import *  # noqa: F403
from aqt.theme import theme_manager


class ColorConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transparent Overlay Settings - Light & Dark Theme")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Get current config
        self.config = mw.addonManager.getConfig(__name__) or {
            "light_theme": {"color": "#ffffff", "alpha": 15},
            "dark_theme": {"color": "#000000", "alpha": 30}
        }

        # Create tab widget for Light/Dark themes
        self.tab_widget = QTabWidget()

        # Light theme tab
        self.light_tab = self.create_theme_tab("light_theme", "Light Theme")
        self.tab_widget.addTab(self.light_tab, "☀️ Light Theme")

        # Dark theme tab
        self.dark_tab = self.create_theme_tab("dark_theme", "Dark Theme")
        self.tab_widget.addTab(self.dark_tab, "🌙 Dark Theme")

        # Set current tab based on current Anki theme
        current_tab = 1 if theme_manager.night_mode else 0
        self.tab_widget.setCurrentIndex(current_tab)

        # Current theme indicator
        theme_status = QLabel()
        current_theme_name = "Dark Theme" if theme_manager.night_mode else "Light Theme"
        theme_status.setText(f"💡 Currently using: {current_theme_name}")
        theme_status.setStyleSheet("font-weight: bold; padding: 10px;")

        # Button layout
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        main_layout.addWidget(theme_status)
        main_layout.addWidget(self.tab_widget)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def create_theme_tab(self, theme_key, theme_name):
        """Create a tab for configuring a specific theme"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Get theme config
        theme_config = self.config.get(theme_key, {"color": "#000000", "alpha": 30})

        # Color selection
        color_layout = QHBoxLayout()
        color_label = QLabel(f"{theme_name} Overlay Color:")
        color_button = QPushButton()
        current_color = QColor(theme_config.get("color", "#000000"))

        # Store references in tab widget for later access
        setattr(tab, 'color_button', color_button)
        setattr(tab, 'current_color', current_color)

        self.update_color_button(color_button, current_color)
        color_button.clicked.connect(lambda: self.choose_color(tab, theme_key))

        color_layout.addWidget(color_label)
        color_layout.addWidget(color_button)
        color_layout.addStretch()

        # Alpha slider
        alpha_layout = QHBoxLayout()
        alpha_label = QLabel("Transparency (0-100):")
        alpha_slider = QSlider(Qt.Orientation.Horizontal)
        alpha_slider.setRange(0, 100)
        alpha_slider.setValue(theme_config.get("alpha", 30))
        alpha_value = QLabel(str(theme_config.get("alpha", 30)))

        # Store references
        setattr(tab, 'alpha_slider', alpha_slider)
        setattr(tab, 'alpha_value', alpha_value)

        alpha_slider.valueChanged.connect(lambda v: alpha_value.setText(str(v)))
        alpha_slider.valueChanged.connect(lambda: self.update_preview(tab))

        alpha_layout.addWidget(alpha_label)
        alpha_layout.addWidget(alpha_slider)
        alpha_layout.addWidget(alpha_value)

        # Preview
        preview_label = QLabel(f"{theme_name} Preview:")
        preview_widget = QWidget()
        preview_widget.setMinimumHeight(100)
        preview_widget.setAutoFillBackground(True)

        # Store reference
        setattr(tab, 'preview_widget', preview_widget)

        self.update_preview(tab)

        layout.addLayout(color_layout)
        layout.addLayout(alpha_layout)
        layout.addWidget(preview_label)
        layout.addWidget(preview_widget)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def choose_color(self, tab, theme_key):
        color = QColorDialog.getColor(tab.current_color, self, f"Choose {theme_key.replace('_', ' ').title()} Color")
        if color.isValid():
            tab.current_color = color
            self.update_color_button(tab.color_button, color)
            self.update_preview(tab)

    def update_color_button(self, button, color):
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name()};
                border: 1px solid black;
                min-width: 60px;
                min-height: 30px;
            }}
        """)

    def update_preview(self, tab):
        alpha = tab.alpha_slider.value()
        color = tab.current_color
        palette = QPalette()
        bg_color = QColor(color)
        bg_color.setAlpha(int(alpha * 2.55))
        palette.setColor(QPalette.ColorRole.Window, bg_color)
        tab.preview_widget.setPalette(palette)

    def get_config(self):
        return {
            "light_theme": {
                "color": self.light_tab.current_color.name(),
                "alpha": self.light_tab.alpha_slider.value()
            },
            "dark_theme": {
                "color": self.dark_tab.current_color.name(),
                "alpha": self.dark_tab.alpha_slider.value()
            }
        }
