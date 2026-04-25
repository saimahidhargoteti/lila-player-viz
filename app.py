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

                    df['event'] = df['event'].apply(
                        lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
                    )

                    all_data.append(df)

                except:
                    continue

    return pd.concat(all_data, ignore_index=True)


df = load_data()
df['is_bot'] = df['user_id'].astype(str).str.isnumeric()

# ----------- SIDEBAR -----------

st.sidebar.header("Filters")

selected_map = st.sidebar.selectbox("Select Map", df['map_id'].unique())

filtered_df = df[df['map_id'] == selected_map]

matches = filtered_df['match_id'].unique()

# Find a match with time variation
good_match = None

for m in matches:
    temp = filtered_df[filtered_df['match_id'] == m]
    if pd.to_datetime(temp['ts']).nunique() > 1:
        good_match = m
        break

selected_match = st.sidebar.selectbox(
    "Select Match",
    matches,
    index=list(matches).index(good_match) if good_match else 0
)

filtered_df = filtered_df[filtered_df['match_id'] == selected_match]

filtered_df = filtered_df[filtered_df['match_id'] == selected_match]

filtered_df = filtered_df.sort_values("ts")


show_heatmap = st.sidebar.checkbox("Show Heatmap")

filtered_df['time_sec'] = range(len(filtered_df))
# ----------- TIME SLIDER -----------

filtered_df = filtered_df.copy()
filtered_df['ts'] = pd.to_datetime(filtered_df['ts'])


start_time = filtered_df['ts'].min()
filtered_df['time_sec'] = (filtered_df['ts'] - start_time).dt.total_seconds()

min_t = int(filtered_df['time_sec'].min())
max_t = int(filtered_df['time_sec'].max())

# ✅ FIX: handle single-point case BEFORE slider
if max_t <= min_t:
    st.warning("⚠️ Not enough events to show playback. Showing full data.")
else:
    selected_time = st.slider(
        "Playback Progress",
        min_value=min_t,
        max_value=max_t,
        value=max_t,
        key="time_slider"
    )

    filtered_df = filtered_df[filtered_df['time_sec'] <= selected_time]
st.caption("Tip: Select a match with time variation to enable timeline playback")

# ----------- CREATE FIG -----------

fig = go.Figure()
config = MAP_CONFIG[selected_map]

# ----------- PLAYER PATHS -----------

for player_id, group in filtered_df.groupby("user_id"):
    xs = []
    ys = []

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
    "BotKilled": "yellow",
    "Loot": "green",
    "KilledByStorm": "purple"
}

event_x = []
event_y = []
event_c = []
event_text = []

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

map_image = Image.open(map_path)
map_image = map_image.resize((1024, 1024))

# ----------- OVERLAY MAP -----------

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


# ----------- HEATMAP (STABLE VERSION) -----------

if show_heatmap:
    heat_x = []
    heat_y = []

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
    st.caption("Heatmap shows kill density (combat hotspots)")

# ----------- SHOW PLOT -----------

st.plotly_chart(fig, use_container_width=True)

# ----------- DEBUG INFO -----------

st.write("### Data Loaded Successfully ✅")
st.write(df.head())
st.write("### Columns")
st.write(df.columns)