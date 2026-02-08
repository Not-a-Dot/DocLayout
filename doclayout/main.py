import os
import sys

# Avoid DBus portal errors on some Linux distros
if sys.platform == "linux":
    os.environ["QT_QPA_PLATFORMTHEME"] = ""

from PySide6.QtWidgets import QApplication
from doclayout.gui.window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Global exception handler to catch silent signal crashes
    def exception_hook(exctype, value, tb):
        print("".join(traceback.format_exception(exctype, value, tb)))
        sys.exit(1)
    sys.excepthook = exception_hook
    
    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()

import traceback

if __name__ == "__main__":
    main()
