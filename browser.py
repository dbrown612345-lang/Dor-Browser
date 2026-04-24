import sys
import os
import json
import time
from pathlib import Path

import yt_dlp
import vt

from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtGui import (
    QDesktopServices,
    QIcon,
    QAction,
    QKeySequence,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit, QWidget,
    QVBoxLayout, QHBoxLayout, QTabBar, QStackedWidget, QFrame, QTextEdit,
    QPushButton, QFileDialog, QLabel, QListWidget, QListWidgetItem,
    QInputDialog, QSlider, QMenu
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineDownloadRequest

from PyQt6.QtMultimedia import (
    QMediaPlayer,
    QAudioOutput,
)
from PyQt6.QtMultimediaWidgets import QVideoWidget

from openai import OpenAI

#If you are unlucky enough to debug this code im sorry -Daniel
#if you are here to edit and you made a change leave your name
#1.Daniel
#2.put your name here, so on and so forth


# API KEYS
OPENAI_KEY = "YOUR_OPENAI_KEY_HERE" # Open AI (chat GPT) Get a key from https://platform.openai.com/account/api-keys
VT_KEY = "YOUR_VIRUSTOTAL_KEY_HERE" # VirusTotal Get a key from https://www.virustotal.com/gui/join-us


 
# SETTINGS
def get_settings_path():
    appdata = os.getenv("APPDATA", str(Path.home()))
    base = Path(appdata) / "DorBrowser"
    base.mkdir(parents=True, exist_ok=True)
    return base / "settings.json"


def load_settings():
    path = get_settings_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_settings(data):
    path = get_settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass



# AI
def ask_ai(prompt: str) -> str:
    if OPENAI_KEY == "YOUR_OPENAI_KEY_HERE":
        return "⚠ Add your OpenAI API key in the code to use AI."
    client = OpenAI(api_key=OPENAI_KEY)
    try:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )
        return resp.output[0].content[0].text
    except Exception as e:
        return f"⚠ AI Error: {e}"



class GxTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.setDocumentMode(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setUsesScrollButtons(True)
        self.setStyleSheet("""
            QTabBar {
                background: #050509;
            }
            QTabBar::tab {
                background: #141420;
                color: #e0e0ff;
                border-radius: 10px;
                padding: 6px 14px;
                margin: 4px;
                border: 1px solid #303050;
            }
            QTabBar::tab:selected {
                background: #0b1724;
                border: 1px solid #00B2FF;
                color: white;
            }
            QTabBar::tab:hover {
                border: 1px solid #00B2FF;
            }
        """)



# MAIN BROWSER
class Browser(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dor Browser")
        self.resize(1400, 900)

        self.settings = load_settings()
        self.background_path = self.settings.get("background_path", None)

        self.tab_bar = GxTabBar()
        self.tab_bar.currentChanged.connect(self.on_tab_changed)
        self.tab_bar.tabCloseRequested.connect(self.close_tab)

        self.views = []
        self.tab_groups = {}
        self.groups = {}

        self.group_bar = QWidget()
        self.group_layout = QHBoxLayout()
        self.group_layout.setContentsMargins(4, 2, 4, 2)
        self.group_layout.setSpacing(6)
        self.group_bar.setLayout(self.group_layout)
        self.group_buttons = {}

        self.stack = QStackedWidget()

        profile = QWebEngineProfile.defaultProfile()
        profile.downloadRequested.connect(self.handle_download)

        toolbar = QToolBar("Navigation")
        toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(toolbar)

        back_action = QAction("⟵", self)
        back_action.triggered.connect(self.go_back)
        toolbar.addAction(back_action)

        forward_action = QAction("⟶", self)
        forward_action.triggered.connect(self.go_forward)
        toolbar.addAction(forward_action)

        reload_action = QAction("⟳", self)
        reload_action.triggered.connect(self.reload_page)
        toolbar.addAction(reload_action)

        new_tab_action = QAction("+", self)
        new_tab_action.triggered.connect(self.new_tab)
        toolbar.addAction(new_tab_action)

        ai_action = QAction("AI", self)
        ai_action.triggered.connect(self.toggle_ai_panel)
        toolbar.addAction(ai_action)

        vt_action = QAction("VT", self)
        vt_action.triggered.connect(self.toggle_vt_panel)
        toolbar.addAction(vt_action)

        downloads_action = QAction("DL", self)
        downloads_action.triggered.connect(self.toggle_downloads_panel)
        toolbar.addAction(downloads_action)

        music_action = QAction("♫", self)
        music_action.triggered.connect(self.toggle_music_panel)
        toolbar.addAction(music_action)

        settings_action = QAction("⚙", self)
        settings_action.triggered.connect(self.toggle_settings_panel)
        toolbar.addAction(settings_action)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.load_from_bar)
        toolbar.addWidget(self.url_bar)

        self.new_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        self.new_tab_shortcut.activated.connect(self.new_tab)

        central = QWidget()
        v = QVBoxLayout()
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(self.group_bar)
        v.addWidget(self.tab_bar)
        v.addWidget(self.stack)
        central.setLayout(v)
        self.setCentralWidget(central)

        self.create_ai_panel()
        self.create_vt_panel()
        self.create_downloads_panel()
        self.create_settings_panel()
        self.create_music_panel()

        self.new_tab()

    
    def new_tab(self, url: str | None = None):
        view = QWebEngineView()
        view.urlChanged.connect(self.on_view_url_changed)
        view.titleChanged.connect(self.on_view_title_changed)

        idx = self.stack.addWidget(view)
        self.views.append(view)
        self.tab_groups[idx] = None

        tab_index = self.tab_bar.addTab("New Tab")
        self.tab_bar.setCurrentIndex(tab_index)

        if url:
            view.setUrl(QUrl(url))
        else:
            self.show_homepage(view)

    def close_tab(self, index: int):
        if self.tab_bar.count() == 1:
            self.views[0].setUrl(QUrl("about:blank"))
            self.show_homepage(self.views[0])
            self.tab_bar.setTabText(0, "New Tab")
            self.tab_groups[0] = None
            return

        view = self.views.pop(index)
        self.stack.removeWidget(view)
        view.deleteLater()

        self.tab_bar.removeTab(index)

        new_groups = {}
        for i, g in self.tab_groups.items():
            if i < index:
                new_groups[i] = g
            elif i > index:
                new_groups[i - 1] = g
        self.tab_groups = new_groups

    def on_tab_changed(self, index: int):
        if index < 0 or index >= len(self.views):
            return
        self.stack.setCurrentIndex(index)
        view = self.views[index]
        url = view.url().toString()
        self.url_bar.setText("" if url == "about:blank" else url)

    def on_view_url_changed(self, qurl: QUrl):
        view = self.sender()
        if view is not self.current_view():
            return
        url = qurl.toString()
        self.url_bar.setText("" if url == "about:blank" else url)

    def on_view_title_changed(self, title: str):
        view = self.sender()
        for i, v in enumerate(self.views):
            if v is view:
                self.tab_bar.setTabText(i, title or "New Tab")
                break

    def current_view(self) -> QWebEngineView | None:
        idx = self.tab_bar.currentIndex()
        if 0 <= idx < len(self.views):
            return self.views[idx]
        return None

    def contextMenuEvent(self, event):
        pos = event.pos()
        global_pos = self.mapToGlobal(pos)
        tab_pos = self.tab_bar.mapFromGlobal(global_pos)
        index = self.tab_bar.tabAt(tab_pos)
        if index < 0:
            return

        menu = QMenu(self)
        add_group = menu.addAction("Add to Group...")
        remove_group = menu.addAction("Remove from Group")
        act = menu.exec(global_pos)
        if act == add_group:
            self.add_tab_to_group(index)
        elif act == remove_group:
            self.remove_tab_from_group(index)

    def add_tab_to_group(self, index: int):
        name, ok = QInputDialog.getText(self, "Group Name", "Enter group name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        self.tab_groups[index] = name
        if name not in self.groups:
            color = "#00B2FF"
            self.groups[name] = color
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(0,178,255,40);
                    color: white;
                    border-radius: 12px;
                    padding: 4px 10px;
                    border: 1px solid rgba(0,178,255,180);
                }}
                QPushButton:checked {{
                    background-color: rgba(0,178,255,90);
                }}
            """)
            btn.clicked.connect(lambda checked, g=name: self.toggle_group(g))
            self.group_layout.addWidget(btn)
            self.group_buttons[name] = btn

    def remove_tab_from_group(self, index: int):
        self.tab_groups[index] = None

    def toggle_group(self, name: str):
        collapsed = not self.group_buttons[name].isChecked()
        self.group_buttons[name].setChecked(not collapsed)
        for i, g in self.tab_groups.items():
            if g == name:
                self.tab_bar.setTabVisible(i, not collapsed)

    
    def go_back(self):
        v = self.current_view()
        if v:
            v.back()

    def go_forward(self):
        v = self.current_view()
        if v:
            v.forward()

    def reload_page(self):
        v = self.current_view()
        if v:
            v.reload()

    def is_url(self, text: str) -> bool:
        text = text.strip()
        if " " in text:
            return False
        return "." in text

    def load_from_bar(self):
        text = self.url_bar.text().strip()
        v = self.current_view()
        if not v:
            return
        if text == "":
            self.show_homepage(v)
            return
        if self.is_url(text):
            if not text.startswith(("http://", "https://")):
                text = "https://" + text
            v.setUrl(QUrl(text))
        else:
            google_url = "https://www.google.com/search?q=" + text.replace(" ", "+")
            v.setUrl(QUrl(google_url))

    
    # HOMEPAGE
    def show_homepage(self, view: QWebEngineView):
        if self.background_path and os.path.exists(self.background_path):
            bg_url = QUrl.fromLocalFile(self.background_path).toString()
            bg_style = f"background: url('{bg_url}') no-repeat center center fixed; background-size: cover;"
        else:
            bg_style = "background: radial-gradient(circle at top, #101020, #050509);"

        door_img = "https://static.vecteezy.com/system/resources/thumbnails/018/249/828/small_2x/3d-rendering-open-blue-door-isolated-png.png"

        html = f"""
        <html>
        <head>
            <style>
                body {{
                    {bg_style}
                    color: white;
                    font-family: Arial;
                    text-align: center;
                    padding-top: 80px;
                }}
                h1 {{
                    font-size: 48px;
                    margin-bottom: 10px;
                    color: #00B2FF;
                }}
                .door-img img {{
                    width: 220px;
                    border-radius: 16px;
                    box-shadow: 0 0 25px rgba(0,178,255,0.6);
                }}
                .search-box input {{
                    width: 50%;
                    padding: 10px 14px;
                    border-radius: 20px;
                    border: 1px solid #00B2FF;
                    background: rgba(0,0,0,0.6);
                    color: white;
                    outline: none;
                }}
                .tiles {{
                    margin-top: 40px;
                    display: flex;
                    justify-content: center;
                    gap: 20px;
                }}
                .tile {{
                    width: 120px;
                    height: 80px;
                    border-radius: 16px;
                    background: rgba(0,0,0,0.6);
                    border: 1px solid #00B2FF;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: 0.2s;
                }}
                .tile:hover {{
                    background: #00B2FF;
                    color: black;
                }}
            </style>
        </head>
        <body>
            <h1>Dor Browser</h1>

            <div class="door-img">
                <img src="{door_img}">
            </div>

            <div class="search-box">
                <input id="homeSearch" placeholder="Search the web..."
                    onkeydown="if(event.key==='Enter'){{window.location.href='https://www.google.com/search?q='+encodeURIComponent(this.value);}}">
            </div>

            <div class="tiles">
                <div class="tile" onclick="window.location.href='https://youtube.com'">YouTube</div>
                <div class="tile" onclick="window.location.href='https://reddit.com'">Reddit</div>
                <div class="tile" onclick="window.location.href='https://github.com'">GitHub</div>
            </div>
        </body>
        </html>
        """
        base = QUrl.fromLocalFile(os.path.dirname(self.background_path)) if self.background_path else QUrl("about:blank")
        view.setHtml(html, base)

    
    # AI PANEL
    def create_ai_panel(self):
        self.ai_panel = QFrame(self)
        self.ai_panel.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.ai_panel.setGeometry(self.width(), 0, 350, self.height())

        layout = QVBoxLayout()
        self.ai_output = QTextEdit()
        self.ai_output.setReadOnly(True)
        layout.addWidget(self.ai_output)

        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Ask the AI...")
        layout.addWidget(self.ai_input)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_ai_message)
        layout.addWidget(send_btn)

        self.ai_panel.setLayout(layout)
        self.ai_open = False

    def toggle_ai_panel(self):
        if self.ai_open:
            self.ai_panel.setGeometry(self.width(), 0, 350, self.height())
            self.ai_open = False
        else:
            self.ai_panel.setGeometry(self.width() - 350, 0, 350, self.height())
            self.ai_open = True

    def send_ai_message(self):
        msg = self.ai_input.text().strip()
        if not msg:
            return
        self.ai_output.append(f"You: {msg}")
        self.ai_input.clear()
        reply = ask_ai(msg)
        self.ai_output.append(f"Dor AI: {reply}\n")

     
    # VIRUSTOTAL PANEL
    def create_vt_panel(self):
        self.vt_panel = QFrame(self)
        self.vt_panel.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.vt_panel.setGeometry(self.width(), 0, 350, self.height())

        layout = QVBoxLayout()

        self.vt_url_input = QLineEdit()
        self.vt_url_input.setPlaceholderText("Enter URL to scan")
        layout.addWidget(self.vt_url_input)

        scan_url_btn = QPushButton("Scan URL")
        scan_url_btn.clicked.connect(self.scan_url_with_vt)
        layout.addWidget(scan_url_btn)

        choose_btn = QPushButton("Choose File")
        choose_btn.clicked.connect(self.choose_file_for_vt)
        layout.addWidget(choose_btn)

        scan_file_btn = QPushButton("Scan File")
        scan_file_btn.clicked.connect(self.scan_file_with_vt)
        layout.addWidget(scan_file_btn)

        self.vt_output = QTextEdit()
        self.vt_output.setReadOnly(True)
        layout.addWidget(self.vt_output)

        self.vt_panel.setLayout(layout)
        self.vt_open = False
        self.vt_file_path = None

    def toggle_vt_panel(self):
        if self.vt_open:
            self.vt_panel.setGeometry(self.width(), 0, 350, self.height())
            self.vt_open = False
        else:
            self.vt_panel.setGeometry(self.width() - 350, 0, 350, self.height())
            self.vt_open = True

    def format_vt_output(self, analysis):
        try:
            stats = analysis.stats
            status = analysis.status

            harmless = stats.get("harmless", 0)
            suspicious = stats.get("suspicious", 0)
            malicious = stats.get("malicious", 0)
            undetected = stats.get("undetected", 0)

            sha256 = getattr(analysis, "sha256", None)
            if sha256 is None and hasattr(analysis, "meta"):
                sha256 = analysis.meta.get("file_info", {}).get("sha256", "N/A")
            if sha256 is None:
                sha256 = "N/A"

            return (
                "=== VirusTotal Scan Summary ===\n\n"
                f"Status: {status}\n\n"
                f"Harmless: {harmless}\n"
                f"Suspicious: {suspicious}\n"
                f"Malicious: {malicious}\n"
                f"Undetected: {undetected}\n\n"
                f"SHA256: {sha256}\n"
            )
        except Exception as e:
            return f"⚠ Error formatting output: {e}"

    def scan_url_with_vt(self):
        url_to_scan = self.vt_url_input.text().strip()
        if not url_to_scan:
            self.vt_output.setText("⚠ Enter a URL to scan.")
            return
        if VT_KEY == "YOUR_VIRUSTOTAL_KEY_HERE":
            self.vt_output.setText("⚠ Add your VirusTotal API key in the code.")
            return

        client = vt.Client(VT_KEY)
        try:
            analysis = client.scan_url(url_to_scan)
            while True:
                analysis = client.get_object(f"/analyses/{analysis.id}")
                if analysis.status == "completed":
                    break
                time.sleep(2)
            self.vt_output.setText(self.format_vt_output(analysis))
        except Exception as e:
            self.vt_output.setText(f"⚠ Error: {e}")
        finally:
            client.close()

    def choose_file_for_vt(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.vt_file_path = file_path
            self.vt_output.setText(f"Selected file:\n{file_path}")

    def scan_file_with_vt(self):
        if VT_KEY == "YOUR_VIRUSTOTAL_KEY_HERE":
            self.vt_output.setText("⚠ Add your VirusTotal API key in the code.")
            return
        if not self.vt_file_path:
            self.vt_output.setText("⚠ Choose a file first.")
            return

        client = vt.Client(VT_KEY)
        try:
            with open(self.vt_file_path, "rb") as f:
                analysis = client.scan_file(f, wait_for_completion=True)
            self.vt_output.setText(self.format_vt_output(analysis))
        except Exception as e:
            self.vt_output.setText(f"⚠ Error: {e}")
        finally:
            client.close()

     
    # DOWNLOADS PANEL
    def create_downloads_panel(self):
        self.downloads_panel = QFrame(self)
        self.downloads_panel.setStyleSheet("background-color: #111; color: white;")
        self.downloads_panel.setGeometry(self.width(), 0, 350, self.height())

        layout = QVBoxLayout()
        title = QLabel("Downloads")
        layout.addWidget(title)

        self.downloads_list = QListWidget()
        layout.addWidget(self.downloads_list)

        self.open_file_btn = QPushButton("Open File")
        self.open_file_btn.clicked.connect(self.open_selected_download)
        layout.addWidget(self.open_file_btn)

        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.clicked.connect(self.open_selected_download_folder)
        layout.addWidget(self.open_folder_btn)

        self.downloads_panel.setLayout(layout)
        self.downloads_open = False
        self.download_items = []

    def toggle_downloads_panel(self):
        if self.downloads_open:
            self.downloads_panel.setGeometry(self.width(), 0, 350, self.height())
            self.downloads_open = False
        else:
            self.downloads_panel.setGeometry(self.width() - 350, 0, 350, self.height())
            self.downloads_open = True

    def add_download_entry(self, path, status):
        item_text = f"{os.path.basename(path)} - {status}\n{path}"
        item = QListWidgetItem(item_text)
        self.downloads_list.addItem(item)
        self.download_items.append({"path": path, "status": status})

    def get_selected_download_path(self):
        row = self.downloads_list.currentRow()
        if row < 0 or row >= len(self.download_items):
            return None
        return self.download_items[row]["path"]

    def open_selected_download(self):
        path = self.get_selected_download_path()
        if path and os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def open_selected_download_folder(self):
        path = self.get_selected_download_path()
        if path and os.path.exists(path):
            folder = os.path.dirname(path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def handle_download(self, download: QWebEngineDownloadRequest):
        suggested = download.downloadFileName()
        default_dir = str(Path.home() / "Downloads")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save File As", os.path.join(default_dir, suggested)
        )
        if not path:
            download.cancel()
            return

        directory = os.path.dirname(path)
        filename = os.path.basename(path)

        download.setDownloadDirectory(directory)
        download.setDownloadFileName(filename)
        download.accept()

        download.finished.connect(lambda: self.auto_scan_download(download))

    def auto_scan_download(self, download: QWebEngineDownloadRequest):
        directory = download.downloadDirectory()
        filename = download.downloadFileName()
        path = os.path.join(directory, filename)

        status = "Completed" if download.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted else "Failed"
        self.add_download_entry(path, status)

        if status == "Completed":
            self.vt_file_path = path
            self.vt_output.setText(f"Downloaded file:\n{path}\n\nScanning...")
            self.scan_file_with_vt()
            if not self.vt_open:
                self.toggle_vt_panel()

        if not self.downloads_open:
            self.toggle_downloads_panel()

     
    # SETTINGS PANEL
    def create_settings_panel(self):
        self.settings_panel = QFrame(self)
        self.settings_panel.setStyleSheet("background-color: #181818; color: white;")
        self.settings_panel.setGeometry(self.width(), 0, 350, self.height())

        layout = QVBoxLayout()
        title = QLabel("Settings")
        layout.addWidget(title)

        self.bg_label = QLabel("Background: " + (self.background_path or "Default"))
        layout.addWidget(self.bg_label)

        choose_bg_btn = QPushButton("Choose Background Image")
        choose_bg_btn.clicked.connect(self.choose_background_image)
        layout.addWidget(choose_bg_btn)

        reset_bg_btn = QPushButton("Reset Background")
        reset_bg_btn.clicked.connect(self.reset_background_image)
        layout.addWidget(reset_bg_btn)

        self.settings_panel.setLayout(layout)
        self.settings_open = False

    def toggle_settings_panel(self):
        if self.settings_open:
            self.settings_panel.setGeometry(self.width(), 0, 350, self.height())
            self.settings_open = False
        else:
            self.settings_panel.setGeometry(self.width() - 350, 0, 350, self.height())
            self.settings_open = True

    def choose_background_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Background Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.background_path = file_path
            self.settings["background_path"] = file_path
            save_settings(self.settings)
            self.bg_label.setText("Background: " + file_path)
            v = self.current_view()
            if v:
                self.show_homepage(v)

    def reset_background_image(self):
        self.background_path = None
        self.settings["background_path"] = None
        save_settings(self.settings)
        self.bg_label.setText("Background: Default")
        v = self.current_view()
        if v:
            self.show_homepage(v)

         
    # MUSIC + VIDEO PANEL
    def create_music_panel(self):
        self.music_panel = QFrame(self)
        self.music_panel.setStyleSheet("background-color: #101018; color: white;")
        self.music_panel.setGeometry(self.width(), 0, 350, self.height())

        layout = QVBoxLayout()
        title = QLabel("Media")
        layout.addWidget(title)

        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(180)
        layout.addWidget(self.video_widget)

        self.music_list = QListWidget()
        layout.addWidget(self.music_list)

        controls_layout = QHBoxLayout()
        self.btn_prev = QPushButton("⏮")
        self.btn_play = QPushButton("⏯")
        self.btn_next = QPushButton("⏭")
        controls_layout.addWidget(self.btn_prev)
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_next)
        layout.addLayout(controls_layout)

        vol_layout = QHBoxLayout()
        vol_label = QLabel("Volume")
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(70)
        vol_layout.addWidget(vol_label)
        vol_layout.addWidget(self.vol_slider)
        layout.addLayout(vol_layout)

        add_local_btn = QPushButton("Add Local Media")
        add_local_btn.clicked.connect(self.add_local_media)
        layout.addWidget(add_local_btn)

        add_stream_btn = QPushButton("Add Stream URL")
        add_stream_btn.clicked.connect(self.add_stream_url)
        layout.addWidget(add_stream_btn)

        add_yt_btn = QPushButton("Add YouTube URL")
        add_yt_btn.clicked.connect(self.add_youtube_url)
        layout.addWidget(add_yt_btn)

        self.music_panel.setLayout(layout)
        self.music_open = False

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.7)
        self.player.setVideoOutput(self.video_widget)

        self.media_urls = [] 
        self.current_index = -1

        self.vol_slider.valueChanged.connect(self.on_volume_changed)
        self.btn_play.clicked.connect(self.toggle_play_pause)
        self.btn_prev.clicked.connect(self.play_prev)
        self.btn_next.clicked.connect(self.play_next)
        self.music_list.itemDoubleClicked.connect(self.play_selected_track)

    def on_volume_changed(self, value):
        self.audio_output.setVolume(value / 100.0)

    def toggle_music_panel(self):
        if self.music_open:
            self.music_panel.setGeometry(self.width(), 0, 350, self.height())
            self.music_open = False
        else:
            self.music_panel.setGeometry(self.width() - 350, 0, 350, self.height())
            self.music_open = True

    def add_local_media(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Media File", "",
            "Media Files (*.mp3 *.wav *.ogg *.mp4 *.mkv *.webm)"
        )
        if not file_path:
            return
        url = QUrl.fromLocalFile(file_path)
        self.media_urls.append(url)
        self.music_list.addItem(file_path)

    def add_stream_url(self):
        url, ok = QInputDialog.getText(self, "Stream URL", "Enter stream URL:")
        if not ok or not url.strip():
            return
        qurl = QUrl(url.strip())
        self.media_urls.append(qurl)
        self.music_list.addItem(url.strip())

    def add_youtube_url(self):
        yt_url, ok = QInputDialog.getText(self, "YouTube URL", "Enter YouTube URL:")
        if not ok or not yt_url.strip():
            return
        yt_url = yt_url.strip()
        try:
            ydl_opts = {
                "format": "best",
                "quiet": True,
                "skip_download": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(yt_url, download=False)
                media_url = info["url"]
            qurl = QUrl(media_url)
            self.media_urls.append(qurl)
            self.music_list.addItem(f"YouTube: {info.get('title','Unknown')}")
        except Exception as e:
            self.music_list.addItem(f"Error: {e}")

    def play_selected_track(self, item):
        row = self.music_list.row(item)
        self.play_track(row)

    def play_track(self, index):
        if index < 0 or index >= len(self.media_urls):
            return
        self.current_index = index
        self.player.setSource(self.media_urls[index])
        self.player.play()

    def play_next(self):
        if not self.media_urls:
            return
        self.current_index = (self.current_index + 1) % len(self.media_urls)
        self.play_track(self.current_index)

    def play_prev(self):
        if not self.media_urls:
            return
        self.current_index = (self.current_index - 1) % len(self.media_urls)
        self.play_track(self.current_index)

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            if self.current_index < 0 and self.media_urls:
                self.current_index = 0
            self.play_track(self.current_index)


     
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.ai_open:
            self.ai_panel.setGeometry(self.width() - 350, 0, 350, self.height())
        if self.vt_open:
            self.vt_panel.setGeometry(self.width() - 350, 0, 350, self.height())
        if self.downloads_open:
            self.downloads_panel.setGeometry(self.width() - 350, 0, 350, self.height())
        if self.settings_open:
            self.settings_panel.setGeometry(self.width() - 350, 0, 350, self.height())
        if self.music_open:
            self.music_panel.setGeometry(self.width() - 350, 0, 350, self.height())
# ahh yes the jankest code in the world.

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Browser()
    window.show()
    sys.exit(app.exec())
