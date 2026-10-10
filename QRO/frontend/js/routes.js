/* =========================================================
   QUANTUMROUTE
   OPTIMIZED VEHICLE ROUTES
   MOVING VEHICLES
   INCIDENT WARNINGS + ALTERNATE ROUTES
========================================================= */


/* =========================================================
   MAP LOCATIONS
========================================================= */

const mapLocations = {

    Warehouse: [17.3850, 78.4867],

    A: [17.3950, 78.4967],

    B: [17.4050, 78.5067],

    C: [17.4150, 78.4967],

    D: [17.4000, 78.4767],

    E: [17.3750, 78.4767]
};


/* =========================================================
   LOCATION DATA
========================================================= */

const locationData = {

    A: {
        id: "A",
        x: 2,
        y: 3,
        demand: 20
    },

    B: {
        id: "B",
        x: 5,
        y: 4,
        demand: 30
    },

    C: {
        id: "C",
        x: 6,
        y: 1,
        demand: 15
    },

    D: {
        id: "D",
        x: 3,
        y: -2,
        demand: 10
    },

    E: {
        id: "E",
        x: -1,
        y: -3,
        demand: 10
    }
};


/* =========================================================
   DEFAULT VEHICLE ROUTES
========================================================= */

const vehicleRoutes = {

    "Vehicle 01":
        ["Warehouse", "A", "B", "C", "Warehouse"],

    "Vehicle 02":
        ["Warehouse", "D", "E", "Warehouse"],

    "Vehicle 03":
        ["Warehouse", "B", "D", "A", "Warehouse"],

    "Vehicle 04":
        ["Warehouse", "C", "E", "Warehouse"]
};


/* =========================================================
   OPTIMIZED VEHICLE ROUTES
========================================================= */

let optimizedVehicleRoutes = {};


/* =========================================================
   VEHICLE CAPACITY
========================================================= */

const vehicleCapacity = 100;


/* =========================================================
   VEHICLE ANIMATION
========================================================= */

let vehicleMarkers = {};

let animationFrames = {};

let animationRunning = false;

let animationSpeed = 0.00045;


/* =========================================================
   VEHICLE ICONS
========================================================= */

const vehicleIcons = {

    "Vehicle 01": "🚚",

    "Vehicle 02": "🚛",

    "Vehicle 03": "🚐",

    "Vehicle 04": "🚙"
};


/* =========================================================
   ALTERNATE ROUTES
========================================================= */

const alternateRoutes = {

    traffic: {

        route:
            ["Warehouse", "A", "D", "C", "Warehouse"],

        distance:
            "39 km",

        time:
            "1 hour 12 minutes"
    },


    blocked: {

        route:
            ["Warehouse", "A", "D", "B", "Warehouse"],

        distance:
            "37 km",

        time:
            "1 hour 08 minutes"
    },


    breakdown: {

        route:
            ["Warehouse", "A", "B", "C", "Warehouse"],

        distance:
            "36 km",

        time:
            "1 hour 05 minutes"
    }
};


/* =========================================================
   LANGUAGE CONFIGURATION
========================================================= */

const voiceLanguages = {

    "en-IN": {
        name: "English",
        voiceLanguage: "en-IN"
    },

    "te-IN": {
        name: "తెలుగు",
        voiceLanguage: "te-IN"
    },

    "hi-IN": {
        name: "हिन्दी",
        voiceLanguage: "hi-IN"
    },

    "ta-IN": {
        name: "தமிழ்",
        voiceLanguage: "ta-IN"
    },

    "kn-IN": {
        name: "ಕನ್ನಡ",
        voiceLanguage: "kn-IN"
    }
};


const LANGUAGE_STORAGE_KEY =
    "quantumRouteVoiceLanguage";


let selectedLanguage = null;

let availableVoices = [];


/* =========================================================
   MAP VARIABLES
========================================================= */

let routeMap = null;

let routeLayers = [];

let incidentLayers = [];

let alternateRouteLayer = null;

let incidentTimer = null;


/* =========================================================
   LOAD SAVED LANGUAGE
========================================================= */

function loadSavedLanguage() {

    const savedLanguage =
        localStorage.getItem(
            LANGUAGE_STORAGE_KEY
        );


    if (
        savedLanguage &&
        voiceLanguages[savedLanguage]
    ) {

        selectedLanguage =
            savedLanguage;

        updateLanguageDisplay();

        return;
    }


    showLanguageModal();
}


/* =========================================================
   LANGUAGE MODAL
========================================================= */

function showLanguageModal() {

    const modal =
        document.getElementById(
            "languageModal"
        );

    if (!modal) return;

    modal.classList.remove("hidden");
}


function hideLanguageModal() {

    const modal =
        document.getElementById(
            "languageModal"
        );

    if (!modal) return;

    modal.classList.add("hidden");
}


/* =========================================================
   SELECT LANGUAGE
========================================================= */

