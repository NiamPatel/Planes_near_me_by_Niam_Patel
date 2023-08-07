import streamlit as st
import requests
import pandas as pd
import streamlit_folium as st_folium
import folium
import pydeck as pdk


def get_aircraft_data(latitude, longitude, radius):
    url = f"https://opensky-network.org/api/states/all?lamin={latitude - 1}&lomin={longitude - 1}&lamax={latitude + 1}&lomax={longitude + 1}"
    headers = {"Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        print("API Status Code:", response.status_code)
        response.raise_for_status()

        try:
            data = response.json()
            print("API Response Data:", data)
            aircraft_data = data.get("states", [])
            filtered_data = []
            if aircraft_data:
                for aircraft in aircraft_data:
                    if len(aircraft) >= 11:
                        lat, lon = aircraft[6], aircraft[5]
                        if haversine_distance(latitude, longitude, lat, lon) <= radius:
                            filtered_data.append((lat, lon, aircraft[1], aircraft[7], aircraft[9], aircraft[10]))
            return filtered_data
        except ValueError as e:
            print("API Response Text:", response.text)
            raise e
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching aircraft data: {e}")
        return []


def create_map(latitude, longitude):
    map_ = folium.Map(location=[latitude, longitude], zoom_start=10)
    return map_


def main():
    st.title("Plane Tracker")
    st.write("See what planes are flying over your head and where they are headed!")

    latitude, longitude = st.sidebar.number_input("Enter your current location (latitude):"), st.sidebar.number_input(
        "Enter your current location (longitude):"
    )
    radius = st.sidebar.slider("Select the search radius (miles)", 1, 100, 10)

    aircraft_data = get_aircraft_data(latitude, longitude, radius)

    if len(aircraft_data) == 0:
        st.warning("No aircraft data available at the moment. Please try again later.")
    else:
        st.markdown("### Currently, the following planes are flying over your location:")
        df = pd.DataFrame(aircraft_data, columns=["LAT", "LON", "Callsign", "Altitude", "Speed", "Heading"])
        st.dataframe(df)

        # Create a deck.gl ScatterplotLayer
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position="[LON, LAT]",
            get_color="[200, 30, 0, 160]",
            get_radius=20000,
        )

        # Set the initial view state for the map
        view_state = pdk.ViewState(
            latitude=latitude,
            longitude=longitude,
            zoom=8,
            pitch=0,
        )

        # Render the map using st.pydeck_chart
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            layers=[layer],
            initial_view_state=view_state,
        ))


def haversine_distance(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2

    R = 3958.8

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


if __name__ == "__main__":
    st.set_page_config(layout="wide")
    main()
