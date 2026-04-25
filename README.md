🎮 Player Journey Tool



Overview



This tool visualizes player movement, behavior, and events across game maps using historical match data. It helps understand player journeys, combat hotspots, and gameplay patterns.



\---



Features



\* Player path visualization on minimap

\* Human vs bot differentiation (blue vs red paths)

\* Event markers:



&#x20; \* Kill

&#x20; \* Death

&#x20; \* Loot

&#x20; \* Storm deaths

\* Match filtering (map + match selection)

\* Timeline playback (based on event sequence / timestamp progression)

\* Heatmap visualization (player activity density)



\---



Tech Stack



\* Python

\* Streamlit

\* Pandas

\* PyArrow

\* Plotly

\* Pillow



\---



Setup Instructions



bash

pip install -r requirements.txt

python -m streamlit run app.py



\---



Deployment



Live App: \*\*\[PASTE YOUR STREAMLIT URL HERE]\*\*



\---



Notes



\* Timeline playback uses event progression. In cases where timestamps lack variation, full data is shown.

\* Heatmap visualizes player density and potential combat hotspots.

\* Coordinate mapping is handled via custom scaling and origin normalization per map.



\---



Folder Structure



lila-player-viz/

├── app.py

├── requirements.txt

├── README.md

├── ARCHITECTURE.md

├── INSIGHTS.md

├── data/

├── maps/



