Architecture Overview



Tech Choices



|**Component**|**Choice**|**Reason**|
|-|-|-|
|UI|Streamlit|Rapid prototyping and easy deployment|
|Data Processing|Pandas|Efficient handling of structured data|
|File Format|Parquet|Fast and compressed columnar storage|
|Visualization|Plotly|Interactive and layered visualization|
|Image Handling|Pillow|Map rendering and resizing|



\---



Data Flow



1\. Load parquet files from data/player\_data

2\. Convert to Pandas DataFrames

3\. Merge all data into a single dataset

4\. Decode event fields

5\. Apply filters:



&#x20;  \* Map

&#x20;  \* Match

6\. Sort events by timestamp

7\. Generate time progression (time\_sec)

8\. Transform coordinates to map space

9\. Render:



&#x20;  \* Player paths

&#x20;  \* Event markers

&#x20;  \* Heatmap overlay



\---



Coordinate Mapping (Key Logic)



Game provides world coordinates (x, z).



We convert them into minimap pixel coordinates:



Step 1: Normalize



u = (x - origin\_x) / scale  

v = (z - origin\_z) / scale



Step 2: Convert to pixels



pixel\_x = u \* 1024  

pixel\_y = (1 - v) \* 1024



Step 3: Overlay on minimap image



Each map has:



\* Custom scale

\* Custom origin



Defined in MAP\_CONFIG.



\---



Timeline Handling



\* Timestamps are converted using pd.to\_datetime

\* Relative time (time\_sec) is calculated from match start

\* Playback slider filters events up to selected time



Fallback:



\* If no variation exists → full data shown



\---



Assumptions



\* Some matches may not have meaningful timestamp variation

\* Coordinate scaling is approximated for visual alignment

\* Event names are interpreted based on dataset labels



\---



Tradeoffs



|**Decision**|**Alternative**|**Reason**|
|-|-|-|
|Streamlit UI|React dashboard|Faster development|
|Histogram heatmap|Kernel density|Simpler + performant|
|Event-based timeline|Absolute time|Data inconsistency|
|Static map images|GIS mapping|Reduced complexity|





\---



System Design Summary



\* Lightweight architecture

\* Local data processing

\* Real-time visualization via Streamlit

\* Designed for exploration and insight generation



