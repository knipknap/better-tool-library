import sys
from PySide.QtCore import QTranslator, QLocale, QLibraryInfo
from btl.const import translations_dir

# Unfortunately FreeCAD does not follow the standard "pt_BR" format,
# for naming the language files, it uses a dash separator instead,
# e.g. "pt-BR".
# This makes it incompatible with the format expected by
# pyside.load(), so we need to assemble our own filename and
# reimplement the search.
locale = QLocale()
locale_name = locale.name()
bcp47 = locale.bcp47Name()
search_filenames = (
    f"btl_{locale_name}.qm",
    f"btl_{locale_name.replace('_', '-')}.qm",
    f"btl_{bcp47}.qm",
)

def install_translator(app):
    # First the translator for Qt built-in strings.
    path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    translator = QTranslator(app)
    if translator.load(locale, 'qtbase', '_', path):
        app.installTranslator(translator)

    # Now a translator for BTL strings.
    translator = QTranslator(app)
    for filename in search_filenames:
        if translator.load(filename, translations_dir):
            app.installTranslator(translator)
            return
    sys.stderr.write(f'Warning: failed to load locale {locale}\n')