function selectVoiceLanguage(languageCode) {

    if (!voiceLanguages[languageCode]) {
        return;
    }


    selectedLanguage =
        languageCode;


    localStorage.setItem(
        LANGUAGE_STORAGE_KEY,
        languageCode
    );


    updateLanguageDisplay();

    hideLanguageModal();

    loadVoices();

    updateVoiceStatus(
        "🎙 Voice Assistant Ready"
    );
}


function changeVoiceLanguage() {

    stopVoice();

    showLanguageModal();
}


function updateLanguageDisplay() {

    const element =
        document.getElementById(
            "currentLanguage"
        );


    if (!element) return;


    if (
        selectedLanguage &&
        voiceLanguages[selectedLanguage]
    ) {

        element.textContent =
            voiceLanguages[
                selectedLanguage
            ].name;

    } else {

        element.textContent =
            "Not selected";
    }
}


/* =========================================================
   VOICE MESSAGES
========================================================= */

function getVoiceMessage(type) {

    const language =
        selectedLanguage || "en-IN";


    if (language === "en-IN") {

        if (type === "traffic") {

            return (
                "Warning. High traffic detected ahead. " +
                "QuantumRoute is calculating an alternate route."
            );
        }


        if (type === "blocked") {

            return (
                "Warning. Road blockage detected. " +
                "The current route is blocked. " +
                "QuantumRoute is selecting an alternate route."
            );
        }


        if (type === "breakdown") {

            return (
                "Warning. Vehicle breakdown detected on the route. " +
                "QuantumRoute is calculating an alternate route."
            );
        }
    }


    if (language === "te-IN") {

        if (type === "traffic") {

            return (
                "హెచ్చరిక. ముందుగా అధిక ట్రాఫిక్ గుర్తించబడింది. " +
                "క్వాంటమ్ రూట్ ప్రత్యామ్నాయ మార్గాన్ని ఎంచుకుంటోంది."
            );
        }


        if (type === "blocked") {

            return (
                "హెచ్చరిక. రహదారి మూసివేయబడింది. " +
                "ప్రస్తుత మార్గం అందుబాటులో లేదు. " +
                "ప్రత్యామ్నాయ మార్గాన్ని ఎంచుకుంటున్నాము."
            );
        }


        if (type === "breakdown") {

            return (
                "హెచ్చరిక. మార్గంలో వాహనం చెడిపోయింది. " +
                "ప్రత్యామ్నాయ మార్గాన్ని ఎంచుకుంటున్నాము."
            );
        }
    }


    if (language === "hi-IN") {

        if (type === "traffic") {

            return (
                "चेतावनी। आगे भारी ट्रैफिक है। " +
                "क्वांटमरूट वैकल्पिक मार्ग खोज रहा है।"
            );
        }


        if (type === "blocked") {

            return (
                "चेतावनी। सड़क बंद है। " +
                "वर्तमान मार्ग उपलब्ध नहीं है। " +
                "वैकल्पिक मार्ग चुना जा रहा है।"
            );
        }


        if (type === "breakdown") {

            return (
                "चेतावनी। मार्ग पर वाहन खराब हो गया है। " +
                "वैकल्पिक मार्ग चुना जा रहा है।"
            );
        }
    }


    if (language === "ta-IN") {

        if (type === "traffic") {

            return (
                "எச்சரிக்கை. முன்னால் அதிக போக்குவரத்து உள்ளது. " +
                "மாற்று வழி தேர்வு செய்யப்படுகிறது."
            );
        }


        if (type === "blocked") {

            return (
                "எச்சரிக்கை. சாலை தடைப்பட்டுள்ளது. " +
                "தற்போதைய பாதை கிடைக்கவில்லை. " +
                "மாற்று பாதை தேர்வு செய்யப்படுகிறது."
            );
        }


        if (type === "breakdown") {

            return (
                "எச்சரிக்கை. வாகனம் பழுதடைந்துள்ளது. " +
                "மாற்று பாதை தேர்வு செய்யப்படுகிறது."
            );
        }
    }


    if (language === "kn-IN") {

        if (type === "traffic") {

            return (
                "ಎಚ್ಚರಿಕೆ. ಮುಂದೆ ಹೆಚ್ಚಿನ ಟ್ರಾಫಿಕ್ ಇದೆ. " +
                "ಪರ್ಯಾಯ ಮಾರ್ಗವನ್ನು ಆಯ್ಕೆ ಮಾಡಲಾಗುತ್ತಿದೆ."
            );
        }


        if (type === "blocked") {

            return (
                "ಎಚ್ಚರಿಕೆ. ರಸ್ತೆ ಬಂದ್ ಆಗಿದೆ. " +
                "ಪ್ರಸ್ತುತ ಮಾರ್ಗ ಲಭ್ಯವಿಲ್ಲ. " +
                "ಪರ್ಯಾಯ ಮಾರ್ಗವನ್ನು ಆಯ್ಕೆ ಮಾಡಲಾಗುತ್ತಿದೆ."
            );
        }


        if (type === "breakdown") {

            return (
                "ಎಚ್ಚರಿಕೆ. ಮಾರ್ಗದಲ್ಲಿ ವಾಹನ ಕೆಟ್ಟುಹೋಗಿದೆ. " +
                "ಪರ್ಯಾಯ ಮಾರ್ಗವನ್ನು ಆಯ್ಕೆ ಮಾಡಲಾಗುತ್ತಿದೆ."
            );
        }
    }


    return "";
}


