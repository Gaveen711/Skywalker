"""Sky Walker desktop design tokens and Qt stylesheet."""

STYLE = """
QWidget { background: #0A1220; color: #E8F2FA; font-family: 'Segoe UI'; font-size: 14px; }
QMainWindow { background: #07111F; }
QFrame#sidebar { background: #0D1B2B; border-right: 1px solid #20384A; }
QFrame#panel { background: #102236; border: 1px solid #244159; border-radius: 14px; }
QLabel#brand { color: #67DDF1; font-size: 22px; font-weight: 700; }
QLabel#title { font-size: 29px; font-weight: 650; }
QLabel#subtle { color: #91A9BC; }
QLabel#metric { color: #69DAED; font-size: 24px; font-weight: 650; }
QPushButton { background: #142A40; border: 1px solid #2B4B62; border-radius: 9px;
  padding: 11px 14px; text-align: left; }
QPushButton:hover { background: #1B3953; border-color: #4ABBD2; }
QPushButton:focus { border: 2px solid #73E0EF; }
QPushButton:disabled { color: #758A9B; background: #102133; }
QPushButton#selected { background: #17405A; border-color: #54CCE3; color: #D9FBFF; }
QTextEdit, QLineEdit { background: #0B1929; border: 1px solid #2B4B62;
  border-radius: 9px; padding: 10px; }
QTextEdit:focus, QLineEdit:focus { border-color: #65D9EC; }
"""
