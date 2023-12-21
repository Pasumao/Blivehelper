from PySide2.QtCore import Signal,QObject

class ui_signal(QObject):
    #收到弹幕
    get_danmaku = Signal(str,str)

    logger=Signal(str)

    logger_browser=Signal(str)

    ass_signals=Signal(int,str)

    ass_logger=Signal(str)

    get_gift=Signal(str)