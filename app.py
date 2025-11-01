import os
import json
import sys
import requests
from dotenv import load_dotenv
from rapidfuzz import fuzz
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                              QLabel, QFrame, QGraphicsDropShadowEffect, QDialog, 
                              QComboBox, QScrollArea, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QPoint
from PyQt6.QtGui import QFont, QTextCursor, QColor, QPalette, QLinearGradient, QPainter, QBrush

load_dotenv()
api_key = os.getenv("TOGETHER_AI_API_KEY")

if not api_key:
    raise ValueError("❌ Clé API non trouvée. Vérifie ton fichier .env.")

DOSSIER_DATA = "data"
FICHIER_BASE = os.path.join(DOSSIER_DATA, "base_connaissances.json")
os.makedirs(DOSSIER_DATA, exist_ok=True)

def verifier_fichier_json():
    if not os.path.exists(FICHIER_BASE):
        with open(FICHIER_BASE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

verifier_fichier_json()

def charger_base(fichier=FICHIER_BASE):
    with open(fichier, "r", encoding="utf-8") as f:
        return json.load(f)

def sauvegarder_base(base, fichier=FICHIER_BASE):
    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=4)

connaissances_locales = charger_base()

def question_deja_connue(question, base, seuil=70):
    for q in base:
        score = fuzz.ratio(question, q)
        if score >= seuil:
            return q
    return None

class APIThread(QThread):
    response_received = pyqtSignal(str)
    
    def __init__(self, question):
        super().__init__()
        self.question = question
        
    def run(self):
        try:
            question_norm = self.question.lower().strip()
            question_similaire = question_deja_connue(question_norm, connaissances_locales)
            
            if question_similaire:
                response = f"🎯 {connaissances_locales[question_similaire]}"
                self.response_received.emit(response)
                return
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "messages": [
                    {"role": "system", "content": "Tu es Jymie, un assistant IA sophistiqué et élégant qui répond toujours en français avec style et précision."},
                    {"role": "user", "content": self.question}
                ],
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 512
            }
            
            response = requests.post("https://api.together.ai/v1/chat/completions", 
                                   headers=headers, json=data, timeout=30)
            response.raise_for_status()
            reponse_ia = response.json()["choices"][0]["message"]["content"]
            
            connaissances_locales[question_norm] = reponse_ia
            sauvegarder_base(connaissances_locales)
            
            self.response_received.emit(reponse_ia)
            
        except Exception as e:
            self.response_received.emit(f"❌ Une erreur s'est produite : {str(e)}")

