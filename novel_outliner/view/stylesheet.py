APP_STYLESHEET = '''

* {
    font-size: 16px;
    icon-size: 24px;
}

QPushButton {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #f6f7fa, stop: 1 #dadbde);
    border: 2px solid #8f8f91;
    border-radius: 6px;
    padding: 2px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #c3c4c7, stop: 1 #f6f7fa);
}

QPushButton:pressed {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #d7d8db, stop: 1 #f6f7fa);
}

QPushButton:disabled {
    opacity: 0.65;
}

QDockWidget::float-button {
    subcontrol-position: top left;
    subcontrol-origin: margin;
    position: absolute;
    top: 0px; left: 4px; bottom: 0px;
    width: 16px;
}

QHeaderView::section {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #2177b0, stop: 0.5 #185b87,
                                      stop: 0.6 #124669, stop:1 #1d608c);
    color: white;
    padding-left: 4px;
    border: 1px solid #6c6c6c;
    border-radius: 6px;
    font-size: 16px;
    font: bold;
}

QToolBar {
    spacing: 1px;
}

'''
