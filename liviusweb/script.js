// Load reports from reports.json
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

// Render report list on index page
async function renderReportList() {
    const container = document.getElementById('report-list');
    if (!container) return;
    
    const reports = await loadReports();
    
    if (reports.length === 0) {
        container.innerHTML = '<p class="loading">No reports yet. Use `/testreport` or `/gd001` in Discord to generate one.</p>';
        return;
    }
    
    container.innerHTML = reports.map(report => `
        <div class="report-card" onclick="window.location.href='report.html?id=${encodeURIComponent(report.filename)}'">
            <h3>${report.title || 'Combat Report'}</h3>
            <div class="meta">
                <span>${report.timestamp || 'Unknown date'}</span>
                <span> • </span>
                <span>${report.author || 'Unknown Pilot'}</span>
            </div>
            <div class="stats">
                <span class="stat damage">⚔️ ${report.total_dmg?.toLocaleString() || '0'}</span>
                <span class="stat healing">💉 ${report.total_heal?.toLocaleString() || '0'}</span>
                <span class="stat kd">💀 ${report.total_kd || '0'}</span>
            </div>
        </div>
    `).join('');
}

// Load individual report on report page
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
        titleEl.textContent = filename.replace(/\.html$/, '').replace(/[_]/g, ' ');
        contentEl.innerHTML = `<iframe srcdoc="${escapeHtml(html)}"></iframe>`;
    } catch (e) {
        titleEl.textContent = 'Report Not Found';
        contentEl.innerHTML = `<p class="loading">The report "${filename}" could not be found. It may have been removed or the URL is incorrect.</p>`;
    }
}

// Helper to escape HTML for iframe srcdoc
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Run appropriate function based on page
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('report-list')) {
        renderReportList();
    }
    if (document.getElementById('report-content')) {
        renderReport();
    }
});
