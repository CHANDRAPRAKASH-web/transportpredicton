
import random
import pandas as pd

modes = ["road", "rail", "air", "water"]
data = []

for _ in range(1000):
    weight = random.randint(1, 1000)
    volume = random.randint(1, 500)
    distance = random.randint(10, 5000)
    priority = random.randint(1, 5)

    road = random.choice([0, 1])
    rail = random.choice([0, 1])
    air = random.choice([0, 1])
    water = random.choice([0, 1])

    # Simple rule-based label for dataset
    if air and distance > 1000 and priority >= 4:
        mode = "air"
    elif rail and 200 < distance < 2000:
        mode = "rail"
    elif water and distance > 500 and volume > 200:
        mode = "water"
    else:
        mode = "road"

    data.append([weight, volume, distance, priority, road, rail, air, water, mode])

df = pd.DataFrame(data, columns=["weight", "volume", "distance", "priority",
                                 "road_available", "rail_available", "air_available", "water_available", "mode"])
df.to_csv("synthetic_train_data.csv", index=False)
print("✅ Synthetic dataset created: synthetic_train_data.csv")