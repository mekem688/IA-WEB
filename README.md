import os
import json
import requests
from dotenv import load_dotenv
import customtkinter as ctk
from tkinter import END
from rapidfuzz import fuzz

# Charger la clé API
load_dotenv()
api_key = os.getenv("TOGETHER_AI_API_KEY")

if not api_key:
    raise ValueError("❌ Clé API non trouvée. Vérifie ton fichier .env.")

# Dossier et fichier
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

# === Utilisation de requests pour l'API Together ===
def repondre(question_utilisateur: str) -> str:
    question = question_utilisateur.lower().strip()
    question_similaire = question_deja_connue(question, connaissances_locales)
    if question_similaire:
        return f"🤖 (réponse locale) {connaissances_locales[question_similaire]}"

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "messages": [
                {"role": "system", "content": "Tu es un assistant intelligent qui répond toujours en français."},
                {"role": "user", "content": question_utilisateur}
            ],
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 512
        }

        response = requests.post("https://api.together.ai/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        reponse_ia = response.json()["choices"][0]["message"]["content"]

        connaissances_locales[question] = reponse_ia
        sauvegarder_base(connaissances_locales)
        return f"🤖 JYMIE : {reponse_ia}"

    except Exception as e:
        return f"❌ Erreur : {e}"

# === Interface graphique avec customtkinter ===

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Jymie IA - Assistant intelligent CM")
app.geometry("800x650")

titre_label = ctk.CTkLabel(app, text="🤖 Jymie IA", font=ctk.CTkFont(size=24, weight="bold"))
titre_label.pack(pady=10)

zone_texte = ctk.CTkTextbox(app, width=750, height=400, corner_radius=8, font=("Consolas", 13))
zone_texte.pack(padx=20, pady=10)
zone_texte.insert(END, "Bienvenue, je suis Jymie IA. Pose-moi une question !\n\n")
zone_texte.configure(state="disabled")

champ_question = ctk.CTkEntry(app, width=650, font=("Arial", 13))
champ_question.pack(padx=10, pady=10, side="left")

def envoyer_question():
    question = champ_question.get()
    if question.strip() == "":
        return
    champ_question.delete(0, END)
    reponse = repondre(question)

    zone_texte.configure(state="normal")
    zone_texte.insert(END, f"👤 Vous : {question}\n{reponse}\n\n")
    zone_texte.configure(state="disabled")
    zone_texte.see(END)

btn_envoyer = ctk.CTkButton(app, text="Envoyer", command=envoyer_question)
btn_envoyer.pack(pady=10, side="left")

champ_question.bind("<Return>", lambda event: envoyer_question())
parametres_fenetre = None

def afficher_parametres():
    global parametres_fenetre
    if parametres_fenetre is not None and parametres_fenetre.winfo_exists():
        parametres_fenetre.lift()
        parametres_fenetre.focus_force()
        return

    parametres_fenetre = ctk.CTkToplevel(app)
    parametres_fenetre.title("Paramètres de Jymie IA")
    parametres_fenetre.geometry("400x300")
    parametres_fenetre.resizable(False, False)

    ctk.CTkLabel(parametres_fenetre, text="Mode d'apparence :", font=ctk.CTkFont(size=14)).pack(pady=(20, 5))

    def changer_mode_appearance(mode):
        ctk.set_appearance_mode(mode)

    mode_appearance_menu = ctk.CTkOptionMenu(
        parametres_fenetre,
        values=["light", "dark", "system"],
        command=changer_mode_appearance
    )
    mode_appearance_menu.pack(pady=(0, 20))

    ctk.CTkLabel(parametres_fenetre, text="Thème de couleur :", font=ctk.CTkFont(size=14)).pack(pady=(10, 5))

    def changer_theme_couleur(theme):
        ctk.set_default_color_theme(theme)

    theme_couleur_menu = ctk.CTkOptionMenu(
        parametres_fenetre,
        values=["blue", "green", "dark-blue"],
        command=changer_theme_couleur
    )
    theme_couleur_menu.pack(pady=5)

btn_parametres = ctk.CTkButton(app, text="⚙️ Paramètres", command=afficher_parametres)
btn_parametres.pack(pady=(5, 10))

# Lancer l'application
app.mainloop()
