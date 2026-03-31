import streamlit as st
import streamlit.components.v1 as components
import os
import base64

BACKEND = "http://127.0.0.1:8000"

st.set_page_config(page_title="Guardian Angel", layout="wide")
st.title("🛡 Guardian Angel – Safe Route Monitoring")

components.html(
f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>

<link
  rel="stylesheet"
  href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<style>
body {{
  margin: 0;
  font-family: Arial, sans-serif;
}}
#panel {{
  padding: 10px;
  background: #111;
  color: white;
  display: flex;
  gap: 10px;
}}
.input-group {{
  position: relative;
  flex: 1;
}}
.input {{
  width: 100%;
  padding: 8px;
  box-sizing: border-box;
}}
.suggestions {{
  background: white;
  color: black;
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 1000;
  max-height: 150px;
  overflow-y: auto;
  border: 1px solid #ccc;
}}
.suggestions div {{
  padding: 6px;
  cursor: pointer;
  border-bottom: 1px solid #eee;
}}
.suggestions div:hover {{
  background: #eee;
}}
#map {{
  height: 550px;
  width: 100%;
}}
</style>
</head>

<body>

<div id="panel">
  <div class="input-group" style="padding: 10px; font-weight: bold; font-size: 1.1em; color: #007bff;">
    📍 FIXED PATH MONITORING
  </div>
  <div class="input-group">
    <input id="from" class="input" placeholder="From location" autocomplete="off"/>
    <div id="from-suggestions" class="suggestions"></div>
  </div>
  <div class="input-group">
    <input id="to" class="input" placeholder="To location" autocomplete="off"/>
    <div id="to-suggestions" class="suggestions"></div>
  </div>
</div>

<div id="map"></div>

<script>
const map = L.map("map").setView([27.19, 78.03], 12);
L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
  attribution: "© OpenStreetMap contributors"
}}).addTo(map);

let fromCoord = null;
let toCoord = null;
let routeLayers = [];
let marker = null;

createStatusDiv();
// Tracking setup will happen once the From location is picked

// ---------------- PHOTON AUTOCOMPLETE ----------------
async function photonSearch(query) {{
  try {{
      const r = await fetch(
        "https://photon.komoot.io/api/?q=" + encodeURIComponent(query)
      );
      return (await r.json()).features;
  }} catch (e) {{
      console.error("Photon Search Error", e);
      return [];
  }}
}}

function attachAutocomplete(inputId, boxId, setter) {{
  const input = document.getElementById(inputId);
  const box = document.getElementById(boxId);

  input.addEventListener("input", async () => {{
    if (input.value.length < 3) {{
      box.innerHTML = "";
      return;
    }}
    const results = await photonSearch(input.value);
    box.innerHTML = "";
    results.slice(0,5).forEach(r => {{
      const d = document.createElement("div");
      d.textContent = r.properties.name + ", " + r.properties.country;
      d.onclick = () => {{
        input.value = d.textContent;
        box.innerHTML = "";
        console.log("Selected:", inputId, r.geometry.coordinates);
        setter([r.geometry.coordinates[1], r.geometry.coordinates[0]]);
        
        // Move marker to 'From' location immediately if selected
        if (inputId === "from") {{
            const coord = [r.geometry.coordinates[1], r.geometry.coordinates[0]];
            if (marker) {{
                marker.setLatLng(coord);
            }} else {{
                marker = L.marker(coord, {{ draggable: true }}).addTo(map);
                setupTracking();
            }}
            map.setView(coord, 14);
        }}

        if (fromCoord && toCoord) {{
            console.log("Both points selected, drawing routes...");
            drawRoutes();
        }}
      }};
      box.appendChild(d);
    }});
  }});
}}

attachAutocomplete("from", "from-suggestions", c => fromCoord = c);
attachAutocomplete("to", "to-suggestions", c => toCoord = c);

