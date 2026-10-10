
/* =========================================================
   QUANTUMROUTE - FRONTEND APPLICATION
   VNQFF-08: Quantum-Enhanced Last-Mile Route Optimisation
   ========================================================= */

"use strict";

window.QR_API_BASE_URL = "http://127.0.0.1:5000";

const QR_API = `${window.QR_API_BASE_URL}/api`;
const QR_RESULTS_KEY = "quantumRouteResults";
const QR_REQUEST_KEY = "quantumRouteRequest";

let qrMap = null;
let qrMapLayer = null;
let qrMapMarkers = null;
let qrMapInitialized = false;
let qrMapRequestId = 0;
let qrMapStartPromise = null;

/* =========================================================
   GENERAL HELPERS
   ========================================================= */

function qrElement(id) {
    return document.getElementById(id);
}

function setText(id, value) {
    const element = qrElement(id);
    if (element) element.textContent = value ?? "--";
}

function setMultiple(ids, value) {
    ids.forEach(id => setText(id, value));
}

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

function qrNumber(value, fallback = 0) {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
}

function qrReadStorage(key) {
    try {
        return JSON.parse(localStorage.getItem(key) || "null");
    } catch (error) {
        console.error(`Unable to read ${key}:`, error);
        return null;
    }
}

function qrSaveStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (error) {
        console.error(`Unable to save ${key}:`, error);
        return false;
    }
}

function qrGetResults() {
    const saved = qrReadStorage(QR_RESULTS_KEY);
    return saved?.result || saved;
}

function qrGetRequest() {
    return qrReadStorage(QR_REQUEST_KEY);
}

function qrGetSelectedMode() {
    return qrElement("qrMapRouteType")?.value === "classical"
        ? "classical"
        : "quantum";
}

function qrGetRoute(result, mode = qrGetSelectedMode()) {
    const selected = result?.[mode];
    if (!selected) return [];

    const route =
        selected.route ??
        selected.best_route ??
        selected.path ??
        selected.bestRoute;

    return Array.isArray(route) ? route : [];
}

function qrGetDistance(result, mode = qrGetSelectedMode()) {
    const selected = result?.[mode];
    if (!selected) return null;

    const distance = Number(
        selected.distance ??
        selected.total_distance ??
        selected.totalDistance
    );

    return Number.isFinite(distance) ? distance : null;
}

function qrGetDemand(result, request) {
    const directValue =
        result?.total_demand ??
        result?.totalDemand ??
        result?.demand;

    if (directValue !== undefined &&
        directValue !== null &&
        directValue !== "") {
        const direct = Number(directValue);
        if (Number.isFinite(direct)) return direct;
    }

    return (request?.deliveries || []).reduce(
        (sum, delivery) => sum + qrNumber(delivery.demand),
        0
    );
}

function qrGetLocationName(location) {
    return [
        location?.address,
        location?.city,
        location?.state,
        location?.country
    ].filter(Boolean).join(", ") || "Location details unavailable";
}

function qrGetLocationId(location, fallback = "STOP") {
    return String(
        location?.id ??
        location?.location_id ??
        location?.name ??
        fallback
    );
}

function qrNormalizeId(value) {
    return String(value ?? "").trim().toUpperCase();
}

/* =========================================================
   BACKEND STATUS
   ========================================================= */

async function checkBackend() {
    const status = qrElement("backendStatus");

    if (status) {
        status.textContent = "Checking...";
        status.classList.remove("offline");
    }

    try {
        const response = await fetch(`${QR_API}/health`, {
            method: "GET",
            headers: { Accept: "application/json" }
        });

        if (!response.ok) {
            throw new Error(`Backend returned HTTP ${response.status}`);
        }

        const data = await response.json();
        const online = data.success !== false;

        if (status) {
            status.textContent = online ? "Online" : "Unavailable";
            status.classList.toggle("offline", !online);
        }

        return online;
    } catch (error) {
        console.error("Backend health check failed:", error);

        if (status) {
            status.textContent = "Offline";
            status.classList.add("offline");
        }

        return false;
    }
}

/* =========================================================
   LOCATION INPUTS
   ========================================================= */

function qrGetLocationContainer() {
    return qrElement("locationsContainer") ||
           qrElement("deliveryLocations");
}