/* =========================================================
   ALTERNATE ROUTE VOICE
========================================================= */

function getAlternateRouteMessage(
    type,
    alternate
) {

    const language =
        selectedLanguage || "en-IN";


    const route =
        alternate.route.join(", ");


    if (language === "en-IN") {

        let message =
            "Alternate route selected. " +
            `The new route is ${route}. ` +
            `Estimated distance is ${alternate.distance}. ` +
            `Estimated travel time is ${alternate.time}. `;


        if (type === "traffic") {

            message +=
                "This route avoids the high traffic area.";
        }


        if (type === "blocked") {

            message +=
                "This route avoids the blocked road.";
        }


        if (type === "breakdown") {

            message +=
                "This route avoids the affected vehicle.";
        }


        return message;
    }


    if (language === "te-IN") {

        return (
            "ప్రత్యామ్నాయ మార్గం ఎంచుకోబడింది. " +
            `కొత్త మార్గం ${route}. ` +
            `దూరం ${alternate.distance}. ` +
            `అంచనా ప్రయాణ సమయం ${alternate.time}.`
        );
    }


    if (language === "hi-IN") {

        return (
            "वैकल्पिक मार्ग चुना गया है। " +
            `नया मार्ग ${route} है। ` +
            `दूरी ${alternate.distance} है।`
        );
    }


    if (language === "ta-IN") {

        return (
            "மாற்று பாதை தேர்வு செய்யப்பட்டுள்ளது. " +
            `புதிய பாதை ${route}. ` +
            `தூரம் ${alternate.distance}.`
        );
    }


    if (language === "kn-IN") {

        return (
            "ಪರ್ಯಾಯ ಮಾರ್ಗವನ್ನು ಆಯ್ಕೆ ಮಾಡಲಾಗಿದೆ. " +
            `ಹೊಸ ಮಾರ್ಗ ${route}. ` +
            `ದೂರ ${alternate.distance}.`
        );
    }


    return "";
}


/* =========================================================
   VOICE ENGINE
========================================================= */


function loadVoices() {
    if (!("speechSynthesis" in window)) {
        availableVoices = [];
        return;
    }

    availableVoices = window.speechSynthesis.getVoices() || [];
}

function findBestVoice(languageCode) {
    if (!("speechSynthesis" in window) || !languageCode) {
        return null;
    }

    loadVoices();

    if (!availableVoices || availableVoices.length === 0) {
        return null;
    }

    const requested = languageCode.toLowerCase();
    const baseLanguage = requested.split("-")[0];

    // 1. Exact language match, for example te-IN
    let voice = availableVoices.find(v =>
        v.lang && v.lang.toLowerCase() === requested
    );

    if (voice) {
        return voice;
    }

    // 2. Same language match, for example te-IN or te-US
    voice = availableVoices.find(v =>
        v.lang &&
        v.lang.toLowerCase().split("-")[0] === baseLanguage
    );

    return voice || null;
}


function speak(text) {

    if (!text) return;


    if (!("speechSynthesis" in window)) {
        return;
    }


    if (!selectedLanguage) {

        showLanguageModal();

        return;
    }


    window.speechSynthesis.cancel();


    const message =
        new SpeechSynthesisUtterance(text);


    message.lang =
        selectedLanguage;


    message.rate =
        0.9;


    message.pitch =
        1;


    const matchingVoice =
        findBestVoice(
            selectedLanguage
        );


    if (matchingVoice) {

        message.voice =
            matchingVoice;
    }


    updateVoiceStatus(
        "🔊 Speaking..."
    );


    message.onend =
        function () {

            updateVoiceStatus(
                "🎙 Voice Assistant Ready"
            );
        };


    message.onerror =
        function () {

            updateVoiceStatus(
                "⚠️ Voice unavailable"
            );
        };


    window.speechSynthesis.speak(
        message
    );
}


function stopVoice() {

    if (
        "speechSynthesis" in window
    ) {

        window.speechSynthesis.cancel();
    }


    if (incidentTimer) {

        clearTimeout(
            incidentTimer
        );

        incidentTimer = null;
    }


    updateVoiceStatus(
        "🔇 Voice stopped"
    );
}


function updateVoiceStatus(message) {

    const status =
        document.getElementById(
            "voiceStatus"
        );


    if (status) {

        status.textContent =
            message;
    }
}


