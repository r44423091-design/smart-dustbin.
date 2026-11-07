
import json
import math
import threading
import webbrowser
import urllib.request
import urllib.error

from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.core.window import Window


# -----------------------------------
# CONFIGURATION
# -----------------------------------

APP_NAME = "Smart Dustbin"

# Set this to your secure backend endpoint.
# Leave empty to use demonstration data.
API_URL = ""

# Demonstration garbage truck location.
# Replace with live phone GPS later.
TRUCK_LAT = 20.2961
TRUCK_LON = 85.8245

FULL_THRESHOLD = 80

Window.clearcolor = (0.94, 0.96, 0.98, 1)


# -----------------------------------
# SAMPLE DUSTBIN DATA
# -----------------------------------

SAMPLE_BINS = [
    {
        "id": "BIN-001",
        "latitude": 20.2961,
        "longitude": 85.8245,
        "fill": 92,
        "online": True
    },
    {
        "id": "BIN-002",
        "latitude": 20.3000,
        "longitude": 85.8300,
        "fill": 35,
        "online": True
    },
    {
        "id": "BIN-003",
        "latitude": 20.2900,
        "longitude": 85.8200,
        "fill": 85,
        "online": True
    },
    {
        "id": "BIN-004",
        "latitude": 20.3100,
        "longitude": 85.8400,
        "fill": 65,
        "online": False
    }
]


# -----------------------------------
# DISTANCE CALCULATION
# -----------------------------------

def calculate_distance(lat1, lon1, lat2, lon2):

    earth_radius = 6371

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


# -----------------------------------
# MAP FUNCTIONS
# -----------------------------------

def open_satellite_map(bin_data):

    lat = bin_data["latitude"]
    lon = bin_data["longitude"]

    url = (
        "https://www.google.com/maps/@"
        f"{lat},{lon},18z"
        "?basemap=satellite"
    )

    webbrowser.open(url)


def open_navigation(bin_data):

    lat = bin_data["latitude"]
    lon = bin_data["longitude"]

    url = (
        "https://www.google.com/maps/dir/?api=1"
        f"&destination={lat},{lon}"
        "&travelmode=driving"
    )

    webbrowser.open(url)


# -----------------------------------
# MAIN APPLICATION
# -----------------------------------

