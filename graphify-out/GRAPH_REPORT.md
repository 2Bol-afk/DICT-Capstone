# Graph Report - .  (2026-06-24)

## Corpus Check
- Corpus is ~9,874 words - fits in a single context window. You may not need a graph.

## Summary
- 132 nodes · 182 edges · 13 communities (9 shown, 4 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 1% AMBIGUOUS · INFERRED: 9 edges (avg confidence: 0.84)
- Token cost: 0 input · 88,439 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Farm Boundary & Map UI|Farm Boundary & Map UI]]
- [[_COMMUNITY_FastAPI Backend Routes|FastAPI Backend Routes]]
- [[_COMMUNITY_PlotReading Markers & Pins|Plot/Reading Markers & Pins]]
- [[_COMMUNITY_Farm Auth & i18nTheme|Farm Auth & i18n/Theme]]
- [[_COMMUNITY_SQLite Data Access Layer|SQLite Data Access Layer]]
- [[_COMMUNITY_Sensor Simulation & Model Training|Sensor Simulation & Model Training]]
- [[_COMMUNITY_Farm Geometry & Sensor Placement|Farm Geometry & Sensor Placement]]
- [[_COMMUNITY_Demo Seeding Script|Demo Seeding Script]]
- [[_COMMUNITY_Offline AI Explain Flow|Offline AI Explain Flow]]
- [[_COMMUNITY_Add Reading Modal (Mock)|Add Reading Modal (Mock)]]
- [[_COMMUNITY_Locate-Me Button Handler|Locate-Me Button Handler]]
- [[_COMMUNITY_Status Message Setter|Status Message Setter]]

## God Nodes (most connected - your core abstractions)
1. `get_conn()` - 14 edges
2. `loadFarms function` - 9 edges
3. `loadPlots function` - 9 edges
4. `simulate_sensor_values()` - 8 edges
5. `selectPlot function` - 6 edges
6. `lookupFarm function (fetch farm by name, list sensors)` - 6 edges
7. `suggest_sensor_points()` - 5 edges
8. `create_farm()` - 5 edges
9. `initMaps function` - 5 edges
10. `Sensor reading data model (soil_n, soil_p, soil_k, soil_ph, air_temp_c, humidity_pct, rainfall_mm, soil_moisture_pct, predicted_crop, confidence)` - 5 edges

## Surprising Connections (you probably didn't know these)
- `simulate_reading()` --calls--> `simulate_sensor_values()`  [EXTRACTED]
  main.py → sensor_sim.py
- `explain()` --calls--> `explain_reading()`  [EXTRACTED]
  main.py → explain.py
- `create_farm()` --calls--> `sensor_count_for()`  [EXTRACTED]
  main.py → geometry.py
- `create_farm()` --calls--> `suggest_sensor_points()`  [EXTRACTED]
  main.py → geometry.py
- `build_plot_reading()` --calls--> `simulate_sensor_values()`  [EXTRACTED]
  simulate_data.py → sensor_sim.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Farm boundary creation flow (Add Plot modal across mock and live dashboard)** — frontend_add_plot_addplotmodal, frontend_dashboard_openaddplot, frontend_dashboard_addplotform_submit_handler, frontend_dashboard_redrawpendingshape, api_farms_post [INFERRED 0.85]
- **Settings subsystem: bilingual text + theme persistence working together** — frontend_dashboard_wrapbilingualtext, frontend_dashboard_applylanguage, frontend_dashboard_applytheme, frontend_dashboard_refreshsettingsui, rationale_bilingual_text_switching, rationale_theme_persistence [INFERRED 0.85]
- **Offline-AI explanation flow shared between admin dashboard and farmer view** — frontend_dashboard_explainbtn_handler, frontend_farmer_explainbtn_handler, api_readings_explain_get, concept_reading [INFERRED 0.85]

## Communities (13 total, 4 thin omitted)

### Community 0 - "Farm Boundary & Map UI"
Cohesion: 0.09
Nodes (27): DELETE /farms/{id} endpoint, GET /farms endpoint, PUT /farms/{id} endpoint, Add Plot Modal (static mock), Button active-state scale micro-interaction, Close button click handler (alert simulation), Click-map-to-set-location pin UI concept, buildSensorLegend function (+19 more)