function addLocation() {
    const container = qrGetLocationContainer();

    if (!container) {
        console.error("Delivery location container not found.");
        showError("Delivery location container was not found.");
        return;
    }

    const existingRows = container.querySelectorAll(".location-row");
    const nextNumber = existingRows.length + 1;

    const row = document.createElement("div");
    row.className = "location-row";
    row.dataset.locationRow = "true";
    row.dataset.rowId = `delivery-${Date.now()}-${nextNumber}`;

    row.innerHTML = `
        <input type="text" class="location-id"
            placeholder="Stop ID (e.g. D001)"
            aria-label="Stop ID"
            value="D${String(nextNumber).padStart(3, "0")}" required>

        <input type="text" class="location-country"
            placeholder="Country" aria-label="Country" required>

        <input type="text" class="location-state"
            placeholder="State" aria-label="State" required>

        <input type="text" class="location-city"
            placeholder="City" aria-label="City" required>

        <input type="number" class="location-demand"
            placeholder="Demand" aria-label="Demand"
            min="0" step="any" value="1" required>

        <button type="button"
            class="remove-location delete-btn"
            aria-label="Remove delivery stop"
            title="Remove delivery">×</button>
    `;

    container.appendChild(row);
}

function removeLocation(buttonOrRow) {
    const row = buttonOrRow instanceof Element
        ? buttonOrRow.closest(".location-row")
        : buttonOrRow;

    if (!row) return;

    const container = qrGetLocationContainer();
    if (container?.contains(row)) row.remove();
}

function getLocationInputs() {
    const container = qrGetLocationContainer();

    if (!container) {
        throw new Error("Delivery location form was not found.");
    }

    const rows = [...container.querySelectorAll(".location-row")];

    if (rows.length === 0) {
        throw new Error("Add at least one delivery location.");
    }

    const ids = new Set();

    return rows.map((row, index) => {
        const id = row.querySelector(".location-id")?.value.trim();
        const country = row.querySelector(".location-country")?.value.trim();
        const state = row.querySelector(".location-state")?.value.trim();
        const city = row.querySelector(".location-city")?.value.trim();
        const demandValue = row.querySelector(".location-demand")?.value;
        const demand = Number(demandValue);

        if (!id || !country || !state || !city) {
            throw new Error(
                `Complete all fields for delivery stop ${index + 1}.`
            );
        }

        if (demandValue === "" ||
            !Number.isFinite(demand) ||
            demand < 0) {
            throw new Error(`Enter a valid demand for stop ${id}.`);
        }

        const normalizedId = id.toUpperCase();

        if (ids.has(normalizedId)) {
            throw new Error(`Duplicate delivery stop ID: ${id}.`);
        }

        ids.add(normalizedId);

        return { id, country, state, city, demand };
    });
}

function getDeliveries() {
    return getLocationInputs();
}

/* =========================================================
   ERROR DISPLAY
   ========================================================= */

function showError(message) {
    let element =
        qrElement("errorMessage") ||
        qrElement("optimizationError") ||
        qrElement("qrDynamicError");

    if (!element) {
        element = document.createElement("div");
        element.id = "qrDynamicError";
        element.setAttribute("role", "alert");
        element.style.cssText =
            "padding:12px;margin:12px 0;border:1px solid #e8b4b4;" +
            "border-radius:8px;color:#9a2525;background:#fff5f5;";

        const target =
            qrElement("optimizationForm") ||
            qrElement("optimizeForm") ||
            document.querySelector("main") ||
            document.body;

        target.prepend(element);
    }

    element.textContent = message;
    element.hidden = false;
    element.classList.remove("hidden");
    element.style.display = "block";
}

function hideError() {
    [
        qrElement("errorMessage"),
        qrElement("optimizationError"),
        qrElement("qrDynamicError")
    ].filter(Boolean).forEach(element => {
        element.hidden = true;
        element.classList.add("hidden");
        element.style.display = "none";
    });
}

/* =========================================================
   ROUTE OPTIMIZATION
   ========================================================= */

