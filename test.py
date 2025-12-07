import math
import random
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# -----------------------------
# PARAMETER DES SZENARIOS
# -----------------------------
# Höfe mit Entfernung zur Mühle (km) und Tagesmenge (Tonnen)
farms = [
    {"name": "Farm A", "distance": 10, "tons": 20},
    {"name": "Farm B", "distance": 25, "tons": 60},
    {"name": "Farm C", "distance": 15, "tons": 18},
]

TRUCK_CAPACITY_TONS = 10      # LKW-Kapazität pro Fahrt (Tonnen)
NUM_TRUCKS = 5               # Anzahl LKWs
STEP_DISTANCE = 0.5           # zurückgelegte Strecke pro Animationsschritt (km)

random.seed(0)

# --------------------------------------------------------
# 1) TRIP-LISTE AUFBAUEN (WELCHE FAHRTEN SIND NÖTIG?)
# --------------------------------------------------------
trips_queue = []
for f in farms:
    n_trips = math.ceil(f["tons"] / TRUCK_CAPACITY_TONS)
    for _ in range(n_trips):
        trips_queue.append(f)
def trip_score(farm):
    distance = farm["distance"]
    tons = farm["tons"]
    return 0.7 * distance + 0.1 * tons  # Beispiel
# STRATEGIE: ITS = zuerst nähere Höfe
trips_queue.sort(key=trip_score)   # einfache Optimierung

print("NEEDED FARMS:", len(trips_queue))

# --------------------------------------------------------
# 2) LKW-ZUSTÄNDE INITIALISIEREN
# --------------------------------------------------------
trucks = []
for i in range(NUM_TRUCKS):
    trucks.append({
        "x": 0.0,          # aktuelle Position (km)
        "state": "idle",   # idle / to_farm / to_mill / loading / unloading
        "farm": None,
        "pause_steps": 0   # für Lade-/Entladezeit
    })

# Anzahl Schritte für Laden/Entladen (nur visuelle Pausen)
LOADING_STEPS = 10
UNLOADING_STEPS = 8

max_dist = max(f["distance"] for f in farms)

# --------------------------------------------------------
# 3) FIGUR VORBEREITEN
# --------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 4))

ax.hlines(0, 0, max_dist, linestyle="--")
ax.set_xlim(-1, max_dist + 1)
ax.set_ylim(-1, NUM_TRUCKS)
ax.set_yticks([])
ax.vlines(0, -0.2, NUM_TRUCKS - 0.5, linestyle=":")
ax.text(0, NUM_TRUCKS - 0.3, "mill", ha="center", fontsize=8)
# Höfe markieren
for f in farms:
    ax.vlines(f["distance"], -0.2, NUM_TRUCKS - 0.5, linestyle=":")
    ax.text(f["distance"], NUM_TRUCKS - 0.3, f["name"], ha="center", fontsize=8)

ax.set_xlabel("DISTANCE FROM MILL (km)")
ax.set_title("Simulation: MANY TRUCKS TRANSPORT TO MILL")

# LKW-Marker
truck_markers = []
colors = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]
for i in range(NUM_TRUCKS):
    (marker,) = ax.plot([], [], "s", markersize=10, label=f"LKW {i+1}", color=colors[i % len(colors)])
    truck_markers.append(marker)

time_text = ax.text(0.02, 0.9, "", transform=ax.transAxes, fontsize=9)
ax.legend(loc="lower right", fontsize=8)

# --------------------------------------------------------
# 4) UPDATE-FUNKTION FÜR DIE ANIMATION
# --------------------------------------------------------
step_counter = 0  # globale "Zeit" in Schritten

def assign_new_trip(truck):
    """Weist einem freien LKW die nächste Fahrt zu (falls vorhanden)."""
    if trips_queue:
        farm = trips_queue.pop(0)
        truck["farm"] = farm
        truck["state"] = "to_farm"
        truck["pause_steps"] = 0
        # Start immer an der Mühle
        truck["x"] = 0.0

def update(frame):
    global step_counter
    step_counter += 1

    # Jeden LKW updaten
    for i, truck in enumerate(trucks):
        # Wenn LKW nichts zu tun hat, neue Fahrt holen
        if truck["state"] == "idle":
            assign_new_trip(truck)

        # Lade-/Entladepausen
        elif truck["state"] in ("loading", "unloading"):
            if truck["pause_steps"] > 0:
                truck["pause_steps"] -= 1
            else:
                if truck["state"] == "loading":
                    truck["state"] = "to_mill"
                elif truck["state"] == "unloading":
                    truck["state"] = "idle"
            # Position bleibt während Pause gleich

        # Fahrt zum Hof
        elif truck["state"] == "to_farm":
            dist = truck["farm"]["distance"]
            truck["x"] += STEP_DISTANCE
            if truck["x"] >= dist:
                truck["x"] = dist
                truck["state"] = "loading"
                truck["pause_steps"] = LOADING_STEPS

        # Fahrt zurück zur Mühle
        elif truck["state"] == "to_mill":
            truck["x"] -= STEP_DISTANCE
            if truck["x"] <= 0:
                truck["x"] = 0
                truck["state"] = "unloading"
                truck["pause_steps"] = UNLOADING_STEPS

        # Marker-Position setzen (LKW i bekommt "Spur" i)
        truck_markers[i].set_data([truck["x"]], [i])

    # Text aktualisieren
    time_text.set_text(f"step: {step_counter}")

    return truck_markers + [time_text]

# Maximale Anzahl Schritte (einfach groß genug wählen)
max_frames = 800

ani = FuncAnimation(
    fig,
    update,
    frames=max_frames,
    interval=80,   # ms zwischen Frames
    blit=True
)

plt.tight_layout()
plt.show()