class MessageBubble(QFrame):
    """Bulle de message ultra-moderne avec glassmorphism"""
    def __init__(self, text, is_user=True):
        super().__init__()
        self.setMaximumWidth(600)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        
        # Icône et nom
        header_layout = QHBoxLayout()
        icon = QLabel("👤" if is_user else "🤖")
        icon.setFont(QFont("Segoe UI Emoji", 16))
        name = QLabel("Vous" if is_user else "Jymie")
        name.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        
        header_layout.addWidget(icon)
        header_layout.addWidget(name)
        header_layout.addStretch()
        
        # Message
        message_label = QLabel(text)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Segoe UI", 11))
        message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        layout.addLayout(header_layout)
        layout.addWidget(message_label)
        
        self.setLayout(layout)
        
        if is_user:
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(102, 126, 234, 0.95),
                        stop:1 rgba(118, 75, 162, 0.95));
                    border-radius: 20px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                QLabel {
                    color: white;
                    background: transparent;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(30, 30, 46, 0.95),
                        stop:1 rgba(24, 24, 37, 0.95));
                    border-radius: 20px;
                    border: 1px solid rgba(102, 126, 234, 0.3);
                }
                QLabel {
                    color: #e0e0e0;
                    background: transparent;
                }
            """)
        
        # Effet d'ombre magnifique
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

class AboutDialog(QDialog):
    """Fenêtre À propos - Biographie de l'auteur"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("À propos de Jymie IA")
        self.setFixedSize(600, 550)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f0c29, stop:0.5 #302b63, stop:1 #24243e);
                border-radius: 20px;
            }
        """)
        self.init_ui()
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.setGraphicsEffect(shadow)
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # En-tête avec icône
        header_layout = QHBoxLayout()
        icon_label = QLabel("👨‍💻")
        icon_label.setFont(QFont("Segoe UI Emoji", 64))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_layout = QVBoxLayout()
        title = QLabel("À propos")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        
        subtitle = QLabel("Créé avec passion")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        header_layout.addWidget(icon_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Ligne de séparation
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: rgba(102, 126, 234, 0.3); height: 2px;")
        layout.addWidget(separator)
        
        # Informations de l'auteur dans un cadre stylé
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(15)
        
        # Nom de l'auteur
        author_name = QLabel("🎓 MEKEM SONFOUO DILANE")
        author_name.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        author_name.setStyleSheet("color: #667eea;")
        info_layout.addWidget(author_name)
        
        # Informations personnelles
        info_data = [
            ("📅", "Date de naissance", "14 Mai 2009"),
            ("🌍", "Lieu de naissance", "Cameroun"),
            ("🎯", "Année actuelle", "2025"),
            ("📚", "Classe", "Première C"),
            ("📍", "Ville", "Douala"),
            ("🏢", "Entreprise", "Technologie 2.0"),
            ("📧", "Email", "mekemdilan@gmail.com"),
            ("📱", "Téléphone", "+237 688 683 918")
        ]
        
        for emoji, label_text, value in info_data:
            item_layout = QHBoxLayout()
            
            emoji_label = QLabel(emoji)
            emoji_label.setFont(QFont("Segoe UI Emoji", 14))
            
            text_label = QLabel(f"{label_text}:")
            text_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            text_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
            text_label.setMinimumWidth(150)
            
            value_label = QLabel(value)
            value_label.setFont(QFont("Segoe UI", 11))
            value_label.setStyleSheet("color: white;")
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            
            item_layout.addWidget(emoji_label)
            item_layout.addWidget(text_label)
            item_layout.addWidget(value_label)
            item_layout.addStretch()
            
            info_layout.addLayout(item_layout)
        
        info_frame.setLayout(info_layout)
        layout.addWidget(info_frame)
        
        # Message inspirant
        quote = QLabel("✨ « L'innovation commence par un rêve et se réalise par la détermination » ✨")
        quote.setFont(QFont("Segoe UI", 10, QFont.Weight.Normal, True))
        quote.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        quote.setAlignment(Qt.AlignmentFlag.AlignCenter)
        quote.setWordWrap(True)
        layout.addWidget(quote)
        
        # Bouton fermer
        close_btn = QPushButton("✨ Fermer")
        close_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 15px;
                padding: 15px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #764ba2, stop:1 #667eea);
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class ParametresDialog(QDialog):
    """Fenêtre de paramètres élégante"""
    theme_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres")
        self.setFixedSize(600, 700)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f0c29, stop:0.5 #302b63, stop:1 #24243e);
                border-radius: 20px;
            }
        """)
        self.init_ui()
        
        # Ombre pour la fenêtre
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.setGraphicsEffect(shadow)
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Titre avec style
        title = QLabel("⚙️  Paramètres")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(10)
        
        # Mode d'apparence
        appearance_label = QLabel("🎨  Mode d'apparence")
        appearance_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        appearance_label.setStyleSheet("color: #a0a0ff;")
        layout.addWidget(appearance_label)
        
        self.appearance_combo = QComboBox()
        self.appearance_combo.addItems(["🌙 Sombre", "☀️ Clair", "🔄 Automatique"])
        self.appearance_combo.setFont(QFont("Segoe UI", 11))
        self.appearance_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 2px solid rgba(102, 126, 234, 0.5);
                border-radius: 12px;
                padding: 12px;
            }
            QComboBox:hover {
                border: 2px solid rgba(102, 126, 234, 1);
                background: rgba(255, 255, 255, 0.15);
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: #1e1e2e;
                color: white;
                selection-background-color: #667eea;
                border: 1px solid #667eea;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.appearance_combo)
        
        # Thème de couleur
        theme_label = QLabel("🎨  Thème de couleur")
        theme_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        theme_label.setStyleSheet("color: #a0a0ff;")
        layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["💜 Violet Cosmique", "💙 Bleu Océan", "💚 Vert Émeraude", "❤️ Rouge Passion"])
        self.theme_combo.setFont(QFont("Segoe UI", 11))
        self.theme_combo.setStyleSheet(self.appearance_combo.styleSheet())
        layout.addWidget(self.theme_combo)
        
        layout.addStretch()
        
        # Bouton fermer stylé
        close_btn = QPushButton("✨ Fermer")
        close_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 15px;
                padding: 15px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #764ba2, stop:1 #667eea);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5568d3, stop:1 #653a8b);
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class JymieIA(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jymie IA - L'avenir de l'intelligence artificielle")
        self.setGeometry(100, 50, 1000, 750)
        self.api_thread = None
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.show_typing_indicator)
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(main_layout)
        
        # Style global avec fond dégradé magnifique
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f0c29, stop:0.33 #302b63, stop:0.66 #24243e, stop:1 #0f0c29);
            }
        """)
        
        # === HEADER SPECTACULAIRE ===
        header = QFrame()
        header.setMinimumHeight(180)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.3),
                    stop:0.5 rgba(118, 75, 162, 0.3),
                    stop:1 rgba(237, 66, 100, 0.3));
                border: none;
                border-bottom: 2px solid rgba(102, 126, 234, 0.5);
            }
        """)
        
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(40, 30, 40, 30)
        header_layout.setSpacing(10)
        
        # Logo et titre
        title_container = QHBoxLayout()
        
        logo = QLabel("✨")
        logo.setFont(QFont("Segoe UI Emoji", 48))
        
        title_text_layout = QVBoxLayout()
        title_text_layout.setSpacing(5)
        
        title_label = QLabel("Jymie")
        title_label.setFont(QFont("Segoe UI", 42, QFont.Weight.Bold))
        title_label.setStyleSheet("""
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #fff, stop:0.5 #667eea, stop:1 #764ba2);
        """)
        
        subtitle_label = QLabel("Intelligence Artificielle de Nouvelle Génération")
        subtitle_label.setFont(QFont("Segoe UI", 13))
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        
        title_text_layout.addWidget(title_label)
        title_text_layout.addWidget(subtitle_label)
        
        title_container.addWidget(logo)
        title_container.addLayout(title_text_layout)
        title_container.addStretch()
        
        # Indicateur de statut animé
        status_container = QHBoxLayout()
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Segoe UI", 16))
        self.status_indicator.setStyleSheet("color: #00ff88;")
        status_text = QLabel("En ligne")
        status_text.setFont(QFont("Segoe UI", 11))
        status_text.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        status_container.addWidget(self.status_indicator)
        status_container.addWidget(status_text)
        title_container.addLayout(status_container)
        
        header_layout.addLayout(title_container)
        header.setLayout(header_layout)
        
        # Animation du statut
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.animate_status)
        self.status_timer.start(1000)
        
        main_layout.addWidget(header)
        
        # === ZONE DE CHAT AVEC SCROLL ===
        chat_container = QWidget()
        chat_container.setStyleSheet("background: transparent;")
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(20, 20, 20, 20)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.05);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(102, 126, 234, 0.5);
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(102, 126, 234, 0.8);
            }
        """)
        
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setSpacing(15)
        self.chat_layout.addStretch()
        self.chat_widget.setLayout(self.chat_layout)
        
        scroll.setWidget(self.chat_widget)
        chat_layout.addWidget(scroll)
        chat_container.setLayout(chat_layout)
        
        main_layout.addWidget(chat_container, stretch=1)
        
        # Message de bienvenue
        welcome_msg = "Bonjour ! Je suis Jymie, votre assistant IA de nouvelle génération. Je suis là pour répondre à toutes vos questions avec intelligence et élégance. Comment puis-je vous aider aujourd'hui ? ✨"
        self.add_message(welcome_msg, is_user=False)
        
        # === ZONE DE SAISIE FUTURISTE ===
        input_container = QWidget()
        input_container.setStyleSheet("""
            QWidget {
                background: rgba(20, 20, 30, 0.8);
                border-top: 1px solid rgba(102, 126, 234, 0.3);
            }
        """)
        input_main_layout = QVBoxLayout()
        input_main_layout.setContentsMargins(30, 20, 30, 20)
        
        input_layout = QHBoxLayout()
        input_layout.setSpacing(15)
        
        self.champ_question = QLineEdit()
        self.champ_question.setPlaceholderText("✍️  Posez votre question à Jymie...")
        self.champ_question.setFont(QFont("Segoe UI", 13))
        self.champ_question.setMinimumHeight(55)
        self.champ_question.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                color: white;
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 27px;
                padding: 0 25px;
            }
            QLineEdit:focus {
                border: 2px solid rgba(102, 126, 234, 0.8);
                background: rgba(255, 255, 255, 0.12);
            }
        """)
        self.champ_question.returnPressed.connect(self.envoyer_question)
        
        # Ombre pour le champ
        input_shadow = QGraphicsDropShadowEffect()
        input_shadow.setBlurRadius(20)
        input_shadow.setColor(QColor(0, 0, 0, 60))
        input_shadow.setOffset(0, 5)
        self.champ_question.setGraphicsEffect(input_shadow)
        
        btn_envoyer = QPushButton("Envoyer  →")
        btn_envoyer.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        btn_envoyer.setMinimumHeight(55)
        btn_envoyer.setMinimumWidth(140)
        btn_envoyer.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_envoyer.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 27px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #764ba2, stop:1 #667eea);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5568d3, stop:1 #653a8b);
            }
        """)
        btn_envoyer.clicked.connect(self.envoyer_question)
        
        # Ombre pour le bouton
        btn_shadow = QGraphicsDropShadowEffect()
        btn_shadow.setBlurRadius(25)
        btn_shadow.setColor(QColor(102, 126, 234, 120))
        btn_shadow.setOffset(0, 8)
        btn_envoyer.setGraphicsEffect(btn_shadow)
        
        input_layout.addWidget(self.champ_question)
        input_layout.addWidget(btn_envoyer)
        
        input_main_layout.addLayout(input_layout)
        
        # Boutons secondaires
        secondary_buttons = QHBoxLayout()
        secondary_buttons.setSpacing(10)
        
        btn_about = QPushButton("ℹ️  À propos")
        btn_about.setFont(QFont("Segoe UI", 10))
        btn_about.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_about.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: rgba(102, 126, 234, 0.2);
                color: white;
                border: 1px solid rgba(102, 126, 234, 0.6);
            }
        """)
        btn_about.clicked.connect(self.afficher_about)
        
        btn_parametres = QPushButton("⚙️  Paramètres")
        btn_parametres.setFont(QFont("Segoe UI", 10))
        btn_parametres.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_parametres.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: rgba(102, 126, 234, 0.2);
                color: white;
                border: 1px solid rgba(102, 126, 234, 0.6);
            }
        """)
        btn_parametres.clicked.connect(self.afficher_parametres)
        
        secondary_buttons.addStretch()
        secondary_buttons.addWidget(btn_about)
        secondary_buttons.addWidget(btn_parametres)
        
        input_main_layout.addLayout(secondary_buttons)
        
        # Footer avec copyright
        footer = QLabel("© 2025 Technologie 2.0 - Créé par MEKEM SONFOUO DILANE")
        footer.setFont(QFont("Segoe UI", 9))
        footer.setStyleSheet("color: rgba(255, 255, 255, 0.5); background: transparent; padding: 5px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        input_main_layout.addWidget(footer)
        
        input_container.setLayout(input_main_layout)
        
        main_layout.addWidget(input_container)
        
        self.scroll_area = scroll
    
    def animate_status(self):
        """Anime l'indicateur de statut"""
        current = self.status_indicator.styleSheet()
        if "color: #00ff88" in current:
            self.status_indicator.setStyleSheet("color: #00cc66;")
        else:
            self.status_indicator.setStyleSheet("color: #00ff88;")
    
    def add_message(self, text, is_user=True):
        """Ajoute un message élégant dans le chat"""
        bubble = MessageBubble(text, is_user)
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container_layout = QHBoxLayout()
        container_layout.setContentsMargins(10, 5, 10, 5)
        
        if is_user:
            container_layout.addStretch()
            container_layout.addWidget(bubble)
        else:
            container_layout.addWidget(bubble)
            container_layout.addStretch()
        
        container.setLayout(container_layout)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, container)
        
        QApplication.processEvents()
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
    
    def envoyer_question(self):
        """Envoie une question avec animation"""
        question = self.champ_question.text().strip()
        if not question:
            return
        
        self.add_message(question, is_user=True)
        self.champ_question.clear()
        self.champ_question.setEnabled(False)
        
        # Ajouter indicateur de réflexion
        self.add_message("💭 Je réfléchis à votre question...", is_user=False)
        
        self.api_thread = APIThread(question)
        self.api_thread.response_received.connect(self.afficher_reponse)
        self.api_thread.start()
    
    def afficher_reponse(self, reponse):
        """Affiche la réponse avec animation"""
        # Supprimer l'indicateur de réflexion
        last_widget = self.chat_layout.itemAt(self.chat_layout.count() - 2).widget()
        if last_widget:
            last_widget.deleteLater()
        
        self.add_message(reponse, is_user=False)
        self.champ_question.setEnabled(True)
        self.champ_question.setFocus()
    
    def afficher_parametres(self):
        """Affiche les paramètres"""
        dialog = ParametresDialog(self)
        dialog.theme_changed.connect(self.change_background)
        dialog.exec()
    
    def apply_background(self):
        """Applique le fond d'écran actuel"""
        self.setStyleSheet(f"""
            QMainWindow {{
                {self.current_background}
            }}
        """)
    
    def change_background(self, wallpaper_name):
        """Change le fond d'écran de l'application"""
        # Normaliser le nom en retirant l'emoji au début
        wallpaper_name = wallpaper_name.strip()
        
        backgrounds = {
            "🌌 Cosmos Violet": """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f0c29, stop:0.33 #302b63, stop:0.66 #24243e, stop:1 #0f0c29);
            """,
            "🌊 Océan Profond": """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #000428, stop:0.5 #004e92, stop:1 #000428);
            """,
            "🌅 Coucher de Soleil": """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ff512f, stop:0.5 #f09819, stop:1 #dd2476);
            """,
            "🌃 Ville Nocturne": """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #232526, stop:0.5 #414345, stop:1 #232526);
            """,
            "🌈 Arc-en-ciel": """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ee0979, stop:0.25 #ff6a00, stop:0.5 #ffd700, 
                    stop:0.75 #00d4ff, stop:1 #8a2be2);
            """,
            "🔥 Flammes": """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ff0844, stop:0.5 #ffb199, stop:1 #ff0844);
            """,
            "❄️ Glacial": """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2c3e50, stop:0.5 #4ca1af, stop:1 #2c3e50);
            """,
            "🌸 Sakura": """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffecd2, stop:0.5 #fcb69f, stop:1 #ff9a9e);
            """,
            "🌲 Forêt Enchantée": """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #134e5e, stop:0.5 #71b280, stop:1 #134e5e);
            """,
            "⚡ Électrique": """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4776e6, stop:0.5 #8e54e9, stop:1 #4776e6);
            """
        }
        
        self.current_background = backgrounds.get(wallpaper_name, backgrounds["🌌 Cosmos Violet"])
        self.apply_background()
        
        # Forcer la mise à jour visuelle
        self.update()
        self.repaint()
        QApplication.processEvents()
    
    def afficher_about(self):
        """Affiche la fenêtre À propos"""
        dialog = AboutDialog(self)
        dialog.exec()
    
    def show_typing_indicator(self):
        """Animation de frappe"""
        pass

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = JymieIA()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