class SmartDustbinApp(App):

    def build(self):

        self.title = APP_NAME

        self.bins = SAMPLE_BINS.copy()

        self.main_layout = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(10)
        )

        # HEADER

        header = Label(
            text="[b]SMART DUSTBIN MONITORING[/b]",
            markup=True,
            size_hint_y=None,
            height=dp(55),
            font_size="20sp",
            color=(0.05, 0.20, 0.35, 1)
        )

        self.main_layout.add_widget(header)

        # DASHBOARD

        self.stats = GridLayout(
            cols=3,
            spacing=dp(7),
            size_hint_y=None,
            height=dp(100)
        )

        self.main_layout.add_widget(self.stats)

        # TRUCK LOCATION

        self.truck_label = Label(
            text="Garbage Truck: GPS demo location",
            size_hint_y=None,
            height=dp(35),
            color=(0.1, 0.2, 0.3, 1)
        )

        self.main_layout.add_widget(self.truck_label)

        # REFRESH BUTTON

        refresh_button = Button(
            text="REFRESH DUSTBIN DATA",
            size_hint_y=None,
            height=dp(45),
            background_color=(0.1, 0.45, 0.75, 1)
        )

        refresh_button.bind(
            on_press=self.refresh_data
        )

        self.main_layout.add_widget(refresh_button)

        # DUSTBIN LIST

        scroll = ScrollView()

        self.bin_list = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None
        )

        self.bin_list.bind(
            minimum_height=self.bin_list.setter(
                "height"
            )
        )

        scroll.add_widget(self.bin_list)

        self.main_layout.add_widget(scroll)

        self.update_dashboard()

        # Refresh every 30 seconds.
        Clock.schedule_interval(
            self.refresh_data,
            30
        )

        return self.main_layout

    # -----------------------------------
    # DASHBOARD
    # -----------------------------------

    def update_dashboard(self):

        self.stats.clear_widgets()

        total = len(self.bins)

        full = sum(
            1 for b in self.bins
            if b["fill"] >= FULL_THRESHOLD
        )

        available = total - full

        values = [
            ("TOTAL", total, (0.1, 0.35, 0.7, 1)),
            ("FULL", full, (0.85, 0.15, 0.15, 1)),
            ("OTHER", available, (0.1, 0.55, 0.25, 1))
        ]

        for title, number, color in values:

            card = BoxLayout(
                orientation="vertical",
                padding=dp(5)
            )

            card.add_widget(
                Label(
                    text=str(number),
                    font_size="25sp",
                    bold=True,
                    color=color
                )
            )

            card.add_widget(
                Label(
                    text=title,
                    font_size="12sp",
                    color=(0.2, 0.2, 0.2, 1)
                )
            )

            self.stats.add_widget(card)

        self.bin_list.clear_widgets()

        for bin_data in self.bins:

            self.create_bin_card(bin_data)

    # -----------------------------------
    # DUSTBIN CARD
    # -----------------------------------

    def create_bin_card(self, bin_data):

        fill = float(bin_data["fill"])

        if fill >= 80:
            status = "FULL"
            color = (0.85, 0.12, 0.12, 1)

        elif fill >= 50:
            status = "WARNING"
            color = (0.9, 0.55, 0.05, 1)

        else:
            status = "NORMAL"
            color = (0.1, 0.55, 0.25, 1)

        card = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            padding=dp(10),
            size_hint_y=None,
            height=dp(205)
        )

        title = Label(
            text=(
                f"[b]{bin_data['id']}[/b] "
                f" - {status}"
            ),
            markup=True,
            font_size="17sp",
            color=color,
            size_hint_y=None,
            height=dp(35)
        )

        card.add_widget(title)

        card.add_widget(
            Label(
                text=f"Garbage Level: {fill:.0f}%",
                color=(0.1, 0.1, 0.1, 1)
            )
        )

        card.add_widget(
            Label(
                text=(
                    f"Location: "
                    f"{bin_data['latitude']}, "
                    f"{bin_data['longitude']}"
                ),
                font_size="11sp",
                color=(0.2, 0.2, 0.2, 1)
            )
        )

        distance = calculate_distance(
            TRUCK_LAT,
            TRUCK_LON,
            bin_data["latitude"],
            bin_data["longitude"]
        )

        # Rough estimate only, not live route ETA.
        estimated_minutes = round(
            distance / 25 * 60
        )

        card.add_widget(
            Label(
                text=(
                    f"Distance: {distance:.2f} km | "
                    f"Estimated: {estimated_minutes} min"
                ),
                font_size="12sp",
                color=(0.15, 0.2, 0.25, 1)
            )
        )

        buttons = BoxLayout(
            spacing=dp(5),
            size_hint_y=None,
            height=dp(40)
        )

        map_button = Button(
            text="SATELLITE MAP"
        )

        map_button.bind(
            on_press=lambda instance, b=bin_data:
            open_satellite_map(b)
        )

        route_button = Button(
            text="NAVIGATE",
            background_color=(0.1, 0.45, 0.75, 1)
        )

        route_button.bind(
            on_press=lambda instance, b=bin_data:
            open_navigation(b)
        )

        buttons.add_widget(map_button)
        buttons.add_widget(route_button)

        card.add_widget(buttons)

        self.bin_list.add_widget(card)

    # -----------------------------------
    # BACKEND DATA
    # -----------------------------------

    def refresh_data(self, *args):

        if not API_URL:
            self.update_dashboard()
            return

        def worker():

            try:
                request = urllib.request.Request(
                    API_URL,
                    headers={
                        "Accept": "application/json"
                    }
                )

                with urllib.request.urlopen(
                    request,
                    timeout=10
                ) as response:

                    data = json.loads(
                        response.read().decode("utf-8")
                    )

                if isinstance(data, list):

                    valid_bins = []

                    for item in data:

                        required = [
                            "id",
                            "latitude",
                            "longitude",
                            "fill"
                        ]

                        if all(k in item for k in required):

                            item["fill"] = max(
                                0,
                                min(100, float(item["fill"]))
                            )

                            valid_bins.append(item)

                    Clock.schedule_once(
                        lambda dt: self.set_bins(valid_bins)
                    )

            except Exception as error:

                print("Backend connection error:", error)

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def set_bins(self, data):

        self.bins = data
        self.update_dashboard()


if __name__ == "__main__":

    SmartDustbinApp().run()
