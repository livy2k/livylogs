// LivyLogs Reports - Script for index page
// This file is loaded by index.html

async function loadReports() {
    try {
        const response = await fetch('reports.json');
        if (!response.ok) throw new Error('Failed to load reports');
        const reports = await response.json();
        return reports;
    } catch (e) {
        console.error('Error loading reports:', e);
        return [];
    }
}

async function renderReportList() {
    const container = document.getElementById('report-list');
    if (!container) return;
    
    const reports = await loadReports();
    
    if (reports.length === 0) {
        container.innerHTML = '<p class="loading">No reports yet. Use `/testreport` or `/gd001` in your Discord channel to generate one.</p>';
        return;
    }
    
    // Render each report as a card
    container.innerHTML = reports.map(report => {
        const statusClass = report.is_duplicate ? "badge-warning" : "badge-primary";
        const statusText = report.is_duplicate ? "DUPLICATE" : "TEMPORARY";
        const mvp = report.mvp || "N/A";
        const kills = report.kills || 0;
        const larp = report.potential_larp || 0;
        const timestamp = report.timestamp || "Unknown";
        const filename = report.filename || "";
        const title = report.title || report.name || "Unnamed Encounter";
        const url = report.url || `reports/${filename}`;

        return `
            <div class="report-card hud-border bg-black/40 rounded-lg p-4 cursor-pointer" onclick="window.open('${url}', '_blank')">
                <div class="flex justify-between items-start mb-3">
                    <div class="badge ${statusClass} badge-xs font-black">${statusText}</div>
                    <div class="text-[8px] font-black opacity-40 uppercase tracking-widest">${timestamp}</div>
                </div>
                <h3 class="text-lg font-orbitron font-black text-primary glow-text-blue truncate mb-2">${title}</h3>
                <div class="flex gap-4 text-[10px]">
                    <div>
                        <span class="opacity-40">MVP</span>
                        <span class="font-bold text-secondary">${mvp}</span>
                    </div>
                    <div>
                        <span class="opacity-40">KILLS</span>
                        <span class="font-bold">${kills}</span>
                    </div>
                    <div>
                        <span class="opacity-40">LARP</span>
                        <span class="font-bold text-accent">+${larp}</span>
                    </div>
                </div>
                <div class="mt-3 text-[8px] opacity-30 truncate">${filename}</div>
            </div>
        `;
    }).join("");
}

async function renderReport() {
    const params = new URLSearchParams(window.location.search);
    const filename = params.get('id');
    
    const titleEl = document.getElementById('report-title');
    const contentEl = document.getElementById('report-content');
    
    if (!filename || !contentEl) return;
    
    try {
        const response = await fetch(`reports/${filename}`);
        if (!response.ok) throw new Error('Report not found');
        const html = await response.text();
        
        if (titleEl) {
            titleEl.textContent = filename.replace(/_/g, ' ').replace('.html', '');
        }
        contentEl.innerHTML = html;
    } catch (e) {
        console.error('Error loading report:', e);
        if (contentEl) {
            contentEl.innerHTML = '<p class="text-error">Error loading report. The file may not exist yet.</p>';
        }
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