/* =========================================================
   ROUTE NAME
========================================================= */

function getLocationName(
    location,
    language
) {

    if (language === "te-IN") {

        if (location === "Warehouse")
            return "వేర్‌హౌస్";
    }


    if (language === "hi-IN") {

        if (location === "Warehouse")
            return "वेयरहाउस";
    }


    if (language === "ta-IN") {

        if (location === "Warehouse")
            return "கிடங்கு";
    }


    if (language === "kn-IN") {

        if (location === "Warehouse")
            return "ಗೋದಾಮು";
    }


    return location;
}


function getVehicleName(
    vehicle,
    language
) {

    if (language === "te-IN")
        return vehicle.replace(
            "Vehicle",
            "వాహనం"
        );

    if (language === "hi-IN")
        return vehicle.replace(
            "Vehicle",
            "वाहन"
        );

    if (language === "ta-IN")
        return vehicle.replace(
            "Vehicle",
            "வாகனம்"
        );

    if (language === "kn-IN")
        return vehicle.replace(
            "Vehicle",
            "ವಾಹನ"
        );

    return vehicle;
}


/* =========================================================
   MAP INITIALIZATION
========================================================= */

function initializeMap() {

    const mapElement =
        document.getElementById(
            "routeMap"
        );


    if (
        !mapElement ||
        typeof L === "undefined"
    ) {

        console.error(
            "Leaflet map could not be initialized."
        );

        return;
    }


    routeMap =
        L.map(
            "routeMap"
        ).setView(
            [17.3950, 78.4867],
            13
        );


    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            attribution:
                "&copy; OpenStreetMap contributors"
        }
    ).addTo(routeMap);


    addMapMarkers();


    drawVehicleRoutes();


    optimizeAllVehicles();
}


/* =========================================================
   MAP MARKERS
========================================================= */

function addMapMarkers() {

    Object.entries(
        mapLocations
    ).forEach(
        ([name, coordinates]) => {

            const isWarehouse =
                name === "Warehouse";


            const icon =
                L.divIcon({

                    className:
                        "quantum-base-marker",

                    html: `
                        <div
                            style="
                                width:38px;
                                height:38px;
                                display:flex;
                                align-items:center;
                                justify-content:center;
                                font-size:28px;
                                background:white;
                                border-radius:50%;
                                border:2px solid #6b4bb6;
                                box-shadow:0 3px 10px rgba(0,0,0,.25);
                            "
                        >
                            ${
                                isWarehouse
                                    ? "🏭"
                                    : "📍"
                            }
                        </div>
                    `,

                    iconSize:
                        [40, 40],

                    iconAnchor:
                        [20, 20]
                });


            L.marker(
                coordinates,
                { icon }
            )
            .addTo(routeMap)
            .bindPopup(
                `<strong>${name}</strong>`
            );
        }
    );
}


/* =========================================================
   ROUTE COORDINATES
========================================================= */

function getRouteCoordinates(route) {

    return route
        .map(
            location => {

                if (
                    location === "DEPOT"
                ) {

                    return mapLocations.Warehouse;
                }


                return mapLocations[
                    location
                ];
            }
        )
        .filter(Boolean);
}


/* =========================================================
   DRAW VEHICLE ROUTES
========================================================= */

function drawVehicleRoutes() {

    if (!routeMap) return;


    routeLayers.forEach(
        layer => {

            if (
                routeMap.hasLayer(
                    layer
                )
            ) {

                routeMap.removeLayer(
                    layer
                );
            }
        }
    );


    routeLayers = [];


    const routesToDraw =
        Object.keys(
            optimizedVehicleRoutes
        ).length > 0
            ? optimizedVehicleRoutes
            : vehicleRoutes;


    Object.entries(
        routesToDraw
    ).forEach(
        ([vehicle, route]) => {

            const coordinates =
                getRouteCoordinates(
                    route
                );


            if (
                coordinates.length < 2
            ) {

                return;
            }


            const line =
                L.polyline(
                    coordinates,
                    {

                        weight:
                            5,

                        opacity:
                            0.80,

                        lineJoin:
                            "round",

                        lineCap:
                            "round"

                    }
                )
                .addTo(routeMap);


            line.bindPopup(
                `<strong>${vehicle}</strong><br>
                 🧠 Quantum Optimized<br>
                 ${route.join(" → ")}`
            );


            routeLayers.push(
                line
            );
        }
    );
}


/* =========================================================
   CREATE MOVING VEHICLE ICON
========================================================= */

function createVehicleIcon(
    vehicle
) {

    const emoji =
        vehicleIcons[
            vehicle
        ] || "🚚";


    return L.divIcon({

        className:
            "moving-vehicle-marker",

        html: `
            <div
                style="
                    width:46px;
                    height:46px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    background:white;
                    border:3px solid #6b4bb6;
                    border-radius:50%;
                    box-shadow:0 4px 14px rgba(0,0,0,.35);
                    font-size:29px;
                    transition:transform 0.1s linear;
                "
                title="${vehicle}"
            >
                ${emoji}
            </div>
        `,

        iconSize:
            [46, 46],

        iconAnchor:
            [23, 23]
    });
}


