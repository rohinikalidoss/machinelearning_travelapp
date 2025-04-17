import torch
import torch.nn as nn
import numpy as np
import requests
import json
from collections import Counter

# ---------------- MAPPINGS ----------------
month_map = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
}
season_map = {"Winter": 1, "Spring": 2, "Summer": 3, "Monsoon": 4, "Autumn": 5}
activity_map = {"Adventure": 1, "Relaxation": 2, "Sightseeing": 3, "Eco Tourism": 4}
budget_map = {"Low": 1, "Medium": 2, "High": 3}

# ---------------- MODEL ----------------
class TravelRecommender(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.fc1 = nn.Linear(5, 10)
        self.fc2 = nn.Linear(10, num_classes)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        return torch.softmax(self.fc2(x), dim=1)

# ---------------- DATA HELPERS ----------------
def balance_dataset(data):
    place_counts = Counter(d.get("Suggested_Place") for d in data if "Suggested_Place" in d)
    min_occurrences = min(place_counts.values(), default=0)
    balanced_data = []
    place_counter = {}

    for d in data:
        place = d.get("Suggested_Place")
        if place and place_counter.get(place, 0) < min_occurrences:
            balanced_data.append(d)
            place_counter[place] = place_counter.get(place, 0) + 1

    return balanced_data

def get_real_user_data():
    try:
        response = requests.get("http://127.0.0.1:5000/getUserData", timeout=60)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.RequestException as e:
        print(f"❌ Error fetching user data: {e}")
        return []

def get_weather_from_api():
    try:
        location_data = requests.get("https://ipinfo.io/json").json()
        city = location_data.get("city", "Chennai")

        print(f"📍 Detected City: {city}")

        # ✅ YOUR ACTIVE API KEY BELOW
        api_key = "81ba64561f8aa96605e3eead04b0b1e6"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

        response = requests.get(url, timeout=10)
        data = response.json()

        print("📦 Weather API Response:", json.dumps(data, indent=2))

        if response.status_code != 200 or "main" not in data:
            raise Exception(data.get("message", "Weather data not available."))

        temperature = data["main"]["temp"]
        weather = data["weather"][0]["main"]

        return temperature, weather
    except Exception as e:
        print(f"⚠️ Error fetching live weather: {e}")
        return 25, "Unknown"

# ---------------- TRAINING ----------------
def train_model(user_data_list):
    if not user_data_list:
        print("⚠️ No user data found! Training aborted.")
        return

    unique_places = sorted(set(user.get("Suggested_Place") for user in user_data_list if user.get("Suggested_Place")))
    place_map = {place: idx for idx, place in enumerate(unique_places)}

    with open("place_map.json", "w") as f:
        json.dump(place_map, f)

    model = TravelRecommender(num_classes=len(place_map))
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    user_data_list = balance_dataset(user_data_list)

    for user in user_data_list:
        features = torch.tensor([
            month_map.get(user.get("Month"), 0),
            budget_map.get(user.get("Budget"), 0),
            user.get("Temperature", 0),
            season_map.get(user.get("Season"), 0),
            activity_map.get(user.get("Activity_Preference"), 0)
        ], dtype=torch.float32).unsqueeze(0)

        label = place_map.get(user.get("Suggested_Place"), 0)
        target = torch.tensor([label], dtype=torch.long)

        optimizer.zero_grad()
        loss = criterion(model(features), target)
        loss.backward()
        optimizer.step()

    torch.save(model.state_dict(), "travel_model.pth")
    print("✅ Model training complete and saved as travel_model.pth")

# ---------------- PREDICTION ----------------
def get_recommendations(user_data):
    try:
        with open("place_map.json", "r") as f:
            place_map = json.load(f)
    except FileNotFoundError:
        print("❌ place_map.json not found. Train the model first.")
        return {"suggested_places": []}

    model = TravelRecommender(num_classes=len(place_map))
    model.load_state_dict(torch.load("travel_model.pth"))
    model.eval()

    features = torch.tensor([
        month_map.get(user_data.get("Month"), 0),
        budget_map.get(user_data.get("Budget"), 0),
        user_data.get("Temperature", 0),
        season_map.get(user_data.get("Season"), 0),
        activity_map.get(user_data.get("Activity_Preference"), 0)
    ], dtype=torch.float32).unsqueeze(0)
    probs = model(features).detach().numpy()[0]
    top_indices = np.argsort(probs)[-3:][::-1]
    predicted_places = [list(place_map.keys())[i] for i in top_indices]
    return {"suggested_places": predicted_places}
def get_user_input():
    def get_valid_input(prompt, valid_map):
        while True:
            val = input(prompt).strip().title()
            if val in valid_map:
                return val
            print("❌ Invalid input! Try again.")
    month = get_valid_input("Enter Month (e.g., March): ", month_map)
    season = get_valid_input("Enter Season (Winter, Spring, Summer, Monsoon, Autumn): ", season_map)
    budget = get_valid_input("Enter Budget (Low, Medium, High): ", budget_map)
    activity = get_valid_input("Enter Activity Preference (Adventure, Relaxation, Sightseeing, Eco Tourism): ", activity_map)
    try:
        group_size = int(input("Enter Group Size (e.g., 2, 4, 6, etc.): ").strip())
    except ValueError:
        print("⚠️ Invalid group size! Using default = 2")
        group_size = 2
    return {
        "Month": month,
        "Season": season,
        "Budget": budget,
        "Activity_Preference": activity,
        "Group_Size": group_size
    }
def add_data_to_db(user_data):
    try:
        response = requests.post("http://127.0.0.1:5000/addUserData", json=user_data, timeout=60)
        response.raise_for_status()
        print("✅ User data successfully added to database!")
    except requests.RequestException as e:
        print(f"❌ Error adding user data: {e}")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    user_data = get_user_input()
    temp, weather = get_weather_from_api()
    user_data["Temperature"] = temp
    user_data["Weather"] = weather
    print(f"\n🌡️ Live Temperature: {temp}°C")
    print(f"☁️ Live Weather: {weather}")
    add_data_to_db(user_data)
    all_user_data = get_real_user_data()
    train_model(all_user_data)
    print("\n🔮 Predicting top travel destinations...")
    prediction = get_recommendations(user_data)
    print("\n🏖️ Suggested Travel Destinations:")
    for place in prediction["suggested_places"]:
        print(f" → {place}")