async function optimizeRoute(event) {
    if (event?.preventDefault) event.preventDefault();

    hideError();

    const button =
        qrElement("optimizeBtn") ||
        qrElement("optimizeButton") ||
        qrElement("optimizeRouteButton") ||
        (event?.currentTarget instanceof HTMLButtonElement
            ? event.currentTarget
            : null);

    const oldButtonText = button?.textContent;

    if (button) {
        button.disabled = true;
        button.textContent = "Optimizing...";
    }

    try {
        const vehicleId =
            qrElement("vehicleId")?.value?.trim() ||
            qrElement("vehicle-id")?.value?.trim() ||
            "VEHICLE-1";

        const capacityInput =
            qrElement("vehicleCapacity") ||
            qrElement("vehicle-capacity") ||
            qrElement("capacity");

        const capacity = Number(capacityInput?.value || 100);

        if (!Number.isFinite(capacity) || capacity <= 0) {
            throw new Error("Vehicle capacity must be greater than zero.");
        }

        const deliveries = getDeliveries();

        const totalDemand = deliveries.reduce(
            (sum, delivery) => sum + delivery.demand,
            0
        );

        if (totalDemand > capacity) {
            throw new Error(
                `Total demand (${totalDemand}) exceeds vehicle capacity (${capacity}).`
            );
        }

        const depot = {
            id: "DEPOT",
            country: "India",
            state: "Andhra Pradesh",
            city: "Vijayawada"
        };

        const requestBody = {
            vehicle_id: vehicleId,
            depot,
            deliveries,
            vehicle_capacity: capacity
        };

        if (!qrSaveStorage(QR_REQUEST_KEY, requestBody)) {
            throw new Error(
                "Unable to save delivery inputs in browser storage."
            );
        }

        const response = await fetch(`${QR_API}/optimize`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json"
            },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                data.error ||
                data.message ||
                `Optimization failed (HTTP ${response.status}).`
            );
        }

        if (data.success === false || data.error) {
            throw new Error(
                data.error || data.message || "Optimization failed."
            );
        }

        const resultData = data.result || data;

        if (!resultData.classical && !resultData.quantum) {
            console.error("Unexpected optimizer response:", data);
            throw new Error(
                "Backend response does not contain classical or quantum results."
            );
        }

        if (!qrSaveStorage(QR_RESULTS_KEY, resultData)) {
            throw new Error(
                "Route optimized, but browser could not save the results."
            );
        }

        displayResults(resultData);
        updateDeliveryNetwork();

        if (window.updateQuantumRouteMap) {
            await window.updateQuantumRouteMap(resultData);
        }

        document.dispatchEvent(new CustomEvent("quantumroute:optimized", {
            detail: {
                request: requestBody,
                results: resultData
            }
        }));

        return resultData;

    } catch (error) {
        console.error("Route optimization failed:", error);
        showError(error.message || "Unable to optimize the route.");
        return null;

    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = oldButtonText || "Optimize Route";
        }
    }
}

/* =========================================================
   RESULTS DISPLAY
   ========================================================= */