/* =========================================================
   CREATE VEHICLE MARKER
========================================================= */

function createVehicleMarker(
    vehicle,
    coordinates
) {

    if (!routeMap) return null;


    const marker =
        L.marker(
            coordinates,
            {

                icon:
                    createVehicleIcon(
                        vehicle
                    ),

                zIndexOffset:
                    5000
            }
        )
        .addTo(routeMap);


    marker.bindPopup(
        `<strong>${vehicle}</strong><br>
         🚚 Vehicle in motion`
    );


    vehicleMarkers[
        vehicle
    ] = marker;


    return marker;
}


/* =========================================================
   CONVERT LAT/LNG TO DISTANCE
========================================================= */

function distanceBetweenPoints(
    p1,
    p2
) {

    const latDifference =
        p2[0] - p1[0];

    const lngDifference =
        p2[1] - p1[1];


    return Math.sqrt(
        latDifference *
        latDifference
        +
        lngDifference *
        lngDifference
    );
}


/* =========================================================
   MOVE VEHICLE BETWEEN TWO POINTS
========================================================= */

function animateVehicleSegment(
    vehicle,
    start,
    end,
    onComplete
) {

    if (!routeMap) return;


    const marker =
        vehicleMarkers[
            vehicle
        ];


    if (!marker) return;


    const startLat =
        start[0];

    const startLng =
        start[1];

    const endLat =
        end[0];

    const endLng =
        end[1];


    const distance =
        distanceBetweenPoints(
            start,
            end
        );


    /*
       Longer distance = longer animation.
       Minimum 3 seconds.
    */

    const duration =
        Math.max(
            3000,
            Math.min(
                9000,
                distance *
                900000
            )
        );


    const startTime =
        performance.now();


    function animate(
        currentTime
    ) {

        if (
            !animationRunning
        ) {

            return;
        }


        const elapsed =
            currentTime -
            startTime;


        let progress =
            elapsed /
            duration;


        if (progress > 1) {

            progress = 1;
        }


        /*
           Smooth movement.
        */

        const smoothProgress =
            progress *
            progress *
            (
                3 -
                2 *
                progress
            );


        const currentLat =
            startLat +
            (
                endLat -
                startLat
            ) *
            smoothProgress;


        const currentLng =
            startLng +
            (
                endLng -
                startLng
            ) *
            smoothProgress;


        marker.setLatLng(
            [
                currentLat,
                currentLng
            ]
        );


        if (
            progress < 1
        ) {

            animationFrames[
                vehicle
            ] =
                requestAnimationFrame(
                    animate
                );

        } else {

            if (
                typeof onComplete ===
                "function"
            ) {

                onComplete();
            }
        }
    }


    animationFrames[
        vehicle
    ] =
        requestAnimationFrame(
            animate
        );
}


/* =========================================================
   MOVE VEHICLE THROUGH COMPLETE ROUTE
========================================================= */

function animateVehicleRoute(
    vehicle,
    route,
    index = 0
) {

    if (!animationRunning)
        return;


    if (
        !route ||
        route.length < 2
    ) {

        return;
    }


    if (
        index >=
        route.length - 1
    ) {

        /*
           Vehicle reached Depot.

           Wait briefly, then restart the route
           so the vehicle continuously moves.
        */

        setTimeout(
            () => {

                if (
                    animationRunning
                ) {

                    animateVehicleRoute(
                        vehicle,
                        route,
                        0
                    );
                }

            },
            1200
        );

        return;
    }


    const start =
        mapLocations[
            route[index]
        ];


    const end =
        mapLocations[
            route[index + 1]
        ];


    if (
        !start ||
        !end
    ) {

        return;
    }


    animateVehicleSegment(
        vehicle,
        start,
        end,
        () => {

            if (
                !animationRunning
            ) {

                return;
            }


            animateVehicleRoute(
                vehicle,
                route,
                index + 1
            );
        }
    );
}


/* =========================================================
   START VEHICLE ANIMATION
========================================================= */

function startVehicleAnimation() {

    if (!routeMap) return;


    stopVehicleAnimation();


    animationRunning = true;


    const routesToAnimate =
        Object.keys(
            optimizedVehicleRoutes
        ).length > 0
            ? optimizedVehicleRoutes
            : vehicleRoutes;


    Object.entries(
        routesToAnimate
    ).forEach(
        ([vehicle, route]) => {

            const coordinates =
                getRouteCoordinates(
                    route
                );


            if (
                coordinates.length < 2
            ) {

                return;
            }


            createVehicleMarker(
                vehicle,
                coordinates[0]
            );


            animateVehicleRoute(
                vehicle,
                route,
                0
            );
        }
    );


    console.log(
        "🚚 Vehicle movement started."
    );
}


