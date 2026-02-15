import tkinter as tk
from tkinter import ttk
import requests
import threading
from datetime import datetime

# ==== Мультимовна система ====
LANGUAGES = {
    "ua": {
        "title": "🌤 Прогноз погоди",
        "search": "Пошук",
        "loading": "Завантаження...",
        "error": "❌ Не вдалося завантажити дані.",
        "city_not_found": "❌ Місто не знайдено. Перевірте правильність назви.",
        "feels_like": "Відчувається як",
        "humidity": "Вологість",
        "wind_speed": "Вітер",
        "placeholder": "Введіть місто (наприклад: Київ)",
        "hourly_forecast": "📅 Прогноз на сьогодні (щогодинно)",
        "multi_day_forecast": "🗓 Прогноз на кілька днів",
        "warnings_title": "⚠️ Погодні попередження:",
        "recommendations_title": "💡 Рекомендації:"
    },
    "en": {
        "title": "🌤 Weather Forecast",
        "search": "Search",
        "loading": "Loading...",
        "error": "❌ Failed to load data.",
        "city_not_found": "❌ City not found. Please check the spelling.",
        "feels_like": "Feels like",
        "humidity": "Humidity",
        "wind_speed": "Wind speed",
        "placeholder": "Enter city (e.g.: Kyiv)",
        "hourly_forecast": "📅 Today's forecast (every 3h)",
        "multi_day_forecast": "🗓 Multi-day forecast",
        "warnings_title": "⚠️ Weather warnings:",
        "recommendations_title": "💡 Recommendations:"
    }
}

