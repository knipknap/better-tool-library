#!/bin/sh
TR_DIR=btl/resources/translations

lupdate `find btl -name "*.ui"` -ts $TR_DIR/ui.in.ts
pylupdate5 `find btl -name "*.py"` -translate-function tr -ts $TR_DIR/py.in.ts

lconvert -no-obsolete -i $TR_DIR/*.in.ts -o $TR_DIR/btl.ts

for FILE in $TR_DIR/btl_*.ts; do
    lrelease $FILE
done