/* =========================================================
   STOP VEHICLE ANIMATION
========================================================= */

function stopVehicleAnimation() {

    animationRunning =
        false;


    Object.values(
        animationFrames
    ).forEach(
        frame => {

            cancelAnimationFrame(
                frame
            );
        }
    );


    animationFrames = {};


    Object.values(
        vehicleMarkers
    ).forEach(
        marker => {

            if (
                routeMap &&
                routeMap.hasLayer(
                    marker
                )
            ) {

                routeMap.removeLayer(
                    marker
                );
            }
        }
    );


    vehicleMarkers = {};
}


/* =========================================================
   RESTART VEHICLE ANIMATION
========================================================= */

function restartVehicleAnimation() {

    stopVehicleAnimation();


    setTimeout(
        () => {

            startVehicleAnimation();

        },
        300
    );
}


/* =========================================================
   BACKEND LOCATIONS
========================================================= */

function buildBackendLocations(
    route
) {

    const locations = [];


    route.forEach(
        location => {

            if (
                location ===
                    "Warehouse" ||
                location ===
                    "DEPOT"
            ) {

                return;
            }


            if (
                !locationData[
                    location
                ]
            ) {

                return;
            }


            locations.push(
                locationData[
                    location
                ]
            );
        }
    );


    return locations;
}


/* =========================================================
   BACKEND DELIVERIES
========================================================= */

function buildBackendDeliveries(
    route
) {

    return route
        .filter(
            location =>
                location !==
                    "Warehouse" &&
                location !==
                    "DEPOT"
        )
        .map(
            location => ({

                location_id:
                    location,

                demand:
                    locationData[
                        location
                    ]?.demand || 0

            })
        );
}


/* =========================================================
   OPTIMIZE ONE VEHICLE
========================================================= */

async function optimizeVehicle(
    vehicle,
    originalRoute
) {

    const locations =
        buildBackendLocations(
            originalRoute
        );


    const deliveries =
        buildBackendDeliveries(
            originalRoute
        );


    if (
        locations.length === 0
    ) {

        return null;
    }


    const payload = {

        vehicle_id:
            vehicle,

        vehicle_capacity:
            vehicleCapacity,

        capacity:
            vehicleCapacity,

        depot_id:
            "DEPOT",

        locations:
            locations,

        deliveries:
            deliveries
    };


    try {

        const response =
            await fetch(
                "http://127.0.0.1:5000/api/optimize",
                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            payload
                        )
                }
            );


        if (
            !response.ok
        ) {

            throw new Error(
                `Optimization API returned ${response.status}`
            );
        }


        const result =
            await response.json();


        if (
            !result ||
            !result.success
        ) {

            throw new Error(
                "Optimization failed"
            );
        }


        let optimizedRoute =
            result.quantum?.route;


        if (
            !optimizedRoute ||
            optimizedRoute.length < 2
        ) {

            optimizedRoute =
                result.classical?.route;
        }


        if (
            !optimizedRoute ||
            optimizedRoute.length < 2
        ) {

            throw new Error(
                "No optimized route returned"
            );
        }


        optimizedRoute =
            optimizedRoute.map(
                location =>
                    location ===
                        "DEPOT"
                        ? "Warehouse"
                        : location
            );


        return {

            route:
                optimizedRoute,

            result:
                result

        };

    } catch (error) {

        console.warn(
            `Optimization failed for ${vehicle}:`,
            error
        );


        return null;
    }
}


/* =========================================================
   OPTIMIZE ALL VEHICLES
========================================================= */

async function optimizeAllVehicles() {

    console.log(
        "🧠 Optimizing vehicle routes..."
    );


    /*
       Stop current vehicle movement
       while routes are changing.
    */

    stopVehicleAnimation();


    optimizedVehicleRoutes = {};


    const vehicleEntries =
        Object.entries(
            vehicleRoutes
        );


    for (
        const [vehicle, route]
        of vehicleEntries
    ) {

        const optimized =
            await optimizeVehicle(
                vehicle,
                route
            );


        if (optimized) {

            optimizedVehicleRoutes[
                vehicle
            ] =
                optimized.route;


            console.log(
                `✅ ${vehicle}:`,
                optimized.route
            );
        }
    }


    drawVehicleRoutes();


    fitMapToRoutes();


    /*
       IMPORTANT:
       Start actual moving vehicles
       AFTER optimized routes are ready.
    */

    startVehicleAnimation();
}


/* =========================================================
   FIT MAP TO ROUTES
========================================================= */

