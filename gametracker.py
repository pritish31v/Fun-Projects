import sys, os, json, re, glob, urllib.request, urllib.parse, webbrowser, traceback

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QCheckBox, QDialog, QComboBox, QSizePolicy,
    QStackedWidget, QListWidget, QMessageBox,
)
from PyQt6.QtCore import Qt, QRectF, QThread, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "games_tracker.json")
STATUSES = ["Not played", "Playing", "Halfway", "Played"]

# ==========================================
# APPLE SYSTEM COLOR PALETTE (macOS Dark)
# ==========================================
APPLE_PALETTE = {
    "bg_window": "#161618",
    "card_bg": "#202024",
    "card_border": "#2E2E33",
    "text_primary": "#FFFFFF",
    "text_secondary": "#98989D",
    "accent_blue": "#0A84FF",
    "status_played": "#30D158",
    "status_playing": "#FF9F0A",
    "status_halfway": "#BF5AF2",
    "status_not_played": "#8E8E93",
    "danger": "#FF453A",
}
STATUS_COLORS = {
    "Not played": APPLE_PALETTE["status_not_played"],
    "Playing": APPLE_PALETTE["status_playing"],
    "Halfway": APPLE_PALETTE["status_halfway"],
    "Played": APPLE_PALETTE["status_played"],
}
SECONDARY = APPLE_PALETTE["text_secondary"]

DEFAULT_GAMES = [
    "Minecraft", "Grand Theft Auto V", "Red Dead Redemption 2", "The Witcher 3: Wild Hunt",
    "Elden Ring", "Cyberpunk 2077", "Counter-Strike 2", "Valorant", "Fortnite",
    "Call of Duty: Warzone", "Apex Legends", "Dota 2", "League of Legends", "God of War",
    "Spider-Man 2", "Hogwarts Legacy", "Baldur's Gate 3", "Stardew Valley", "Terraria",
    "Among Us", "Rocket League", "Portal 2", "Half-Life 2", "Skyrim", "Fallout 4",
    "The Last of Us Part II", "Horizon Zero Dawn", "Assassin's Creed Valhalla", "Hollow Knight",
    "Celeste", "Undertale", "Dead Cells", "Hades", "Subnautica", "Genshin Impact",
    "Super Mario Odyssey", "The Legend of Zelda: Breath of the Wild", "Ghost of Tsushima",
    "Forza Horizon 5", "EA Sports FC 25", "Overwatch 2", "Lethal Company", "Phasmophobia",
    "Dead by Daylight", "Rainbow Six Siege", "Left 4 Dead 2", "Dark Souls III", "Bloodborne",
    "Monster Hunter: World", "Resident Evil 4", "Destiny 2", "Starfield", "Diablo IV",
    "It Takes Two", "Cuphead", "Death Stranding", "Batman: Arkham Knight", "Doom Eternal",
]