function displayResults(resultData) {
    const data = resultData?.result || resultData || {};

    const classical = data.classical || {};
    const quantum =
        data.quantum ||
        data.quantum_result ||
        data.qaoa ||
        {};

    console.log("DISPLAY RESULTS:", data);
    console.log("QUANTUM DETAILS:", quantum);
    console.log("QUANTUM METHOD:", quantum.method);
    console.log("QUANTUM QUBITS:", quantum.qubits);
    console.log("QUANTUM PROBABILITY:", quantum.probability);

    const classicalDistance = qrGetDistance(data, "classical");
    const quantumDistance = qrGetDistance(data, "quantum");

    setText(
        "classicalDistance",
        classicalDistance == null
            ? "--"
            : `${classicalDistance.toFixed(2)} km`
    );

    setText(
        "quantumDistance",
        quantumDistance == null
            ? "--"
            : `${quantumDistance.toFixed(2)} km`
    );

    setText(
        "classicalCost",
        classical.cost == null
            ? "--"
            : Number(classical.cost).toFixed(2)
    );

    setText(
        "quantumCost",
        quantum.cost == null
            ? "--"
            : Number(quantum.cost).toFixed(2)
    );

    const comparison = data.comparison || data.route_comparison || {};

    const distanceDifference =
        comparison.distance_difference ??
        (
            classicalDistance != null && quantumDistance != null
                ? Math.abs(classicalDistance - quantumDistance)
                : null
        );

    setText(
        "distanceDifference",
        distanceDifference == null
            ? "--"
            : `${Number(distanceDifference).toFixed(2)} km`
    );

    const request = qrGetRequest();
    const demand = qrGetDemand(data, request);

    setMultiple(["totalDemand", "total-demand"], demand);
    setText("qrPerformanceDemand", `${demand} units`);

    setText(
        "classicalRoute",
        qrGetRoute(data, "classical").join(" → ") || "--"
    );

    setText(
        "quantumRoute",
        qrGetRoute(data, "quantum").join(" → ") || "--"
    );

    // Quantum optimizer metadata
    const summary = data.optimization_summary || {};
    const optimizer = quantum.optimizer_details || quantum.metadata || {};

    const method =
        quantum.method ??
        quantum.optimizer ??
        quantum.quantum_method ??
        quantum.algorithm ??
        optimizer.method ??
        summary.quantum_method ??
        "Method not reported";

    const qubits =
        quantum.qubits ??
        quantum.num_qubits ??
        quantum.qubits_used ??
        quantum.numQubits ??
        optimizer.qubits ??
        optimizer.num_qubits ??
        null;

    const probability =
        quantum.probability_percent != null
            ? Number(quantum.probability_percent)
            : quantum.probability != null
                ? Number(quantum.probability) * 100
                : null;

    setMultiple(
        ["optimizationMethod", "quantumMethod", "qrOptimizationMethod"],
        method
    );

    setMultiple(
        ["qubitsUsed", "qubits", "qrPerformanceQubits"],
        qubits == null ? "Not reported" : String(qubits)
    );

    setMultiple(
        ["quantumProbability", "probability", "qrQuantumProbability"],
        probability != null && Number.isFinite(probability)
            ? `${probability.toFixed(2)}%`
            : "Not available"
    );

    setText(
        "qrPerformanceDistance",
        quantumDistance == null
            ? "-- km"
            : `${quantumDistance.toFixed(2)} km`
    );

    setText(
        "dashboardOptimizedDistance",
        quantumDistance == null
            ? "-- km"
            : `${quantumDistance.toFixed(2)} km`
    );

    const resultsBox = qrElement("resultContainer");

    if (resultsBox) {
        resultsBox.hidden = false;
        resultsBox.classList.remove("hidden");
        resultsBox.style.display = "";
    }

    updateDeliveryNetwork();
}

/* =========================================================
   CLEAR RESULTS
   ========================================================= */

function clearResults() {
    [
        "classicalDistance",
        "quantumDistance",
        "classicalCost",
        "quantumCost",
        "distanceDifference",
        "totalDemand",
        "total-demand",
        "classicalRoute",
        "quantumRoute",
        "optimizationMethod",
        "quantumMethod",
        "qrOptimizationMethod",
        "qubitsUsed",
        "qubits",
        "qrPerformanceQubits",
        "quantumProbability",
        "probability",
        "qrQuantumProbability",
        "qrPerformanceDistance",
        "qrPerformanceDemand",
        "dashboardOptimizedDistance",
        "qrRecommendedDistance",
        "qrRecommendedRoute"
    ].forEach(id => setText(id, "--"));

    try {
        localStorage.removeItem(QR_RESULTS_KEY);
        localStorage.removeItem(QR_REQUEST_KEY);
    } catch (error) {
        console.error("Unable to clear saved route results:", error);
    }

    const resultsBox = qrElement("resultContainer");

    if (resultsBox) {
        resultsBox.hidden = true;
        resultsBox.classList.add("hidden");
    }

    updateDeliveryNetwork();

    if (qrMapLayer) qrMapLayer.clearLayers();
    if (qrMapMarkers) qrMapMarkers.clearLayers();

    setText("qrMapStatus", "Optimize a route to display the map.");
}

/* =========================================================
   DYNAMIC DELIVERY NETWORK
   ========================================================= */

function qrMatchStop(routeId, depot, deliveries) {
    const stops = [depot, ...deliveries];
    const id = qrNormalizeId(routeId);

    const exact = stops.find(stop => qrNormalizeId(stop.id) === id);
    if (exact) return exact;

    if (["DEPOT", "START", "END"].includes(id)) return depot;

    const letter = id.match(/^(?:LOCATION\s*)?([A-Z])$/);

    if (letter) {
        const index = letter[1].charCodeAt(0) - "A".charCodeAt(0);
        return deliveries[index] || null;
    }

    if (/^\d+$/.test(id)) {
        const number = Number(id);
        if (number === 0) return depot;
        return deliveries[number - 1] || null;
    }

    return null;
}

