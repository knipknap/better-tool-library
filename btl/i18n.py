import sys
from PySide.QtCore import QTranslator, QLocale
from btl.const import translations_dir

def install_translator(app):
    translator = QTranslator(app)
    if not translator.load(QLocale.system(), 'btl', '.', translations_dir):
        sys.stderr.write(f'Warning: failed to load locale\n')
    app.installTranslator(translator)