// ---------------- OSRM ROUTING ----------------
async function drawRoutes() {{
  routeLayers.forEach(l => map.removeLayer(l));
  routeLayers = [];

  const url =
    `https://router.project-osrm.org/route/v1/driving/` +
    `${{fromCoord[1]}},${{fromCoord[0]}};${{toCoord[1]}},${{toCoord[0]}}` +
    `?alternatives=true&overview=full&geometries=geojson`;

  try {{
      const statusDiv = document.getElementById("status-display");
      const r = await fetch(url);
        if (!r.ok) throw new Error("OSRM returned " + r.status);
      const data = await r.json();

      if (!data.routes || data.routes.length === 0) {{
          alert("No routes found between these locations!");
          return;
      }}

      data.routes.forEach((r, i) => {{
        const coords = r.geometry.coordinates.map(p => [p[1], p[0]]);
        const line = L.polyline(coords, {{
          color: "#3498db", // Light Blue
          weight: 5,
          opacity: 0.4,
          cursor: "pointer"
        }}).addTo(map);
        
        line.bindPopup(`<b>Route ${{i+1}}</b><br>${{Math.round(r.distance / 1000 * 10) / 10}} km | ${{Math.round(r.duration / 60)}} min<br><button onclick="window.selectRoute(${{i}})" style="cursor:pointer; background:#007bff; color:white; border:none; padding:5px 10px; border-radius:3px; margin-top:5px;">Select This Route</button>`);

        window.selectRoute = (index) => {{
            const selectedLine = routeLayers[index];
            const statusDiv = document.getElementById("status-display");
            
            // Set all to light blue
            routeLayers.forEach(l => l.setStyle({{color:"#3498db", opacity: 0.4, weight: 5}}));
            // Set selected to deep blue
            selectedLine.setStyle({{color:"#0047ab", opacity: 1, weight: 8}});
            
            const selectedData = data.routes[index];
            statusDiv.style.backgroundColor = "#007bff";
            statusDiv.innerText = "🛰️ Connecting to Guardian Agent...";
            window.isTrackingStarted = false; // RESET TRACKING

            fetch("{BACKEND}/set-path", {{
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{
                    route: selectedData.geometry.coordinates,
                    eta_seconds: Math.round(selectedData.duration)
                }})
            }}).then(res => {{
                if(res.ok) {{
                    statusDiv.style.backgroundColor = "#28a745";
                    statusDiv.innerHTML = "<b>✅ ROUTE LOCKED</b><br>Move marker to start tracking.";
                    if (marker) map.removeLayer(marker);
                    marker = L.marker(selectedLine.getLatLngs()[0], {{ draggable: true }}).addTo(map);
                    setupTracking();
                }}
                else alert("Failed to save route");
            }}).catch(e => alert("Backend error: " + e));
        }};

        line.on("mouseover", () => {{ if(line.options.color === "#3498db") line.setStyle({{color: "#2980b9", opacity: 0.8}}); }});
        line.on("mouseout", () => {{ if(line.options.color === "#3498db") line.setStyle({{color: "#3498db", opacity: 0.4}}); }});
        line.on("click", () => window.selectRoute(i));

        routeLayers.push(line);
      }});
      
      statusDiv.style.backgroundColor = "#111";
      statusDiv.innerHTML = "<b>📍 SELECT YOUR ROUTE</b><br>Click a route line on the map to start tracking.";
      
      map.fitBounds(L.featureGroup(routeLayers).getBounds());
  }} catch (e) {{
      alert("Routing Error: " + e.message);
      console.error(e);
  }}
}}

function setupTracking() {{
  if (!marker) return;
  marker.off("dragend");
  marker.on("dragend", () => {{
      window.isTrackingStarted = true; // START TRACKING ON FIRST MOVE
      sendUpdate();
  }});

  if (window.trackingInterval) clearInterval(window.trackingInterval);
  window.trackingInterval = setInterval(() => {{ if (marker) sendUpdate(); }}, 10000);
}}

async function sendUpdate() {{
  if (!window.isTrackingStarted) {{
      console.log("Tracking not started yet - awaiting movement.");
      return;
  }}
  
  const p = marker.getLatLng();
  const statusDiv = document.getElementById("status-display");

  try {{
      const res = await fetch("{BACKEND}/move", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ lat: p.lat, lng: p.lng, mode: "fixed" }})
      }});
      
      const data = await res.json();
      const dist = data.distance_m !== undefined ? ` (${{data.distance_m}}m)` : "";
      const status = data.status || "UNKNOWN";
      
      if (data.decision === "EMERGENCY_DEVIATION" || data.decision === "EMERGENCY_TIMEOUT") {{
          statusDiv.style.backgroundColor = "#dc3545"; // Red
          statusDiv.innerHTML = `<b>🚨 EMERGENCY ALERT</b><br>${{status}}${{dist}}`;
          if (!window.alertSent) {{
              alert(`🚨 EMERGENCY: ${{status}} detected! Guardian has been alerted.`);
              window.alertSent = true;
          }}
      }} else if (status === "DEVIATION" || status === "ODD_PLACE" || status === "OUTSIDE_PATTERN") {{
          // It's a deviation, but maybe not (yet) an alert or cooldown is active
          statusDiv.style.backgroundColor = "#dc3545"; // Red
          statusDiv.innerHTML = `<b>🚨 DEVIATED</b><br>${{status}}${{dist}}`;
          window.alertSent = false;
      }} else if (data.decision === "SEND_SAFETY_NOTICE" || data.decision === "WAIT_FOR_REPLY") {{
          statusDiv.style.backgroundColor = "#fd7e14"; // Orange
          statusDiv.innerHTML = `<b>⚠️ ${{status}} DETECTED</b><br>Please reply to the WhatsApp check!`;
          window.alertSent = false;
      }} else {{
          statusDiv.style.backgroundColor = "#28a745"; // Green
          statusDiv.innerHTML = `<b>✅ ${{status}}${{dist}}</b><br>Path monitoring active.`;
          window.alertSent = false;
      }}
  }} catch (e) {{
      console.error("Error connecting to backend", e);
  }}
}}

function createStatusDiv() {{
    let div = document.getElementById("status-display");
    if (div) return div;

    div = document.createElement("div");
    div.id = "status-display";
    div.style.position = "absolute";
    div.style.top = "10px";
    div.style.right = "10px";
    div.style.padding = "10px 20px";
    div.style.borderRadius = "5px";
    div.style.color = "white";
    div.style.fontWeight = "bold";
    div.style.backgroundColor = "gray";
    div.style.zIndex = "1000";
    div.innerText = "Select mode and drag marker";
    document.getElementById("map").appendChild(div);
    return div;
}}
</script>

</body>
</html>
""",
height=650
)
