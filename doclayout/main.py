import os
import sys
import traceback
import logging

# Avoid DBus portal errors on some Linux distros
if sys.platform == "linux":
    os.environ["QT_QPA_PLATFORMTHEME"] = ""

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from PySide6.QtWidgets import QApplication
from doclayout.gui.window import MainWindow

def exception_hook(exctype, value, tb):
    """
    Global exception handler for uncaught exceptions.
    
    Args:
        exctype: Exception type.
        value: Exception value.
        tb: Traceback object.
    """
    logger.critical("Uncaught exception", exc_info=(exctype, value, tb))
    sys.exit(1)

def main():
    """
    Main entry point for the DocLayout GUI application.
    
    Initializes the Qt application, sets up exception handling,
    and displays the main window.
    """
    # Set global exception handler before creating QApplication
    sys.excepthook = exception_hook
    
    app = QApplication(sys.argv)
    
    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.critical("Fatal error during application startup: %s", e, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
