import tkinter as tk
from tkinter import simpledialog, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# ---------- 1. Fenêtres d'entrée ----------
root = tk.Tk()
root.withdraw()

try:
    dev_fonctionnelle = simpledialog.askstring(
        "Devise fonctionnelle", "Code ISO (ex. EUR) :")
    dev_risque = simpledialog.askstring(
        "Devise risque", "Code ISO (ex. USD) :")
    spot_live = float(simpledialog.askstring(
        "Spot", f"Taux {dev_fonctionnelle}/{dev_risque} actuel :"))
    strike_fwd = float(simpledialog.askstring(
        "Strike du forward", "Strike contractuel :"))
    notional = float(simpledialog.askstring(
        "Notional", f"Montant couvert en {dev_risque} :"))
    
    sens_couv = simpledialog.askstring(
        "Sens de la couverture",
        "Long (acheteur) ou Short (vendeur) ? [L/S] :")
    if sens_couv is None or sens_couv.upper() not in {"L", "S"}:
        raise ValueError("Sens de couverture non reconnu (L ou S attendu).")
    direction = 1 if sens_couv.upper() == "L" else -1
    
    pips_step = int(simpledialog.askstring(
        "Pas de sensibilité",
        "Nombre de pips par pas (1, 10, 100, 1000) :"))
    borne_min_str = simpledialog.askstring(
        "Borne MIN",
        "Borne basse du spot (ex. 1.05 ou 5% pour -5 % du spot) :")
    borne_max_str = simpledialog.askstring(
        "Borne MAX",
        "Borne haute du spot (ex. 1.15 ou 5% pour +5 % du spot) :")
except (TypeError, ValueError) as e:
    messagebox.showerror("Erreur", f"Entrée invalide : {e}")
    root.destroy()
    raise SystemExit()

# ---------- 2. Interprétation des bornes ----------
def parse_borne(value_str: str, spot_ref: float, sens: int) -> float:
    """Convertit une borne utilisateur en niveau de spot float."""
    value_str = value_str.strip()
    if value_str.endswith("%"):
        pct = float(value_str.rstrip("%")) / 100.0
        return spot_ref * (1 + sens * pct)
    return float(value_str)

borne_min = parse_borne(borne_min_str, spot_live, -1)
borne_max = parse_borne(borne_max_str, spot_live, +1)

if borne_min >= borne_max:
    messagebox.showerror("Erreur", "Borne min ≥ borne max.")
    root.destroy()
    raise SystemExit()

# ---------- 3. Grille de scénarios ----------
step = pips_step * 1e-4
n_steps = int(round((borne_max - borne_min) / step)) + 1
spots = np.linspace(borne_min, borne_max, n_steps)
delta_spot = spots - spot_live

# ---------- 4. Calcul du P&L (sens inclus) ----------
pnl = direction * (spots - strike_fwd) * notional  # devise fonctionnelle

# ---------- 5. DataFrame & affichage console ----------
df = pd.DataFrame({
    f"Spot {dev_fonctionnelle}/{dev_risque}": np.round(spots, 6),
    "Δ Spot": np.round(delta_spot, 6),
    f"P&L ({dev_fonctionnelle})": np.round(pnl, 2)
})

print("\n==== MATRICE DE SENSIBILITÉ ====\n")
print(df.to_string(index=False))

# ---------- 6. Graphique ----------
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(spots, pnl, marker='o')
ax.axhline(0, linewidth=0.8, linestyle='--')
ax.set_title(f"Sensibilité Forward {dev_fonctionnelle}/{dev_risque} "
             f"({'Long' if direction==1 else 'Short'})")
ax.set_xlabel(f"Spot {dev_fonctionnelle}/{dev_risque}")
ax.set_ylabel(f"P&L ({dev_fonctionnelle})")
ax.grid(True)
plt.tight_layout()
plt.show()

# ---------- 7. Export CSV ----------
if messagebox.askyesno("Export CSV", "Souhaitez-vous exporter la matrice en CSV ?"):
    filename = simpledialog.askstring(
        "Nom du fichier", "Chemin/nom du fichier (ex. sensi_fx.csv) :")
    if filename:
        df.to_csv(filename, index=False)
        messagebox.showinfo("Export OK", f"CSV enregistré : {os.path.abspath(filename)}")

# ---------- 8. Export graphique ----------
if messagebox.askyesno("Export PNG", "Souhaitez-vous enregistrer le graphique ?"):
    png_name = simpledialog.askstring(
        "Nom du fichier PNG", "Chemin/nom du fichier (ex. sensi_fx.png) :")
    if png_name:
        fig.savefig(png_name, dpi=150)
        messagebox.showinfo("Export OK", f"PNG enregistré : {os.path.abspath(png_name)}")

root.destroy()
