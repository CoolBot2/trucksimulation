
#NOTE: 75% ai generated code for speed purposes

import math
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# -----------------------------
# SCENARIO PARAMETERS
# -----------------------------
farms = [
    {"name": "Farm A", "distance": 10, "tons": 121},
    {"name": "Farm B", "distance": 25, "tons": 47},
    {"name": "Farm C", "distance": 15, "tons": 91},
]

NUM_TRUCKS = 5                 # number of trucks (lanes in the animation)
TASK_CHUNK_TONS = 10           # demand chunk size (tons) per task
ROUTE_CAPACITY_TONS = 30       # truck capacity per route (can visit several farms)
STEP_DISTANCE = 0.5            # km per animation step
LOADING_STEPS = 8              # frames waiting at farm (loading)
UNLOADING_STEPS = 8            # frames waiting at mill (unloading)

random.seed(0)

# --------------------------------------------------------
# 1) BUILD CVRP TASKS (10-ton chunks at each farm)
# --------------------------------------------------------
tasks = []
for f in farms:
    remaining = f["tons"]
    while remaining > 0:
        load = min(TASK_CHUNK_TONS, remaining)
        tasks.append({
            "name": f["name"],
            "distance": f["distance"],
            "demand": load
        })
        remaining -= load

print("Number of tasks (10-ton chunks):", len(tasks))

# --------------------------------------------------------
# 2) SIMPLE GREEDY CVRP HEURISTIC -> BUILD ROUTES
#    Each route: mill (0) -> several farms -> mill
# --------------------------------------------------------
unused_tasks = tasks.copy()
routes = []   # list of routes; each route is a list of tasks (in visiting order)

while unused_tasks:
    cap_rem = ROUTE_CAPACITY_TONS
    pos = 0.0
    tour = []

    while True:
        # tasks that fit into remaining capacity
        candidates = [t for t in unused_tasks if t["demand"] <= cap_rem]
        if not candidates:
            break

        # choose nearest candidate to current position
        next_task = min(candidates, key=lambda t: abs(t["distance"] - pos))
        tour.append(next_task)
        cap_rem -= next_task["demand"]
        pos = next_task["distance"]
        unused_tasks.remove(next_task)

    routes.append(tour)

print("\nPlanned routes (CVRP greedy heuristic):")
for i, tour in enumerate(routes, start=1):
    seq = "mill"
    for t in tour:
        seq += f" -> {t['name']}"
    seq += " -> mill"
    print(f"Route {i}: {seq}")

# --------------------------------------------------------
# 3) ASSIGN ROUTES TO TRUCKS (ROUND-ROBIN)
# --------------------------------------------------------
truck_routes = [[] for _ in range(NUM_TRUCKS)]
for idx, route in enumerate(routes):
    truck_id = idx % NUM_TRUCKS
    truck_routes[truck_id].append(route)

# --------------------------------------------------------
# 4) BUILD POSITION & CAPACITY PATHS + FARM EVENTS
# --------------------------------------------------------
def build_path_and_capacity_for_truck(route_list,
                                      step_distance=STEP_DISTANCE,
                                      loading_steps=LOADING_STEPS,
                                      unloading_steps=UNLOADING_STEPS):
    """
    For a given list of routes, build:
      - positions over time
      - remaining capacity over time
      - a list of events: (frame_index, farm_name, demand_loaded)
    The truck starts each route at the mill with full capacity.
    """
    positions = []
    capacities = []
    events = []  # list of (frame_index, farm_name, demand)

    for tour in route_list:
        pos = 0.0
        cap = ROUTE_CAPACITY_TONS

        # initial point at mill
        positions.append(pos)
        capacities.append(cap)

        # visit each task in the tour
        for task in tour:
            target = task["distance"]

            # move from current pos to farm
            distance = target - pos
            steps = max(1, int(abs(distance) / step_distance))
            xs = np.linspace(pos, target, steps, endpoint=False)
            for x in xs:
                positions.append(x)
                capacities.append(cap)
            pos = target

            # loading at farm: capacity decreases
            start_load_idx = len(positions)  # first loading frame index
            cap -= task["demand"]
            for _ in range(loading_steps):
                positions.append(pos)
                capacities.append(cap)

            # record event: at start_load_idx farm demand is reduced
            events.append((start_load_idx, task["name"], task["demand"]))

        # return to mill
        distance = 0.0 - pos
        steps = max(1, int(abs(distance) / step_distance))
        xs = np.linspace(pos, 0.0, steps)
        for x in xs:
            positions.append(x)
            capacities.append(cap)
        pos = 0.0

        # unloading at mill
        for _ in range(unloading_steps):
            positions.append(pos)
            capacities.append(cap)

        # after unloading, reset capacity to full for next route
        positions.append(pos)
        capacities.append(ROUTE_CAPACITY_TONS)

    # if no routes, keep truck at mill with full capacity
    if not positions:
        positions = [0.0]
        capacities = [ROUTE_CAPACITY_TONS]

    return np.array(positions), np.array(capacities), events