function fitMapToRoutes() {

    if (!routeMap) return;


    const allCoordinates = [];


    const routes =
        Object.keys(
            optimizedVehicleRoutes
        ).length > 0
            ? optimizedVehicleRoutes
            : vehicleRoutes;


    Object.values(
        routes
    ).forEach(
        route => {

            allCoordinates.push(
                ...getRouteCoordinates(
                    route
                )
            );
        }
    );


    if (
        allCoordinates.length < 2
    ) {

        return;
    }


    const bounds =
        L.latLngBounds(
            allCoordinates
        );


    routeMap.fitBounds(
        bounds,
        {
            padding:
                [40, 40]
        }
    );
}


/* =========================================================
   INCIDENT MARKER
========================================================= */

function addIncidentMarker(
    locationName,
    type
) {

    if (!routeMap) return;


    const coordinates =
        mapLocations[
            locationName
        ];


    if (!coordinates) return;


    const icons = {

        traffic:
            "🚦",

        blocked:
            "🚧",

        breakdown:
            "🚨"
    };


    const titles = {

        traffic:
            "HIGH TRAFFIC",

        blocked:
            "ROAD BLOCKED",

        breakdown:
            "VEHICLE BREAKDOWN"
    };


    const icon =
        L.divIcon({

            className:
                "quantum-incident-marker",

            html: `
                <div
                    style="
                        width:50px;
                        height:50px;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        font-size:32px;
                        background:white;
                        border:3px solid #dc2626;
                        border-radius:50%;
                        box-shadow:0 4px 14px rgba(0,0,0,.35);
                        position:relative;
                        z-index:9999;
                    "
                >
                    ${icons[type]}

                    <span
                        style="
                            position:absolute;
                            top:-27px;
                            left:50%;
                            transform:translateX(-50%);
                            background:#dc2626;
                            color:white;
                            padding:3px 7px;
                            border-radius:5px;
                            font-size:10px;
                            font-weight:700;
                            white-space:nowrap;
                        "
                    >
                        ${titles[type]}
                    </span>
                </div>
            `,

            iconSize:
                [50, 50],

            iconAnchor:
                [25, 25],

            popupAnchor:
                [0, -25]
        });


    const marker =
        L.marker(
            coordinates,
            {

                icon,

                zIndexOffset:
                    10000
            }
        )
        .addTo(routeMap);


    marker.bindPopup(
        `<strong>
            ${getIncidentTitle(type)}
        </strong><br>
        Location: ${locationName}`
    );


    marker.openPopup();


    incidentLayers.push(
        marker
    );
}


/* =========================================================
   INCIDENT TITLE
========================================================= */

function getIncidentTitle(type) {

    if (
        type === "traffic"
    ) {

        return "🚦 High Traffic";
    }


    if (
        type === "blocked"
    ) {

        return "🚧 Road Blocked";
    }


    if (
        type === "breakdown"
    ) {

        return "🚨 Vehicle Breakdown";
    }


    return "Route Incident";
}


/* =========================================================
   INCIDENT MESSAGE
========================================================= */

function addIncidentMessage(
    type,
    alternate
) {

    const incidentList =
        document.getElementById(
            "incidentList"
        );


    if (!incidentList) return;


    incidentList.innerHTML = `

        <div class="
            incident-item
            ${type}
        ">

            <div class="incident-title">

                ${getIncidentTitle(type)}

            </div>


            <div class="
                incident-description
            ">

                <strong>
                    🔄 Alternate Route:
                </strong>

                ${alternate.route.join(
                    " → "
                )}

                <br><br>

                <strong>
                    Distance:
                </strong>

                ${alternate.distance}

                <br>

                <strong>
                    Estimated Time:
                </strong>

                ${alternate.time}

            </div>

        </div>
    `;
}


/* =========================================================
   ANNOUNCE INCIDENT
========================================================= */

function announceIncident(type) {

    const warning =
        getVoiceMessage(type);


    if (!warning) return;


    speak(warning);


    if (incidentTimer) {

        clearTimeout(
            incidentTimer
        );
    }


    incidentTimer =
        setTimeout(
            () => {

                showAlternateRoute(
                    type
                );

            },
            4000
        );
}


/* =========================================================
   SHOW ALTERNATE ROUTE
========================================================= */

function showAlternateRoute(type) {

    const alternate =
        alternateRoutes[
            type
        ];


    if (!alternate) {

        console.error(
            "No alternate route found:",
            type
        );

        return;
    }


    /*
       Stop normal vehicle animation
       while alternate route is displayed.
    */

    stopVehicleAnimation();


    drawAlternateRoute(
        alternate.route
    );


    addIncidentMessage(
        type,
        alternate
    );


    /*
       Put one vehicle on the alternate route.

       For demo purposes the first vehicle
       is redirected.
    */

    const affectedVehicle =
        "Vehicle 01";


    const alternateRoute =
        alternate.route;


    const coordinates =
        getRouteCoordinates(
            alternateRoute
        );


    if (
        coordinates.length >= 2
    ) {

        createVehicleMarker(
            affectedVehicle,
            coordinates[0]
        );


        animationRunning =
            true;


        animateVehicleRoute(
            affectedVehicle,
            alternateRoute,
            0
        );
    }


    const message =
        getAlternateRouteMessage(
            type,
            alternate
        );


    setTimeout(
        () => {

            speak(message);

        },
        300
    );
}


