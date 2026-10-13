import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def create_master_architecture_diagram():
    # Canvas setup - 16:9 Ultra HD
    fig = plt.figure(figsize=(19.2, 10.8), dpi=150)
    fig.patch.set_facecolor('#0B0F17')
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor('#0B0F17')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # 1. Subtle Cybernetic Background Grid & Radial Glows
    for x in range(4, 100, 4):
        ax.plot([x, x], [0, 100], color='#14213d', lw=0.4, alpha=0.25)
    for y in range(4, 100, 4):
        ax.plot([0, 100], [y, y], color='#14213d', lw=0.4, alpha=0.25)

    # Ambient Glow Halos
    ax.add_patch(patches.Circle((18, 52), 22, color='#0F2B48', alpha=0.3, ec=None))
    ax.add_patch(patches.Circle((48, 52), 24, color='#0D382E', alpha=0.3, ec=None))
    ax.add_patch(patches.Circle((78, 52), 22, color='#182E4B', alpha=0.3, ec=None))

    # 2. Top Header Branding Banner
    header_box = patches.FancyBboxPatch((3.5, 87.5), 93, 10, boxstyle="round,pad=0.5,rounding_size=1.2",
                                        facecolor='#0F172A', edgecolor='#1E293B', lw=1.5)
    ax.add_patch(header_box)

    # Indian Tricolor glowing accent line under header
    ax.plot([4.5, 34], [87.5, 87.5], color='#FF9933', lw=3.2, alpha=0.95)
    ax.plot([34, 66], [87.5, 87.5], color='#FFFFFF', lw=3.2, alpha=0.95)
    ax.plot([66, 95.5], [87.5, 87.5], color='#10B981', lw=3.2, alpha=0.95)

    ax.text(6.0, 93.8, "AURA", color='#10B981', fontsize=26, fontweight='bold', va='center')
    ax.text(15.5, 93.8, "— Sustainable Facility & Estate Intelligence Platform", color='#F8FAFC', fontsize=17, fontweight='bold', va='center')
    ax.text(6.0, 90.0, "End-to-End System Architecture  |  3-Sigma Anomaly Engine  |  Human-in-the-Loop Decision Support", color='#94A3B8', fontsize=11.5, va='center')

    # Team & PS Badge (Top Right)
    badge = patches.FancyBboxPatch((74, 89.2), 21.0, 6.5, boxstyle="round,pad=0.3,rounding_size=0.8",
                                   facecolor='#1E293B', edgecolor='#334155', lw=1.2)
    ax.add_patch(badge)
    ax.text(84.5, 93.6, "TEAM AURIX-0.3  •  PS-04", color='#38BDF8', fontsize=11.5, fontweight='bold', ha='center', va='center')
    ax.text(84.5, 91.0, "BPUT Hackathon 2026", color='#94A3B8', fontsize=10, ha='center', va='center')

    # 3. Four Architecture Stage Columns
    stages = [
        {
            "num": "01",
            "title": "IoT & Telemetry Ingestion",
            "subtitle": "15-Min Live Sensor Stream",
            "x": 3.5,
            "w": 21.0,
            "color": "#38BDF8",
            "items": [
                ("[METERS]", "Multi-Ward Smart Sub-Meters"),
                ("[LOOP]", "15-Minute Telemetry Streaming"),
                ("[PILOT]", "5 Hospital Wards Monitored"),
                (" ", "Emergency, ICU, General, OPD, Admin"),
                ("[SIGNALS]", "Energy (kWh), Occupancy, Temp"),
                ("[PROTOCOLS]", "Modbus-RTU & MQTT Gateway Ready")
            ]
        },
        {
            "num": "02",
            "title": "Python AI Analytics",
            "subtitle": "Diurnal Baseline & 3-Sigma",
            "x": 27.5,
            "w": 22.0,
            "color": "#10B981",
            "items": [
                ("[BASELINE]", "24h Diurnal Seasonal Window"),
                (" ", "Historical t-96 interval reference"),
                ("[SCORING]", "3-Sigma Statistical Z-Score:"),
                (" ", r"$Z = \frac{x - \mu_{seasonal}}{\sigma_{seasonal}} > 3.0$"),
                ("[SPEED]", "< 3.0s Live Surge Detection"),
                ("[PRECISION]", "Zero Baseline False Positives")
            ]
        },
        {
            "num": "03",
            "title": "Enterprise Backend",
            "subtitle": "Java Spring Boot & MySQL",
            "x": 52.5,
            "w": 21.0,
            "color": "#A855F7",
            "items": [
                ("[STACK]", "Java 21 + Spring Boot 3.3"),
                ("[DATABASE]", "MySQL 8.0 Normalized Schema"),
                ("[CONTRACT]", "Decoupled Energy Contract API"),
                ("[SIMULATOR]", "Synthetic Sensor Replay Engine"),
                ("[REST API]", "Secure Microservice Endpoints"),
                ("[SCALE]", "Multi-Tenant Campus Architecture")
            ]
        },
        {
            "num": "04",
            "title": "Decision-Support UI",
            "subtitle": "React 18 & Action Plan",
            "x": 76.5,
            "w": 20.0,
            "color": "#F59E0B",
            "items": [
                ("[CHARTS]", "60 FPS Responsive SVG Visuals"),
                ("[CHECKLIST]", "4-Step Ground Action Checklist"),
                ("[TARIFF]", "Live ~Rs 1,534 / hr Loss Metric"),
                ("[CARBON]", "Live +157 kg CO2e / hr Footprint"),
                ("[WHAT-IF]", "Simulation Scenario Recovery"),
                ("[PERSONAS]", "Admin / BMS Ops / Sustainability")
            ]
        }
    ]

    for st in stages:
        # Card Background
        card = patches.FancyBboxPatch((st["x"], 25.5), st["w"], 59, boxstyle="round,pad=0.5,rounding_size=1.2",
                                      facecolor='#0F172A', edgecolor=st["color"], lw=1.6, alpha=0.96)
        ax.add_patch(card)

        # Step Number Pill
        pill = patches.FancyBboxPatch((st["x"] + 1.2, 78.8), 3.2, 3.4, boxstyle="round,pad=0.2,rounding_size=0.6",
                                     facecolor=st["color"], edgecolor='none', alpha=0.95)
        ax.add_patch(pill)
        ax.text(st["x"] + 2.8, 80.5, st["num"], color='#0B0F17', fontsize=12, fontweight='bold', ha='center', va='center')

        # Stage Titles
        ax.text(st["x"] + 5.2, 81.3, st["title"], color='#F8FAFC', fontsize=12.5, fontweight='bold', va='center')
        ax.text(st["x"] + 5.2, 79.0, st["subtitle"], color=st["color"], fontsize=10.2, fontweight='bold', va='center')

        # Divider line
        ax.plot([st["x"] + 1.2, st["x"] + st["w"] - 1.2], [76.5, 76.5], color='#1E293B', lw=1.2)

        # Items
        y_pos = 72.2
        for tag, text in st["items"]:
            if tag.strip():
                ax.text(st["x"] + 1.2, y_pos, tag, color=st["color"], fontsize=8.6, fontweight='bold', va='center')
                ax.text(st["x"] + 7.6, y_pos, text, color='#F1F5F9', fontsize=9.4, fontweight='normal', va='center')
            else:
                ax.text(st["x"] + 7.6, y_pos, text, color='#94A3B8', fontsize=9.0, fontweight='bold' if "$" in text else 'normal', va='center')
            y_pos -= 5.4

    # 4. Connecting Arrows between Columns
    arrow_positions = [(24.7, 54.5), (49.7, 54.5), (73.7, 54.5)]
    for ax_pos, ay_pos in arrow_positions:
        arrow = patches.FancyArrow(ax_pos, ay_pos, 2.6, 0, width=0.6, head_width=2.4, head_length=1.1,
                                   facecolor='#10B981', edgecolor='#059669', alpha=0.95)
        ax.add_patch(arrow)

    # 5. Bottom Validation & Pilot Results Banner
    bottom_box = patches.FancyBboxPatch((3.5, 3.5), 93, 19.5, boxstyle="round,pad=0.5,rounding_size=1.2",
                                        facecolor='#0F172A', edgecolor='#10B981', lw=1.3)
    ax.add_patch(bottom_box)

    # Pilot Badge Pill
    pilot_pill = patches.FancyBboxPatch((5.5, 18.5), 29.0, 3.2, boxstyle="round,pad=0.2,rounding_size=0.5",
                                        facecolor='#064E3B', edgecolor='#10B981', lw=1.1)
    ax.add_patch(pilot_pill)
    ax.text(20.0, 20.1, "PILOT BENCHMARK: GOVT HOSPITAL BHUBANESWAR", color='#34D399', fontsize=9.5, fontweight='bold', ha='center', va='center')

    # Left Mini Trend Chart Simulation
    t = np.linspace(0, 10, 100)
    base_wave = 8.5 + 1.3 * np.sin(t * 1.5)
    ax.plot(np.linspace(6, 33, 100), base_wave, color='#10B981', lw=2.2, label='Normal Baseline')
    
    # Anomaly Spike on Mini Trend
    spike_t = np.linspace(23, 27, 30)
    spike_val = 8.5 + 1.3 * np.sin(spike_t * 1.5) + 6.8 * np.exp(-((spike_t - 25)**2)/0.6)
    ax.plot(spike_t, spike_val, color='#EF4444', lw=2.8)
    ax.plot([25, 25], [8.5, 16.5], color='#EF4444', lw=1.2, ls=':')
    ax.scatter([25], [16.2], color='#EF4444', s=75, zorder=5)
    
    # Spike callout badge
    spike_callout = patches.FancyBboxPatch((18.5, 14.8), 13.0, 2.6, boxstyle="round,pad=0.2,rounding_size=0.4",
                                          facecolor='#7F1D1D', edgecolor='#EF4444', lw=0.9)
    ax.add_patch(spike_callout)
    ax.text(25.0, 16.1, "15:30 SPIKE (+191.7 kWh)", color='#FECACA', fontsize=8.2, fontweight='bold', ha='center', va='center')

    ax.text(19.5, 5.2, "Real-Time 15-Minute Sensor Telemetry vs Learned Diurnal Baseline", color='#94A3B8', fontsize=8.8, ha='center')

    # Middle Verified Metric Cards
    # Metric 1: Financial
    m1 = patches.FancyBboxPatch((36.5, 5.2), 18.5, 14.2, boxstyle="round,pad=0.3,rounding_size=0.6",
                                facecolor='#1E293B', edgecolor='#F59E0B', lw=1.1)
    ax.add_patch(m1)
    ax.text(45.75, 16.6, "ESTIMATED TARIFF LOSS", color='#94A3B8', fontsize=9.0, fontweight='bold', ha='center')
    ax.text(45.75, 12.0, "Rs 1,534 / hr", color='#FBBF24', fontsize=17, fontweight='bold', ha='center')
    ax.text(45.75, 7.5, "Odisha Ref Tariff: Rs 8.00/kWh", color='#64748B', fontsize=8.2, ha='center')

    # Metric 2: Carbon
    m2 = patches.FancyBboxPatch((57.0, 5.2), 18.5, 14.2, boxstyle="round,pad=0.3,rounding_size=0.6",
                                facecolor='#1E293B', edgecolor='#10B981', lw=1.1)
    ax.add_patch(m2)
    ax.text(66.25, 16.6, "CARBON OVERLOAD", color='#94A3B8', fontsize=9.0, fontweight='bold', ha='center')
    ax.text(66.25, 12.0, "+157.2 kg/hr", color='#34D399', fontsize=17, fontweight='bold', ha='center')
    ax.text(66.25, 7.5, "CEA Standard: 0.82 kg CO2e/kWh", color='#64748B', fontsize=8.2, ha='center')

    # Metric 3: Response Speed
    m3 = patches.FancyBboxPatch((77.5, 5.2), 17.5, 14.2, boxstyle="round,pad=0.3,rounding_size=0.6",
                                facecolor='#1E293B', edgecolor='#38BDF8', lw=1.1)
    ax.add_patch(m3)
    ax.text(86.25, 16.6, "DETECTION LATENCY", color='#94A3B8', fontsize=9.0, fontweight='bold', ha='center')
    ax.text(86.25, 12.0, "< 3.0 Seconds", color='#38BDF8', fontsize=17, fontweight='bold', ha='center')
    ax.text(86.25, 7.5, "vs 30-Day Passive Lag", color='#64748B', fontsize=8.2, ha='center')

    # Output paths
    out_brain = r"C:\Users\amana\.gemini\antigravity-ide\brain\ad08a3cd-93f9-47ed-8daa-471fbff941df\AURA_Master_Architecture_Diagram.png"
    out_assets = r"C:\BPUT_HACK_2026\presentation_assets\AURA_Master_Architecture_Diagram.png"

    plt.savefig(out_brain, format='png', dpi=150, facecolor='#0B0F17')
    plt.savefig(out_assets, format='png', dpi=150, facecolor='#0B0F17')
    plt.close()
    print("Master diagram regenerated successfully at:", out_assets)

if __name__ == "__main__":
    create_master_architecture_diagram()