function updateDeliveryNetwork() {
    const container = qrElement("deliveryNetworkRoute");
    if (!container) return;

    const data = qrGetResults();
    const request = qrGetRequest();

    if (!data || !request?.depot ||
        !Array.isArray(request.deliveries)) {
        container.innerHTML =
            "<p>Run route optimization to view the recommended route.</p>";

        setText("deliveryRouteStatus", "Waiting for route");
        setText("qrRecommendedRoute", "--");
        setText("qrRecommendedDistance", "-- km");
        return;
    }

    const mode = qrGetSelectedMode();
    const route = qrGetRoute(data, mode);

    if (route.length === 0) {
        container.innerHTML =
            `<p>No ${escapeHtml(mode)} route is available.</p>`;

        setText("deliveryRouteStatus", "Route unavailable");
        return;
    }

    const depot = { ...request.depot, id: request.depot.id || "DEPOT" };
    const deliveries = request.deliveries;

    const matchedRoute = route.map(routeId => ({
        routeId,
        stop: qrMatchStop(routeId, depot, deliveries)
    }));

    if (matchedRoute.some(item => !item.stop)) {
        console.error("Route stop IDs do not match saved locations.", {
            route, depot, deliveries
        });

        container.innerHTML =
            "<p>Some route IDs do not match the submitted locations. Check the backend route IDs in the browser console.</p>";

        setText("deliveryRouteStatus", "Route ID mismatch");
        return;
    }

    container.innerHTML = matchedRoute.map((item, index) => {
        const stop = item.stop;
        const isDepot =
            qrNormalizeId(stop.id) === qrNormalizeId(depot.id);

        const title = isDepot
            ? (index === matchedRoute.length - 1
                ? "RETURN DEPOT"
                : "DEPOT")
            : `DELIVERY ${qrGetLocationId(stop)}`;

        return `
            <div class="delivery-network-stop">
                <span class="delivery-network-number">${index + 1}</span>
                <div>
                    <strong>${escapeHtml(title)}</strong>
                    <p>${escapeHtml(qrGetLocationName(stop))}</p>
                </div>
            </div>
            ${index < matchedRoute.length - 1
                ? '<div class="delivery-network-arrow">↓</div>'
                : ""}
        `;
    }).join("");

    setText(
        "deliveryRouteStatus",
        `✓ ${mode === "quantum" ? "Quantum" : "Classical"} Route`
    );

    setText("qrRecommendedRoute", route.map(String).join(" → "));

    const distance = qrGetDistance(data, mode);

    setText(
        "qrRecommendedDistance",
        distance === null ? "-- km" : `${distance.toFixed(2)} km`
    );

    if (mode === "quantum") {
        setText(
            "dashboardOptimizedDistance",
            distance === null ? "-- km" : `${distance.toFixed(2)} km`
        );
    }
}

/* =========================================================
   MAP UTILITIES
   ========================================================= */

function qrLoadScript(src) {
    return new Promise((resolve, reject) => {
        const existing = [...document.scripts].find(
            script => script.src === src
        );

        if (existing) {
            if (existing.dataset.loaded === "true" || window.L) {
                resolve();
                return;
            }

            existing.addEventListener("load", resolve, { once: true });
            existing.addEventListener(
                "error",
                () => reject(new Error(`Could not load ${src}`)),
                { once: true }
            );
            return;
        }

        const script = document.createElement("script");
        script.src = src;
        script.async = true;

        script.onload = () => {
            script.dataset.loaded = "true";
            resolve();
        };

        script.onerror = () => reject(
            new Error(`Could not load map library: ${src}`)
        );

        document.head.appendChild(script);
    });
}

