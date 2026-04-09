from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# =======================
#  Firebase push config
# =======================
FCM_SERVER_KEY = "308210805779"
TOKENS = []

# =======================
# OpenWeather config
# =======================
API_KEY = "f4e716af3321dcdd1242d7218277447a"
CITY = "Kraśnik,PL"

# =======================
#  Pola
# =======================
CROPS = {
    "maliny": {"area": 0.08},      # 8 arów
    "porzeczka": {"area": 0.28}    # 28 arów
}

# =======================
# Pełny cykl zabiegów
# =======================
TASK_TEMPLATES = [
    # Wiosna
    {"name": "Cięcie sanitarne", "type": "mechaniczne", "month": 3},

    # Choroby grzybowe
    {"name": "Ochrona przed mączniakiem", "type": "fungicyd", "month": 4, "min_temp": 10},
    {"name": "Ochrona przed szarą pleśnią", "type": "fungicyd", "month": 5, "humidity": 70},

    # Szkodniki
    {"name": "Zwalczanie mszyc", "type": "insektycyd", "month": 5, "min_temp": 12},
    {"name": "Zwalczanie przędziorków", "type": "akaracyd", "month": 6, "min_temp": 18},

    # Nawożenie
    {"name": "Nawożenie azotowe", "type": "nawóz", "month": 4, "dose_per_ha": 100},
    {"name": "Nawożenie potasowe", "type": "nawóz", "month": 6, "dose_per_ha": 80},

    # Jesień
    {"name": "Oprysk po zbiorach", "type": "fungicyd", "month": 9}
]

# =======================
# Pobieranie pogody
# =======================
def get_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
    try:
        res = requests.get(url).json()
        return {"temp": res["main"]["temp"], "humidity": res["main"]["humidity"]}
    except:
        # fallback w przypadku problemów z API
        return {"temp": 20, "humidity": 50}

# =======================
# Generowanie zadań
# =======================
def generate_tasks():
    today = datetime.today()
    weather = get_weather()
    result = []

    for crop, data in CROPS.items():
        for t in TASK_TEMPLATES:
            if t["month"] != today.month:
                continue

            # warunki pogodowe
            if "min_temp" in t and weather["temp"] < t["min_temp"]:
                continue
            if "humidity" in t and weather["humidity"] < t["humidity"]:
                continue

            dose = 0
            if "dose_per_ha" in t:
                dose = t["dose_per_ha"] * data["area"]

            result.append({
                "crop": crop,
                "name": t["name"],
                "type": t["type"],
                "date": today.strftime("%Y-%m-%d"),
                "dose": round(dose, 2)
            })
    return result

# =======================
# Push notification
# =======================
def send_push(title, body):
    url = "https://fcm.googleapis.com/fcm/send"
    headers = {
        "Authorization": f"key={FCM_SERVER_KEY}",
        "Content-Type": "application/json"
    }
    for token in TOKENS:
        data = {"to": token, "notification": {"title": title, "body": body}}
        try:
            requests.post(url, json=data, headers=headers)
        except:
            pass

# =======================
# Sprawdzanie przypomnień
# =======================
def check_tasks():
    tasks = generate_tasks()
    today = datetime.today().date()
    for t in tasks:
        d = datetime.strptime(t["date"], "%Y-%m-%d").date()

        # przypomnienie tydzień wcześniej
        if today == d - timedelta(days=7):
            send_push("Za tydzień zabieg!", f"{t['name']} ({t['crop']})")

        # przypomnienie w dniu
        if today == d:
            send_push("DZIŚ zabieg!", f"{t['name']} ({t['crop']})")

# =======================
# Flask routes
# =======================
@app.route("/")
def home():
    tasks = generate_tasks()
    weather = get_weather()
    return render_template("index.html", tasks=tasks, weather=weather)

@app.route("/save-token", methods=["POST"])
def save_token():
    token = request.json.get("token")
    if token and token not in TOKENS:
        TOKENS.append(token)
    return jsonify({"status": "ok"})

@app.route("/send-test")
def test_push():
    send_push("Test Push", "Powiadomienie Testowe Działa!")
    return "Push wysłany!"

# =======================
# Uruchamianie APScheduler dla przypomnień
# =======================

scheduler = BackgroundScheduler()
scheduler.add_job(check_tasks, 'interval', hours=1)  # sprawdza co godzinę
scheduler.start()

# =======================
# Uruchomienie serwera
# =======================
if __name__ == "__main__":
    app.run(debug=True)