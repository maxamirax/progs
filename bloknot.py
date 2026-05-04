import sys, datetime, os, json, base64, re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QTextEdit, 
                             QVBoxLayout, QWidget, QPushButton, QHBoxLayout, 
                             QInputDialog, QFileDialog, QMessageBox, QMenu, 
                             QColorDialog, QFontDialog, QFrame, QScrollArea, QLabel, QDialog)
from PyQt6.QtGui import (QFont, QAction, QTextCursor, QKeyEvent, QShortcut, 
                         QKeySequence, QColor, QIcon, QPixmap, QImage)
from PyQt6.QtCore import QTimer, Qt, QByteArray, QBuffer, QIODevice

DB_FILE = "autosave_data.json"

class ImagePreviewDialog(QDialog):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Просмотр (Колесо мыши - зум)")
        self.resize(1000, 800)
        self.pixmap = pixmap
        self.scale_factor = 1.0
        layout = QVBoxLayout(self)
        self.scroll = QScrollArea()
        self.img_label = QLabel()
        self.img_label.setPixmap(self.pixmap)
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setWidget(self.img_label)
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0: self.scale_factor *= 1.1
        else: self.scale_factor *= 0.9
        new_w = int(self.pixmap.width() * self.scale_factor)
        self.img_label.setPixmap(self.pixmap.scaledToWidth(max(100, new_w), Qt.TransformationMode.SmoothTransformation))

class SmartTextEdit(QTextEdit):
    def __init__(self, add_entry_func):
        super().__init__()
        self.add_entry_func = add_entry_func
        self.setFont(QFont("Segoe UI", 12))
        self.setAcceptRichText(True)

    def mouseDoubleClickEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        char_format = cursor.charFormat()
        if char_format.isImageFormat():
            img_name = char_format.toImageFormat().name()
            if img_name.startswith("data:image"):
                data = img_name.split(",")[1]
                pix = QPixmap(); pix.loadFromData(base64.b64decode(data))
                ImagePreviewDialog(pix, self).exec()
        else: super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Shift and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            if event.nativeScanCode() == 54 or event.nativeVirtualKey() == 161:
                self.add_entry_func(self); return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        if source.hasImage():
            img = QImage(source.imageData())
            if not img.isNull():
                ba = QByteArray(); buf = QBuffer(ba); buf.open(QIODevice.OpenModeFlag.WriteOnly)
                img.save(buf, "JPG", 80)
                base64_data = ba.toBase64().data().decode()
                self.insertHtml(f'<br><img src="data:image/jpg;base64,{base64_data}" width="500"><br>')
        else: super().insertFromMimeData(source)

class ClientLogPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_dark_theme = False
        self.setWindowTitle("ClientLog Pro v30.0")
        self.resize(1200, 850)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(0); self.main_layout.setContentsMargins(0, 0, 0, 0)

        # ВЕРХНЯЯ ПАНЕЛЬ
        self.top_panel = QFrame(); self.top_panel.setObjectName("TopPanel")
        self.top_layout = QHBoxLayout(self.top_panel)
        
        # Группа: Клиенты
        self.add_btn = QPushButton("➕ Новый клиент")
        self.add_btn.setObjectName("AddBtn")
        self.add_btn.clicked.connect(lambda: self.add_client_tab("Новый клиент"))
        
        # Группа: Тема
        self.theme_btn = QPushButton("🌓 Сменить тему")
        self.theme_btn.clicked.connect(self.toggle_theme)

        self.top_layout.addWidget(self.add_btn)
        self.top_layout.addSpacing(20)
        self.top_layout.addStretch()
        self.top_layout.addWidget(self.theme_btn)
        self.main_layout.addWidget(self.top_panel)

        # ТАБЫ
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True); self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.tabBarDoubleClicked.connect(self.rename_client)
        self.tabs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.show_tab_context_menu)
        self.main_layout.addWidget(self.tabs)
        
        self.load_data()
        if self.tabs.count() == 0: self.add_client_tab("Мой клиент")
        self.apply_theme()
        
        self.auto_save_timer = QTimer(); self.auto_save_timer.timeout.connect(self.save_data)
        self.auto_save_timer.start(2000)

    def add_client_tab(self, name, content="", color=None):
        tab_widget = QWidget(); tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0); tab_layout.setSpacing(0)
        
        # Панель инструментов внутри таба
        tools_frame = QFrame(); tools_frame.setFixedHeight(50); tools_frame.setObjectName("ToolsFrame")
        tools_layout = QHBoxLayout(tools_frame)
        
        text_edit = SmartTextEdit(self.add_entry)
        if content: text_edit.setHtml(content)
        
        btn_font = QPushButton("Abc Шрифт"); btn_font.clicked.connect(lambda: self.change_font(text_edit))
        btn_color = QPushButton("🎨 Цвет текста"); btn_color.clicked.connect(lambda: self.change_color(text_edit))
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine); sep.setFrameShadow(QFrame.Shadow.Sunken)
        
        btn_time = QPushButton("🕒 Метка времени (R-Shift)"); btn_time.clicked.connect(lambda: self.add_entry(text_edit))
        info_label = QLabel("📸 Вставка фото: Ctrl+V | Увеличение: Дабл-клик")
        info_label.setStyleSheet("color: #888; font-size: 10px; margin-left: 10px;")

        tools_layout.addWidget(btn_font); tools_layout.addWidget(btn_color)
        tools_layout.addWidget(sep)
        tools_layout.addWidget(btn_time)
        tools_layout.addWidget(info_label)
        tools_layout.addStretch()
        
        tab_layout.addWidget(tools_frame); tab_layout.addWidget(text_edit)
        idx = self.tabs.addTab(tab_widget, name)
        if color: self.update_tab_color(idx, color)

    def show_tab_context_menu(self, pos):
        idx = self.tabs.tabBar().tabAt(pos)
        if idx != -1:
            menu = QMenu(self)
            color_act = QAction("🎨 Выбрать цвет вкладки", self)
            color_act.triggered.connect(lambda: self.pick_tab_color(idx))
            menu.addAction(color_act); menu.exec(self.tabs.mapToGlobal(pos))

    def pick_tab_color(self, idx):
        color = QColorDialog.getColor()
        if color.isValid(): self.update_tab_color(idx, color.name())

    def update_tab_color(self, idx, color_hex):
        self.tabs.widget(idx).setProperty("tab_color", color_hex)
        pix = QPixmap(12, 12); pix.fill(QColor(color_hex))
        self.tabs.setTabIcon(idx, QIcon(pix))
        self.tabs.tabBar().setTabTextColor(idx, QColor(color_hex))

    def apply_theme(self):
        dark = self.is_dark_theme
        bg = "#1e1e1e" if dark else "#ffffff"
        panel = "#2d2d2d" if dark else "#f8f9fa"
        text = "#e0e0e0" if dark else "#2c3e50"
        border = "#3e3e3e" if dark else "#dee2e6"
        accent = "#0078d4"

        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {bg}; }}
            #TopPanel {{ background-color: {panel}; border-bottom: 2px solid {accent}; padding: 5px; }}
            #ToolsFrame {{ background-color: {panel}; border-bottom: 1px solid {border}; padding: 2px; }}
            QTextEdit {{ background-color: {bg}; color: {text}; border: none; padding: 15px; selection-background-color: {accent}; }}
            QPushButton {{ background-color: {bg}; border: 1px solid {border}; padding: 6px 12px; color: {text}; border-radius: 4px; }}
            QPushButton:hover {{ background-color: {accent}; color: white; }}
            #AddBtn {{ background-color: {accent}; color: white; font-weight: bold; }}
            QTabWidget::pane {{ border-top: 1px solid {border}; }}
            QTabBar::tab {{ background: {panel}; color: {text}; padding: 12px 25px; border-right: 1px solid {border}; }}
            QTabBar::tab:selected {{ background: {bg}; border-bottom: 3px solid {accent}; font-weight: bold; }}
            QMenu {{ background-color: {panel}; color: {text}; border: 1px solid {border}; }}
            QMenu::item:selected {{ background-color: {accent}; }}
        """)
        for i in range(self.tabs.count()):
            c = self.tabs.widget(i).property("tab_color")
            if c: self.update_tab_color(i, c)

    def add_entry(self, text_edit):
        now = datetime.datetime.now().strftime('%d.%m.%Y | %H:%M')
        line = "#444" if self.is_dark_theme else "#ddd"
        self.tabs.widget(self.tabs.currentIndex()).setProperty("last_update", now)
        text_edit.insertHtml(f"<br><hr style='border:none; border-top:1px solid {line};'><div style='color:#888; font-size:10px;'>ЗАПИСЬ: {now}</div><br>")

    def save_data(self):
        data = []
        for i in range(self.tabs.count()):
            edit = self.tabs.widget(i).findChild(SmartTextEdit)
            if edit: data.append({"name": self.tabs.tabText(i), "text": edit.toHtml(), "color": self.tabs.widget(i).property("tab_color")})
        with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

    def load_data(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    for item in json.load(f): self.add_client_tab(item['name'], item['text'], item.get('color'))
            except: pass

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme; self.apply_theme()

    def rename_client(self, i):
        n, ok = QInputDialog.getText(self, "Имя", "Клиент:", text=self.tabs.tabText(i))
        if ok and n: self.tabs.setTabText(i, n)

    def close_tab(self, i):
        if self.tabs.count() > 1: self.tabs.removeTab(i)

    def change_font(self, edit):
        font, ok = QFontDialog.getFont(edit.currentFont(), self)
        if ok: edit.setCurrentFont(font)

    def change_color(self, edit):
        color = QColorDialog.getColor()
        if color.isValid(): edit.setTextColor(color)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ClientLogPro()
    window.show()
    sys.exit(app.exec())
