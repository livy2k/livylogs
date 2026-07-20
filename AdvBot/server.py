"""
LivyLogs Reports Server for Wasmer Edge
Serves combat reports from GitHub repository with search and display functionality.
"""

import json
import os
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests

# Configuration
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "livy2k/livylogsv1")
GITHUB_BRANCH = "main"
PORT = int(os.environ.get("PORT", 8080))

class ReportHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        if path == "/" or path == "/index.html":
            self.serve_index()
        elif path == "/api/reports":
            self.serve_reports_list(params)
        elif path.startswith("/api/report/"):
            filename = path[len("/api/report/"):]
            self.serve_report_content(filename)
        elif path.startswith("/reports/"):
            # Serve raw report files from GitHub
            self.serve_github_file(path.lstrip("/"))
        elif path == "/api/search":
            self.serve_search(params)
        elif path == "/api/health":
            self.send_json({"status": "ok", "repo": GITHUB_REPO})
        else:
            self.send_error(404, "Not Found")
    
    def serve_index(self):
        """Serve the main HTML page."""
        html = self.get_index_html()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_reports_list(self, params):
        """Return list of reports from GitHub."""
        page = int(params.get("page", [1])[0])
        limit = int(params.get("limit", [20])[0])
        search = params.get("search", [""])[0]
        
        reports = self.fetch_reports_from_github()
        
        # Filter by search
        if search:
            search_lower = search.lower()
            reports = [r for r in reports if 
                      search_lower in r.get("title", "").lower() or
                      search_lower in r.get("author", "").lower() or
                      search_lower in r.get("filename", "").lower()]
        
        # Sort by timestamp (newest first)
        reports.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
        
        # Paginate
        total = len(reports)
        start = (page - 1) * limit
        end = start + limit
        page_reports = reports[start:end]
        
        self.send_json({
            "status": "success",
            "reports": page_reports,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        })
    
    def serve_report_content(self, filename):
        """Return the HTML content of a specific report."""
        content = self.fetch_file_from_github(f"reports/{filename}")
        if content:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode())
        else:
            self.send_error(404, f"Report {filename} not found")
    
    def serve_github_file(self, path):
        """Serve a file directly from GitHub."""
        content = self.fetch_file_from_github(path)
        if content:
            # Determine content type
            if path.endswith(".html"):
                content_type = "text/html; charset=utf-8"
            elif path.endswith(".css"):
                content_type = "text/css; charset=utf-8"
            elif path.endswith(".js"):
                content_type = "application/javascript; charset=utf-8"
            elif path.endswith(".json"):
                content_type = "application/json; charset=utf-8"
            elif path.endswith(".png"):
                content_type = "image/png"
            elif path.endswith(".jpg") or path.endswith(".jpeg"):
                content_type = "image/jpeg"
            else:
                content_type = "text/plain; charset=utf-8"
            
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            if isinstance(content, str):
                self.wfile.write(content.encode())
            else:
                self.wfile.write(content)
        else:
            self.send_error(404, f"File {path} not found")
    
    def serve_search(self, params):
        """Search reports by query."""
        query = params.get("q", [""])[0]
        if not query:
            self.send_json({"status": "error", "message": "Missing search query"})
            return
        
        reports = self.fetch_reports_from_github()
        
        # Search in title, author, filename
        query_lower = query.lower()
        results = []
        for r in reports:
            score = 0
            if query_lower in r.get("title", "").lower():
                score += 10
            if query_lower in r.get("author", "").lower():
                score += 5
            if query_lower in r.get("filename", "").lower():
                score += 3
            if query_lower in r.get("mvp", "").lower():
                score += 2
            
            if score > 0:
                results.append({"report": r, "score": score})
        
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        self.send_json({
            "status": "success",
            "results": [r["report"] for r in results[:50]],
            "total": len(results)
        })
    
    def fetch_reports_from_github(self):
        """Fetch reports.json from GitHub."""
        content = self.fetch_file_from_github("reports.json")
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return []
        return []
    
    def fetch_file_from_github(self, path):
        """Fetch a file from GitHub repository."""
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
        headers = {
            "Accept": "application/vnd.github.v3.raw"
        }
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                return None
            else:
                print(f"GitHub API error: {response.status_code} for {path}")
                return None
        except Exception as e:
            print(f"Error fetching {path}: {e}")
            return None
    
    def send_json(self, data):
        """Send JSON response."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def send_error(self, code, message):
        """Send error response."""
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "error", "message": message}).encode())
    
    def get_index_html(self):
        """Return the main HTML page with search and display."""
        return """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LivyLogs Combat Reports</title>
    <link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css" rel="stylesheet" type="text/css" />
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        :root { --starwars-blue: #00ecff; --starwars-red: #ff003c; --starwars-yellow: #ffe81f; }
        body { font-family: 'JetBrains Mono', monospace; background-color: #05070a; background-image: radial-gradient(circle at 50% 50%, #1a202c 0%, #05070a 100%); }
        h1, .font-orbitron { font-family: 'Orbitron', sans-serif; }
        .hud-border { border: 1px solid rgba(0, 236, 255, 0.2); box-shadow: 0 0 15px rgba(0, 236, 255, 0.1); }
        .glow-text-blue { text-shadow: 0 0 10px rgba(0, 236, 255, 0.5); }
        .report-card { transition: all 0.3s; }
        .report-card:hover { transform: translateY(-2px); box-shadow: 0 0 20px rgba(0, 236, 255, 0.2); }
        .scanline { width: 100%; height: 100px; z-index: 5; background: linear-gradient(0deg, rgba(0, 236, 255, 0) 0%, rgba(0, 236, 255, 0.02) 50%, rgba(0, 236, 255, 0) 100%); position: absolute; animation: scan 8s linear infinite; pointer-events: none; }
        @keyframes scan { from { top: -100px; } to { top: 100%; } }
        #reportViewer { display: none; }
        #reportViewer.active { display: block; }
        #reportList.active { display: none; }
        .loading-spinner { border: 3px solid rgba(0, 236, 255, 0.1); border-top: 3px solid #00ecff; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8 text-slate-300">
    <div class="max-w-[1800px] mx-auto relative">
        <!-- Header -->
        <div class="flex flex-col md:flex-row justify-between items-stretch mb-8 hud-border bg-black/60 backdrop-blur-md p-6 rounded-lg border-l-4 border-l-primary gap-6 relative overflow-hidden">
            <div class="scanline"></div>
            <div class="relative z-10">
                <div class="flex items-center gap-4 mb-2">
                    <div class="w-10 h-1 rounded-full bg-primary shadow-[0_0_15px_#00ecff]"></div>
                    <h1 class="text-3xl font-black text-primary tracking-[0.2em] glow-text-blue uppercase">LivyLogs Combat Reports</h1>
                </div>
                <p class="text-[10px] font-bold tracking-[0.4em] text-primary/60 uppercase ml-14">Sector 7-B Combat Data Feed • Encrypted Link Active</p>
            </div>
            <div class="flex items-center gap-4 relative z-10">
                <div class="join hud-border bg-black/40">
                    <input id="searchInput" type="text" placeholder="SEARCH REPORTS..." class="input input-bordered input-xs join-item bg-transparent border-none text-[9px] w-48 focus:outline-none" onkeyup="searchReports(event)">
                    <button class="btn btn-primary btn-xs join-item" onclick="searchReports()">SEARCH</button>
                </div>
                <div class="w-px h-12 bg-white/10 mx-2"></div>
                <div class="flex flex-col items-end">
                    <span class="text-[9px] font-black opacity-40 uppercase tracking-widest">Total Reports</span>
                    <span id="totalReports" class="text-2xl font-orbitron font-black text-secondary glow-text-blue tracking-tighter">0</span>
                </div>
            </div>
        </div>

        <!-- Report List View -->
        <div id="reportList" class="active">
            <div id="reportsContainer" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div class="loading-spinner"></div>
            </div>
            <div id="pagination" class="flex justify-center gap-2 mt-8"></div>
        </div>

        <!-- Report Viewer -->
        <div id="reportViewer">
            <button onclick="closeViewer()" class="btn btn-ghost btn-sm mb-4">
                ← BACK TO LIST
            </button>
            <div id="reportContent" class="hud-border bg-black/40 rounded-lg p-4 min-h-[600px]">
                <div class="loading-spinner"></div>
            </div>
        </div>
    </div>

    <script>
        let currentPage = 1;
        let currentSearch = "";
        let totalPages = 1;

        async function fetchReports(page = 1, search = "") {
            const url = `/api/reports?page=${page}&limit=12&search=${encodeURIComponent(search)}`;
            try {
                const response = await fetch(url);
                const data = await response.json();
                if (data.status === "success") {
                    renderReports(data.reports);
                    document.getElementById("totalReports").textContent = data.total;
                    totalPages = data.total_pages;
                    renderPagination(data.page, data.total_pages);
                }
            } catch (error) {
                console.error("Error fetching reports:", error);
                document.getElementById("reportsContainer").innerHTML = 
                    '<div class="col-span-full text-center py-20"><p class="text-error">Error loading reports. Make sure the server is running.</p></div>';
            }
        }

        function renderReports(reports) {
            const container = document.getElementById("reportsContainer");
            if (reports.length === 0) {
                container.innerHTML = '<div class="col-span-full text-center py-20"><p class="opacity-40">No reports found.</p></div>';
                return;
            }

            container.innerHTML = reports.map(report => {
                const statusClass = report.is_duplicate ? "badge-warning" : "badge-primary";
                const statusText = report.is_duplicate ? "DUPLICATE" : "TEMPORARY";
                const mvp = report.mvp || "N/A";
                const kills = report.kills || 0;
                const larp = report.potential_larp || 0;
                const timestamp = report.timestamp || "Unknown";
                const filename = report.filename || "";
                const title = report.title || report.name || "Unnamed Encounter";

                return `
                    <div class="report-card hud-border bg-black/40 rounded-lg p-4 cursor-pointer" onclick="viewReport('${filename}')">
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

        function renderPagination(current, total) {
            const container = document.getElementById("pagination");
            if (total <= 1) {
                container.innerHTML = "";
                return;
            }

            let html = "";
            if (current > 1) {
                html += `<button class="btn btn-ghost btn-xs" onclick="goToPage(${current - 1})">← PREV</button>`;
            }
            
            for (let i = 1; i <= total; i++) {
                if (i === current) {
                    html += `<button class="btn btn-primary btn-xs">${i}</button>`;
                } else if (i === 1 || i === total || Math.abs(i - current) <= 2) {
                    html += `<button class="btn btn-ghost btn-xs" onclick="goToPage(${i})">${i}</button>`;
                } else if (Math.abs(i - current) === 3) {
                    html += `<span class="opacity-40">...</span>`;
                }
            }

            if (current < total) {
                html += `<button class="btn btn-ghost btn-xs" onclick="goToPage(${current + 1})">NEXT →</button>`;
            }

            container.innerHTML = html;
        }

        function goToPage(page) {
            currentPage = page;
            fetchReports(page, currentSearch);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function searchReports(event) {
            if (event && event.key !== "Enter" && event.type !== "click") return;
            currentSearch = document.getElementById("searchInput").value;
            currentPage = 1;
            fetchReports(1, currentSearch);
        }

        async function viewReport(filename) {
            document.getElementById("reportList").classList.remove("active");
            document.getElementById("reportViewer").classList.add("active");
            document.getElementById("reportContent").innerHTML = '<div class="loading-spinner"></div>';

            try {
                const response = await fetch(`/api/report/${filename}`);
                if (response.ok) {
                    const html = await response.text();
                    document.getElementById("reportContent").innerHTML = html;
                } else {
                    document.getElementById("reportContent").innerHTML = 
                        '<div class="text-center py-20"><p class="text-error">Report not found.</p></div>';
                }
            } catch (error) {
                document.getElementById("reportContent").innerHTML = 
                    '<div class="text-center py-20"><p class="text-error">Error loading report.</p></div>';
            }
        }

        function closeViewer() {
            document.getElementById("reportViewer").classList.remove("active");
            document.getElementById("reportList").classList.add("active");
            document.getElementById("reportContent").innerHTML = '<div class="loading-spinner"></div>';
        }

        // Initial load
        fetchReports();
    </script>
</body>
</html>"""

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), ReportHandler)
    print(f"LivyLogs Reports Server running on port {PORT}")
    print(f"Fetching reports from: https://github.com/{GITHUB_REPO}")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