async function qrFetchJson(url, options = {}, timeoutMs = 12000) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status} from ${url}`);
        }

        return await response.json();
    } finally {
        clearTimeout(timeout);
    }
}

async function qrGeocode(location) {
    try {
        const result = await qrFetchJson(`${QR_API}/geocode`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(location)
        }, 10000);

        const lat = Number(result.lat ?? result.latitude);
        const lon = Number(result.lon ?? result.lng ?? result.longitude);

        if (Number.isFinite(lat) && Number.isFinite(lon)) {
            return { lat, lon };
        }

        if (Array.isArray(result.results) && result.results.length) {
            const first = result.results[0];
            const firstLat = Number(first.lat ?? first.latitude);
            const firstLon = Number(
                first.lon ?? first.lng ?? first.longitude
            );

            if (Number.isFinite(firstLat) && Number.isFinite(firstLon)) {
                return { lat: firstLat, lon: firstLon };
            }
        }
    } catch (error) {
        console.warn(
            "Backend geocoding unavailable; trying map geocoder.",
            error
        );
    }

    const query = encodeURIComponent(qrGetLocationName(location));

    const data = await qrFetchJson(
        `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=${query}`,
        {},
        12000
    );

    if (!Array.isArray(data) || !data.length) {
        throw new Error(
            `Could not find map coordinates for ${qrGetLocationName(location)}.`
        );
    }

    return {
        lat: Number(data[0].lat),
        lon: Number(data[0].lon)
    };
}

async function qrGetRoadRoute(coordinates) {
    if (coordinates.length < 2) {
        throw new Error("At least two locations are required for road routing.");
    }

    const coordinateString = coordinates
        .map(point => `${point.lon},${point.lat}`)
        .join(";");

    const url =
        `https://router.project-osrm.org/route/v1/driving/${coordinateString}` +
        "?overview=full&geometries=geojson&steps=false";

    const data = await qrFetchJson(url, {}, 20000);

    if (data.code !== "Ok" || !data.routes?.length) {
        throw new Error("A driving route could not be found for these locations.");
    }

    return data.routes[0];
}

/* =========================================================
   LEAFLET MAP
   ========================================================= */

const QRMap = {
    async start() {
        const mapElement = qrElement("qrLiveMap");
        if (!mapElement) return;

        // Avoid multiple simultaneous map initializations.
        if (qrMapStartPromise) return qrMapStartPromise;

        qrMapStartPromise = (async () => {
            try {
                if (!window.L) {
                    await qrLoadScript(
                        "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
                    );
                }

                if (!window.L) {
                    throw new Error("Leaflet map library did not initialize.");
                }

                if (!qrMapInitialized) {
                    qrMap = window.L.map(mapElement)
                        .setView([16.5062, 80.6480], 7);

                    window.L.tileLayer(
                        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                        {
                            maxZoom: 19,
                            attribution: "&copy; OpenStreetMap contributors"
                        }
                    ).addTo(qrMap);

                    qrMapLayer = window.L.layerGroup().addTo(qrMap);
                    qrMapMarkers = window.L.layerGroup().addTo(qrMap);
                    qrMapInitialized = true;

                    setTimeout(() => qrMap?.invalidateSize(), 100);
                }

                const results = qrGetResults();
                const request = qrGetRequest();

                if (results && request) {
                    await this.update(results);
                } else {
                    setText(
                        "qrMapStatus",
                        "Optimize a route to display the map."
                    );
                }
            } catch (error) {
                console.error("Map initialization failed:", error);
                setText("qrMapStatus", `Map unavailable: ${error.message}`);
            } finally {
                qrMapStartPromise = null;
            }
        })();

        return qrMapStartPromise;
    },

    async update(resultData = qrGetResults()) {
        const requestId = ++qrMapRequestId;

        if (!qrElement("qrLiveMap")) return;

        if (!qrMapInitialized || !qrMap) {
            await this.start();

            if (!qrMapInitialized || !qrMap) return;

            // start() may already have drawn the saved results.
            if (requestId !== qrMapRequestId) return;
        }

        const results = resultData?.result || resultData;
        const request = qrGetRequest();

        if (!results || !request?.depot ||
            !Array.isArray(request.deliveries)) {
            setText("qrMapStatus", "Optimize a route to display the map.");
            return;
        }

        const mode = qrGetSelectedMode();
        const route = qrGetRoute(results, mode);

        if (!route.length) {
            setText("qrMapStatus", `No ${mode} route is available.`);
            return;
        }

        const depot = request.depot;
        const deliveries = request.deliveries;

        const stops = route.map(routeId =>
            qrMatchStop(routeId, depot, deliveries)
        );

        if (stops.some(stop => !stop)) {
            console.error("Map route could not match all stop IDs.", {
                route,
                depot,
                deliveries
            });

            setText(
                "qrMapStatus",
                "Map route IDs do not match the submitted delivery locations."
            );
            return;
        }

        setText("qrMapStatus", "Finding delivery coordinates...");

        try {
            const coordinates = [];

            for (const stop of stops) {
                if (requestId !== qrMapRequestId) return;

                const point = await qrGeocode(stop);

                if (!Number.isFinite(point.lat) ||
                    !Number.isFinite(point.lon)) {
                    throw new Error(
                        `Invalid coordinates for ${qrGetLocationName(stop)}`
                    );
                }

                coordinates.push(point);
            }

            if (requestId !== qrMapRequestId) return;

            setText("qrMapStatus", "Calculating driving route...");

            const roadRoute = await qrGetRoadRoute(coordinates);

            if (requestId !== qrMapRequestId) return;

            qrMapLayer.clearLayers();
            qrMapMarkers.clearLayers();

            const latLngs = roadRoute.geometry.coordinates.map(
                coordinate => [coordinate[1], coordinate[0]]
            );

            window.L.polyline(latLngs, {
                color: mode === "quantum" ? "#7950d8" : "#2777c8",
                weight: 5,
                opacity: 0.85
            }).addTo(qrMapLayer);

            coordinates.forEach((point, index) => {
                const stop = stops[index];
                const isDepot =
                    qrNormalizeId(stop.id) === qrNormalizeId(depot.id);

                const title = isDepot
                    ? (index === stops.length - 1
                        ? "Return Depot"
                        : "Depot")
                    : `Delivery ${qrGetLocationId(stop)}`;

                window.L.marker([point.lat, point.lon])
                    .bindPopup(
                        `<strong>${escapeHtml(title)}</strong><br>` +
                        escapeHtml(qrGetLocationName(stop))
                    )
                    .addTo(qrMapMarkers);
            });

            const bounds = window.L.latLngBounds(latLngs);

            if (bounds.isValid()) {
                qrMap.fitBounds(bounds, { padding: [25, 25] });
            }

            const roadDistanceKm = roadRoute.distance / 1000;

            setText(
                "qrMapStatus",
                `${mode} road route displayed successfully.`
            );

            // Keep the optimizer's distance in the results.
            // The map's road distance is displayed in the map status only.
            console.log(
                "Mapped road distance:",
                `${roadDistanceKm.toFixed(2)} km`
            );

        } catch (error) {
            if (requestId !== qrMapRequestId) return;

            console.error("Road map update failed:", error);
            setText(
                "qrMapStatus",
                `Unable to draw road route: ${error.message}`
            );
        }
    }
};