CURRENT_LANG = "ua"
URL_TEMPLATE = "https://wttr.in/{city}?format=j1"

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title(LANGUAGES[CURRENT_LANG]["title"])
        self.root.geometry("800x900")
        self.root.configure(bg="#f5f9ff")
        self.bg_color = "#f5f9ff"
        self.card_bg = "#ffffff"

        # ======= Fullscreen =======
        self.is_fullscreen = True
        self.root.attributes("-fullscreen", True)
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)

        self.lang = CURRENT_LANG
        self.translations = LANGUAGES[self.lang]

        # ======= Стиль =======
        self.style = ttk.Style()
        self.setup_styles()

        # ======= Інтерфейс =======
        self.create_widgets()
        self.load_weather()

    # ======= Fullscreen =======
    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)

    def exit_fullscreen(self, event=None):
        self.is_fullscreen = False
        self.root.attributes("-fullscreen", False)

    # ======= Стиль =======
    def setup_styles(self):
        self.style.configure("TButton", font=("Segoe UI", 12), padding=6, relief="flat", background="#4dd0e1")
        self.style.map("TButton", background=[('active', '#00acc1')])
        self.style.configure("TEntry", padding=6, font=("Segoe UI", 12))

    # ======= Інтерфейс =======
    def create_widgets(self):
        # ==== Верхнє меню мов ====
        lang_frame = tk.Frame(self.root, bg=self.bg_color)
        lang_frame.pack(pady=10)

        self.ua_label = tk.Label(lang_frame, text="🇺🇦", font=("Arial", 16), bg=self.bg_color, cursor="hand2")
        self.ua_label.pack(side="left", padx=5)
        self.ua_label.bind("<Button-1>", lambda e: self.change_language("ua"))

        self.en_label = tk.Label(lang_frame, text="🇬🇧", font=("Arial", 16), bg=self.bg_color, cursor="hand2")
        self.en_label.pack(side="left", padx=5)
        self.en_label.bind("<Button-1>", lambda e: self.change_language("en"))

        # ==== Заголовок ====
        self.title_label = tk.Label(self.root, text=self.translations["title"],
                                    font=("Segoe UI", 24, "bold"), bg=self.bg_color)
        self.title_label.pack(pady=10)

        # ==== Введення міста ====
        input_frame = tk.Frame(self.root, bg=self.bg_color)
        input_frame.pack(pady=10)

        self.city_entry = ttk.Entry(input_frame, width=30, font=("Segoe UI", 12))
        self.city_entry.insert(0, self.translations["placeholder"])
        self.city_entry.pack(side="left", padx=5)

        self.search_button = ttk.Button(input_frame, text=self.translations["search"],
                                        command=self.update_city, style="TButton")
        self.search_button.pack(side="left")

        self.city_entry.bind("<Return>", lambda e: self.update_city())

        # ==== Статус завантаження ====
        self.loading_label = tk.Label(self.root, text="", font=("Segoe UI", 14), bg=self.bg_color)
        self.loading_label.pack(pady=20)

        # ==== Контейнер з скролом ====
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg=self.bg_color)
        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.weather_frame = tk.Frame(self.canvas, bg=self.bg_color)
        self.canvas.create_window((0,0), window=self.weather_frame, anchor="nw")

        self.weather_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    # ======= Зміна мови =======
    def change_language(self, lang):
        self.lang = lang
        self.translations = LANGUAGES[lang]
        self.root.title(self.translations["title"])
        self.title_label.config(text=self.translations["title"])
        self.search_button.config(text=self.translations["search"])
        current_text = self.city_entry.get().strip()
        if current_text in [LANGUAGES["ua"]["placeholder"], LANGUAGES["en"]["placeholder"]]:
            self.city_entry.delete(0, tk.END)
            self.city_entry.insert(0, self.translations["placeholder"])
        self.display_weather()  # Оновлення

    # ======= Оновлення міста =======
    def update_city(self):
        city = self.city_entry.get().strip()
        placeholder = self.translations["placeholder"]
        if not city or city == placeholder:
            city = "Kyiv"

        # Показуємо завантаження
        self.loading_label.config(text=self.translations["loading"])
        self.loading_label.pack(pady=20)
        for widget in self.weather_frame.winfo_children():
            widget.destroy()

        def fetch():
            try:
                response = requests.get(URL_TEMPLATE.format(city=city))
                print(f"✅ Status code: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    self.root.after(0, self.display_weather, data)
                elif response.status_code == 404:
                    self.root.after(0, self.show_city_not_found)
                else:
                    self.root.after(0, self.show_error)
            except Exception as e:
                print(f"⚠️ Error loading data: {e}")
                self.root.after(0, self.show_error)

        threading.Thread(target=fetch).start()

    def show_error(self):
        self.loading_label.config(text=self.translations["error"])

    def show_city_not_found(self):
        self.loading_label.config(text=self.translations["city_not_found"])

    # ======= Відображення погоди =======
    def display_weather(self, data=None):
        self.loading_label.config(text="")
        self.loading_label.pack_forget()
        for widget in self.weather_frame.winfo_children():
            widget.destroy()

        if not data or "current_condition" not in data or "weather" not in data:
            self.show_error()
            return

        current = data["current_condition"][0]
        forecast_list = data["weather"]

        try:
            city_name = data["nearest_area"][0]["areaName"][0]["value"]
            country = data["nearest_area"][0]["country"][0]["value"]
            full_city_name = f"{city_name}, {country}"
        except:
            full_city_name = "Невідоме місто" if self.lang=="ua" else "Unknown city"

        temp = current.get("temp_C","N/A")
        feels_like = current.get("FeelsLikeC","N/A")
        humidity = current.get("humidity","N/A")
        wind_speed = current.get("windspeedKmph","N/A")
        description = current.get("weatherDesc",[{"value": "немає опису" if self.lang=="ua" else "no description"}])[0]["value"]

        # ==== Поточна погода ====
        info_card = tk.Frame(self.weather_frame, bg=self.card_bg, bd=2, relief="groove", padx=15, pady=15)
        info_card.pack(fill="x", pady=10)
        tk.Label(info_card, text=full_city_name, font=("Segoe UI", 20, "bold"), bg=self.card_bg).pack(anchor="w")
        tk.Label(info_card, text=f"{temp}°C", font=("Segoe UI", 36), bg=self.card_bg).pack(anchor="w")
        tk.Label(info_card, text=f"{self.translations['feels_like']}: {feels_like}°C", font=("Segoe UI", 12), bg=self.card_bg).pack(anchor="w")
        tk.Label(info_card, text=f"{self.translations['humidity']}: {humidity}%", font=("Segoe UI",12), bg=self.card_bg).pack(anchor="w")
        tk.Label(info_card, text=f"{self.translations['wind_speed']}: {wind_speed} km/h", font=("Segoe UI",12), bg=self.card_bg).pack(anchor="w")
        tk.Label(info_card, text=description.capitalize(), font=("Segoe UI",14), bg=self.card_bg).pack(anchor="w", pady=(10,0))

        # ==== Щогодинний прогноз ====
        hourly_card = tk.Frame(self.weather_frame, bg=self.card_bg, bd=2, relief="groove", padx=15, pady=10)
        hourly_card.pack(fill="x", pady=10)
        tk.Label(hourly_card, text=self.translations["hourly_forecast"], font=("Segoe UI",14,"bold"), bg=self.card_bg).pack(anchor="w", pady=(5,10))

        hourly_data = forecast_list[0].get("hourly", [])
        for hour_data in hourly_data[::4]:
            time_code = hour_data.get("time","0")
            hour = str(int(time_code)//100).zfill(2)+":00"
            temp_c = hour_data.get("tempC","N/A")
            desc = hour_data.get("weatherDesc",[{"value":"немає даних" if self.lang=="ua" else "no data"}])[0]["value"]
            line = tk.Frame(hourly_card, bg=self.card_bg)
            line.pack(fill="x", pady=2)
            tk.Label(line,text=hour,font=("Segoe UI",10), bg=self.card_bg).pack(side="left")
            tk.Label(line,text=f"{temp_c}°C", font=("Segoe UI",10), bg=self.card_bg).pack(side="left", padx=10)
            tk.Label(line,text=desc,font=("Segoe UI",10), bg=self.card_bg).pack(side="right")

        # ==== Прогноз на кілька днів ====
        forecast_card = tk.Frame(self.weather_frame, bg=self.card_bg, bd=2, relief="groove", padx=15, pady=10)
        forecast_card.pack(fill="x", pady=10)
        tk.Label(forecast_card, text=self.translations["multi_day_forecast"], font=("Segoe UI",14,"bold"), bg=self.card_bg).pack(anchor="w", pady=(5,10))

        for day in forecast_list[:5]:
            date_str = datetime.strptime(day["date"],"%Y-%m-%d").strftime("%a %d %b")
            temp_min = day.get("mintempC","N/A")
            temp_max = day.get("maxtempC","N/A")
            desc = day.get("hourly",[{}])[0].get("weatherDesc",[{"value":"немає даних" if self.lang=="ua" else "no data"}])[0]["value"]
            line = tk.Frame(forecast_card,bg=self.card_bg)
            line.pack(fill="x", pady=2)
            tk.Label(line,text=date_str,font=("Segoe UI",11), bg=self.card_bg).pack(side="left")
            tk.Label(line,text=f"{temp_min}°C / {temp_max}°C", font=("Segoe UI",11), bg=self.card_bg).pack(side="left", padx=10)
            tk.Label(line,text=desc,font=("Segoe UI",10), bg=self.card_bg).pack(side="right")

        # ==== Рекомендації ====
        recommendations = self.get_recommendations(current)
        rec_card = tk.Frame(self.weather_frame, bg=self.card_bg, bd=2, relief="groove", padx=15, pady=10)
        rec_card.pack(fill="x", pady=10)
        tk.Label(rec_card, text=self.translations["recommendations_title"], font=("Segoe UI",14,"bold"), bg=self.card_bg).pack(anchor="w", pady=(5,10))
        for rec in recommendations:
            tk.Label(rec_card, text=f"• {rec}", font=("Segoe UI",10), bg=self.card_bg).pack(anchor="w")

        # ==== Попередження ====
        warnings = self.check_warnings(current)
        if warnings:
            warn_card = tk.Frame(self.weather_frame, bg=self.card_bg, bd=2, relief="groove", padx=15, pady=10)
            warn_card.pack(fill="x", pady=10)
            tk.Label(warn_card,text=self.translations["warnings_title"], fg="red", font=("Segoe UI",14,"bold"), bg=self.card_bg).pack(anchor="w", pady=(5,10))
            for warn in warnings:
                tk.Label(warn_card, text=f"• {warn}", fg="red", font=("Segoe UI",10), bg=self.card_bg).pack(anchor="w")

    # ======= Рекомендації =======
    def get_recommendations(self, weather_data):
        recommendations=[]
        try: temp_c=int(weather_data.get("temp_C",0))
        except: temp_c=0
        rain_chance=int(weather_data.get("chanceofrain",0))
        snow_chance=int(weather_data.get("chanceofsnow",0))
        uv_index=int(weather_data.get("uvIndex",0))

        if temp_c<5: recommendations.append("🧣 Одягни шапку та рукавички.")
        elif 5<=temp_c<15: recommendations.append("🧥 Можливо, знадобиться куртка.")
        elif 15<=temp_c<25: recommendations.append("👕 Зручна одежа — гарний вибір.")

        if rain_chance>70: recommendations.append("🌂 Візьми парасольку!")
        if snow_chance>50: recommendations.append("🎿 Готуйся до снігу!")
        if uv_index>3: recommendations.append("☀️ Нанеси сонячний крем.")

        if not recommendations: recommendations.append("🌤 Сьогодні чудова погода!" if self.lang=="ua" else "🌤 Great weather today!")
        return recommendations

    # ======= Попередження =======
    def check_warnings(self, weather_data):
        warnings=[]
        rain_chance=int(weather_data.get("chanceofrain",0))
        snow_chance=int(weather_data.get("chanceofsnow",0))
        wind_speed=int(weather_data.get("windspeedKmph",0))
        temp_c=int(weather_data.get("temp_C",0))
        if rain_chance>80: warnings.append("🌧 Очікується сильний дощ. Уникайте прогулянок без парасолі." if self.lang=="ua" else "🌧 Heavy rain expected. Avoid going out without an umbrella.")
        if snow_chance>50: warnings.append("🌨 Можливий сніг. Обережно на дорогах!" if self.lang=="ua" else "🌨 Snow possible. Drive carefully.")
        if wind_speed>40: warnings.append("🌬 Сильний вітер! Утримуйте речі." if self.lang=="ua" else "🌬 Strong wind! Hold on to your belongings.")
        if temp_c<-5: warnings.append("❄️ Морозна погода. Тепло вдягайтеся!" if self.lang=="ua" else "❄️ Freezing cold. Dress warmly.")
        return warnings

    # ======= Автозавантаження =======
    def load_weather(self):
        def fetch():
            try:
                city="Kyiv"
                response = requests.get(URL_TEMPLATE.format(city=city))
                print(f"✅ Status code: {response.status_code}")
                if response.status_code==200:
                    data=response.json()
                    self.root.after(0,self.display_weather,data)
                elif response.status_code == 404:
                    self.root.after(0, self.show_city_not_found)
                else:
                    self.root.after(0, self.show_error)
            except:
                self.root.after(0, self.show_error)
        threading.Thread(target=fetch).start()


if __name__=="__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()
