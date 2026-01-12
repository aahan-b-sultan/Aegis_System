let isScanning = false;
let scanInterval = null;

// Initialize Plotly Heatmap
const layout = {
    paper_bgcolor: '#000000',
    plot_bgcolor: '#000000',
    margin: { t: 0, b: 0, l: 0, r: 0 },
    xaxis: { showgrid: false, zeroline: false, showticklabels: false },
    yaxis: { showgrid: false, zeroline: false, showticklabels: false },
    coloraxis: { showscale: false }
};

Plotly.newPlot('radar-heatmap', [{
    z: [[0,0],[0,0]], 
    type: 'heatmap',
    colorscale: 'Viridis' 
}], layout, {displayModeBar: false});


// --- SCENARIO LOGIC ---

async function loadScenario(type) {
    addLog(`System: Loading ${type.toUpperCase()} protocols...`);
    const statusDiv = document.getElementById('scenario-status');
    statusDiv.innerText = "Connecting to Virtual Sensor...";
    statusDiv.className = "mt-4 text-xs text-slate-500 italic text-center";
    
    try {
        const res = await fetch(`/api/v1/radar/load-scenario/${type}`, { method: 'POST' });
        const data = await res.json();
        
        if (res.ok) {
            statusDiv.innerText = `LINK ESTABLISHED: ${type.toUpperCase()} DATASET`;
            // Cyan for Success
            statusDiv.className = "mt-4 text-xs text-[#45E3FF] italic text-center font-bold shadow-cyan-500/50";
            addLog(`Success: Connected to ${type.toUpperCase()} stream.`);
        } else {
            throw new Error(data.detail);
        }
    } catch (e) {
        statusDiv.innerText = "ERROR: DATA LINK FAILED";
        statusDiv.className = "mt-4 text-xs text-[#FF7582] italic text-center";
        addLog(`Error: ${e.message}`, true);
    }
}

