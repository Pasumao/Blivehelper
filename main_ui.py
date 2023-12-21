from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile,QObject,QEvent,Qt,QSettings
import logging
from bilibili import bilibili,live_room,ass,cangku
from threading import Thread
from Signal import ui_signal
from gift import gift,gift_mapping
from PySide2.QtGui import QPixmap,QColor, QPalette
from PySide2.QtWidgets import QLabel,QSizePolicy,QHBoxLayout,QLineEdit,QPushButton,QCheckBox,QVBoxLayout,QWidget
import os
import asyncio


class MainWindow(QObject):
    def __init__(self,debug=False):
        super().__init__()
        #log部分
        self.__debug = debug
        self.logger = logging.getLogger(f"GUI")
        self.logger.setLevel(logging.DEBUG if self.__debug else logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "[%(asctime)s][%(levelname)s] %(message)s"
                )
            )
            self.logger.addHandler(handler)
        #log部分

        #信号部分
        self.ui_signal=ui_signal()
        #信号部分

        #读取主菜单
        self.logger.debug("读取main.ui")

        file=QFile("gui/main.ui")
        file.open(QFile.ReadOnly)
        file.close()
        self.main_ui=QUiLoader().load(file)

        ##礼物图片显示
        # if not os.path.exists("gift_imgs"):
        #     # 如果不存在则创建文件夹
        #     os.makedirs("gift_list")
        self.get_gift_img_label()
        self.display_gifts_imgs()
        ##礼物图片显示

        self.mapping=[]
        self.gift_mapping_name=[]
        self.gift_mapping_dict={}

        self.setting=QSettings("Mysoft","Blivehelper")

        self.loudsetting()

        self.connect()
        #读取主菜单

        self.mapping_layout_set={}
        self.row=2
        self.main_ui.mapping_on_checkbox_1.stateChanged.connect(self.on_mapping_func)
        self.main_ui.danmaku_path_edit.setAcceptDrops(True)  # 允许拖放操作
        self.main_ui.danmaku_path_edit.installEventFilter(self)

    # 事件过滤器处理拖放事件
    def eventFilter(self, source, event):
        if event.type() == QEvent.DragEnter:
            if event.mimeData().hasUrls():
                event.accept()
            else:
                event.ignore()
        elif event.type() == QEvent.Drop:
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                self.main_ui.danmaku_path_edit.setText(file_path)  # 在QLineEdit上显示文件的绝对路径
            return True
        return super().eventFilter(source, event)

    def loudsetting(self):
        #分析页面
        ##读取UID
        ass_uid=self.setting.value("ass_uid")
        if ass_uid:
            self.main_ui.ass_uid_edit.setText(ass_uid)
        ##读取UID
        #分析页面
        
        #主页页面
        ##直播间号
        room_id=self.setting.value("room_id")
        if room_id:
            self.main_ui.room_id_lineedit.setText(room_id)
        ##直播间号
        #主页页面

    def connect(self):

        #自定义信号类

        @self.ui_signal.ass_logger.connect
        def ass_logger_browser_func(msg):
            self.main_ui.ass_logger_browser.insertPlainText(msg)
            scrollbar = self.main_ui.ass_logger_browser.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        @self.ui_signal.get_danmaku.connect
        def update_logger_browser_get_danmakusw_func(speaker,dm):
            msg="[弹幕]"+speaker+":"+dm+"\n"
            self.logger.debug(msg)
            self.main_ui.logger_browser.insertPlainText(msg)

        @self.ui_signal.logger.connect
        def update_logger_browser_bili_logger_func(log):
            msg="[系统]"+log+"\n"
            self.logger.info(log)
            self.main_ui.logger_browser.insertPlainText(msg)

        @self.ui_signal.logger_browser.connect
        def logger_browser_func(msg):
            self.main_ui.logger_browser.insertPlainText(msg)
            scrollbar = self.main_ui.logger_browser.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        @self.ui_signal.ass_signals.connect
        def ass_signals_func(mindm,point):
            self.logger.debug("ass统计结束")
            self.ui_signal.ass_logger.emit("===================================\n")
            self.ui_signal.ass_logger.emit("本场直播平均每小时弹幕数为：{}\n".format(str(mindm)))
            self.ui_signal.ass_logger.emit("可能的剪辑点如下:\n{}\n".format(point))
            self.ui_signal.ass_logger.emit("===================================\n")
            image_path = "gui/ass.png"
            pixmap = QPixmap(image_path)
            #pixmap=pixmap.scaled(50,50)
            self.main_ui.ass_img_label.setPixmap(pixmap)

        @self.ui_signal.get_gift.connect
        def get_gift_mapping_func(ggift):
            msg="[礼物]"+ggift+"\n"
            self.ui_signal.logger_browser.emit(msg)
            for i in self.gift_mapping_name:
                if ggift in i:
                    gift_mapping(self.gift_mapping_dict[i])
                    return
                
        #自定义信号类

        @self.main_ui.update_gift_list_button.clicked.connect
        def update_gift_list_func():
            self.logger.debug("开始更新礼物列表")
            bb=bilibili(self.ui_signal)
            self.t_update_gift_list=Thread(target =bb.update_gift_list,daemon=True)
            self.t_update_gift_list.start()
            self.logger.debug("更新礼物列表结束")

        def get_room_id_func():
            self.logger.debug("获取直播间号")
            self.room_id=self.main_ui.room_id_lineedit.text()
            self.logger.debug("直播间号为{}".format(self.room_id))

        #主页
        ##连接直播间
        @self.main_ui.connect_live_button.clicked.connect
        def connect_live_func():
            def run_():
                get_room_id_func()
                self.logger.info("直播间连接中")
                self.ui_signal.logger.emit("直播间连接中")
                self.room=live_room(self.room_id,self.ui_signal)
                self.t_room_connect=Thread(target =self.room.connect,daemon=True)
                self.t_room_connect.start()
                self.logger.info("直播间连接成功")
                self.ui_signal.logger.emit("直播间连接成功")
            try:
                if self.t_room_connect.is_alive():
                    self.logger.debug("直播间已连接")
                    self.ui_signal.logger.emit("直播间已连接")
                    return
                else:
                    run_()
            except:
                run_()
        ##连接直播间
        
        ##断开直播间
        @self.main_ui.disconnect_live_button.clicked.connect
        def disconnect_live_func():
            terminate_thread(self.t_room_connect)
            self.logger.debug("直播间连接断开")
            self.ui_signal.logger.emit("直播间连接断开")
        ##断开直播间
            
        #主页

        @self.main_ui.update_area_list_button.clicked.connect
        def update_area_list_func():
            self.logger.info("开始更新分区列表")
            bilibili.update_area_list()
            self.logger.info("分区列表更新完毕")



        @self.main_ui.surch_gift_lineedit.textChanged.connect
        def searchImages():
            search_text = self.main_ui.surch_gift_lineedit.text()
            for i in reversed(range(self.main_ui.gridLayout_2.count())):
                self.main_ui.gridLayout_2.itemAt(i).widget().deleteLater()
            if search_text=="":
                self.get_gift_img_label()
                self.display_gifts_imgs()
                return
            self.logger.debug("刷新礼物图片标签")
            self.get_gift_img_label(search_text,mode=2)
            self.display_gifts_imgs()

        @self.main_ui.ass_start_button.clicked.connect
        def ass_start_func():
            dm_path=self.main_ui.danmaku_path_edit.text()
            if not os.path.exists(dm_path):
                self.logger.debug("弹幕文件地址错误")
                msg="弹幕文件地址错误"
                self.ui_signal.ass_logger.emit(msg)
                return 
            self.logger.info("获取弹幕文件")
            self.ui_signal.ass_logger.emit("统计即将开始，请等待结果\n")
            
            self.ass=ass(self.ui_signal,dm_path)
            self.t_ass_xml=Thread(target =self.ass.ass_xml,daemon=True)
            self.t_ass_xml.start()



        @self.main_ui.ass_uid_edit.textChanged.connect
        def save_changed_ass_uid_func():
            ass_uid=self.main_ui.ass_uid_edit.text()
            self.setting.setValue("ass_uid",ass_uid)
            self.setting.sync()

        @self.main_ui.get_cangku_button.clicked.connect
        def get_cangku_func():
                
            def isnum(num):
                try:
                    int(num)
                    return True
                except:
                    return False
                
            def t_get_cangku_func():
                ass_uid=self.main_ui.ass_uid_edit.text()
                user=bilibili()
                if asyncio.run(user.isuid(ass_uid)):
                    user_name=user.get_user_name()
                    self.ui_signal.ass_logger.emit("检测到用户:{}\n".format(user_name))
                else:
                    self.ui_signal.ass_logger.emit("uid输入错误，或该用户不存在\n")
                    return
                pagemun=self.main_ui.ass_pagemun_edit.text()
                if isnum(pagemun):
                    page=int(pagemun)
                elif pagemun=="":
                    page=1
                else:
                    self.ui_signal.ass_logger.emit("输入页数有误，请修改后重试\n")
                    return
                try:
                    ck=cangku(ass_uid)
                    cangku_list=ck.get_huifang_str(page)
                    self.ui_signal.ass_logger.emit(cangku_list)
                except:
                    self.ui_signal.ass_logger.emit("该用户没有直播回放\n")

            self.t_get_cangku=Thread(target =t_get_cangku_func,daemon=True)
            self.t_get_cangku.start()

        @self.main_ui.cangku_id_edit.returnPressed.connect
        def cangku_id_textChanged_func():

            def isnum(num):
                try:
                    int(num)
                    return True
                except:
                    return False

            def t_cangku_id_textChanged_func():
                ass_uid=self.main_ui.ass_uid_edit.text()
                user=bilibili()
                if asyncio.run(user.isuid(ass_uid)):
                    user_name=user.get_user_name()
                    self.ui_signal.ass_logger.emit("检测到用户:{}\n".format(user_name))
                else:
                    self.ui_signal.ass_logger.emit("uid输入错误，或该用户不存在\n")
                    return
                ass_num=self.main_ui.cangku_id_edit.text()
                if isnum(ass_num):
                    ass_c=ass()
                    bvid=ass_c.get_bv_id(ass_num,ass_uid)
                    self.main_ui.ass_bvid_edit.setText(bvid)
                    self.ui_signal.ass_logger.emit("获取用户：{}的第{}个直播回放的BVID成功\n".format(user_name,ass_num))
                else:
                    self.ui_signal.ass_logger.emit("输入的直播回放ID错误，请重新输入\n")
                    return
                
            self.t_cangku_id_textChanged=Thread(target =t_cangku_id_textChanged_func,daemon=True)
            self.t_cangku_id_textChanged.start()

        @self.main_ui.ass_online_button.clicked.connect
        def ass_online_func():
            bvid=self.main_ui.ass_bvid_edit.text()
            if bvid=="":
                self.ui_signal.ass_logger.emit("请输入BV号\n")
                return

            self.ui_signal.ass_logger.emit("分析视频{}开始，请稍等\n".format(bvid))
            self.ass=ass(signal=self.ui_signal,bvid=bvid)
            self.t_ass_online_=Thread(target =self.ass.ass_online_func,daemon=True)
            self.t_ass_online_.start()



        @self.main_ui.add_mapping_button.clicked.connect
        def add_mapping_func():
            new_mapping_layout=QHBoxLayout()
            new_mapping_layout.setObjectName("mapping_layout_{}".format(str(self.row)))
            
            new_gift_name=QLineEdit()
            new_gift_name.setObjectName("gift_name_mapping_{}".format(str(self.row)))
            new_gift_name.setMaximumSize(80,20)
            new_gift_name.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
            new_mapping_checkbox=QCheckBox("开启")
            new_mapping_checkbox.setObjectName("mapping_on_checkbox_{}".format(str(self.row)))
            #new_mapping_label.setMaximumSize(30,20)
            new_mapping_checkbox.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
            new_one_key=QLineEdit()
            new_one_key.setObjectName("one_key_{}".format(str(self.row)))
            new_one_key.setMaximumSize(50,20)
            new_one_key.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
            new_two_key=QLineEdit()
            new_two_key.setObjectName("two_key_{}".format(str(self.row)))
            new_two_key.setMaximumSize(50,20)
            new_two_key.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
            new_three_key=QLineEdit()
            new_three_key.setObjectName("three_key_{}".format(str(self.row)))
            new_three_key.setMaximumSize(50,20)
            new_three_key.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
            new_cancel_mapping_button=QPushButton("X")
            new_cancel_mapping_button.setObjectName("cancel_mapping_button_{}".format(str(self.row)))
            new_cancel_mapping_button.setMaximumSize(20,20)
            new_cancel_mapping_button.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)

            new_mapping_layout.addWidget(new_gift_name)
            new_mapping_layout.addWidget(new_mapping_checkbox)
            new_mapping_layout.addWidget(new_one_key)
            new_mapping_layout.addWidget(new_two_key)
            new_mapping_layout.addWidget(new_three_key)
            new_mapping_layout.addWidget(new_cancel_mapping_button)
            num=self.main_ui.mapping_layout.count()-1
            self.main_ui.mapping_layout.insertLayout(num,new_mapping_layout)

            new_mapping_checkbox.stateChanged.connect(self.on_mapping_func)
            new_cancel_mapping_button.clicked.connect(self.less_mapping_func)
            self.mapping_layout_set["mapping_layout_{}".format(self.row)]=new_mapping_layout
            self.row+=1
            pass

    def less_mapping_func(self):
        sender_object=self.sender()
        a=sender_object.objectName()
        num=str(int(a[a.find("_",20)+1:]))
        print(num,self.mapping_layout_set)
        for i in range(self.mapping_layout_set["mapping_layout_{}".format(num)].count()):
            item = self.mapping_layout_set["mapping_layout_{}".format(num)].takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.mapping_layout_set["mapping_layout_{}".format(num)].deleteLater()
        del self.mapping_layout_set["mapping_layout_{}".format(num)]
        #self.main_ui.update()

    def on_mapping_func(self,state):
        sender_object=self.sender()
        a=sender_object.objectName()
        num=str(int(a[a.find("_",15)+1:]))
        if state == Qt.Checked:
            for i in range(self.mapping_layout_set["mapping_layout_{}".format(num)].count()):
                item = self.mapping_layout_set["mapping_layout_{}".format(num)].itemAt(i)
                let=item.widget()
                if isinstance(let, QLineEdit):
                    let.setReadOnly(True)
                    obn=let.objectName()
                    if obn=="gift_name_mapping_{}".format(num):
                        giftname=let.text()
                    elif obn=="one_key_{}".format(num):
                        k1=let.text()
                    elif obn=="two_key_{}".format(num):
                        k2=let.text()
                    elif obn=="three_key_{}".format(num):
                        k3=let.text()
                    readonly_palette = let.palette()
                    readonly_palette.setColor(let.backgroundRole(), Qt.lightGray)
                    let.setPalette(readonly_palette)

            self.gift_mapping_name.append(giftname)
            self.gift_mapping_dict[giftname]=[k1,k2,k3]

        else:
            for i in range(self.mapping_layout_set["mapping_layout_{}".format(num)].count()):
                item = self.mapping_layout_set["mapping_layout_{}".format(num)].itemAt(i)
                let=item.widget()
                if isinstance(let, QLineEdit):
                    let.setReadOnly(False)
                    obn=let.objectName()
                    if obn=="gift_name_mapping_{}".format(num):
                        giftname=let.text()
                    readonly_palette = let.palette()
                    readonly_palette.setColor(QPalette.Base, QColor(255, 255, 255))
                    let.setPalette(readonly_palette)
            self.gift_mapping_name.remove(giftname)
            del self.gift_mapping_dict[giftname]

    def display_gifts_imgs(self):
        for i in range(len(self.imageLabels)):
            image_path = "gifts_imgs/{}".format(self.gift_list[i])
            pixmap = QPixmap(image_path)
            pixmap=pixmap.scaled(50,50)
            self.imageLabels[i].setPixmap(pixmap)
        try:
            if 32-i>0:
                for k in range(32-i):
                    i+=1
                    space_label=QLabel(self.main_ui.scrollAreaWidgetContents)
                    self.main_ui.gridLayout_2.addWidget(space_label,i // 3, i % 3)
        except:
            pass
        
    def get_gift_img_label(self,surch_str="",mode=1):
        try:
            self.gift_list=gift.get_gifts_img_path(surch_str,mode)
        except:
            self.gift_list=[]
        self.imageLabels =[]
        for i in range(len(self.gift_list)):
            gift_vbox = QVBoxLayout()

            gift_label = QLabel(self.main_ui.scrollAreaWidgetContents)
            gift_label.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
            gift_label.setMaximumSize(100,100)
            self.imageLabels.append(gift_label)
            giftname=self.gift_list[i][:self.gift_list[i].find(".")]
            gift_text_label=QLabel(giftname)
            gift_text_label.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)

            gift_vbox.addWidget(gift_label)
            gift_vbox.addWidget(gift_text_label)
            gift_widget = QWidget()
            gift_widget.setLayout(gift_vbox)
            self.main_ui.gridLayout_2.addWidget(gift_widget,i // 3, i % 3)

import ctypes
def terminate_thread(thread):
    if not thread.is_alive():
        return
    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")