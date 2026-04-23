import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit,
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QFrame
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

#If you are unlucky enough to debug this code im sorry -Daniel
#if you are here to edit and you made a change leave your name
#1.Daniel
#2.put your name here, so on and so forth


from openai import OpenAI

def ask_ai(prompt):
    client = OpenAI(api_key="svcacct-D79878OUq0iZpOjuvc6XfXpMd6rKsFg8-HsIkkhiR6cbkrt4edY27m89UENMiRt20u8Cj5jwMtT3BlbkFJAkCqhBWm57SSbwLzwWIs0Nfv3PzffOzDEOfxm3e2ZEwB6q_m4Mxvq5xUHN2lqGhN8tn8ggFqYA")  # <-- paste your key here ONLY on your computer

    try:
        response = client.responses.create(
            model="gpt-3.5-turbo",
            input=prompt
        )
        return response.output[0].content[0].text

    except Exception as e:
        return f"⚠ AI Error: {e}"


    try:
        response = requests.post(url, json=data, headers=headers)
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except:
        return "⚠ Error contacting AI API."


class Browser(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dor Browser")
        self.resize(1200, 800)

        # Web view
        self.view = QWebEngineView()
        self.setCentralWidget(self.view)

        # Toolbar
        toolbar = QToolBar("Navigation")
        self.addToolBar(toolbar)

        # Back
        back_action = QAction("Back", self)
        back_action.triggered.connect(self.view.back)
        toolbar.addAction(back_action)

        # Forward
        forward_action = QAction("Forward", self)
        forward_action.triggered.connect(self.view.forward)
        toolbar.addAction(forward_action)

        # Reload
        reload_action = QAction("Reload", self)
        reload_action.triggered.connect(self.view.reload)
        toolbar.addAction(reload_action)

        # AI Assistant toggle button
        ai_action = QAction("AI", self)
        ai_action.triggered.connect(self.toggle_ai_panel)
        toolbar.addAction(ai_action)

        # URL/Search bar
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.load_from_bar)
        toolbar.addWidget(self.url_bar)

        # AI Assistant Panel
        self.create_ai_panel()

        # Load homepage
        self.show_homepage()

        # Sync URL bar
        self.view.urlChanged.connect(self.update_url_bar)

    # AI PANEL UI
    def create_ai_panel(self):
        self.ai_panel = QFrame(self)
        self.ai_panel.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.ai_panel.setGeometry(self.width(), 0, 350, self.height())
        self.ai_panel.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout()

        self.ai_output = QTextEdit()
        self.ai_output.setReadOnly(True)
        self.ai_output.setStyleSheet("background-color: #111; color: white;")
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
        user_msg = self.ai_input.text().strip()
        if not user_msg:
            return

        self.ai_output.append(f"You: {user_msg}")
        self.ai_input.clear()

        ai_reply = ask_ai(user_msg)
        self.ai_output.append(f"Dor AI: {ai_reply}\n")

    # URL + SEARCH HANDLING
    def is_url(self, text):
        text = text.strip()
        if " " in text:
            return False
        return "." in text

    def load_from_bar(self):
        text = self.url_bar.text().strip()

        if text == "":
            self.show_homepage()
            return

        self.load_input(text)

    def load_input(self, text):
        if self.is_url(text):
            if not text.startswith(("http://", "https://")):
                text = "https://" + text
            self.view.setUrl(QUrl(text))
        else:
            google_url = "https://www.google.com/search?q=" + text.replace(" ", "+")
            self.view.setUrl(QUrl(google_url))

    def update_url_bar(self, qurl):
        url = qurl.toString()
        if url != "about:blank":
            self.url_bar.setText(url)

    def show_homepage(self):
        html = """
        <html>
        <head>
            <style>
                body {
                    background: linear-gradient(135deg, #1a1a1a, #0d0d0d);
                    color: white;
                    font-family: Arial;
                    text-align: center;
                    padding-top: 80px;
                }
                h1 {
                    font-size: 48px;
                    margin-bottom: 10px;
                    color: #00B2FF;
                }
                .search-box {
                    margin-top: 30px;
                }
                input {
                    width: 60%;
                    padding: 15px;
                    border-radius: 30px;
                    border: none;
                    font-size: 18px;
                    outline: none;
                    text-align: center;
                }
                .tiles {
                    margin-top: 50px;
                    display: flex;
                    justify-content: center;
                    gap: 20px;
                }
                .tile {
                    width: 120px;
                    height: 120px;
                    background: #00B2FF;
                    border-radius: 15px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-size: 16px;
                    cursor: pointer;
                    transition: 0.2s;
                }
                .tile:hover {
                    background: #333;
                }
            </style>

            <script>
                function doSearch(event) {
                    if (event.key === "Enter") {
                        let q = document.getElementById("homeSearch").value;
                        window.location.href = "https://www.google.com/search?q=" + encodeURIComponent(q);
                    }
                }
            </script>
        </head>
        <body>
            <h1>Dor Browser</h1>

            <div class="search-box">
                <input id="homeSearch" placeholder="Search the web..." onkeydown="doSearch(event)">
            </div>

            <div class="tiles">
                <div class="tile" onclick="window.location.href='https://youtube.com'">YouTube</div>
                <div class="tile" onclick="window.location.href='https://reddit.com'">Reddit</div>
                <div class="tile" onclick="window.location.href='https://github.com'">Github</div>
            </div>

            <div class="ai-button" onclick="window.location.href='ai://open'">Open AI Assistant</div>
        </body>
        </html>
        """
        self.view.setHtml(html, QUrl("about:blank"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Browser()
    window.show()
    sys.exit(app.exec_())