async function loadRandom() {
    addLog(`System: Initiating BLIND TEST sequence...`);
    const statusDiv = document.getElementById('scenario-status');
    statusDiv.innerText = "SEARCHING FOR SIGNAL...";
    // Purple for Mystery
    statusDiv.className = "mt-4 text-xs text-[#A163F7] italic text-center animate-pulse";
    
    try {
        const res = await fetch(`/api/v1/radar/load-random`, { method: 'POST' });
        const data = await res.json();
        
        if (res.ok) {
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

// --- RADAR CONTROL ---

function toggleRadar(active) {
    if (scanInterval) clearInterval(scanInterval); 

    isScanning = active;
    document.getElementById('btn-start').disabled = active;
    document.getElementById('btn-stop').disabled = !active;
    
    if (active) {
        addLog("Radar: Scan Sequence Initiated.");
        scanInterval = setInterval(fetchFrame, 250); 
    } else {
        addLog("Radar: Sequence Halted.");
        clearInterval(scanInterval);
    }
}

async function fetchFrame() {
    const start = performance.now();
    try {
        const res = await fetch('/api/v1/radar/scan');
        const data = await res.json();
        
        if (!res.ok) throw new Error(data.detail);

        Plotly.react('radar-heatmap', [{
            z: data.heatmap_data, 
            type: 'heatmap',
            colorscale: 'Inferno',
            zmin: 0,
            zmax: 1
        }], layout);

        updateDashboard(data);
        
        const lat = Math.round(performance.now() - start);
        document.getElementById('latency-val').innerText = `${lat} ms`;

    } catch (e) {
        console.error(e);
        toggleRadar(false); 
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

    if (data.is_threat) {
        // THREAT: Use Salmon Red (#FF7582)
        threatPanel.className = "mt-6 p-6 border-2 border-[#FF7582] bg-[#FF7582]/10 rounded-lg text-center shadow-[0_0_20px_rgba(255,117,130,0.4)]";
        labelDiv.className = "text-4xl font-bold mt-2 text-[#FF7582] drop-shadow-[0_0_5px_rgba(255,117,130,0.8)]";
        confBar.className = "h-full bg-[#FF7582] w-0 transition-all duration-300";
    } else {
        // SAFE: Use Cyan (#45E3FF)
        threatPanel.className = "mt-6 p-6 border-2 border-[#45E3FF] bg-[#45E3FF]/10 rounded-lg text-center shadow-[0_0_20px_rgba(69,227,255,0.4)]";
        labelDiv.className = "text-4xl font-bold mt-2 text-[#45E3FF] drop-shadow-[0_0_5px_rgba(69,227,255,0.8)]";
        confBar.className = "h-full bg-[#45E3FF] w-0 transition-all duration-300";
    }
}

function addLog(msg, isError = false) {
    const logs = document.getElementById('logs');
    if (logs) {
        const entry = document.createElement('div');
        const time = new Date().toLocaleTimeString('en-US', {hour12: false});
        // Error = Red, Info = Muted
        const colorClass = isError ? 'text-[#FF7582]' : 'text-slate-400';
        entry.innerHTML = `<span class="opacity-50">[${time}]</span> <span class="${colorClass}">${msg}</span>`;
        logs.prepend(entry);
    }
}

// --- FILE UPLOAD LISTENER ---
const uploadInput = document.getElementById('manual-upload');
if (uploadInput) {
    uploadInput.addEventListener('change', async function(e) {
        if (e.target.files.length === 0) return;
        
        const file = e.target.files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        addLog(`System: Uploading external file: ${file.name}...`);
        const statusDiv = document.getElementById('scenario-status');
        statusDiv.innerText = "UPLOADING...";
        
        try {
            const res = await fetch('/api/v1/radar/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            
            if (res.ok) {
                statusDiv.innerText = "EXTERNAL SOURCE LOCKED";
                statusDiv.className = "mt-4 text-xs text-[#6F88FC] italic text-center font-bold";
                addLog("Radar: External data stream active.");
            } else {
                throw new Error(data.detail);
            }
        } catch (e) {
            statusDiv.innerText = "UPLOAD ERROR";
            addLog(`Error: ${e.message}`, true);
        }
        e.target.value = '';
    });
}

// --- HISTORY MODAL ---
function toggleHistory(show) {
    const modal = document.getElementById('history-modal');
    if (show) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        loadHistoryData();
    } else {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

async function loadHistoryData() {
    const tbody = document.getElementById('history-body');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="6" class="p-4 text-center animate-pulse text-[#A163F7]">Loading encrypted logs...</td></tr>';
    
    try {
        const res = await fetch('/api/v1/radar/history');
        const data = await res.json();
        
        tbody.innerHTML = '';
        data.forEach(row => {
            // Fix Date format
            const date = new Date(row.timestamp).toLocaleString('en-GB', {
                day: 'numeric', month: 'short', year: 'numeric', 
                hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true 
            });

            // Use New Colors for Table
            const color = row.is_threat ? 'text-[#FF7582]' : 'text-[#45E3FF]';
            const status = row.is_threat ? 'THREAT' : 'CLEARED';
            const badgeStyle = row.is_threat 
                ? 'border-[#FF7582] text-[#FF7582] bg-[#FF7582]/10' 
                : 'border-[#45E3FF] text-[#45E3FF] bg-[#45E3FF]/10';

            tbody.innerHTML += `
                <tr class="hover:bg-slate-800 transition-colors border-b border-slate-800">
                    <td class="p-3 whitespace-nowrap text-slate-300">${date}</td>
                    <td class="p-3 text-xs text-slate-500 font-mono">${row.filename}</td>
                    <td class="p-3 ${color} font-bold tracking-wider">${row.target_class}</td>
                    <td class="p-3 text-slate-300">${row.confidence.toFixed(1)}%</td>
                    <td class="p-3">
                        <span class="border px-2 py-1 rounded text-[10px] font-bold ${badgeStyle}">
                            ${status}
                        </span>
                    </td>
                    <td class="p-3 text-right">
                        <a href="/api/v1/radar/report/${row.id}" target="_blank" class="text-[#6F88FC] hover:text-white text-xs border border-[#6F88FC] bg-[#6F88FC]/20 px-2 py-1 rounded transition-colors">
                            📄 PDF
                        </a>
                    </td>
                </tr>
            `;
        });
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-[#FF7582]">Connection Failed: ${e.message}</td></tr>`;
    }
}