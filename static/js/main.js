let isScanning = false;
let scanInterval = null;

// Initialize Plotly Heatmap
const layout = {
    paper_bgcolor: '#000000',
    plot_bgcolor: '#000000',
    margin: { t: 0, b: 0, l: 0, r: 0 },
    xaxis: { showgrid: false, zeroline: false, showticklabels: false },
    yaxis: { showgrid: false, zeroline: false, showticklabels: false },
    coloraxis: { showscale: false } // Hide colorbar for clean look
};

Plotly.newPlot('radar-heatmap', [{
    z: [[0,0],[0,0]], // Empty init
    type: 'heatmap',
    colorscale: 'Viridis'
}], layout, {displayModeBar: false});


// 1. Load Scenario
async function loadScenario(type) {
    addLog(`System: Loading ${type.toUpperCase()} protocols...`);
    const statusDiv = document.getElementById('scenario-status');
    statusDiv.innerText = "Connecting to Virtual Sensor...";
    
    try {
        const res = await fetch(`/api/v1/radar/load-scenario/${type}`, { method: 'POST' });
        const data = await res.json();
        
        if (res.ok) {
            statusDiv.innerText = `LINK ESTABLISHED: ${type.toUpperCase()} DATASET`;
            statusDiv.classList.add('text-emerald-500');
            addLog(`Success: Connected to ${type.toUpperCase()} stream.`);
        } else {
            throw new Error(data.detail);
        }
    } catch (e) {
        statusDiv.innerText = "ERROR: DATA LINK FAILED";
        statusDiv.classList.remove('text-emerald-500');
        addLog(`Error: ${e.message}`, true);
    }
}

// 2. Toggle Scanning
function toggleRadar(active) {
    isScanning = active;
    document.getElementById('btn-start').disabled = active;
    document.getElementById('btn-stop').disabled = !active;
    
    if (active) {
        addLog("Radar: Scan Sequence Initiated.");
        scanInterval = setInterval(fetchFrame, 500); // Poll every 500ms
    } else {
        addLog("Radar: Sequence Halted.");
        clearInterval(scanInterval);
    }
}

// 3. Fetch Frame from Backend
async function fetchFrame() {
    const start = performance.now();
    try {
        const res = await fetch('/api/v1/radar/scan');
        const data = await res.json();
        
        if (!res.ok) throw new Error(data.detail);

        // Update Heatmap
        Plotly.react('radar-heatmap', [{
            z: data.heatmap_data, // The matrix from Python
            type: 'heatmap',
            colorscale: 'Inferno',
            zmin: 0,
            zmax: 1
        }], layout);

        // Update UI
        updateDashboard(data);
        
        // Latency Calc
        const lat = Math.round(performance.now() - start);
        document.getElementById('latency-val').innerText = `${lat} ms`;

    } catch (e) {
        console.error(e);
        toggleRadar(false); // Stop if error
        addLog("Error: Signal Lost. " + e.message, true);
    }
}

function updateDashboard(data) {
    const labelDiv = document.getElementById('target-label');
    const confVal = document.getElementById('conf-val');
    const confBar = document.getElementById('conf-bar');
    const threatPanel = document.getElementById('threat-panel');

    labelDiv.innerText = data.target_class;
    confVal.innerText = data.confidence.toFixed(1) + "%";
    confBar.style.width = data.confidence + "%";

    // Threat Logic Styling
    if (data.is_threat) {
        threatPanel.className = "mt-6 p-6 border-2 border-red-600 bg-red-900/20 rounded-lg text-center shadow-[0_0_15px_rgba(220,38,38,0.5)]";
        labelDiv.classList.remove('text-slate-600');
        labelDiv.classList.add('text-red-500');
        confBar.className = "h-full bg-red-500 w-0 transition-all duration-300";
    } else {
        threatPanel.className = "mt-6 p-6 border-2 border-emerald-600 bg-emerald-900/20 rounded-lg text-center shadow-[0_0_15px_rgba(5,150,105,0.5)]";
        labelDiv.classList.remove('text-slate-600');
        labelDiv.classList.add('text-emerald-500');
        confBar.className = "h-full bg-emerald-500 w-0 transition-all duration-300";
    }
}

function addLog(msg, isError = false) {
    const logs = document.getElementById('logs');
    const entry = document.createElement('div');
    const time = new Date().toLocaleTimeString('en-US', {hour12: false});
    entry.innerHTML = `<span class="opacity-50">[${time}]</span> <span class="${isError ? 'text-red-400' : 'text-slate-300'}">${msg}</span>`;
    logs.prepend(entry);
}

// Add this new function
async function loadRandom() {
    addLog(`System: Initiating BLIND TEST sequence...`);
    const statusDiv = document.getElementById('scenario-status');
    statusDiv.innerText = "SEARCHING FOR SIGNAL...";
    statusDiv.className = "mt-4 text-xs text-purple-400 italic text-center animate-pulse";
    
    try {
        const res = await fetch(`/api/v1/radar/load-random`, { method: 'POST' });
        const data = await res.json();
        
        if (res.ok) {
            // It will say "INTERCEPTING UNKNOWN SIGNAL SOURCE..."
            statusDiv.innerText = data.details; 
            addLog(`Radar: Unknown signal locked. Ready to scan.`);
        } else {
            throw new Error(data.detail);
        }
    } catch (e) {
        statusDiv.innerText = "ERROR: INJECTION FAILED";
        addLog(`Error: ${e.message}`, true);
    }
}