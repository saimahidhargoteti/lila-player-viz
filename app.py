import streamlit as st
import pandas as pd
import os
import pyarrow.parquet as pq
import plotly.graph_objects as go
from PIL import Image

# ----------- MAP CONFIG -----------

MAP_CONFIG = {
    "AmbroseValley": {"scale": 900, "origin_x": -370, "origin_z": -473},
    "GrandRift": {"scale": 581, "origin_x": -290, "origin_z": -290},
    "Lockdown": {"scale": 1000, "origin_x": -500, "origin_z": -500},
}

def world_to_map(x, z, config):
    u = (x - config["origin_x"]) / config["scale"]
    v = (z - config["origin_z"]) / config["scale"]

    pixel_x = u * 1024
    pixel_y = (1 - v) * 1024

    return pixel_x, pixel_y


st.title("🎮 Player Journey Tool")

# ----------- LOAD DATA -----------

@st.cache_data
def load_data():
    base_path = "data/player_data"
    all_data = []

    for day in os.listdir(base_path):
        day_path = os.path.join(base_path, day)

        if os.path.isdir(day_path):
            for file in os.listdir(day_path):
                file_path = os.path.join(day_path, file)

                try:
                    table = pq.read_table(file_path)
                    df = table.to_pandas()

                    # ✅ Add date column
                    df['date'] = day

                    # Decode event column
                    df['event'] = df['event'].apply(
                        lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
                    )

                    all_data.append(df)

                except:
                    continue

    return pd.concat(all_data, ignore_index=True)


df = load_data()
df['is_bot'] = df['user_id'].astype(str).str.isnumeric()

# ----------- SIDEBAR FILTERS -----------

st.sidebar.header("Filters")

# ✅ DATE FILTER
selected_date = st.sidebar.selectbox(
    "Select Date",
    sorted(df['date'].unique()),
    key="date_filter"
)

filtered_df = df[df['date'] == selected_date]

# ✅ MAP FILTER
selected_map = st.sidebar.selectbox(
    "Select Map",
    filtered_df['map_id'].unique(),
    key="map_filter"
)

filtered_df = filtered_df[filtered_df['map_id'] == selected_map]

# ✅ MATCH FILTER
matches = filtered_df['match_id'].unique()

selected_match = st.sidebar.selectbox(
    "Select Match",
    matches,
    key="match_filter"
)

filtered_df = filtered_df[filtered_df['match_id'] == selected_match]

filtered_df = filtered_df.sort_values("ts")

# ----------- HEATMAP TOGGLE -----------

show_heatmap = st.sidebar.checkbox("Show Heatmap")

# ----------- TIME HANDLING -----------

filtered_df = filtered_df.copy()
filtered_df['ts'] = pd.to_datetime(filtered_df['ts'])

start_time = filtered_df['ts'].min()
filtered_df['time_sec'] = (filtered_df['ts'] - start_time).dt.total_seconds()

min_t = int(filtered_df['time_sec'].min())
max_t = int(filtered_df['time_sec'].max())

if max_t <= min_t:
    st.warning("⚠️ Not enough time variation. Showing full match.")
else:
    selected_time = st.slider(
        "Playback Progress",
        min_value=min_t,
        max_value=max_t,
        value=max_t,
        key="time_slider"
    )

    filtered_df = filtered_df[filtered_df['time_sec'] <= selected_time]

st.caption("Tip: Select a match with time variation to enable playback")

# ----------- CREATE FIG -----------

fig = go.Figure()
config = MAP_CONFIG[selected_map]

# ----------- PLAYER PATHS -----------

for player_id, group in filtered_df.groupby("user_id"):
    xs, ys = [], []

    for row in group.itertuples():
        px, py = world_to_map(row.x, row.z, config)
        xs.append(px)
        ys.append(py)

    color = "red" if group['is_bot'].iloc[0] else "blue"

    fig.add_trace(go.Scatter(
        x=xs,
        y=ys,
        mode='lines',
        line=dict(color=color),
        showlegend=False
    ))

# ----------- EVENT MARKERS -----------

event_colors = {
    "Kill": "red",
    "Killed": "black",
    "BotKill": "orange",
    "BotKilled": "gray",
    "Loot": "green",
    "KilledByStorm": "purple"
}

event_x, event_y, event_c, event_text = [], [], [], []

for row in filtered_df.itertuples():
    if row.event not in ["Position", "BotPosition"]:
        px, py = world_to_map(row.x, row.z, config)

        event_x.append(px)
        event_y.append(py)
        event_c.append(event_colors.get(row.event, "white"))
        event_text.append(row.event)

fig.add_trace(go.Scatter(
    x=event_x,
    y=event_y,
    mode='markers',
    marker=dict(size=6, color=event_c),
    text=event_text,
    hoverinfo='text',
    name="Events"
))

# ----------- LOAD MAP -----------

map_path = f"maps/{selected_map}_Minimap.png"
if selected_map == "Lockdown":
    map_path = "maps/Lockdown_Minimap.jpg"

map_image = Image.open(map_path).resize((1024, 1024))

# ----------- MAP OVERLAY -----------

fig.update_layout(
    images=[dict(
        source=map_image,
        xref="x",
        yref="y",
        x=0,
        y=1024,
        sizex=1024,
        sizey=1024,
        sizing="stretch",
        layer="below"
    )],
    xaxis=dict(visible=False),
    yaxis=dict(visible=False, scaleanchor="x"),
    height=800
)

# ----------- HEATMAP -----------

if show_heatmap:
    heat_x, heat_y = [], []

    for _, row in filtered_df.iterrows():
        px, py = world_to_map(row['x'], row['z'], config)
        heat_x.append(px)
        heat_y.append(py)

    fig.add_trace(go.Histogram2d(
        x=heat_x,
        y=heat_y,
        colorscale='YlOrRd',
        showscale=True,
        opacity=0.4,
        nbinsx=30,
        nbinsy=30
    ))

# ----------- LEGEND -----------

st.markdown("""
### Legend:
- 🔵 Human paths  
- 🔴 Bot paths  
- 🟢 Loot  
- ⚫ Death  
- 🔴 Kill  
- 🟣 Storm  
""")

if show_heatmap:
    st.caption("Heatmap shows activity density (combat hotspots)")

# ----------- SHOW PLOT -----------

st.plotly_chart(fig, use_container_width=True)

# ----------- DEBUG -----------

st.write("### Data Loaded Successfully ✅")
st.write(df.head())
st.write("### Columns")
st.write(df.columns)