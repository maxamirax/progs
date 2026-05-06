"""
PROJECT: ClientLog Pro
VERSION: 66.0 (STABLE - ALIGNMENT & BUBBLES FIXED)

ПОСЛЕДНИЕ ПРАВКИ (HARRY_LOG):
- UI: Идеальное выравнивание всех элементов в TopPanel и ToolsFrame.
- BUBBLES: Восстановлена высота и внутренние отступы облаков текста (50% ширины).
- FIX: Поиск работает через .setBackground (без вылетов).
- FIX: Все блоки 'with' разнесены по строкам (без SyntaxError).
"""

import sys, datetime, os, json, base64, ctypes
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QTextEdit, QTabBar,
                             QVBoxLayout, QWidget, QPushButton, QHBoxLayout, 
                             QInputDialog, QFileDialog, QMessageBox, QMenu, 
                             QColorDialog, QFontDialog, QFrame, QScrollArea, QLabel, 
                             QDialog, QLineEdit, QDateTimeEdit, QGraphicsDropShadowEffect)
from PyQt6.QtGui import (QFont, QAction, QTextCursor, QKeyEvent, 
                         QColor, QIcon, QPixmap, QImage, QTextCharFormat, QTextDocument, QBrush)
from PyQt6.QtCore import QTimer, Qt, QByteArray, QBuffer, QIODevice, QPropertyAnimation, QPoint

# --- КОНФИГУРАЦИЯ ---
DATA_DIR = "work_data"
MASTER_BACKUP = "system_master_archive.bak"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def set_lock(path, lock=True):
    if os.path.exists(path):
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
            if lock: ctypes.windll.kernel32.SetFileAttributesW(path, attrs | 0x01)
            else: ctypes.windll.kernel32.SetFileAttributesW(path, attrs & ~0x01)
        except: pass

# --- ВИЗУАЛ ---

class ImagePreviewDialog(QDialog):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Просмотр")
        self.resize(1000, 800); self.pixmap = pixmap; self.scale_factor = 1.0
        l = QVBoxLayout(self); self.sc = QScrollArea(); self.img = QLabel()
        self.img.setPixmap(self.pixmap); self.img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sc.setWidget(self.img); self.sc.setWidgetResizable(True); l.addWidget(self.sc)
    def wheelEvent(self, event):
        self.scale_factor *= 1.1 if event.angleDelta().y() > 0 else 0.9
        self.img.setPixmap(self.pixmap.scaledToWidth(max(100, int(self.pixmap.width() * self.scale_factor)), Qt.TransformationMode.SmoothTransformation))