/* =========================================================
   DRAW ALTERNATE ROUTE
========================================================= */

function drawAlternateRoute(
    route
) {

    if (!routeMap) return;


    if (
        alternateRouteLayer
    ) {

        routeMap.removeLayer(
            alternateRouteLayer
        );

        alternateRouteLayer =
            null;
    }


    const coordinates =
        getRouteCoordinates(
            route
        );


    if (
        coordinates.length < 2
    ) {

        return;
    }


    alternateRouteLayer =
        L.polyline(
            coordinates,
            {

                weight:
                    8,

                opacity:
                    0.95,

                dashArray:
                    "12, 8"

            }
        )
        .addTo(routeMap);


    alternateRouteLayer.bindPopup(
        `<strong>
            🔄 Alternate Route
        </strong><br>
        ${route.join(" → ")}`
    );


    routeMap.fitBounds(
        alternateRouteLayer.getBounds(),
        {
            padding:
                [40, 40]
        }
    );
}


/* =========================================================
   HIGH TRAFFIC
========================================================= */

function demoTraffic() {

    clearPreviousIncident();


    addIncidentMarker(
        "B",
        "traffic"
    );


    announceIncident(
        "traffic"
    );
}


/* =========================================================
   ROAD BLOCK
========================================================= */

function demoRoadBlock() {

    clearPreviousIncident();


    addIncidentMarker(
        "C",
        "blocked"
    );


    announceIncident(
        "blocked"
    );
}


/* =========================================================
   VEHICLE BREAKDOWN
========================================================= */

function demoBreakdown() {

    clearPreviousIncident();


    addIncidentMarker(
        "D",
        "breakdown"
    );


    announceIncident(
        "breakdown"
    );
}


/* =========================================================
   CLEAR INCIDENT
========================================================= */

function clearPreviousIncident() {

    if (
        "speechSynthesis" in window
    ) {

        window.speechSynthesis.cancel();
    }


    if (
        incidentTimer
    ) {

        clearTimeout(
            incidentTimer
        );

        incidentTimer =
            null;
    }


    incidentLayers.forEach(
        marker => {

            if (
                routeMap &&
                routeMap.hasLayer(
                    marker
                )
            ) {

                routeMap.removeLayer(
                    marker
                );
            }
        }
    );


    incidentLayers = [];


    if (
        alternateRouteLayer &&
        routeMap
    ) {

        routeMap.removeLayer(
            alternateRouteLayer
        );

        alternateRouteLayer =
            null;
    }


    /*
       Restart normal vehicle routes.
    */

    restartVehicleAnimation();
}


/* =========================================================
   CLEAR WARNINGS
========================================================= */

function clearWarnings() {

    clearPreviousIncident();


    const incidentList =
        document.getElementById(
            "incidentList"
        );


    if (incidentList) {

        incidentList.innerHTML = `

            <div class="incident-item">

                <div class="incident-title">

                    No active warnings

                </div>

                <div class="
                    incident-description
                ">

                    All monitored routes
                    are currently clear.

                </div>

            </div>
        `;
    }


    updateVoiceStatus(
        "🎙 Voice Assistant Ready"
    );
}


/* =========================================================
   EXPLAIN ALL ROUTES
========================================================= */

function speakCompleteNetwork() {

    /*
       Voice is incident-based.
       Do not speak the normal routes.
    */

    updateVoiceStatus(
        "🎙 Voice Assistant Ready"
    );
}


/* =========================================================
   BROWSER VOICE EVENT
========================================================= */

if (
    "speechSynthesis" in window
) {

    window.speechSynthesis.onvoiceschanged =
        function () {

            loadVoices();

        };
}


/* =========================================================
   PAGE LOAD
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        loadVoices();

        loadSavedLanguage();

        initializeMap();

        updateVoiceStatus(
            "🎙 Voice Assistant Ready"
        );
    }
);


/* =========================================================
   GLOBAL FUNCTIONS
========================================================= */

window.selectVoiceLanguage =
    selectVoiceLanguage;


window.changeVoiceLanguage =
    changeVoiceLanguage;


window.speakCompleteNetwork =
    speakCompleteNetwork;


window.stopVoice =
    stopVoice;


window.demoTraffic =
    demoTraffic;


window.demoRoadBlock =
    demoRoadBlock;


window.demoBreakdown =
    demoBreakdown;


window.clearWarnings =
    clearWarnings;


/*
   Optional controls if you want to call them
   from the browser console later.
*/

window.startVehicleAnimation =
    startVehicleAnimation;


window.stopVehicleAnimation =
    stopVehicleAnimation;


window.restartVehicleAnimation =
    restartVehicleAnimation;