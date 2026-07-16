"""Global Qt stylesheet for NGOKAF TRANS."""
from __future__ import annotations

from resources import theme as T


def global_stylesheet(font_family: str) -> str:
    return f"""
    QWidget {{
        font-family: "{font_family}";
        color: {T.TEXT_PRIMARY};
        background: transparent;
        font-size: 13px;
    }}
    QMainWindow, QDialog {{
        background-color: {T.BG_MAIN};
    }}
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
        background-color: {T.BG_INPUT};
        border: 1px solid {T.BORDER};
        border-radius: {T.RADIUS_INPUT}px;
        padding: 6px 10px;
        font-size: {T.SIZE_INPUT}px;
        color: {T.TEXT_INPUT};
        min-height: 22px;
        max-height: 36px;
    }}
    QTextEdit, QPlainTextEdit {{
        max-height: none;
        min-height: 48px;
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
        border: 1px solid {T.PRIMARY};
    }}
    QPushButton#primaryBtn {{
        background-color: #3D2E00;
        color: {T.TEXT_WHITE};
        border: none;
        border-radius: {T.RADIUS_BUTTON}px;
        font-size: {T.SIZE_BUTTON}px;
        font-weight: 600;
        padding: 8px 18px;
        min-height: 36px;
    }}
    QPushButton#primaryBtn:hover {{
        background-color: #2A1F00;
    }}
    QPushButton#primaryBtn:disabled {{
        background-color: #7A6B4A;
    }}
    QPushButton#secondaryBtn {{
        background-color: {T.BG_CARD};
        color: {T.TEXT_PRIMARY};
        border: 1px solid {T.BORDER};
        border-radius: {T.RADIUS_BUTTON}px;
        font-size: {T.SIZE_BUTTON}px;
        font-weight: 600;
        padding: 8px 14px;
        min-height: 36px;
    }}
    QPushButton#secondaryBtn:hover {{
        background-color: {T.BG_INPUT};
    }}
    QPushButton#actionBtn {{
        background-color: {T.BG_CARD};
        color: {T.TEXT_PRIMARY};
        border: 1px solid {T.BORDER};
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 8px;
        min-height: 20px;
    }}
    QPushButton#actionBtn:hover {{
        background-color: {T.BG_INPUT};
    }}
    QPushButton#linkBtn {{
        background: transparent;
        border: none;
        color: {T.PRIMARY_ALT};
        font-size: 13px;
        text-align: right;
    }}
    QLabel#cardTitle {{
        color: {T.PRIMARY_ALT};
        font-size: {T.SIZE_CARD_TITLE}px;
        font-weight: 700;
    }}
    QLabel#fieldLabel {{
        color: {T.TEXT_LABEL};
        font-size: {T.SIZE_LABEL}px;
        font-weight: 600;
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QCheckBox {{
        color: {T.TEXT_SECONDARY};
        font-size: 13px;
        spacing: 6px;
    }}
    QToolTip {{
        background-color: {T.BG_CARD};
        color: {T.TEXT_PRIMARY};
        border: 1px solid {T.BORDER};
        padding: 4px;
    }}
    """