# ==========================================
# HELPERS
# ==========================================
def tint(hex_color, alpha):
    """Hex color to rgba() string with alpha 0-255."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def score_color(score):
    try:
        v = int(score)
    except (TypeError, ValueError):
        return SECONDARY
    if v >= 75:
        return APPLE_PALETTE["status_played"]
    if v >= 50:
        return APPLE_PALETTE["status_playing"]
    return APPLE_PALETTE["danger"]


def repolish(w):
    w.style().unpolish(w)
    w.style().polish(w)


def make_button(text, color, height=32, radius=8, filled=False):
    b = QPushButton(text)
    b.setFixedHeight(height)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if filled:
        b.setStyleSheet(f"""
            QPushButton {{ background-color: {color}; color: #FFFFFF; border: 1px solid {color};
                border-radius: {radius}px; padding: 0 16px; font-size: 12px; font-weight: 600; }}
            QPushButton:hover {{ border-color: #FFFFFF; }}
        """)
    else:
        b.setStyleSheet(f"""
            QPushButton {{ background-color: {tint(color, 36)}; color: {color};
                border: 1px solid {tint(color, 110)}; border-radius: {radius}px;
                padding: 0 14px; font-size: 12px; font-weight: 600; }}
            QPushButton:hover {{ border-color: {color}; }}
        """)
    return b


# ==========================================
# STEAM: LOCAL LIBRARY SCAN
# ==========================================
def steam_installed_games():
    roots = [r"C:\Program Files (x86)\Steam", r"C:\Program Files\Steam",
             os.path.expanduser("~/.local/share/Steam"),
             os.path.expanduser("~/Library/Application Support/Steam")]
    libs = set()
    for root in roots:
        libs.add(os.path.join(root, "steamapps"))
        vdf = os.path.join(root, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf):
            with open(vdf, encoding="utf-8", errors="ignore") as f:
                for p in re.findall(r'"path"\s+"([^"]+)"', f.read()):
                    libs.add(os.path.join(p.replace("\\\\", "\\"), "steamapps"))
    names = set()
    for lib in libs:
        for acf in glob.glob(os.path.join(lib, "appmanifest_*.acf")):
            with open(acf, encoding="utf-8", errors="ignore") as f:
                m = re.search(r'"name"\s+"([^"]+)"', f.read())
            if m and not re.search(r"Steamworks|Redistributable|Proton", m.group(1)):
                names.add(m.group(1))
    return sorted(names)


# ==========================================
# STEAM STORE SEARCH (no API key)
# ==========================================
def http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "GameTracker/4.1"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def steam_search(term):
    url = "https://store.steampowered.com/api/storesearch/?" + urllib.parse.urlencode(
        {"term": term, "l": "english", "cc": "US"})
    return http_json(url).get("items", [])


def steam_details(appid):
    url = "https://store.steampowered.com/api/appdetails?" + urllib.parse.urlencode(
        {"appids": appid, "l": "english"})
    data = http_json(url).get(str(appid), {})
    if not data.get("success"):
        return None
    d = data["data"]
    price = "Free" if d.get("is_free") else d.get("price_overview", {}).get("final_formatted", "N/A")
    return {
        "name": d.get("name", "Unknown"),
        "desc": re.sub(r"<[^>]+>", "", d.get("short_description", "")).strip(),
        "developers": ", ".join(d.get("developers", [])) or "Unknown",
        "genres": [g["description"] for g in d.get("genres", [])],
        "release": d.get("release_date", {}).get("date", "Unknown"),
        "price": price,
        "metacritic": str(d.get("metacritic", {}).get("score", "N/A")),
        "url": f"https://store.steampowered.com/app/{appid}",
    }


class Worker(QThread):
    """Runs a network call off the UI thread and reports (result, error)."""
    done = pyqtSignal(object, object)

    def __init__(self, func, arg):
        super().__init__()
        self.func, self.arg = func, arg

    def run(self):
        try:
            self.done.emit(self.func(self.arg), None)
        except Exception as ex:
            self.done.emit(None, ex)


# ==========================================
# CIRCULAR COMPLETION RING
# ==========================================
class AppleProgressRing(QWidget):
    def __init__(self, percent=0, parent=None):
        super().__init__(parent)
        self.percent = percent
        self.setFixedSize(72, 72)

    def set_percent(self, val):
        self.percent = max(0, min(100, int(val)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(7, 7, 58, 58)

        track_pen = QPen(QColor(255, 255, 255, 18), 6)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawEllipse(rect)

        if self.percent > 0:
            arc_pen = QPen(QColor(APPLE_PALETTE["status_played"]), 6)
            arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(arc_pen)
            painter.drawArc(rect, 90 * 16, int(-(self.percent / 100.0) * 360 * 16))

        painter.setPen(QColor(APPLE_PALETTE["text_primary"]))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 16, 72, 22), Qt.AlignmentFlag.AlignCenter, f"{self.percent}%")

        painter.setPen(QColor(SECONDARY))
        painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Medium))
        painter.drawText(QRectF(0, 36, 72, 16), Qt.AlignmentFlag.AlignCenter, "COMPLETED")
        painter.end()


# ==========================================
# STAT CARD
# ==========================================
class StatCard(QFrame):
    def __init__(self, title, count=0, color="#FFFFFF", parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setFixedHeight(76)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        dot = QFrame()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
        layout.addWidget(dot)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self.count_label = QLabel(str(count))
        self.count_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #FFFFFF;")
        title_label = QLabel(title.upper())
        title_label.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {SECONDARY};")
        text_layout.addWidget(self.count_label)
        text_layout.addWidget(title_label)
        layout.addLayout(text_layout)
        layout.addStretch()

    def update_count(self, count):
        self.count_label.setText(str(count))


# ==========================================
# GAME ROW (library)
# ==========================================
class GameRow(QFrame):
    cycle_requested = pyqtSignal(str)

    def __init__(self, title, status):
        super().__init__()
        self.title = title
        self.status = status
        self.setObjectName("GameRow")
        self.setFixedHeight(54)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(14)

        self.checkbox = QCheckBox()
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.checkbox)

        name = QLabel(title)
        name.setStyleSheet("font-size: 14px; font-weight: 500; color: #FFFFFF;")
        layout.addWidget(name)
        layout.addStretch()

        self.pill = QPushButton()
        self.pill.setFixedHeight(28)
        self.pill.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pill.clicked.connect(lambda: self.cycle_requested.emit(self.title))
        layout.addWidget(self.pill)

        self.set_status(status)

    def set_status(self, status):
        self.status = status
        color = STATUS_COLORS[status]
        self.pill.setText(status)
        self.pill.setStyleSheet(f"""
            QPushButton {{ background-color: {tint(color, 42)}; color: {color};
                border: 1px solid {tint(color, 110)}; border-radius: 14px;
                padding: 4px 14px; font-size: 12px; font-weight: 600; }}
            QPushButton:hover {{ border-color: {color}; }}
        """)


# ==========================================
# DETAIL PANEL (discover)
# ==========================================
class DetailPanel(QFrame):
    add_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("DetailCard")
        self.info = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 26, 28, 24)
        lay.setSpacing(10)

        self.title = QLabel()
        self.title.setWordWrap(True)
        self.title.setStyleSheet("font-size: 22px; font-weight: 700;")
        self.meta = QLabel()
        self.meta.setObjectName("Muted")
        self.meta.setWordWrap(True)
        self.genres = QLabel()
        self.genres.setWordWrap(True)
        self.genres.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {APPLE_PALETTE['accent_blue']};")
        self.desc = QLabel()
        self.desc.setWordWrap(True)
        self.desc.setStyleSheet("font-size: 13px; color: #C7C7CC;")

        stats = QHBoxLayout()
        stats.setSpacing(10)
        price_box, self.price_val = self._stat_box("Price")
        score_box, self.score_val = self._stat_box("Metacritic")
        lib_box, self.lib_val = self._stat_box("In library")
        for box in (price_box, score_box, lib_box):
            stats.addWidget(box)
        stats.addStretch()

        add_hdr = QLabel("Add to library as")
        add_hdr.setObjectName("Muted")
        row = QHBoxLayout()
        row.setSpacing(8)
        for s in STATUSES:
            b = make_button(s, STATUS_COLORS[s], height=34, radius=17)
            b.clicked.connect(lambda _=False, s=s: self.add_requested.emit(s))
            row.addWidget(b)
        row.addStretch()

        steam_btn = make_button("Open Steam page", "#3A3A3C", height=34, radius=17, filled=True)
        steam_btn.clicked.connect(self.open_page)

        lay.addWidget(self.title)
        lay.addWidget(self.meta)
        lay.addWidget(self.genres)
        lay.addWidget(self.desc)
        lay.addSpacing(8)
        lay.addLayout(stats)
        lay.addSpacing(8)
        lay.addWidget(add_hdr)
        lay.addLayout(row)
        lay.addWidget(steam_btn, 0, Qt.AlignmentFlag.AlignLeft)
        lay.addStretch()

        self.show_empty()

    def _stat_box(self, caption):
        box = QFrame()
        box.setObjectName("StatBox")
        box.setFixedWidth(150)
        v = QVBoxLayout(box)
        v.setContentsMargins(14, 10, 14, 10)
        v.setSpacing(2)
        val = QLabel("-")
        val.setStyleSheet("font-size: 16px; font-weight: 700;")
        cap = QLabel(caption.upper())
        cap.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {SECONDARY};")
        v.addWidget(val)
        v.addWidget(cap)
        return box, val

    def show_empty(self):
        self.info = None
        self.title.setText("Search for a game")
        self.meta.setText("Developer, release date and genres appear here.")
        self.genres.setText("")
        self.desc.setText("")
        for lbl in (self.price_val, self.score_val, self.lib_val):
            lbl.setText("-")
            lbl.setStyleSheet("font-size: 16px; font-weight: 700;")

    def show_game(self, info, lib_status):
        self.info = info
        self.title.setText(info["name"])
        self.meta.setText(f"{info['developers']}  •  {info['release']}")
        self.genres.setText("  ·  ".join(info["genres"][:6]) or "No genres listed")
        self.desc.setText(info["desc"] or "No description available.")
        self.price_val.setText(info["price"])
        self.score_val.setText(info["metacritic"])
        self.score_val.setStyleSheet(
            f"font-size: 16px; font-weight: 700; color: {score_color(info['metacritic'])};")
        lib = lib_status or "Not added"
        self.lib_val.setText(lib)
        self.lib_val.setStyleSheet(
            f"font-size: 16px; font-weight: 700; color: {STATUS_COLORS.get(lib, SECONDARY)};")

    def open_page(self):
        if self.info:
            webbrowser.open(self.info["url"])


# ==========================================
# ADD GAME DIALOG
# ==========================================
class AddGameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Game")
        self.setFixedSize(380, 250)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(10)

        header = QLabel("New Game Title")
        header.setStyleSheet("font-size: 16px; font-weight: 700;")
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. Cyberpunk 2077")

        lbl = QLabel("Initial Status")
        lbl.setObjectName("Muted")
        self.status_combo = QComboBox()
        self.status_combo.addItems(STATUSES)
        self.status_combo.setFixedHeight(36)

        lay.addWidget(header)
        lay.addWidget(self.input_name)
        lay.addWidget(lbl)
        lay.addWidget(self.status_combo)
        lay.addStretch()

        btns = QHBoxLayout()
        btns.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet("""
            QPushButton { background: transparent; color: #8E8E93; border: none;
                font-size: 13px; padding: 6px 14px; }
            QPushButton:hover { color: #FFFFFF; }
        """)
        cancel.clicked.connect(self.reject)
        add = make_button("Add Game", APPLE_PALETTE["accent_blue"], height=34, radius=8, filled=True)
        add.setFixedWidth(120)
        add.clicked.connect(self.accept)
        btns.addWidget(cancel)
        btns.addWidget(add)
        lay.addLayout(btns)


# ==========================================
# MAIN WINDOW
# ==========================================
class AppleGameTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Tracker")
        self.resize(1080, 760)
        self.setMinimumSize(900, 620)

        self.games = self.load_games()     # {title: status}
        self.active_filter = "All"
        self.rows = []
        self.workers = []
        self.details_cache = {}
        self.search_results = []

        self.init_ui()
        self.setStyleSheet(STYLE)
        self.rebuild_rows()
        self.refresh_metrics()
        self.save_games()

    # ----- data -----
    def load_games(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return {k: (v if v in STATUSES else "Not played") for k, v in data.items()}
            except (OSError, json.JSONDecodeError):
                pass
        return {g: "Not played" for g in DEFAULT_GAMES}

    def save_games(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.games, f, indent=2, ensure_ascii=False)

    # ----- layout -----
    def init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(28, 24, 28, 20)
        main.setSpacing(18)

        header = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(4)
        title = QLabel("Game Tracker")
        title.setObjectName("AppTitle")
        subtitle = QLabel("YOUR PERSONAL COLLECTION")
        subtitle.setObjectName("AppSubtitle")

        seg = QHBoxLayout()
        seg.setSpacing(4)
        self.btn_lib = QPushButton("Library")
        self.btn_lib.setObjectName("SegmentActive")
        self.btn_lib.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_disc = QPushButton("Discover")
        self.btn_disc.setObjectName("SegmentInactive")
        self.btn_disc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lib.clicked.connect(lambda: self.switch_page(0))
        self.btn_disc.clicked.connect(lambda: self.switch_page(1))
        seg.addWidget(self.btn_lib)
        seg.addWidget(self.btn_disc)
        seg.addStretch()

        left.addWidget(title)
        left.addWidget(subtitle)
        left.addSpacing(6)
        left.addLayout(seg)
        header.addLayout(left)
        header.addStretch()
        self.progress_ring = AppleProgressRing()
        header.addWidget(self.progress_ring)
        main.addLayout(header)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.cards = {}
        for name, color in [("Total", APPLE_PALETTE["accent_blue"])] + \
                           [(s, STATUS_COLORS[s]) for s in STATUSES]:
            card = StatCard(name, 0, color)
            self.cards[name] = card
            cards.addWidget(card)
        main.addLayout(cards)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.build_library_page())
        self.stack.addWidget(self.build_discover_page())
        main.addWidget(self.stack, 1)

    def switch_page(self, idx):
        self.stack.setCurrentIndex(idx)
        self.btn_lib.setObjectName("SegmentActive" if idx == 0 else "SegmentInactive")
        self.btn_disc.setObjectName("SegmentInactive" if idx == 0 else "SegmentActive")
        repolish(self.btn_lib)
        repolish(self.btn_disc)

    # ----- library page -----
    def build_library_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        bar = QHBoxLayout()
        bar.setSpacing(10)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search games by title...")
        self.search_box.setFixedHeight(36)
        self.search_box.textChanged.connect(self.apply_filters)
        bar.addWidget(self.search_box, 1)

        self.filter_buttons = {}
        for cat in ["All"] + STATUSES:
            btn = QPushButton(cat)
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, c=cat: self.set_filter(c))
            self.filter_buttons[cat] = btn
            bar.addWidget(btn)
        lay.addLayout(bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.list_container = QWidget()
        self.list_container.setObjectName("ListContainer")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 8, 0)
        self.list_layout.setSpacing(8)
        scroll.setWidget(self.list_container)
        lay.addWidget(scroll, 1)

        lay.addWidget(self.build_dock())
        self.set_filter("All")
        return page

    def build_dock(self):
        dock = QFrame()
        dock.setObjectName("BottomDock")
        dock.setFixedHeight(64)
        d = QHBoxLayout(dock)
        d.setContentsMargins(18, 10, 18, 10)
        d.setSpacing(10)

        lbl = QLabel("Set selected to:")
        lbl.setObjectName("Muted")
        d.addWidget(lbl)
        for s in STATUSES:
            b = make_button(s, STATUS_COLORS[s], height=32, radius=16)
            b.clicked.connect(lambda _=False, s=s: self.batch_set_status(s))
            d.addWidget(b)
        d.addStretch()

        remove = make_button("Remove", APPLE_PALETTE["danger"], height=34, radius=8)
        remove.clicked.connect(self.remove_selected)
        add = make_button("+ Add Custom", "#8E8E93", height=34, radius=8)
        add.clicked.connect(self.open_add_dialog)
        steam = make_button("Scan Steam", APPLE_PALETTE["accent_blue"], height=34, radius=8, filled=True)
        steam.clicked.connect(self.scan_steam)

        d.addWidget(remove)
        d.addWidget(add)
        d.addWidget(steam)
        return dock

    def set_filter(self, cat):
        self.active_filter = cat
        for name, btn in self.filter_buttons.items():
            btn.setProperty("active", "true" if name == cat else "false")
            repolish(btn)
        self.apply_filters()

    def apply_filters(self):
        if not hasattr(self, "search_box") or not hasattr(self, "rows"):
            return
        q = self.search_box.text().strip().lower()
        for row in self.rows:
            ok_search = not q or q in row.title.lower()
            ok_filter = self.active_filter == "All" or row.status == self.active_filter
            row.setVisible(ok_search and ok_filter)

    def rebuild_rows(self):
        checked = {r.title for r in self.rows if r.checkbox.isChecked()}
        while (item := self.list_layout.takeAt(0)) is not None:
            if item.widget():
                item.widget().deleteLater()
        self.rows = []
        for title in sorted(self.games, key=str.lower):
            row = GameRow(title, self.games[title])
            row.checkbox.setChecked(title in checked)
            row.cycle_requested.connect(self.cycle_status)
            self.rows.append(row)
            self.list_layout.addWidget(row)
        self.list_layout.addStretch()
        self.apply_filters()

    def refresh_metrics(self):
        total = len(self.games)
        counts = {s: sum(1 for v in self.games.values() if v == s) for s in STATUSES}
        self.cards["Total"].update_count(total)
        for s in STATUSES:
            self.cards[s].update_count(counts[s])
        pct = round(counts["Played"] / total * 100) if total else 0
        self.progress_ring.set_percent(pct)

    # ----- status changes -----
    def set_many(self, titles, status):
        for t in titles:
            self.games[t] = status
        for row in self.rows:
            if row.title in titles:
                row.set_status(status)
        self.save_games()
        self.refresh_metrics()
        self.apply_filters()

    def cycle_status(self, title):
        i = STATUSES.index(self.games[title])
        self.set_many([title], STATUSES[(i + 1) % len(STATUSES)])

    def batch_set_status(self, status):
        titles = [r.title for r in self.rows if r.checkbox.isChecked()]
        if titles:
            self.set_many(titles, status)

    # ----- add / remove / scan -----
    def open_add_dialog(self):
        dlg = AddGameDialog(self)
        if dlg.exec():
            title = dlg.input_name.text().strip()
            if not title:
                return
            self.games[title] = dlg.status_combo.currentText()
            self.save_games()
            self.rebuild_rows()
            self.refresh_metrics()

    def remove_selected(self):
        titles = [r.title for r in self.rows if r.checkbox.isChecked()]
        if not titles:
            return
        answer = QMessageBox.question(self, "Remove games",
                                      f"Remove {len(titles)} game(s) from your library?")
        if answer != QMessageBox.StandardButton.Yes:
            return
        for t in titles:
            self.games.pop(t, None)
        self.save_games()
        self.rebuild_rows()
        self.refresh_metrics()

    def scan_steam(self):
        found = steam_installed_games()
        if not found:
            QMessageBox.information(self, "Steam", "No installed Steam games were found on this PC.")
            return
        added = 0
        for name in found:
            if name not in self.games:
                self.games[name] = "Not played"
                added += 1
        self.save_games()
        self.rebuild_rows()
        self.refresh_metrics()
        QMessageBox.information(self, "Steam", f"Found {len(found)} installed games, added {added} new.")

    # ----- discover page -----
    def build_discover_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        bar = QHBoxLayout()
        bar.setSpacing(10)
        self.disc_input = QLineEdit()
        self.disc_input.setPlaceholderText("Search the Steam store...")
        self.disc_input.setFixedHeight(40)
        self.disc_input.returnPressed.connect(self.do_search)
        bar.addWidget(self.disc_input, 1)
        go = make_button("Search", APPLE_PALETTE["accent_blue"], height=40, radius=10, filled=True)
        go.setFixedWidth(110)
        go.clicked.connect(self.do_search)
        bar.addWidget(go)
        lay.addLayout(bar)

        self.disc_status = QLabel("Type a game name and press Enter. Results come from the Steam store.")
        self.disc_status.setObjectName("Muted")
        lay.addWidget(self.disc_status)

        body = QHBoxLayout()
        body.setSpacing(16)
        self.result_list = QListWidget()
        self.result_list.setObjectName("ResultList")
        self.result_list.setFixedWidth(360)
        self.result_list.currentRowChanged.connect(self.on_result_selected)
        body.addWidget(self.result_list)

        self.detail = DetailPanel()
        self.detail.add_requested.connect(self.add_from_discover)
        body.addWidget(self.detail, 1)
        lay.addLayout(body, 1)
        return page

    def run_task(self, func, arg, callback):
        self.workers = [w for w in self.workers if w.isRunning()]
        w = Worker(func, arg)
        w.done.connect(callback)
        self.workers.append(w)
        w.start()

    def do_search(self):
        term = self.disc_input.text().strip()
        if not term:
            return
        self.disc_status.setText(f'Searching for "{term}"...')
        self.run_task(steam_search, term, self.on_search_done)

    def on_search_done(self, items, error):
        if error:
            self.disc_status.setText(f"Could not reach Steam: {error}")
            return
        self.search_results = (items or [])[:40]
        self.result_list.clear()
        for it in self.search_results:
            self.result_list.addItem(self.result_label(it["name"]))
        self.disc_status.setText(
            f"{len(self.search_results)} result(s). Select a game to see details."
            if self.search_results else "No games found. Try a different name.")

    def result_label(self, name):
        return f"{name}   ·   {self.games[name]}" if name in self.games else name

    def refresh_result_labels(self):
        for i, it in enumerate(self.search_results):
            self.result_list.item(i).setText(self.result_label(it["name"]))

    def on_result_selected(self, row):
        if row < 0 or row >= len(self.search_results):
            return
        appid = self.search_results[row]["id"]
        if appid in self.details_cache:
            self.show_detail(self.details_cache[appid])
            return
        self.disc_status.setText("Loading game details...")
        self.run_task(steam_details, appid,
                      lambda info, err, a=appid: self.on_details(a, info, err))

    def on_details(self, appid, info, error):
        if error or not info:
            self.disc_status.setText("Could not load details for this game.")
            return
        self.details_cache[appid] = info
        self.show_detail(info)
        self.disc_status.setText("Choose a status to add it to your library.")

    def show_detail(self, info):
        self.detail.show_game(info, self.games.get(info["name"]))

    def add_from_discover(self, status):
        info = self.detail.info
        if not info:
            return
        name = info["name"]
        self.games[name] = status
        self.save_games()
        self.rebuild_rows()
        self.refresh_metrics()
        self.refresh_result_labels()
        self.show_detail(info)
        self.disc_status.setText(f'Saved "{name}" as {status}.')


# ==========================================
# APPLE HIG DARK STYLESHEET
# ==========================================
STYLE = """
QWidget { font-family: "Segoe UI", "Helvetica Neue", sans-serif; color: #FFFFFF; }
QMainWindow { background-color: #161618; }
QLabel { background: transparent; }
#ListContainer { background: transparent; }
#AppTitle { font-size: 26px; font-weight: 700; color: #FFFFFF; }
#AppSubtitle { font-size: 11px; font-weight: 600; color: #8E8E93; }
#Muted { font-size: 12px; color: #8E8E93; }

#SegmentActive { background-color: #3A3A3C; color: #FFFFFF; border: none; border-radius: 6px;
    padding: 4px 14px; font-size: 12px; font-weight: 600; }
#SegmentInactive { background: transparent; color: #8E8E93; border: none; border-radius: 6px;
    padding: 4px 14px; font-size: 12px; }
#SegmentInactive:hover { color: #FFFFFF; }

#StatCard { background-color: #202024; border: 1px solid #2E2E33; border-radius: 12px; }
#GameRow { background-color: #202024; border: 1px solid #2E2E33; border-radius: 10px; }
#GameRow:hover { background-color: #26262B; border-color: #38383E; }
#DetailCard { background-color: #202024; border: 1px solid #2E2E33; border-radius: 16px; }
#StatBox { background-color: #1C1C1F; border: 1px solid #2E2E33; border-radius: 12px; }
#BottomDock { background-color: #1C1C1F; border: 1px solid #2E2E33; border-radius: 14px; }

QLineEdit { background-color: #202024; border: 1px solid #2E2E33; border-radius: 10px;
    padding: 6px 14px; color: #FFFFFF; font-size: 13px; selection-background-color: #0A84FF; }
QLineEdit:focus { border: 1px solid #0A84FF; }

QPushButton[active="true"] { background-color: #202024; color: #FFFFFF; border: 1px solid #0A84FF;
    border-radius: 17px; padding: 0 16px; font-size: 12px; font-weight: 600; }
QPushButton[active="false"] { background-color: transparent; color: #8E8E93; border: 1px solid #2E2E33;
    border-radius: 17px; padding: 0 16px; font-size: 12px; }
QPushButton[active="false"]:hover { background-color: #202024; color: #FFFFFF; border-color: #3E3E44; }

QCheckBox::indicator { width: 18px; height: 18px; border-radius: 5px;
    border: 1px solid #48484A; background-color: #1C1C1E; }
QCheckBox::indicator:checked { background-color: #0A84FF; border-color: #0A84FF; }

#ResultList { background-color: #202024; border: 1px solid #2E2E33; border-radius: 12px;
    padding: 6px; color: #FFFFFF; font-size: 13px; outline: none; }
#ResultList::item { padding: 10px 12px; border-radius: 8px; }
#ResultList::item:hover { background-color: #2C2C2E; }
#ResultList::item:selected { background-color: #0A84FF; color: #FFFFFF; }

QComboBox { background-color: #161618; border: 1px solid #2E2E33; border-radius: 8px;
    padding: 6px 12px; color: #FFFFFF; font-size: 13px; }
QComboBox QAbstractItemView { background-color: #202024; color: #FFFFFF;
    selection-background-color: #0A84FF; border: 1px solid #2E2E33; }
QDialog { background-color: #202024; }

QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #3A3A3C; border-radius: 4px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
"""


def show_error(exc_type, exc, tb):
    """Show any uncaught error in a popup so it can't fail silently."""
    msg = "".join(traceback.format_exception(exc_type, exc, tb))
    print(msg)
    QMessageBox.critical(None, "Game Tracker error", msg)


if __name__ == "__main__":
    sys.excepthook = show_error
    app = QApplication(sys.argv)
    window = AppleGameTracker()
    window.show()
    sys.exit(app.exec())