truck_paths = []
truck_caps = []
all_events = []  # collect events from all trucks

for route_list in truck_routes:
    p, c, e = build_path_and_capacity_for_truck(route_list)
    truck_paths.append(p)
    truck_caps.append(c)
    all_events.extend(e)

max_len = max(len(p) for p in truck_paths)
max_dist = max(f["distance"] for f in farms)

print("\nMax animation steps:", max_len)

# --------------------------------------------------------
# 5) PRECOMPUTE REMAINING TONS AT EACH FARM OVER TIME
# --------------------------------------------------------
farm_index = {f["name"]: i for i, f in enumerate(farms)}
num_farms = len(farms)
farm_totals = [f["tons"] for f in farms]

# initialize remaining tons: start with full demand everywhere
farm_remaining = [[farm_totals[i]] * max_len for i in range(num_farms)]

# for each loading event, subtract demand from that farm at all later frames
for frame_idx, farm_name, demand in all_events:
    fi = farm_index[farm_name]
    for t in range(frame_idx, max_len):
        farm_remaining[fi][t] -= demand
        if farm_remaining[fi][t] < 0:
            farm_remaining[fi][t] = 0  # just in case

farm_remaining = np.array(farm_remaining)  # shape: (num_farms, max_len)

# --------------------------------------------------------
# 6) PLOT SETUP
# --------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 4))

# road
ax.hlines(0, 0, max_dist, linestyle="--")
ax.set_xlim(-1, max_dist + 1)
ax.set_ylim(-1, NUM_TRUCKS)
ax.set_yticks([])

# mill marker
ax.vlines(0, -0.2, NUM_TRUCKS - 0.5, linestyle=":")
ax.text(0, NUM_TRUCKS - 0.3, "mill", ha="center", fontsize=8)

# farm markers on the road
for f in farms:
    ax.vlines(f["distance"], -0.2, NUM_TRUCKS - 0.5, linestyle=":")
    ax.text(f["distance"], NUM_TRUCKS - 0.3, f["name"], ha="center", fontsize=8)

ax.set_xlabel("DISTANCE FROM MILL (km)")
ax.set_title("CVRP-style simulation: trucks, capacities, and remaining farm demand")

# truck markers + capacity labels
truck_markers = []
truck_labels = []
colors = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]

for i in range(NUM_TRUCKS):
    (marker,) = ax.plot([], [], "s", markersize=10,
                        label=f"Truck {i+1}",
                        color=colors[i % len(colors)])
    truck_markers.append(marker)
    # capacity label above the truck
    label = ax.text(0, i + 0.1, "", fontsize=7, ha="center", va="bottom")
    truck_labels.append(label)

time_text = ax.text(0.02, 0.9, "", transform=ax.transAxes, fontsize=9)

# farm remaining text block (option B: grouped on the side)
farm_texts = []
for i, f in enumerate(farms):
    txt = ax.text(0.65, 0.9 - 0.08 * i,
                  "",
                  transform=ax.transAxes,
                  fontsize=8,
                  ha="left",
                  va="center")
    farm_texts.append(txt)

ax.legend(loc="lower right", fontsize=8)

# --------------------------------------------------------
# 7) ANIMATION
# --------------------------------------------------------
def init():
    for i in range(NUM_TRUCKS):
        truck_markers[i].set_data([], [])
        truck_labels[i].set_text("")
    for txt in farm_texts:
        txt.set_text("")
    time_text.set_text("")
    return truck_markers + truck_labels + farm_texts + [time_text]

def update(frame):
    step = frame

    # update trucks (position + remaining capacity)
    for i in range(NUM_TRUCKS):
        path = truck_paths[i]
        caps = truck_caps[i]
        idx = min(step, len(path) - 1)
        x = path[idx]
        y = i

        truck_markers[i].set_data([x], [y])
        truck_labels[i].set_position((x, y + 0.1))
        truck_labels[i].set_text(f"{caps[idx]:.0f}t")

    # update remaining tons at farms
    for fi, f in enumerate(farms):
        rem = farm_remaining[fi][min(step, max_len - 1)]
        farm_texts[fi].set_text(f"{f['name']}: {rem:.0f}t left")

    time_text.set_text(f"step: {step}")
    return truck_markers + truck_labels + farm_texts + [time_text]

ani = FuncAnimation(
    fig,
    update,
    frames=max_len,
    init_func=init,
    interval=80,
    blit=True
)

plt.tight_layout()
plt.show()
