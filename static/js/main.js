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
        threatPanel.className = "mt-6 p-6 border-2 border-[#FF7582] bg-[#FF7582]/10 rounded-lg text-center shadow-[0_0_20px_rgba(255,117,130,0.4)]";
        labelDiv.className = "text-4xl font-bold mt-2 text-[#FF7582] drop-shadow-[0_0_5px_rgba(255,117,130,0.8)]";
        confBar.className = "h-full bg-[#FF7582] w-0 transition-all duration-300";
    } else {
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
        const colorClass = isError ? 'text-[#FF7582]' : 'text-slate-400';
        entry.innerHTML = `<span class="opacity-50">[${time}]</span> <span class="${colorClass}">${msg}</span>`;
        logs.prepend(entry);
    }
}

// --- FILE UPLOAD ---
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
            const res = await fetch('/api/v1/radar/upload', { method: 'POST', body: formData });
            const data = await res.json();
            if (res.ok) {
                statusDiv.innerText = "EXTERNAL SOURCE LOCKED";
                statusDiv.className = "mt-4 text-xs text-[#6F88FC] italic text-center font-bold";
                addLog("Radar: External data stream active.");
            } else { throw new Error(data.detail); }
        } catch (e) {
            statusDiv.innerText = "UPLOAD ERROR";
            addLog(`Error: ${e.message}`, true);
        }
        e.target.value = '';
    });
}

// --- HISTORY MODAL LOGIC ---
function toggleHistory(show) {
    const modal = document.getElementById('history-modal');
    // Select the inner glass panel (first child)
    const panel = modal.firstElementChild; 

    if (show) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        
        // Add Animation
        panel.classList.add('modal-animate');
        
        loadHistoryData();
    } else {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        
        // Reset Animation so it can play again next time
        panel.classList.remove('modal-animate');
    }
}

async function loadHistoryData() {
    const tbody = document.getElementById('history-body');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="7" class="p-4 text-center animate-pulse text-[#A163F7]">Loading encrypted logs...</td></tr>';
    
    try {
        const res = await fetch('/api/v1/radar/history');
        const data = await res.json();
        
        tbody.innerHTML = '';
        data.forEach(row => {
            const date = new Date(row.timestamp).toLocaleString('en-GB', {
                day: 'numeric', month: 'short', year: 'numeric', 
                hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true 
            });

            const color = row.is_threat ? 'text-[#FF7582]' : 'text-[#45E3FF]';
            const status = row.is_threat ? 'THREAT' : 'CLEARED';
            const badgeStyle = row.is_threat 
                ? 'border-[#FF7582] text-[#FF7582] bg-[#FF7582]/10' 
                : 'border-[#45E3FF] text-[#45E3FF] bg-[#45E3FF]/10';

            // VERIFICATION COLUMN LOGIC
            const verifyCell = row.user_verified 
                ? `<span class="text-[#45E3FF] text-[10px] font-bold">✅ ${row.corrected_label}</span>`
                : `<button onclick="openFeedback(${row.id})" class="text-slate-400 hover:text-white text-[10px] border border-slate-600 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 transition-colors">❓ VERIFY</button>`;

            tbody.innerHTML += `
                <tr class="hover:bg-slate-800 transition-colors border-b border-slate-800">
                    <td class="p-3 whitespace-nowrap text-slate-300">${date}</td>
                    <td class="p-3 text-xs text-slate-500 font-mono">${row.filename}</td>
                    <td class="p-3 ${color} font-bold tracking-wider">${row.target_class}</td>
                    <td class="p-3 text-slate-300">${row.confidence.toFixed(1)}%</td>
                    <td class="p-3"><span class="border px-2 py-1 rounded text-[10px] font-bold ${badgeStyle}">${status}</span></td>
                    <td class="p-3 text-center">${verifyCell}</td>
                    <td class="p-3 text-right">
                        <a href="/api/v1/radar/report/${row.id}" target="_blank" class="text-[#6F88FC] hover:text-white text-xs border border-[#6F88FC] bg-[#6F88FC]/20 px-2 py-1 rounded transition-colors">📄 PDF</a>
                    </td>
                </tr>
            `;
        });
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="7" class="p-4 text-center text-[#FF7582]">Connection Failed: ${e.message}</td></tr>`;
    }
}

// --- FEEDBACK & ANALYTICS ---

function openFeedback(id) {
    document.getElementById('feedback-scan-id').value = id;
    document.getElementById('display-scan-id').innerText = "#" + id; // Show ID to user
    
    const modal = document.getElementById('feedback-modal');
    const panel = modal.firstElementChild; // The inner glass panel

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    panel.classList.add('modal-animate'); // Trigger pop-in animation
}

// Function to close the modal
function closeFeedback() {
    const modal = document.getElementById('feedback-modal');
    const panel = modal.firstElementChild;
    
    // Remove animation class
    panel.classList.remove('modal-animate');
    
    // Hide modal
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

// Function to close when clicking the black background
function closeFeedbackOutside(event) {
    // If the click target IS the background wrapper (id="feedback-modal"), close it.
    // (We prevented bubbling on the inner panel using event.stopPropagation() in HTML)
    if (event.target.id === 'feedback-modal') {
        closeFeedback();
    }
}

async function submitCorrection(label) {
    const id = document.getElementById('feedback-scan-id').value;
    try {
        await fetch('/api/v1/radar/feedback', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ scan_id: id, correct_label: label })
        });
        
        closeFeedback(); // Close modal on success
        loadHistoryData(); // Refresh table
    } catch(e) { 
        alert("Error saving feedback"); 
    }
}


function toggleAnalytics(show) {
    const modal = document.getElementById('analytics-modal');
    const panel = modal.firstElementChild;

    if (show) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        panel.classList.add('modal-animate'); // Animation
        loadAnalytics();
    } else {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        panel.classList.remove('modal-animate');
    }
}

async function loadAnalytics() {
    try {
        const res = await fetch('/api/v1/radar/stats');
        const data = await res.json();
        
        // 1. Pie Chart
        const pieData = [{
            values: [data.class_counts.DRONE, data.class_counts.CAR, data.class_counts.HUMAN],
            labels: ['Drone', 'Car', 'Human'],
            type: 'pie',
            marker: { colors: ['#FF7582', '#F59E0B', '#45E3FF'] }
        }];
        
        const layoutPie = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#94a3b8' },
            margin: { t:0, b:0, l:0, r:0 },
            showlegend: true
        };
        Plotly.newPlot('chart-pie', pieData, layoutPie, {displayModeBar: false});

        // 2. Bar Chart
        const barData = [{
            x: ['Threats', 'Safe'],
            y: [data.threats, data.total - data.threats],
            type: 'bar',
            marker: { color: ['#FF7582', '#45E3FF'] }
        }];
        
        const layoutBar = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#94a3b8' },
            margin: { t:20, b:30, l:30, r:20 },
            yaxis: { gridcolor: '#334155' }
        };
        Plotly.newPlot('chart-bar', barData, layoutBar, {displayModeBar: false});
        
    } catch(e) { console.error("Analytics Error:", e); }
}

// --- SECURITY LOGIC ---
function logout() {
    if(confirm("Confirm Session Termination?")) {
        // 1. Destroy the security token
        localStorage.removeItem('aegis_token');
        
        // 2. Redirect to the new Landing Page (Root)
        window.location.href = '/';
    }
}