/* =========================================================
   GLOBAL FUNCTIONS
   ========================================================= */

window.addLocation = addLocation;
window.removeLocation = removeLocation;
window.getLocationInputs = getLocationInputs;
window.getDeliveries = getDeliveries;
window.optimizeRoute = optimizeRoute;
window.displayResults = displayResults;
window.clearResults = clearResults;
window.updateDeliveryNetwork = updateDeliveryNetwork;
window.checkBackend = checkBackend;
window.QRMap = QRMap;

window.updateQuantumRouteMap = resultData => QRMap.update(resultData);
window.updateMapWithResults = resultData => QRMap.update(resultData);

/* =========================================================
   EVENT HANDLERS
   ========================================================= */

document.addEventListener("click", function (event) {
    if (!(event.target instanceof Element)) return;

    const deleteButton = event.target.closest(
        "#locationsContainer .remove-location, " +
        "#locationsContainer .delete-btn, " +
        "#deliveryLocations .remove-location, " +
        "#deliveryLocations .delete-btn"
    );

    if (!deleteButton) return;

    event.preventDefault();
    removeLocation(deleteButton);
});

/* =========================================================
   PAGE INITIALIZATION
   ========================================================= */

function initializeQuantumRoute() {
    checkBackend();
    updateDeliveryNetwork();

    const routeSelector = qrElement("qrMapRouteType");

    if (routeSelector && !routeSelector.dataset.qrBound) {
        routeSelector.dataset.qrBound = "true";

        routeSelector.addEventListener("change", async function () {
            updateDeliveryNetwork();
            await QRMap.update();
        });
    }

    if (qrElement("qrLiveMap")) {
        QRMap.start();
    }

    const savedResults = qrGetResults();

    if (savedResults) {
        displayResults(savedResults);
    }
}

if (document.readyState === "loading") {
    document.addEventListener(
        "DOMContentLoaded",
        initializeQuantumRoute,
        { once: true }
    );
} else {
    initializeQuantumRoute();
}

/* =========================================================
   CROSS-TAB STORAGE UPDATES
   ========================================================= */

window.addEventListener("storage", function (event) {
    if (event.key === QR_RESULTS_KEY || event.key === QR_REQUEST_KEY) {
        updateDeliveryNetwork();

        if (window.QRMap) {
            QRMap.update();
        }
    }
});
