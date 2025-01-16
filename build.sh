pyinstaller -F \
    --add-data=src/utils:utils \
    --add-data=src/ui:ui \
    --add-data=src/widgets:widgets \
    --add-data=src/constants.py:. \
    --hidden-import=adata \
    --hidden-import=numpy \
    --hidden-import=matplotlib \
    --hidden-import=matplotlib.backends.backend_qt5 \
    --hidden-import=matplotlib.backends.backend_qt5agg \
    --icon=assets/icon.ico \
    -w \
    ./src/main.py --clean