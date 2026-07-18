from fpdf import FPDF
import datetime


def build_example_pdf(output_path: str = "discord_example_report.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "LivyLogs - Example Discord Combat Report", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.ln(5)

    # Discord-style summary block
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "1) Discord message example", ln=True)
    pdf.set_font("Courier", "", 9)
    discord_block = (
        "[LIVIUS REPORT] Encounter: DWB Outpost Push\\n"
        "Duration: 03:28 | Team DPS: 5,942 | Team HPS: 1,184\\n"
        "Top Damage: IiIiIiIi (612,480)\\n"
        "Top Healing: Medico (141,223)\\n"
        "Status Events: KD=17 PD=11 INT=24 INC=8\\n"
        "Report URL: https://your-site/reports/encounter_20260718_1347.html"
    )
    pdf.multi_cell(0, 5, discord_block, border=1)
    pdf.ln(4)

    # CSS sample
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "2) CSS style sample used by report", ln=True)
    pdf.set_font("Courier", "", 8)
    css_sample = (
        ".hud-border { border: 1px solid rgba(0,236,255,0.35); }\\n"
        ".lane-friendly { background: rgba(34,197,94,0.15); }\\n"
        ".lane-enemy { background: rgba(239,68,68,0.15); }\\n"
        ".badge-kd { color:#fff; background:#ef4444; font-weight:700; }\\n"
        ".badge-int { color:#001018; background:#22d3ee; font-weight:700; }\\n"
        ".swimlane-grid { border-top:1px dashed rgba(255,255,255,0.2); }"
    )
    pdf.multi_cell(0, 4.6, css_sample, border=1)
    pdf.ln(4)

    # Swimlane timeline example
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "3) Event tracking swimlane (example timeline)", ln=True)
    pdf.set_font("Courier", "", 8)

    header = "Time     | Friendly Lane            | Enemy Lane"
    divider = "---------+--------------------------+--------------------------"
    rows = [
        "00:03.2  | YOU -> KD on Rancor      |",
        "00:05.8  |                          | Rancor -> INT on YOU",
        "00:09.1  | Healer +14,220 HPS tick  |",
        "00:12.7  |                          | IiIiIiIi takes PD",
        "00:18.4  | Loot event: Composite    |",
        "00:24.0  | YOU casts INT on IiIiIiIi |",
        "00:29.0  | INT cooldown complete     |",
    ]

    pdf.multi_cell(0, 4.8, header)
    pdf.multi_cell(0, 4.8, divider)
    for row in rows:
        pdf.multi_cell(0, 4.8, row)

    pdf.ln(4)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(
        0,
        4.5,
        "This is a visual example of what your Discord-facing report content can look like: "
        "summary block + CSS style profile + swimlane event timeline.",
    )

    pdf.output(output_path)
    print(f"Created: {output_path}")


if __name__ == "__main__":
    build_example_pdf()