### Community 1 - "FastAPI Backend Routes"
Cohesion: 0.11
Nodes (18): BaseModel, explain_reading(), Ask the local Ollama model to explain a prediction. Raises requests.RequestExcep, create_plot(), create_reading(), edit_farm(), explain(), farm_by_name() (+10 more)

### Community 2 - "Plot/Reading Markers & Pins"
Cohesion: 0.16
Nodes (17): GET /plots endpoint, GET /readings/{plot_id} endpoint, POST /readings endpoint, POST /readings/simulate endpoint, Plot/Sensor sub-plot data model (plot_id, owner_name, lat, lng, predicted_crop, confidence), Sensor reading data model (soil_n, soil_p, soil_k, soil_ph, air_temp_c, humidity_pct, rainfall_mm, soil_moisture_pct, predicted_crop, confidence), N/P/K/pH/Temp/Humidity/Rainfall/Moisture input fields concept, simulateValues function (+9 more)

### Community 3 - "Farm Auth & i18n/Theme"
Cohesion: 0.13
Nodes (16): GET /farms/by-name/{name} endpoint, POST /farms endpoint, Farm data model (farm_id, farm_name, owner_name, hectares, polygon, sensors), addPlotForm submit handler (POST /farms), applyLanguage function, applyTheme function, openAddPlot function, refreshSettingsUI function (+8 more)

### Community 4 - "SQLite Data Access Layer"
Cohesion: 0.29
Nodes (14): delete_farm(), get_all_farms(), get_all_readings(), get_conn(), get_farm(), get_farm_by_name(), get_latest_for_farm(), get_latest_per_plot() (+6 more)

### Community 5 - "Sensor Simulation & Model Training"
Cohesion: 0.29
Nodes (6): DataFrame, Pick a random PH-relevant crop and sample realistic sensor values for it., sample_reading(), simulate_sensor_values(), build_plot_reading(), main()

### Community 6 - "Farm Geometry & Sensor Placement"
Cohesion: 0.32
Nodes (7): _point_in_polygon(), Point-in-polygon + sensor placement suggestion for drawn farm shapes., Pick n points spread inside the polygon. Falls back to the centroid if the     p, sensor_count_for(), suggest_sensor_points(), create_farm(), Register a farm boundary and auto-place sensor sub-plots inside it     (5 sensor

### Community 8 - "Offline AI Explain Flow"
Cohesion: 1.00
Nodes (3): GET /readings/{id}/explain endpoint, explainBtn click handler (GET /readings/{id}/explain), explainBtn click handler (GET /readings/{id}/explain)

## Ambiguous Edges - Review These
- `redrawPendingShape function` → `finishShapeBtn click handler (compute hectares + sensor count)`  [AMBIGUOUS]
  frontend/dashboard.html · relation: calls

## Knowledge Gaps
- **22 isolated node(s):** `Close button click handler (alert simulation)`, `Button active-state scale micro-interaction`, `readingForm submit handler (demo, preventDefault)`, `Add Reading Modal (static mock)`, `pinColor function` (+17 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `redrawPendingShape function` and `finishShapeBtn click handler (compute hectares + sensor count)`?**
  _Edge tagged AMBIGUOUS (relation: calls) - confidence is low._
- **Why does `loadFarms function` connect `Farm Boundary & Map UI` to `Farm Auth & i18n/Theme`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `loadPlots function` connect `Plot/Reading Markers & Pins` to `Farm Boundary & Map UI`, `Farm Auth & i18n/Theme`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **What connects `Ask the local Ollama model to explain a prediction. Raises requests.RequestExcep`, `Point-in-polygon + sensor placement suggestion for drawn farm shapes.`, `Pick n points spread inside the polygon. Falls back to the centroid if the     p` to the rest of the system?**
  _36 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Farm Boundary & Map UI` be split into smaller, more focused modules?**
  _Cohesion score 0.08547008547008547 - nodes in this community are weakly interconnected._
- **Should `FastAPI Backend Routes` be split into smaller, more focused modules?**
  _Cohesion score 0.1076923076923077 - nodes in this community are weakly interconnected._
- **Should `Farm Auth & i18n/Theme` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._