"""Sky Walker desktop design tokens and Qt stylesheet."""
STYLE = """
QWidget { background: #0b1422; color: #e7eef6; font-family: 'Segoe UI'; font-size: 10pt; }
QLabel, QCheckBox { background: transparent; }
QFrame#sidebar { background: #080f1b; border-right: 1px solid #203047; }
QFrame#panel, QFrame#voicePanel { background: #101e30; border: 1px solid #263a50; border-radius: 16px; }
QFrame#voicePanel { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #13283b,stop:1 #101b2d); }
QFrame#metricCard { background: #101c2c; border: 1px solid #25364b; border-radius: 10px; }
QLabel#brand { color: #e7eef6; font-size: 17pt; font-weight: 600; }
QLabel#title { font-size: 25pt; font-weight: 600; }
QLabel#sectionTitle { font-size: 12pt; font-weight: 600; }
QLabel#subtle { color: #a0b2c8; }
QLabel#metric { color: #bceef4; font-size: 11pt; font-weight: 600; }
QLabel#badge { color: #85dbea; background: #142e3c; border: 1px solid #2b5260; border-radius: 12px; padding: 5px 12px; }
QPushButton { background: #182a40; border: 1px solid #344b65; border-radius: 8px; padding: 10px 13px; text-align: center; min-height: 20px; }
QPushButton:hover { background: #233c55; border-color: #5bd8ed; }
QPushButton:pressed { background: #304b62; }
QPushButton:focus, QComboBox:focus, QCheckBox:focus { border: 2px solid #86e4f2; }
QPushButton:disabled { color: #8293a9; background: #142033; border-color: #27374c; }
QPushButton[nav="true"] { text-align: left; background: transparent; border: 1px solid transparent; padding: 11px 14px; }
QPushButton[nav="true"]:hover { background: #142338; }
QPushButton#selected { background: #163246; border: 1px solid #355c70; color: #95e6f3; }
QPushButton#primary { background: #69d7e9; color: #081821; border: 1px solid #69d7e9; font-weight: 600; }
QPushButton#primary:hover { background: #a1edf6; }
QPushButton#primary:disabled { background: #243e50; border-color: #344b65; color: #91aabc; }
QPushButton#danger { color: #f2b9a7; border-color: #654c50; }
QTextEdit, QPlainTextEdit, QLineEdit, QListWidget { background: #0c1727; border: 1px solid #344b65; border-radius: 8px; padding: 10px; selection-background-color: #285975; }
QTextEdit#chatHistory { border: none; background: transparent; font-size: 11pt; padding: 2px; }
QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus, QListWidget:focus { border-color: #86e4f2; }
QLineEdit { min-height: 24px; }
QComboBox { background: #0e1c2d; border: 1px solid #344b65; border-radius: 7px; padding: 7px 10px; min-height: 22px; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView { background: #132339; color: #e7eef6; selection-background-color: #285975; }
QCheckBox { spacing: 8px; padding: 5px 0; }
QCheckBox:disabled { color: #8c9bb0; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #60768e; border-radius: 4px; background: #0e1c2d; }
QCheckBox::indicator:checked { background: #69d7e9; border: 3px solid #294b61; }
QStatusBar { background: #080f1b; color: #9aadc4; font-size: 9pt; }
QScrollBar:vertical { background: transparent; width: 9px; margin: 0; }
QScrollBar::handle:vertical { background: #39536c; border-radius: 4px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { background: #1b3047; color: #eef6ff; border: 1px solid #5c7891; padding: 6px; }
"""
