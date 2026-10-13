import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, PathPatch
from matplotlib.path import Path
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import os

def create_signature_logo():
    # 1. Create High-Res Base Figure
    fig, ax = plt.subplots(figsize=(10, 10), dpi=200)
    fig.patch.set_facecolor('#0B0F17')
    ax.set_facecolor('#0B0F17')
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.axis('off')

    # Radial ambient glow in center
    radii = np.linspace(0.1, 7.5, 60)
    for r in radii:
        alpha = max(0.0, 0.12 * (1.0 - (r / 7.5)**1.5))
        circle = plt.Circle((0, 0.5), r, color='#0F2338', alpha=alpha, ec=None)
        ax.add_patch(circle)

    # Ambient Tricolor Glow Halos
    saffron_glow = plt.Circle((-1.8, 3.5), 3.5, color='#FF7A00', alpha=0.08, ec=None)
    green_glow = plt.Circle((2.5, -2.5), 3.5, color='#10B981', alpha=0.08, ec=None)
    white_glow = plt.Circle((0, 1.0), 3.0, color='#FFFFFF', alpha=0.05, ec=None)
    ax.add_patch(saffron_glow)
    ax.add_patch(green_glow)
    ax.add_patch(white_glow)

    # Outer decorative fine cybernetic orbits
    theta = np.linspace(0, 2*np.pi, 200)
    ax.plot(7.5 * np.cos(theta), 7.5 * np.sin(theta), color='#ffffff', alpha=0.06, lw=1.0, ls='--')
    
    # Saffron arc (Top-Left)
    theta_s = np.linspace(np.pi*0.55, np.pi*1.15, 80)
    ax.plot(7.2 * np.cos(theta_s), 7.2 * np.sin(theta_s), color='#FF9933', alpha=0.45, lw=2.0)

    # Green arc (Bottom-Right)
    theta_g = np.linspace(-np.pi*0.45, np.pi*0.15, 80)
    ax.plot(7.2 * np.cos(theta_g), 7.2 * np.sin(theta_g), color='#10B981', alpha=0.45, lw=2.0)

    # --- LUXURY SIGNATURE 'A' BEZIER PATHS ---
    
    # 1. Left Upstroke (Saffron -> White)
    verts_left = [
        (-4.2, -5.0),  # Start low left with flourish
        (-3.8, -1.0),
        (-1.5, 4.2),
        (0.0, 6.2),    # Apex
    ]
    codes_left = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
    path_left = Path(verts_left, codes_left)

    # Draw Glow layers for Left Upstroke
    for w, a in [(18, 0.08), (12, 0.18), (8, 0.35), (4.5, 0.95)]:
        patch = PathPatch(path_left, facecolor='none', edgecolor='#FF9933', lw=w, alpha=a, capstyle='round')
        ax.add_patch(patch)
    # Core bright inner stroke
    patch_core_left = PathPatch(path_left, facecolor='none', edgecolor='#FFA834', lw=2.8, alpha=1.0, capstyle='round')
    ax.add_patch(patch_core_left)

    # 2. Right Downstroke & Flowing Ribbon Tail (White -> India Green)
    verts_right = [
        (0.0, 6.2),    # Apex
        (1.8, 4.0),
        (3.5, -2.5),
        (4.5, -5.2),   # Bottom right sweep
    ]
    codes_right = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
    path_right = Path(verts_right, codes_right)

    # Draw Glow layers for Right Downstroke
    for w, a in [(18, 0.08), (12, 0.18), (8, 0.35), (4.5, 0.95)]:
        patch = PathPatch(path_right, facecolor='none', edgecolor='#10B981', lw=w, alpha=a, capstyle='round')
        ax.add_patch(patch)
    # Core bright inner stroke
    patch_core_right = PathPatch(path_right, facecolor='none', edgecolor='#34D399', lw=2.8, alpha=1.0, capstyle='round')
    ax.add_patch(patch_core_right)

    # 3. Dynamic Signature Calligraphic Crossbar (Floating Tricolor Ribbon)
    verts_cross = [
        (-5.5, -0.8),  # Extended left loop
        (-2.0, 1.2),
        (2.5, 0.5),
        (6.2, -1.8),   # Dynamic right flourish
    ]
    codes_cross = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
    path_cross = Path(verts_cross, codes_cross)

    for w, a in [(14, 0.08), (9, 0.2), (5, 0.45), (3.0, 0.95)]:
        patch = PathPatch(path_cross, facecolor='none', edgecolor='#FFFFFF', lw=w, alpha=a, capstyle='round')
        ax.add_patch(patch)
    patch_core_cross = PathPatch(path_cross, facecolor='none', edgecolor='#FFFFFF', lw=1.8, alpha=1.0, capstyle='round')
    ax.add_patch(patch_core_cross)

    # 4. Apex White Neon Spark
    ax.scatter([0.0], [6.2], s=250, color='#FFFFFF', alpha=0.9, zorder=10)
    ax.scatter([0.0], [6.2], s=700, color='#FF9933', alpha=0.3, zorder=9)

    # 5. Tail Emerald Spark
    ax.scatter([4.5], [-5.2], s=180, color='#10B981', alpha=0.9, zorder=10)
    ax.scatter([4.5], [-5.2], s=500, color='#10B981', alpha=0.3, zorder=9)

    # 6. Crossbar Left Saffron Spark
    ax.scatter([-5.5], [-0.8], s=120, color='#FF9933', alpha=0.85, zorder=10)

    # Bottom Branding Typography
    ax.text(0, -7.2, "AURIX", color='#FFFFFF', fontsize=22, fontweight='bold',
            ha='center', va='center', fontfamily='sans-serif', alpha=0.92)
    
    ax.text(0, -8.1, "SUSTAINABLE AI", color='#10B981', fontsize=11, fontweight='semibold',
            ha='center', va='center', fontfamily='sans-serif', alpha=0.85)

    # Save output
    out_brain = r"C:\Users\amana\.gemini\antigravity-ide\brain\ad08a3cd-93f9-47ed-8daa-471fbff941df\aurix_signature_letter_a.png"
    out_assets = r"C:\BPUT_HACK_2026\presentation_assets\AURIX_Signature_Letter_A.png"

    plt.tight_layout()
    plt.savefig(out_brain, format='png', dpi=200, bbox_inches='tight', facecolor='#0B0F17')
    plt.savefig(out_assets, format='png', dpi=200, bbox_inches='tight', facecolor='#0B0F17')
    plt.close()
    print("Successfully created signature logo at:", out_assets)

if __name__ == "__main__":
    create_signature_logo()