class ReminderDialog(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setFixedSize(380, 200); self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.container = QFrame(self); self.container.setGeometry(10, 10, 360, 180)
        self.container.setStyleSheet("background-color: #ffffff; border: 2px solid #3390ec; border-radius: 15px;")
        shadow = QGraphicsDropShadowEffect(blurRadius=25, color=QColor(0,0,0,150)); self.container.setGraphicsEffect(shadow)
        l = QVBoxLayout(self.container); m = QLabel(f"<b><font color='#3390ec' size='5'>🔔 НАПОМИНАНИЕ</font></b><br><br>{text}")
        m.setWordWrap(True); m.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btns = QHBoxLayout(); b1 = QPushButton("✅ ОК"); b2 = QPushButton("🕒 1 МИН")
        b1.setStyleSheet("background:#3390ec; color:white; padding:10px; border-radius:10px; font-weight:bold;")
        b2.setStyleSheet("background:#f1f1f1; color:#333; padding:10px; border-radius:10px;")
        b1.clicked.connect(self.accept); b2.clicked.connect(self.reject)
        btns.addWidget(b1); btns.addWidget(b2); l.addWidget(m); l.addLayout(btns)
    def showEvent(self, e): super().showEvent(e); self.shake()
    def shake(self):
        self.a = QPropertyAnimation(self, b"pos"); self.a.setDuration(500); c = self.pos()
        for i in range(1, 11): self.a.setKeyValueAt(i/10, c + QPoint(10 if i%2==0 else -10, 0))
        self.a.start()

class SmartTextEdit(QTextEdit):
    def __init__(self, add_entry_func):
        super().__init__()
        self.add_entry_func = add_entry_func; self.setFont(QFont("Segoe UI", 12)); self.setAcceptRichText(True)

    def mouseDoubleClickEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        fmt = cursor.charFormat()
        if fmt.isImageFormat():
            name = fmt.toImageFormat().name()
            if name.startswith("data:image"):
                try:
                    raw_data = name.split(",")[-1]
                    pix = QPixmap()
                    pix.loadFromData(base64.b64decode(raw_data))
                    if not pix.isNull(): ImagePreviewDialog(pix, self).exec()
                except: pass
        else: super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        cursor = self.textCursor()
        if "📍" in cursor.block().text():
            if event.key() not in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
                self.moveCursor(QTextCursor.MoveOperation.NextBlock); return
        if event.key() == Qt.Key.Key_Shift and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            if event.nativeScanCode() in (54, 161): self.add_entry_func(self); return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        if source.hasImage():
            img = QImage(source.imageData())
            ba = QByteArray(); buf = QBuffer(ba); buf.open(QIODevice.OpenModeFlag.WriteOnly)
            img.save(buf, "JPG", 80)
            data = ba.toBase64().data().decode()
            self.insertHtml(f'<br><img src="data:image/jpg;base64,{data}" width="500" style="border: 2px solid #dfe5ec; border-radius: 12px;"><br>')
            self.moveCursor(QTextCursor.MoveOperation.End)
        else: super().insertFromMimeData(source)

# --- ГЛАВНОЕ ОКНО ---

class ClientLogPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ClientLog Pro v66.0")
        self.resize(1200, 850); self.reminders = []
        cw = QWidget(); self.setCentralWidget(cw); self.main_l = QVBoxLayout(cw); self.main_l.setContentsMargins(0,0,0,0); self.main_l.setSpacing(0)

        # ТОР-ПАНЕЛЬ (ВЫРАВНИВАНИЕ)
        self.top = QFrame(); self.top.setObjectName("TopPanel"); tl = QHBoxLayout(self.top)
        self.top.setFixedHeight(75); tl.setContentsMargins(15, 0, 15, 0); tl.setSpacing(10)
        
        self.add_b = QPushButton("➕ Новый клиент"); self.add_b.clicked.connect(lambda: self.add_client_tab("Новый клиент"))
        self.open_b = QPushButton("📂 Открыть"); self.open_b.clicked.connect(self.open_external_file)
        
        self.search = QLineEdit(); self.search.setPlaceholderText("🔍 Глобальный поиск..."); self.search.setFixedWidth(350)
        self.search.textChanged.connect(self.run_search)
        
        self.btn_prev = QPushButton("<"); self.btn_prev.setFixedSize(40, 40); self.btn_prev.setObjectName("SearchNav")
        self.btn_prev.clicked.connect(lambda: self.navigate_search(False))
        self.btn_next = QPushButton(">"); self.btn_next.setFixedSize(40, 40); self.btn_next.setObjectName("SearchNav")
        self.btn_next.clicked.connect(lambda: self.navigate_search(True))
        
        tl.addWidget(self.add_b); tl.addWidget(self.open_b); tl.addSpacing(20)
        tl.addWidget(self.search); tl.addWidget(self.btn_prev); tl.addWidget(self.btn_next)
        tl.addStretch()
        self.main_l.addWidget(self.top)

        self.tabs = QTabWidget(); self.tabs.setTabsClosable(True); self.tabs.tabCloseRequested.connect(self.close_tab_request); self.tabs.tabBarDoubleClicked.connect(self.rename_tab); self.tabs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu); self.tabs.customContextMenuRequested.connect(self.show_tab_menu); self.main_l.addWidget(self.tabs)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f2f5; }
            #TopPanel, #ToolsFrame { background-color: #ffffff; border-bottom: 1px solid #dfe5ec; }
            QTabBar::tab { background: #ffffff; color: #707579; padding: 12px 25px; border-right: 1px solid #f1f1f1; min-width: 140px; }
            QTabBar::tab:selected { background: #ffffff; color: #3390ec; border-bottom: 3px solid #3390ec; font-weight: bold; }
            QTextEdit { background-color: #f0f2f5; border: none; padding: 10px; }
            QLineEdit { background-color: #f1f1f1; border-radius: 15px; border: 1px solid #dfe5ec; padding: 10px 15px; color: #222; font-size: 14px; }
            
            QPushButton { 
                background-color: #3390ec; color: white; border-radius: 12px; 
                padding: 10px 20px; font-weight: bold; border: none; min-height: 45px; 
            }
            QPushButton:hover { background-color: #2b82d9; }
            
            #SearchNav { background-color: #3390ec; color: white; border-radius: 20px; font-size: 20px; padding: 0; min-height: 40px; }
            
            #ToolsFrame QPushButton { 
                background-color: #f1f1f1; color: #3390ec; border: 1px solid #dfe5ec; 
                padding: 10px 20px; min-width: 125px; min-height: 42px; font-size: 14px;
            }
            #ToolsFrame QPushButton:hover { background-color: #e1f0ff; }
        """)
        
        self.load_data(); self.ensure_diary()
        self.stimer = QTimer(); self.stimer.timeout.connect(self.save_data); self.stimer.start(15000)
        self.rtimer = QTimer(); self.rtimer.timeout.connect(self.check_reminders); self.rtimer.start(2000)

    def add_entry(self, ed):
        """ Бабл с восстановленной высотой и зазорами """
        now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        header = f'<div style="color: #3390ec; font-weight: bold; margin-top: 20px; margin-left: 10px; margin-bottom: 5px;">📍 {now}</div>'
        # Добавлен padding 15px и фиксированный неразрывный пробел для высоты
        bubble = (
            f'<table width="50%" style="margin-bottom: 10px;">'
            f'<tr><td style="background-color: white; border: 1px solid #dfe5ec; border-radius: 12px; '
            f'padding: 15px; color: #222; line-height: 1.5;">'
            f'&nbsp;</td></tr></table><br>'
        )
        ed.append(header + bubble)
        ed.moveCursor(QTextCursor.MoveOperation.End)
        cur = ed.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.Up, QTextCursor.MoveMode.MoveAnchor, 2)
        ed.setTextCursor(cur)

    def save_data(self):
        master_log = []
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i); ed = w.findChild(SmartTextEdit); path = w.property("file_path")
            if ed and path:
                meta = {"name": self.tabs.tabText(i), "content": ed.toHtml(), "color": w.property("tab_color")}
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False)
                master_log.append(f"--- {self.tabs.tabText(i)} ---\n{ed.toHtml()}")
        if master_log:
            set_lock(MASTER_BACKUP, False)
            with open(MASTER_BACKUP, "a", encoding="utf-8") as mb:
                mb.write("\n".join(master_log) + "\n" + "="*50 + "\n")
            set_lock(MASTER_BACKUP, True)

    def run_search(self, text):
        q = text.lower(); self.clear_search_highlight()
        if not q: return
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i).findChild(SmartTextEdit)
            if ed and q in ed.toPlainText().lower():
                self.tabs.tabBar().setTabTextColor(i, QColor("#e74c3c"))
                self.tabs.setCurrentIndex(i)
                cur = ed.document().find(q)
                fmt = QTextCharFormat()
                fmt.setBackground(QBrush(QColor("yellow")))
                while not cur.isNull():
                    cur.mergeCharFormat(fmt)
                    cur = ed.document().find(q, cur)

    def add_client_tab(self, name, content="", color=None, filename=None):
        t = QWidget(); l = QVBoxLayout(t); l.setContentsMargins(0,0,0,0); l.setSpacing(0)
        tools = QFrame(); tools.setFixedHeight(60); tools.setObjectName("ToolsFrame"); tl = QHBoxLayout(tools)
        tl.setContentsMargins(10, 0, 10, 0); tl.setSpacing(10)
        ed = SmartTextEdit(self.add_entry); (ed.setHtml(content) if content else None)
        b1=QPushButton("🕒 Время"); b1.clicked.connect(lambda: self.add_entry(ed))
        b2=QPushButton("⏰ Напомнить"); b2.clicked.connect(lambda: self.set_alarm(ed))
        b3=QPushButton("Abc Шрифт"); b3.clicked.connect(lambda: self.change_font(ed))
        b4=QPushButton("💾 Сохранить как..."); b4.clicked.connect(lambda: self.save_tab_as(t))
        tl.addWidget(b1); tl.addWidget(b2); tl.addWidget(b3); tl.addStretch(); tl.addWidget(b4)
        l.addWidget(tools); l.addWidget(ed); idx = self.tabs.addTab(t, name)
        if not filename: filename = f"t_{datetime.datetime.now().timestamp()}.html"
        t.setProperty("file_path", os.path.join(DATA_DIR, filename)); (self.apply_tab_color(idx, color) if color else None)
        self.tabs.setCurrentIndex(idx); return idx

    def load_data(self):
        if os.path.exists(DATA_DIR):
            for f in sorted(os.listdir(DATA_DIR)):
                if f.endswith(".html"):
                    try:
                        with open(os.path.join(DATA_DIR, f), "r", encoding="utf-8") as file:
                            d = json.load(file); self.add_client_tab(d["name"], d["content"], filename=f, color=d.get("color"))
                    except: pass

    def ensure_diary(self):
        diaries = [i for i in range(self.tabs.count()) if "ДНЕВНИК" in self.tabs.tabText(i).upper()]
        if not diaries: self.add_client_tab("📓 ЛИЧНЫЙ ДНЕВНИК")
        elif len(diaries) > 1:
            for i in reversed(diaries[1:]): self.tabs.removeTab(i)
        for i in range(self.tabs.count()):
            if "ДНЕВНИК" in self.tabs.tabText(i).upper(): self.tabs.tabBar().setTabButton(i, QTabBar.ButtonPosition.RightSide, None)

    def navigate_search(self, forward=True):
        q = self.search.text()
        if not q: return
        ed = self.tabs.currentWidget().findChild(SmartTextEdit)
        f = QTextDocument.FindFlag(0) if forward else QTextDocument.FindFlag.FindBackward
        if not ed.find(q, f):
            cur = ed.textCursor(); cur.movePosition(QTextCursor.MoveOperation.End if not forward else QTextCursor.MoveOperation.Start); ed.setTextCursor(cur); ed.find(q, f)

    def clear_search_highlight(self):
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i).findChild(SmartTextEdit)
            if ed: cur = ed.textCursor(); cur.select(QTextCursor.SelectionType.Document); cur.setCharFormat(QTextCharFormat())
            c = self.tabs.widget(i).property("tab_color"); self.tabs.tabBar().setTabTextColor(i, QColor(c if c else "#707579"))

    def close_tab_request(self, idx):
        if "ДНЕВНИК" in self.tabs.tabText(idx).upper(): return
        pw, ok = QInputDialog.getText(self, "Защита", "Пароль 111:", QLineEdit.EchoMode.Password)
        if ok and pw == "111":
            p = self.tabs.widget(idx).property("file_path"); (os.remove(p) if os.path.exists(p) else None); self.tabs.removeTab(idx)

    def rename_tab(self, idx):
        n, ok = QInputDialog.getText(self, "Имя", "Клиент:", text=self.tabs.tabText(idx)); (self.tabs.setTabText(idx, n) if ok else None)

    def show_tab_menu(self, pos):
        idx = self.tabs.tabBar().tabAt(pos)
        if idx != -1:
            m = QMenu(self); m.addAction("🎨 ПОКРАСИТЬ", lambda: self.pick_color(idx)); m.addAction("💾 СОХРАНИТЬ КАК", lambda: self.save_tab_as(self.tabs.widget(idx))); m.exec(self.tabs.mapToGlobal(pos))

    def pick_color(self, idx):
        c = QColorDialog.getColor(); (self.apply_tab_color(idx, c.name()) if c.isValid() else None)

    def apply_tab_color(self, idx, color_hex):
        self.tabs.widget(idx).setProperty("tab_color", color_hex); self.tabs.tabBar().setTabTextColor(idx, QColor(color_hex))
        pix = QPixmap(14, 14); pix.fill(QColor(color_hex)); self.tabs.setTabIcon(idx, QIcon(pix)); self.save_data()

    def change_font(self, ed):
        f, ok = QFontDialog.getFont(ed.font(), self); (ed.setCurrentFont(f) if ok else None)

    def save_tab_as(self, widget):
        ed = widget.findChild(SmartTextEdit); p, _ = QFileDialog.getSaveFileName(self, "Сохранить как...", "", "HTML (*.html);;TXT (*.txt)")
        if p:
            with open(p, "w", encoding="utf-8") as f:
                f.write(ed.toHtml() if p.endswith(".html") else ed.toPlainText())

    def open_external_file(self):
        p, _ = QFileDialog.getOpenFileName(self, "Открыть", "", "HTML (*.html);;Text (*.txt);;All (*)")
        if p:
            with open(p, "r", encoding="utf-8") as f: c = f.read()
            self.add_client_tab(os.path.basename(p), c)

    def set_alarm(self, ed):
        d = QDialog(self); d.setWindowTitle("Напоминание"); l = QVBoxLayout(d)
        dt = QDateTimeEdit(datetime.datetime.now()); dt.setCalendarPopup(True); msg = QLineEdit(); btn = QPushButton("OK")
        btn.clicked.connect(d.accept); l.addWidget(dt); l.addWidget(msg); l.addWidget(btn)
        if d.exec():
            t = dt.dateTime().toPyDateTime()
            self.reminders.append({"time": t.isoformat(), "text": msg.text(), "done": False})
            self.add_entry(ed); ed.insertPlainText(f"🔔 НАПОМИНАНИЕ: {msg.text()}")

    def check_reminders(self):
        now = datetime.datetime.now()
        for r in self.reminders:
            if not r.get("done") and datetime.datetime.fromisoformat(r["time"]) <= now:
                QApplication.beep(); dlg = ReminderDialog(r["text"], self)
                if dlg.exec(): r["done"] = True
                else: r["time"] = (now + datetime.timedelta(minutes=1)).isoformat()

if __name__ == "__main__":
    app = QApplication(sys.argv); w = ClientLogPro(); w.show(); sys.exit(app.exec())
