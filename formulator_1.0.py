# =============================================================================
#  formulator_delta.py
#
#  The 3D Printing Formulator  —  v1.0
#  A desktop recipe calculator for ceramic resin / paste formulations
#  used in Vat Photopolymerisation and Direct Ink Writing 3D printing.
#
#  Author:      Dr Athanasios (Thanos) Goulas
#  Affiliation: 
#  Contact:     thanosgoulas@outlook.com
#
#  Version 1.0  —  2026
#
# =============================================================================
#  COPYRIGHT & INTELLECTUAL PROPERTY NOTICE
# =============================================================================
#
#  Copyright (c) 2026 Dr Athanasios (Thanos) Goulas. All rights reserved.
#
#  This software — including its source code, algorithms, logic, user
#  interface design, materials database, and all associated documentation —
#  is the sole intellectual property of Dr Athanasios (Thanos) Goulas.
#  Materials.
#
#  All rights reserved. No part of this software may be:
#    - Reproduced, copied, or duplicated in any form or by any means
#    - Modified, adapted, translated, or reverse-engineered
#    - Distributed, sublicensed, sold, or commercially exploited
#    - Presented or published under any other name or authorship
#    - Used to create derivative works without express written permission
#
#  Unauthorised use, reproduction, or claiming of authorship — in whole
#  or in part — constitutes a violation of intellectual property law and
#  may result in civil and/or criminal legal action.
#
#  Academic or research use by colleagues at  is
#  permitted for non-commercial internal purposes only, provided full
#  attribution to the author is maintained at all times.
#
#  For licensing, collaboration, or permissions contact:
#  thanosgoulas@outlook.com
#
# =============================================================================
#  TECHNICAL NOTES
# =============================================================================
#
#  The app solves two formulation problems:
#    Forward:  given component amounts, compute wt.%/vol.% composition.
#    Inverse:  given a target solids loading, compute component amounts.
#
#  Dependencies: tkinter (stdlib), reportlab
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json, os, sys, subprocess, urllib.parse, tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                Paragraph, Spacer, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# ── Embedded flask icon (base64 ICO) ─────────────────────────────────
ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABJElEQVR4nMWX0RGEIAxEgbk6tIKzPq1A69MKtBHuixsMwWRBNDP3cRjyliUyaA0Y3bj6q+fHMliknipZgtaIca3g2rlZhbnJ+/wVwf20JWM5N1gHauC5vFzNRECN5VJwtZ2UEAdnLZpHGWITIsX7aVOLTAS0tJ5GzHJPw6kIeAvujtcFWNR+6SxAm/ADZV/AtIcUDWgLYghdafiPCnm9B9QCkJUhuXATxgDaA2gDGlO4BRyoBF4soAaYCJCuTaWvl2busQz20oFQoESEdu7tb8E+fyHBzhj+vlZqPdcbXK3AdHTgiYhZ7BbkVk/HmxxO3bh6NLpx/f+kPMpLbPfeN70dWWtPzGQLaEJLOCsgJIaoOfH6aTvVYlmaQi0/TmG77/48/wE6Dt3w6uz8RwAAAABJRU5ErkJggg=="

def _set_icon(window):
    """Apply the flask icon to any tk.Toplevel or Tk window."""
    try:
        import tempfile, base64 as _b64
        ico_data = _b64.b64decode(ICON_B64)
        tmp = tempfile.NamedTemporaryFile(suffix=".ico", delete=False)
        tmp.write(ico_data); tmp.close()
        window.iconbitmap(tmp.name)
    except Exception:
        pass  # silently ignore if icon can't be set

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ─────────────────────────────────────────────
#  WINDOWS SYSTEM PALETTE
# ─────────────────────────────────────────────
# ── App identity — update before each release ────────────────────────
APP_VERSION        = "1.0"
REGISTRATION_EMAIL = "thanosgoulas@outlook.com"   # <- replace before release
# ─────────────────────────────────────────────
# ── Modern SaaS dashboard colour tokens ──────────────────────────────
SIDEBAR     = "#1C2B4A"   # Deep navy sidebar
SIDEBAR_HOV = "#273A5E"   # Sidebar hover
SIDEBAR_SEL = "#2E4575"   # Sidebar selected
SIDEBAR_FG  = "#C8D6F0"   # Sidebar text
SIDEBAR_FG2 = "#7A93C4"   # Sidebar muted text

BG          = "#EEF2F8"   # App canvas — soft blue-grey
BG_WHITE    = "#FFFFFF"   # Card surface
BG_HDR      = "#F5F7FC"   # Subtle section bg
BG_ALT      = "#F8FAFD"   # Alternating row
BORDER      = "#E2E8F4"   # Card border
BORDER_MED  = "#C5CEDF"   # Control stroke
SEL_BG      = "#2563EB"   # Selection
SEL_FG      = "#FFFFFF"
ACCENT      = "#2563EB"   # Primary blue
ACCENT_HOV  = "#1D54D4"   # Hover
ACCENT_PRE  = "#1748BF"   # Pressed
ACCENT_SOFT = "#EBF1FF"   # Tint bg
BTN_FG      = "#FFFFFF"
BTN_RED     = "#DC2626"
BTN_GREEN   = "#16A34A"
BTN_BLUE    = "#2563EB"
BTN_GREY    = "#64748B"
TEXT        = "#0F172A"
TEXT_DIM    = "#334155"
TEXT_MUTED  = "#64748B"
TOTAL_BG    = "#DBEAFE"

FWD_MODES = [
    "Mass (g)", "Volume (cm3)",
    "wt.% to Reference", "vol.% to Reference",
    "wt.% of Total", "vol.% of Total",
]
INV_MODES = [
    "Primary", "Balance",
    "wt.% to Reference", "vol.% to Reference",
    "wt.% of Total Suspension", "vol.% of Total Suspension",
    "Independent Mass (g)", "Independent Vol (cm3)",
]

DEFAULT_MATERIALS = [
    # ── Ceramics ──────────────────────────────────────────────────────
    {"acronym": "Al2O3",                           "name": "Alumina (Corundum)",                                                       "density": 3.980, "ri": 1.765, "mw": 101.96},
    {"acronym": "ZrO2",                               "name": "Zirconium Dioxide (Monoclinic, Baddeleyite)",                                               "density": 5.680, "ri": 2.13,  "mw": 123.22},
    {"acronym": "3YSZ",                              "name": "3 mol.% Y2O3-stabilised ZrO2",                                                            "density": 6.050, "ri": 2.17, "mw": 123.22},
    {"acronym": "4YSZ",                              "name": "4 mol.% Y2O3-stabilised ZrO2",                                                            "density": 5.980, "ri": 2.17, "mw": 123.22},
    {"acronym": "5YSZ",                              "name": "5 mol.% Y2O3-stabilised ZrO2",                                                            "density": 5.9600, "ri": 2.165, "mw": 123.22},
    {"acronym": "8YSZ",                              "name": "8 mol.% Y2O3-stabilised ZrO2",                                                            "density": 5.900, "ri": 2.15, "mw": 123.22},
    {"acronym": "10YSZ",                             "name": "10 mol.% Y2O3-stabilised ZrO2",                                                            "density": 5.70, "ri": 2.14, "mw": 123.22},
    {"acronym": "12YSZ",                             "name": "12 mol.% Y2O3-stabilised ZrO2",                                                            "density": 5.60, "ri": 2.13, "mw": 123.22},
    {"acronym": "SiC",                   "name": "Silicon Carbide (α-SiC)",                                                         "density": 3.210, "ri": 2.65, "mw": 40.1},
    {"acronym": "Si3N4",                   "name": "Silicon Nitride (β-Si3N4)",                                                       "density": 3.440, "ri": 2.02, "mw": 140.28},
    {"acronym": "AlN",                  "name": "Aluminum Nitride",                                                         "density": 3.260, "ri": 2.1, "mw": 40.99},
    {"acronym": "HAp",                    "name": "Hydroxyapatite, Ca10(PO4)6(OH)2",                                                         "density": 3.156, "ri": 1.65, "mw": 502.31},
    {"acronym": "TCP",              "name": "Tricalcium Phosphate, Ca3(PO4)2",                                                         "density": 3.140, "ri": 1.63, "mw": 310.18},
    {"acronym": "BaTiO3",                   "name": "Barium Titanate",                                                      "density": 6.020, "ri": 2.4, "mw": 233.19},
    {"acronym": "TiO2",                           "name": "Titania (Rutile)",                                                        "density": 4.230, "ri": 2.49, "mw": 79.87},
    {"acronym": "Y2O3",                            "name": "Yttria",                                                        "density": 5.010, "ri": 1.92, "mw": 225.81},
    {"acronym": "MgO",                          "name": "Magnesia (Periclase)",                                                         "density": 3.580, "ri": 1.736, "mw": 40.3},
    # ── Classic dopants / sintering aids ──────────────────────────────────
    {"acronym": "CaO",                            "name": "Calcia (Lime)",                                                         "density": 3.350, "ri": 1.838, "mw": 56.08},
    {"acronym": "CeO2",                             "name": "Ceria",                                                        "density": 7.220, "ri": 2.35, "mw": 172.11},
    {"acronym": "Sc2O3",                           "name": "Scandia",                                                       "density": 3.840, "ri": 1.95, "mw": 137.92},
    {"acronym": "Dy2O3",                         "name": "Dysprosia",                                                       "density": 7.80, "ri": 1.98, "mw": 372.99},
    {"acronym": "Er2O3",                             "name": "Erbia",                                                       "density": 8.640, "ri": 1.99, "mw": 382.52},
    {"acronym": "La2O3",                          "name": "Lanthana",                                                       "density": 6.510, "ri": 1.99, "mw": 325.81},
    {"acronym": "Cr2O3",                           "name": "Chromia (Eskolaite)",                                                       "density": 5.220, "ri": 2.55, "mw": 151.99},
    {"acronym": "SiO2",                            "name": "Silica (Amorphous)",                                                        "density": 2.650, "ri": 1.459, "mw": 60.08},
    {"acronym": "SrAl2O4",               "name": "Strontium Monoaluminate",                                                     "density": 3.500, "ri": 1.72, "mw": 205.58},
    {"acronym": "Mullite",                           "name": "3Al2O3·2SiO2",                                                            "density": 3.170, "ri": 1.64, "mw": 426.05},
    {"acronym": "Cordierite",                        "name": "Mg2Al4Si5O18",                                                            "density": 2.510, "ri": 1.54, "mw": 584.96},
    {"acronym": "MgAl2O4",                            "name": "Spinel (MgAl2O4)",                                                     "density": 3.580, "ri": 1.719, "mw": 142.27},
    {"acronym": "Y3Al5O12",                               "name": "Yttrium Aluminium Garnet",                                                    "density": 4.550, "ri": 1.83, "mw": 593.7},
    # ── ZTA variants (Al₂O₃ matrix + vol% ZrO₂) ──────────────────────────
    {"acronym": "ZTA 95/5",                          "name": "95vol%Al2O3–5vol%ZrO2",                                       "density": 4.083, "ri": None, "mw": None},
    {"acronym": "ZTA 90/10",                         "name": "90vol%Al2O3–10vol%ZrO2",                                      "density": 4.187, "ri": None, "mw": None},
    {"acronym": "ZTA 85/15",                         "name": "85vol%Al2O3–15vol%ZrO2",                                      "density": 4.290, "ri": None, "mw": None},
    {"acronym": "ZTA 83/17 – BIOLOX delta type",     "name": "83vol%Al2O3–17vol%ZrO2 (BIOLOX Delta type)",                                                            "density": 4.332, "ri": None, "mw": None},
    {"acronym": "ZTA 80/20",                         "name": "80vol%Al2O3–20vol%ZrO2",                                      "density": 4.394, "ri": None, "mw": None},
    {"acronym": "ZTA 75/25",                         "name": "75vol%Al2O3–25vol%ZrO2",                                      "density": 4.497, "ri": None, "mw": None},
    {"acronym": "ZTA 70/30",                         "name": "70vol%Al2O3–30vol%ZrO2",                                      "density": 4.601, "ri": None, "mw": None},
    # ── ATZ variants (ZrO₂ matrix + vol% Al₂O₃) ──────────────────────────
    {"acronym": "ATZ 90/10",                         "name": "90vol%ZrO2–10vol%Al2O3",                                      "density": 5.843, "ri": None, "mw": None},
    {"acronym": "ATZ 80/20",                         "name": "80vol%ZrO2–20vol%Al2O3",                                      "density": 5.636, "ri": None, "mw": None},
    {"acronym": "ATZ 75/25",                         "name": "75vol%ZrO2–25vol%Al2O3",                                      "density": 5.532, "ri": None, "mw": None},
    {"acronym": "ATZ 70/30",                         "name": "70vol%ZrO2–30vol%Al2O3",                                      "density": 5.429, "ri": None, "mw": None},
    {"acronym": "ATZ 60/40",                         "name": "60vol%ZrO2–40vol%Al2O3",                                      "density": 5.222, "ri": None, "mw": None},
    # ── Piezoelectric / dielectric ceramics ───────────────────────────────
    # PZT: theoretical density for PbZr0.52Ti0.48O3 (MPB composition)
    # from XRD (Bhatt 2010, Scirp): 7.78 g/cm³
    {"acronym": "PZT",                               "name": "PbZr0.52Ti0.48O3, MPB",                                       "density": 7.780, "ri": 2.5, "mw": None},
    # CCTO: calculated from unit cell a=7.391 Å, Im3-bar, Z=2
    # M(CaCu3Ti4O12)=614.17, ρ=5.05 g/cm³
    {"acronym": "CCTO",                              "name": "CaCu3Ti4O12",                                                 "density": 5.050, "ri": 2.1, "mw": None},
    # BZT: Ba(Zr0.2Ti0.8)O3, a≈4.030 Å, Z=1
    {"acronym": "BZT",                               "name": "Ba(Zr0.2Ti0.8)O3",                                            "density": 6.090, "ri": None, "mw": None},
    # BF-BT: 0.7BiFeO3–0.3BaTiO3, MPB composition, a≈3.960 Å
    {"acronym": "BF-BT",                             "name": "0.7BiFeO3–0.3BaTiO3, MPB",                                    "density": 7.660, "ri": None, "mw": None},
    # SrTiO3: cubic Pm-3m a=3.905 Å, Z=1; Wikipedia 5.12/5.13 g/cm³
    {"acronym": "SrTiO3",                "name": "Strontium Titanate (Tausonite)",                                                      "density": 5.120, "ri": 2.41, "mw": 183.49},
    # KNN: K0.5Na0.5NbO3, orthorhombic, a=3.9615 b=5.6514 c=5.6856 Å, Z=2
    {"acronym": "KNN",                               "name": "K0.5Na0.5NbO3",                                               "density": 4.490, "ri": None, "mw": None},
    # ── Sodium-ion conductor / battery ceramics ───────────────────────────
    # Na2Ti3O7: monoclinic P21/m a=8.571 b=3.804 c=9.133 Å β=101.57° Z=2
    {"acronym": "Na2Ti3O7",                          "name": "Sodium Trititanate",                                       "density": 3.430, "ri": None, "mw": 301.71},
    # LiFePO4: olivine Pnma a=10.338 b=6.011 c=4.695 Å Z=4; widely cited 3.6 g/cm³
    {"acronym": "LiFePO4",                           "name": "Lithium Iron Phosphate (Triphylite)",                                   "density": 3.600, "ri": 1.68, "mw": 157.76},
    # Sodium β-alumina NaAl11O17: "generally recognised full density" = 3.26 g/cm³
    # (US Patent 4052538; sintered samples reach 96–98% of 3.26 g/cm³)
    {"acronym": "Sodium β-alumina",                  "name": "NaAl11O17, β-Alumina Solid Electrolyte",                                                   "density": 3.260, "ri": None, "mw": None},
    # Sodium β″-alumina Na2O·5.33Al2O3 — slightly higher than β due to more Na
    {"acronym": "Sodium β″-alumina",                 "name": "Na2O·5.33Al2O3, β″-Alumina",                                              "density": 3.270, "ri": None, "mw": None},
    # NASICON Na3Zr2Si2PO12: R3-bar-c hex a=9.042 c=22.715 Å Z=6 → 3.29 g/cm³
    {"acronym": "NASICON",                           "name": "Na3Zr2Si2PO12",                                               "density": 3.290, "ri": None, "mw": None},
    # LATP Li1.3Al0.3Ti1.7(PO4)3: NASICON-type, a=8.502 c=20.853 Å Z=6 → 2.93 g/cm³
    {"acronym": "LATP",                              "name": "Li1.3Al0.3Ti1.7(PO4)3",                                       "density": 2.930, "ri": None, "mw": None},
    # LAGP Li1.5Al0.5Ge1.5(PO4)3: NASICON-type, a=8.287 c=20.421 Å Z=6 → 3.43 g/cm³
    {"acronym": "LAGP",                              "name": "Li1.5Al0.5Ge1.5(PO4)3",                                       "density": 3.430, "ri": None, "mw": None},
    # ── Bismuth Molybdates (BMO) ──────────────────────────────────────────
    # α-Bi2Mo3O12 monoclinic P21/c a=7.89 b=11.70 c=12.24 Å β=116.33° Z=4
    {"acronym": "α-Bi2Mo3O12",                       "name": "α-Phase Bismuth Molybdate",                                         "density": 5.890, "ri": None, "mw": 897.77},
    # β-Bi2Mo2O9 monoclinic a=11.85 b=11.50 c=12.02 Å β=90.8° Z=8
    {"acronym": "β-Bi2Mo2O9",                        "name": "β-Phase Bismuth Molybdate",                                         "density": 6.110, "ri": None, "mw": 705.77},
    # γ-Bi2MoO6 orthorhombic Pca21 — X-ray density from sintering paper 7.85 g/cm³
    {"acronym": "γ-Bi2MoO6",                         "name": "γ-Phase Bismuth Molybdate",                                         "density": 7.850, "ri": None, "mw": 513.77},
    # ── Silver Molybdates ─────────────────────────────────────────────────
    # Ag2Mo2O7 monoclinic C2/c a=9.23 b=9.95 c=6.85 Å β=107.5° Z=4
    {"acronym": "Ag2Mo2O7",                          "name": "Silver Dimolybdate",                                          "density": 5.960, "ri": None, "mw": 511.61},
    # Ag2MoO4 cubic spinel-type Fd3-m a=9.310 Å Z=8
    {"acronym": "Ag2MoO4",                           "name": "Silver Molybdate",                                            "density": 6.190, "ri": None, "mw": 375.67},
    # ── Titanates (functional ceramics) ──────────────────────────────────
    # CaTiO3 orthorhombic Pbnm a=5.381 b=5.443 c=7.645 Å Z=4
    {"acronym": "CaTiO3",                  "name": "Calcium Titanate (Perovskite)",                                                      "density": 4.030, "ri": 2.35, "mw": 135.94},
    # MgTiO3 ilmenite R3-bar hex a=5.055 c=13.898 Å Z=6
    {"acronym": "MgTiO3",                "name": "Magnesium Titanate (Geikielite)",                                                      "density": 3.890, "ri": 1.94, "mw": 120.19},
    # Mg2TiO4 spinel cubic Fd3-m a=8.442 Å Z=8
    {"acronym": "Mg2TiO4",                           "name": "Magnesium Orthotitanate",                                     "density": 3.540, "ri": 1.95, "mw": 160.49},
    # MgTi2O5 karrooite orthorhombic Bbmm a=9.738 b=9.961 c=3.716 Å Z=4
    {"acronym": "MgTi2O5",                           "name": "Karrooite (Pseudobrookite Structure)",                                                   "density": 3.690, "ri": None, "mw": 200.49},
    # ── Carbonates ────────────────────────────────────────────────────────
    # BaCO3 witherite orthorhombic Pmcn a=5.314 b=8.904 c=6.430 Å Z=4
    {"acronym": "BaCO3",                  "name": "Barium Carbonate (Witherite)",                                                       "density": 4.290, "ri": 1.676, "mw": 197.34},
    # CaCO3 calcite R3-bar-c hex a=4.989 c=17.062 Å Z=6
    {"acronym": "CaCO3",                 "name": "Calcium Carbonate (Calcite)",                                              "density": 2.710, "ri": 1.66, "mw": 100.09},
    # Na2CO3 monoclinic C2/m a=8.920 b=5.244 c=6.050 Å β=101.4° Z=4
    {"acronym": "Na2CO3",                  "name": "Sodium Carbonate",                                                      "density": 2.540, "ri": 1.535, "mw": 105.99},
    # ── Niobium Pentoxide ─────────────────────────────────────────────────
    # T-phase Nb2O5 monoclinic C2, literature value 4.55 g/cm³
    {"acronym": "Nb2O5",                 "name": "Niobium Pentoxide",                                                       "density": 4.550, "ri": 2.19, "mw": 265.81},
    # ── Metals ────────────────────────────────────────────────────────────
    # Gold FCC a=4.078 Å, Z=4 → 19.30 g/cm³ (Wikipedia: 19.30)
    {"acronym": "Au",                              "name": "Gold",                                                          "density": 19.300, "ri": None, "mw": 196.97},
    # Silver FCC a=4.086 Å, Z=4 → 10.49 g/cm³ (Wikipedia: 10.49)
    {"acronym": "Ag",                            "name": "Silver",                                                          "density": 10.490, "ri": None, "mw": 107.87},
    # Copper FCC a=3.615 Å, Z=4 → 8.94 g/cm³ (Wikipedia: 8.96)
    {"acronym": "Cu",                            "name": "Copper",                                                          "density": 8.960, "ri": None, "mw": 63.55},
    # Nickel FCC a=3.524 Å, Z=4 → 8.91 g/cm³ (Wikipedia: 8.908)
    {"acronym": "Ni",                            "name": "Nickel",                                                          "density": 8.908, "ri": None, "mw": 58.69},
    # Titanium α-HCP a=2.951 c=4.684 Å, Z=2 → 4.50 g/cm³ (Wikipedia: 4.506)
    {"acronym": "Ti",                          "name": "Titanium, Commercially Pure",                                                "density": 4.506, "ri": None, "mw": 47.87},
    # Aluminium FCC a=4.050 Å, Z=4 → 2.70 g/cm³ (Wikipedia: 2.70)
    {"acronym": "Al",                         "name": "Aluminium",                                                          "density": 2.700, "ri": None, "mw": 26.98},
    # Iron α-BCC a=2.866 Å, Z=2 → 7.87 g/cm³ (Wikipedia: 7.87)
    {"acronym": "Fe",                              "name": "Iron (α-Ferrite)",                                                        "density": 7.874, "ri": None, "mw": 55.85},
    # 316L SS austenitic: literature 7.96-7.99 g/cm³ (ASTM/ASM Metals Handbook)
    {"acronym": "316L Stainless Steel",              "name": "Fe–Cr18–Ni12–Mo2.5–Mn2, Low Carbon",                                                            "density": 7.980, "ri": None, "mw": None},
    # Inconel alloys — from Special Metals datasheets
    {"acronym": "Inconel 625",                       "name": "Ni–Cr22–Mo9–Nb3.5 Superalloy",                                                            "density": 8.440, "ri": None, "mw": None},
    {"acronym": "Inconel 718",                       "name": "Ni–Cr19–Nb5–Mo3 Precipitation-hardened Superalloy",                                                            "density": 8.190, "ri": None, "mw": None},
    {"acronym": "Inconel 600",                       "name": "Ni–Cr16–Fe8 Superalloy",                                                            "density": 8.470, "ri": None, "mw": None},
    {"acronym": "Inconel X-750",                     "name": "Ni–Cr15–Fe7–Ti2.5–Al0.7 Age-hardened Superalloy",                                                            "density": 8.280, "ri": None, "mw": None},
    # ── Monomers / Oligomers ──────────────────────────────────────────
    {"acronym": "PEG250DA",                         "name": "Polyethylene Glycol 250 Diacrylate",                                                            "density": 1.120, "ri": 1.47, "mw": 250.0},
    {"acronym": "PEG575DA",                         "name": "Polyethylene Glycol 575 Diacrylate",                                                            "density": 1.120, "ri": 1.468, "mw": 575.0},
    {"acronym": "PEG200",                           "name": "Polyethylene Glycol 200",                                                            "density": 1.124, "ri": 1.459, "mw": 200.0},
    {"acronym": "PEG400",                           "name": "Polyethylene Glycol 400",                                                            "density": 1.128, "ri": 1.465, "mw": 400.0},
    {"acronym": "PEG600",                           "name": "Polyethylene Glycol 600",                                                            "density": 1.126, "ri": 1.467, "mw": 600.0},
    {"acronym": "HDDA",                              "name": "1,6-Hexanediol Diacrylate",                                   "density": 1.010, "ri": 1.456, "mw": 226.27},
    {"acronym": "TMPTA",                             "name": "Trimethylolpropane Triacrylate",                              "density": 1.109, "ri": 1.472, "mw": 296.32},
    {"acronym": "TMP(EO)3TA",                        "name": "Trimethylolpropane Ethoxylate (3) Triacrylate",               "density": 1.110, "ri": 1.469, "mw": 428.46},
    {"acronym": "IBOA",                              "name": "Isobornyl Acrylate",                                          "density": 0.986, "ri": 1.474, "mw": 208.3},
    {"acronym": "IBOMA",                             "name": "Isobornyl Methacrylate",                                      "density": 0.988, "ri": 1.477, "mw": 222.32},
    {"acronym": "ACMO",                              "name": "4-Acryloylmorpholine",                                        "density": 1.122, "ri": 1.512, "mw": 141.17},
    {"acronym": "PEG200DA",                          "name": "Polyethylene Glycol 200 Diacrylate",                          "density": 1.110, "ri": 1.464, "mw": 308.33},
    {"acronym": "PEG400DA",                          "name": "Polyethylene Glycol 400 Diacrylate",                          "density": 1.120, "ri": 1.466, "mw": 508.55},
    {"acronym": "PEG600DA",                          "name": "Polyethylene Glycol 600 Diacrylate",                          "density": 1.130, "ri": 1.468, "mw": 708.77},
    {"acronym": "CTFA",                              "name": "Cyclic Trimethylolpropane Formal Acrylate",                   "density": 1.030, "ri": 1.46, "mw": 200.23},
    {"acronym": "MPDDA",                             "name": "2-Methyl-1,3-propanediol Diacrylate",                         "density": 1.020, "ri": 1.454, "mw": 226.27},
    {"acronym": "BEDA",                              "name": "1,4-Butanediol Ethylene Oxide Diacrylate",                    "density": 1.050, "ri": 1.454, "mw": 214.26},
    {"acronym": "BPA(EO)4DA",                        "name": "Bisphenol A Ethoxylate (4) Diacrylate",                       "density": 1.13, "ri": 1.537, "mw": 512.55},
    {"acronym": "BPA(EO)4DMA",                       "name": "Bisphenol A Ethoxylate (4) Dimethacrylate",                   "density": 1.14, "ri": 1.535, "mw": 540.58},
    {"acronym": "BPA(EO)10DMA",                      "name": "Bisphenol A Ethoxylate (10) Dimethacrylate",                  "density": 1.13, "ri": 1.511, "mw": 804.94},
    {"acronym": "DCPA",                              "name": "Dicyclopentanyl Acrylate",                                    "density": 1.06, "ri": 1.49, "mw": 204.27},
    {"acronym": "DiTMPTA",                           "name": "Ditrimethylolpropane Tetraacrylate",                          "density": 1.11, "ri": 1.476, "mw": 466.52},
    {"acronym": "DMAA",                              "name": "Dimethylacrylamide",                                          "density": 1.056, "ri": 1.472, "mw": 99.13},
    {"acronym": "DPGDA",                             "name": "Dipropylene Glycol Diacrylate",                               "density": 1.055, "ri": 1.45, "mw": 242.27},
    {"acronym": "DPHA",                              "name": "Dipentaerythritol Hexaacrylate",                              "density": 1.174, "ri": 1.489, "mw": 578.57},
    {"acronym": "EOEOEA",                            "name": "2-(2-Ethoxyethoxy)ethyl Acrylate",                            "density": 1.01, "ri": 1.437, "mw": 188.22},
    {"acronym": "GPTA",                              "name": "Glycerol Propoxylate Triacrylate",                            "density": 1.107, "ri": 1.461, "mw": 428.46},
    {"acronym": "IDA",                               "name": "Isodecyl Acrylate",                                           "density": 0.884, "ri": 1.44, "mw": 212.33},
    {"acronym": "LA",                                "name": "Lauryl Acrylate",                                             "density": 0.882, "ri": 1.442, "mw": 240.38},
    {"acronym": "NP(EO)4A",                          "name": "Nonylphenol Ethoxylate (4) Acrylate",                         "density": 1.065, "ri": 1.494, "mw": 450.58},
    {"acronym": "NP(EO)8A",                          "name": "Nonylphenol Ethoxylate (8) Acrylate",                         "density": 1.08, "ri": 1.489, "mw": 626.82},
    {"acronym": "NPG(PO)2DA",                        "name": "Neopentyl Glycol Propoxylate Diacrylate",                     "density": 1.02, "ri": 1.446, "mw": 328.4},
    {"acronym": "PEG200DMA",                         "name": "Polyethylene Glycol 200 Dimethacrylate",                      "density": 1.1, "ri": 1.463, "mw": 336.38},
    {"acronym": "PEG300DA",                          "name": "Polyethylene Glycol 300 Diacrylate",                          "density": 1.115, "ri": 1.466, "mw": 408.44},
    {"acronym": "PEG400DMA",                         "name": "Polyethylene Glycol 400 Dimethacrylate",                      "density": 1.11, "ri": 1.466, "mw": 536.61},
    {"acronym": "PETA",                              "name": "Pentaerythritol Triacrylate",                                 "density": 1.174, "ri": 1.48, "mw": 298.29},
    {"acronym": "PH(EO)4A",                          "name": "Phenol Ethoxylate (4) Acrylate",                              "density": 1.095, "ri": 1.5, "mw": 324.37},
    {"acronym": "PHEA",                              "name": "Phenoxyethyl Acrylate",                                       "density": 1.107, "ri": 1.517, "mw": 192.21},
    {"acronym": "PPTTA",                             "name": "Pentaerythritol Propoxylate Tetraacrylate",                   "density": 1.12, "ri": 1.471, "mw": 572.62},
    {"acronym": "TCDDA",                             "name": "Tricyclodecane Dimethanol Diacrylate",                        "density": 1.1, "ri": 1.503, "mw": 304.38},
    {"acronym": "TEGDMA",                            "name": "Triethylene Glycol Dimethacrylate",                           "density": 1.075, "ri": 1.461, "mw": 286.32},
    {"acronym": "TMP(EO)6TA",                        "name": "Trimethylolpropane Ethoxylate (6) Triacrylate",               "density": 1.09, "ri": 1.47, "mw": 560.62},
    {"acronym": "TMP(EO)9TA",                        "name": "Trimethylolpropane Ethoxylate (9) Triacrylate",               "density": 1.095, "ri": 1.469, "mw": 692.79},
    {"acronym": "TMP(EO)15TA",                       "name": "Trimethylolpropane Ethoxylate (15) Triacrylate",              "density": 1.1, "ri": 1.471, "mw": 956.13},
    {"acronym": "TMP(PO)3TA",                        "name": "Trimethylolpropane Propoxylate Triacrylate",                  "density": 1.06, "ri": 1.459, "mw": 470.55},
    {"acronym": "TMCHA",                             "name": "3,3,5-Trimethylcyclohexyl Acrylate",                          "density": 1.003, "ri": 1.453, "mw": 196.29},
    {"acronym": "TPGDA",                             "name": "Tripropylene Glycol Diacrylate",                              "density": 1.051, "ri": 1.45, "mw": 300.35},
    # ── Salts / Additives ─────────────────────────────────────────────
    {"acronym": "LiTFSI",                            "name": "",                                                            "density": 1.330, "ri": None, "mw": 287.09},
    {"acronym": "KH-570",                            "name": "3-Methacryloxypropyltrimethoxysilane",                                                        "density": 1.045, "ri": 1.429, "mw": 248.36},
    # ── Photoinitiators ───────────────────────────────────────────────
    {"acronym": "BAPO",                              "name": "Bis(2,4,6-trimethylbenzoyl)phenylphosphine oxide",            "density": 1.190, "ri": None, "mw": 418.41},
    {"acronym": "TPO",                               "name": "2,4,6-Trimethylbenzoyldiphenylphosphine Oxide",               "density": 1.218, "ri": None, "mw": 348.37},
    {"acronym": "TPO-L",                             "name": "Ethyl(2,4,6-trimethylbenzoyl)phenylphosphinate",              "density": 1.140, "ri": None, "mw": 316.32},
    {"acronym": "ITX",                               "name": "2-Isopropylthioxanthone",                                     "density": 1.200, "ri": None, "mw": 254.33},
    {"acronym": "DETX",                              "name": "2,4-Diethylthioxanthone",                                     "density": 1.1780, "ri": 1.631, "mw": 268.37},
    {"acronym": "CQ",                                "name": "Camphorquinone",                                              "density": 0.982, "ri": None, "mw": 166.17},
    # ── Photoinitiators & co-initiators ──────────────────────────────────────
    {"acronym": "ABD",                               "name": "Poly(oxy-1,2-ethanediyl) Aminobenzoate",                      "density": 1.1, "ri": None, "mw": None},
    {"acronym": "BDK",                               "name": "2,2-Dimethoxy-2-phenylacetophenone",                          "density": 1.19, "ri": None, "mw": 256.3},
    {"acronym": "BDMM",                              "name": "2-Benzyl-2-(dimethylamino)-1-(4-morpholinophenyl)butanone",   "density": 1.13, "ri": None, "mw": 368.47},
    {"acronym": "BMS",                               "name": "4-Benzoyl-4'-methyldiphenyl Sulphide",                        "density": 1.2, "ri": None, "mw": 320.43},
    {"acronym": "BP",                                "name": "Benzophenone",                                                "density": 1.11, "ri": 1.611, "mw": 182.22},
    {"acronym": "DEAP",                              "name": "2,2-Diethoxyacetophenone",                                    "density": 1.02, "ri": None, "mw": 196.24},
    {"acronym": "EHA",                               "name": "2-Ethylhexyl 4-dimethylaminobenzoate",                        "density": 1.01, "ri": None, "mw": 277.4},
    {"acronym": "EMK",                               "name": "4,4'-Bis(diethylamino)benzophenone",                          "density": 1.06, "ri": None, "mw": 268.36},
    {"acronym": "EPD",                               "name": "Ethyl 4-dimethylaminobenzoate",                               "density": 1.095, "ri": None, "mw": 193.24},
    {"acronym": "HCPK",                              "name": "1-Hydroxycyclohexyl Phenyl Ketone",                           "density": 1.17, "ri": None, "mw": 204.27},
    {"acronym": "HMPP",                              "name": "2-Hydroxy-2-methylpropiophenone",                             "density": 1.073, "ri": None, "mw": 164.2},
    {"acronym": "Irg2959",                           "name": "2-Hydroxy-4'-(2-hydroxyethoxy)-2-methylpropiophenone",        "density": 1.183, "ri": None, "mw": 224.25},
    {"acronym": "Irg784",                            "name": "Bis(eta5-cyclopentadienyl)bis(2,6-difluorophenyl)titanium",   "density": 1.54, "ri": None, "mw": 494.37},
    {"acronym": "LAP",                               "name": "Lithium Phenyl-2,4,6-trimethylbenzoylphosphinate",            "density": 1.3, "ri": None, "mw": 286.24},
    {"acronym": "MBB",                               "name": "Methyl 2-benzoylbenzoate",                                    "density": 1.22, "ri": None, "mw": 240.26},
    {"acronym": "MBF",                               "name": "Methyl Benzoylformate",                                       "density": 1.19, "ri": None, "mw": 164.16},
    {"acronym": "MDEA",                              "name": "N-Methyldiethanolamine",                                      "density": 1.038, "ri": 1.468, "mw": 119.16},
    {"acronym": "PBZ",                               "name": "4-Phenylbenzophenone",                                        "density": 1.2, "ri": None, "mw": 258.32},
    {"acronym": "PMP",                               "name": "2-Methyl-1-(4-methylthiophenyl)-2-morpholinopropan-1-one",    "density": 1.18, "ri": None, "mw": 279.36},
    # ── Dispersants (BYK) ─────────────────────────────────────────────
    {"acronym": "DISPERBYK-103",                     "name": "Polyester Phosphoric Acid Ester Salt",                                                            "density": 1.060, "ri": None, "mw": None},
    {"acronym": "DISPERBYK-108",                     "name": "Hydroxy-functional Carboxylic Ester with Pigment-affinic Groups",                                                            "density": 0.940, "ri": None, "mw": None},
    {"acronym": "DISPERBYK-111",                     "name": "Phosphoric Acid Ester",                                                            "density": 1.160, "ri": None, "mw": None},
    {"acronym": "DISPERBYK-118",                     "name": "Polymeric Phosphoric Acid Ester",                                                            "density": 1.070, "ri": None, "mw": None},
    {"acronym": "DISPERBYK-145",                     "name": "Phosphoric Ester Copolymer",                                                            "density": 1.070, "ri": None, "mw": None},
    {"acronym": "DISPERBYK-168",                     "name": "Modified Polyurethane",                                                            "density": 1.100, "ri": None, "mw": None},
    {"acronym": "DISPERBYK-180",                     "name": "Alkylolammonium Salt of Acidic Copolymer",                                                            "density": 1.080, "ri": None, "mw": None},
    {"acronym": "DISPERBYK-2013",                    "name": "Styrene-maleic Anhydride Copolymer",                                                            "density": 1.100, "ri": None, "mw": None},
    {"acronym": "DISPERBYK-2030",                    "name": "High Molecular Weight Copolymer",                                                            "density": 1.040, "ri": None, "mw": None},
    {"acronym": "BYK-W 969",                         "name": "Hydroxy-functional Alkylammonium Salt of Acidic Copolymer",                                                            "density": 1.090, "ri": 1.52, "mw": None},
    {"acronym": "BYK-W 980",                         "name": "Salt of Unsaturated Polyamine Amides and Acidic Polyesters",                                                            "density": 0.990, "ri": None, "mw": None},
    {"acronym": "BYKJET-9142",                       "name": "Polymeric Carboxylic Acid Ester",                                                            "density": 1.010, "ri": None,  "mw": None},
    {"acronym": "TEGO Foamex N",                     "name": "Polydimethylsiloxane Defoamer (contains Silica)",                                           "density": 1.000, "ri": None,  "mw": None},
    {"acronym": "ALS",                               "name": "Ammonium Lauryl Sulfate (Ammonium Dodecyl Sulfate)",                                        "density": 1.059, "ri": None,  "mw": 283.43},
    {"acronym": "SLS",                               "name": "Sodium Lauryl Sulfate (Sodium Dodecyl Sulfate)",                                            "density": 1.010, "ri": None,  "mw": 288.38},
    {"acronym": "β-Alanine",                         "name": "Beta-Alanine (3-Aminopropanoic Acid)",                                                      "density": 1.437, "ri": 1.465, "mw": 89.09},
    {"acronym": "PVP",                               "name": "Polyvinylpyrrolidone (Povidone)",                                                           "density": 1.200, "ri": 1.530, "mw": None},
    {"acronym": "NVP",                               "name": "N-Vinylpyrrolidone (1-Vinyl-2-Pyrrolidinone)",                                              "density": 1.040, "ri": 1.512, "mw": 111.14},
    {"acronym": "VMOX",                              "name": "Vinyl Methyl Oxazolidinone (3-Ethenyl-5-Methyl-1,3-Oxazolidin-2-One)",                     "density": 1.085, "ri": None,  "mw": 127.14},
    # ── Non-ionic surfactants ─────────────────────────────────────────────
    {"acronym": "Triton X-100",                      "name": "",                                                            "density": 1.065, "ri": 1.49, "mw": 647.0},
    # ── Darvan dispersants (Vanderbilt Minerals) — densities from official TDS ──
    {"acronym": "Darvan C-N",                        "name": "Ammonium Polymethacrylate, 25% Aq.",                          "density": 1.120, "ri": None, "mw": None},
    {"acronym": "Darvan 821-A",                      "name": "Ammonium Polyacrylate, 40% Aq.",                              "density": 1.160, "ri": None, "mw": None},
    {"acronym": "Darvan 7-N",                        "name": "Sodium Polymethacrylate, 25% Aq.",                            "density": 1.160, "ri": None, "mw": None},
    {"acronym": "Darvan 811",                        "name": "Sodium Polyacrylate, 43% Aq.",                                "density": 1.300, "ri": None, "mw": None},
    # ── Anionic dispersants (non-aqueous / universal) ─────────────────────
    {"acronym": "Oleic acid",                        "name": "(9Z)-Octadec-9-enoic Acid",                                                            "density": 0.895, "ri": 1.461, "mw": 282.46},
    {"acronym": "Stearic acid",                      "name": "Octadecanoic Acid",                                                       "density": 0.847, "ri": 1.43, "mw": 284.48},
    {"acronym": "Citric acid",                       "name": "Citric Acid (2-Hydroxypropane-1,2,3-tricarboxylic Acid)",                                                       "density": 1.665, "ri": 1.498, "mw": 192.12},
    {"acronym": "Polyacrylic acid",                  "name": "Poly(acrylic acid)",                                                         "density": 1.150, "ri": 1.527, "mw": None},
    # ── Cationic dispersants ─────────────────────────────────────────────
    {"acronym": "Polyethyleneimine",                 "name": "Poly(ethyleneimine), Branched",                                               "density": 1.030, "ri": 1.55, "mw": None},
    # ── Solvents ──────────────────────────────────────────────────────
    {"acronym": "Ethanol",                           "name": "",                                                            "density": 0.789, "ri": 1.361, "mw": 46.07},
    {"acronym": "Isopropanol",                       "name": "Isopropyl Alcohol",                                                         "density": 0.786, "ri": 1.377, "mw": 60.1},
    {"acronym": "Water",                             "name": "H2O",                                                         "density": 1.000, "ri": 1.333, "mw": 18.02},
    # F127 (Pluronic F-127 / Poloxamer 407) aqueous solutions in DIW
    # Experimental densities — effective hydrated F127 density ~1.06 g/cm³ in solution
    {"acronym": "F127 5 wt.% in DIW",                "name": "",                                                            "density": 1.003, "ri": 1.334, "mw": None},
    {"acronym": "F127 10 wt.% in DIW",               "name": "",                                                            "density": 1.006, "ri": 1.335, "mw": None},
    {"acronym": "F127 15 wt.% in DIW",               "name": "",                                                            "density": 1.009, "ri": 1.336, "mw": None},
    {"acronym": "F127 20 wt.% in DIW",               "name": "",                                                            "density": 1.011, "ri": 1.337, "mw": None},
    {"acronym": "F127 25 wt.% in DIW",               "name": "",                                                            "density": 1.014, "ri": 1.338, "mw": None},
    {"acronym": "F127 30 wt.% in DIW",               "name": "",                                                            "density": 1.017, "ri": 1.339, "mw": None},
    {"acronym": "Glycerol",                          "name": "",                                                            "density": 1.261, "ri": 1.474, "mw": 92.09},
    {"acronym": "DMSO",                              "name": "Dimethyl Sulfoxide",                                          "density": 1.100, "ri": 1.479, "mw": 78.13},
    {"acronym": "Toluene",                           "name": "",                                                            "density": 0.867, "ri": 1.497, "mw": 92.14},
    {"acronym": "Cyclohexanone",                     "name": "",                                                            "density": 0.947, "ri": 1.451, "mw": 98.14},
    {"acronym": "Propylene Carbonate",               "name": "4-Methyl-1,3-dioxolan-2-one",                                                          "density": 1.205, "ri": 1.421, "mw": 102.09},
    {"acronym": "Mineral Oil",                       "name": "Mineral Oil, Light Grade",                                                       "density": 0.860, "ri": 1.47, "mw": None},
    {"acronym": "DINP",                              "name": "Diisononyl Phthalate",                                        "density": 0.970, "ri": 1.486, "mw": 418.61},
    {"acronym": "PPG-400",                           "name": "Polypropylene Glycol 400",                                    "density": 1.036, "ri": 1.45, "mw": 400.0},
    {"acronym": "EGDA",                              "name": "Ethylene Glycol Diacetate",                                   "density": 1.104, "ri": 1.415, "mw": 146.14},
]

# ─────────────────────────────────────────────
#  MATERIALS DATABASE
# ─────────────────────────────────────────────
def _app_data_dir():
    """Return a writable directory for persistent app data.
    • Frozen .exe: %%APPDATA%%\\3DPrintingFormulator  (survives Program Files installs)
    • Dev mode (.py): script directory (existing behaviour unchanged)
    """
    if getattr(sys, 'frozen', False):
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        d = os.path.join(base, '3DPrintingFormulator')
    else:
        d = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(d, exist_ok=True)
    return d

def _db_path():
    return os.path.join(_app_data_dir(), "3dpformulator_materialsdatabase.json")

def _migrate_entry(m):
    """Convert old single-name format to new acronym/name split."""
    if "acronym" in m:
        return m
    combined = m.get("name", "")
    if " (" in combined:
        idx = combined.index(" (")
        acronym  = combined[:idx]
        fullname = combined[idx+2:].rstrip(")")
    else:
        acronym  = combined
        fullname = ""
    return {"acronym": acronym, "name": fullname,
            "density": float(m.get("density", 1.0)),
            "ri": m.get("ri", None), "mw": m.get("mw", None)}

def load_materials_db():
    path = _db_path()
    if os.path.exists(path):
        try:
            with open(path) as f:
                return [_migrate_entry(m) for m in json.load(f)]
        except Exception:
            pass
    # First run — seed with defaults and save
    save_materials_db(DEFAULT_MATERIALS)
    return DEFAULT_MATERIALS[:]

def save_materials_db(materials):
    try:
        with open(_db_path(), "w") as f:
            json.dump(sorted(materials, key=lambda m: m["acronym"].lower()), f, indent=2)
    except Exception as e:
        messagebox.showerror(_T("DB Error"), f"Could not save materials database:\n{e}")


# ─────────────────────────────────────────────
#  APP SETTINGS  (persistence + apply helpers)
# ─────────────────────────────────────────────
SETTINGS_DEFAULTS = {
    "font_scale":           "Normal",   # Small | Normal | Large | Extra Large
    "confirm_destructive":  True,       # prompt before Remove / Clear All
    "colorblind_mode":      False,      # CB-safe palette (blue/orange instead of green/red)
    "high_contrast":        False,      # dark theme
    "large_targets":        False,      # bigger button padding for touch/motor accessibility
    "language":             "en",       # UI language code
}

FONT_SCALE_MAP = {
    "Small":       1.25,
    "Normal":      1.5,
    "Large":       1.75,
    "Extra Large": 2.1,
}

def _settings_path():
    return os.path.join(_app_data_dir(), "3dpformulator_usersettings.json")

def load_settings():
    path = _settings_path()
    if os.path.exists(path):
        try:
            with open(path) as f:
                stored = json.load(f)
            s = dict(SETTINGS_DEFAULTS)
            s.update(stored)
            return s
        except Exception:
            pass
    return dict(SETTINGS_DEFAULTS)

def save_settings(s):
    try:
        with open(_settings_path(), "w") as f:
            json.dump(s, f, indent=2)
    except Exception as e:
        messagebox.showerror(_T("Settings Error"), f"Could not save settings:\n{e}")

# Global scale factor — ratio of current font scale to the base (1.25).
# Multiply any hardcoded pixel dimension by _SF to make it scale-aware.
# Base is 1.25 (Small), so Normal(1.5) → _SF=1.20, Large(1.75) → _SF=1.40
_SF = 1.20   # default: Normal

def _apply_font_scale(root, scale_label):
    global _SF
    factor = FONT_SCALE_MAP.get(scale_label, 1.5)
    root.tk.call('tk', 'scaling', factor)
    _SF = factor / 1.25   # scale relative to the Small baseline

def _apply_cjk_font(lang_code):
    """Switch to a CJK/Devanagari-capable font when needed.
    Falls back silently if the font is not installed."""
    special = {"zh", "ja", "ko", "hi"}
    if lang_code not in special:
        return
    candidates = {
        "zh": ["Microsoft YaHei", "SimSun", "Arial Unicode MS"],
        "ja": ["Meiryo", "MS Gothic", "Yu Gothic", "Arial Unicode MS"],
        "ko": ["Malgun Gothic", "Gulim", "Arial Unicode MS"],
        "hi": ["Nirmala UI", "Mangal", "Arial Unicode MS"],
    }
    try:
        import tkinter.font as tkfont
        available = set(tkfont.families())
        for font_name in candidates.get(lang_code, []):
            if font_name in available:
                tkfont.nametofont("TkDefaultFont").configure(family=font_name)
                tkfont.nametofont("TkTextFont").configure(family=font_name)
                tkfont.nametofont("TkFixedFont").configure(family=font_name)
                return
    except Exception:
        pass

def _s(px):
    """Scale a pixel dimension by the current font scale factor."""
    return max(1, int(round(px * _SF)))

def _apply_colorblind(enabled):
    global BTN_GREEN, BTN_RED
    if enabled:
        BTN_GREEN = "#0077BB"
        BTN_RED   = "#EE7733"
    else:
        BTN_GREEN = "#16A34A"
        BTN_RED   = "#DC2626"

def _apply_high_contrast(root, enabled):
    global BG, BG_WHITE, BG_HDR, BG_ALT, TEXT, TEXT_DIM, TEXT_MUTED
    global BORDER, BORDER_MED, TOTAL_BG
    if enabled:
        BG         = "#1A1A2E"; BG_WHITE   = "#16213E"; BG_HDR    = "#0F3460"
        BG_ALT     = "#1A1A2E"; TEXT       = "#E0E0E0"; TEXT_DIM  = "#A0A0B0"
        TEXT_MUTED = "#7070A0"; BORDER     = "#2A2A4E"; BORDER_MED= "#3A3A6E"
        TOTAL_BG   = "#0F3460"
    else:
        BG         = "#EEF2F8"; BG_WHITE   = "#FFFFFF"; BG_HDR    = "#F5F7FC"
        BG_ALT     = "#F8FAFD"; TEXT       = "#0F172A"; TEXT_DIM  = "#334155"
        TEXT_MUTED = "#64748B"; BORDER     = "#E2E8F4"; BORDER_MED= "#C5CEDF"
        TOTAL_BG   = "#DBEAFE"
    root.configure(bg=BG)

def _apply_large_targets(enabled):
    """Increase button padx/pady for easier clicking on touch screens."""
    global _BTN_PADX, _BTN_PADY
    if enabled:
        _BTN_PADX = 20
        _BTN_PADY = 10
    else:
        _BTN_PADX = 14
        _BTN_PADY = 6

# Default button padding values — overridden by large_targets setting
_BTN_PADX = 14
_BTN_PADY = 6

# ─────────────────────────────────────────────
#  INTERNATIONALISATION
# ─────────────────────────────────────────────
# Language codes and display names for the Settings dropdown.
LANGUAGES = {
    "en": "English",
    "el": "Ελληνικά (Greek)",
    "fr": "Français (French)",
    "de": "Deutsch (German)",
    "es": "Español (Spanish)",
    "it": "Italiano (Italian)",
    "nl": "Nederlands (Dutch)",
    "zh": "中文 (Chinese)",
    "ja": "日本語 (Japanese)",
    "ko": "한국어 (Korean)",
    "hi": "हिन्दी (Hindi)",
}


TRANSLATIONS = {

"el": {  # Greek
    "Inverse Solver": "Αντίστροφος Επιλύτης",
    "Forward Formulator": "Άμεσος Υπολογισμός",
    "Materials DB": "Β.Δ. Υλικών",
    "Settings": "Ρυθμίσεις",
    "Help": "Βοήθεια",
    "Recipe / File Name:": "Όνομα Συνταγής / Αρχείου:",
    "💾 Save": "💾 Αποθήκευση",
    "📂 Load": "📂 Φόρτωση",
    "📄 Export PDF": "📄 Εξαγωγή PDF",
    "📤 Share": "📤 Κοινοποίηση",
    "➕ Add": "➕ Προσθήκη",
    "✏ Update": "✏ Ενημέρωση",
    "🗑 Remove": "🗑 Αφαίρεση",
    "▲ Up": "▲ Πάνω",
    "▼ Down": "▼ Κάτω",
    "✖ Clear All": "✖ Εκκαθάριση",
    "⚙ SOLVE": "⚙ ΕΠΙΛΥΣΗ",
    "⚙ CALCULATE": "⚙ ΥΠΟΛΟΓΙΣΜΟΣ",
    "➕ Add / Update": "➕ Προσθήκη / Ενημέρωση",
    "🗑 Delete": "🗑 Διαγραφή",
    "⊕ Create Blend": "⊕ Δημιουργία Μίγματος",
    "✖ Clear fields": "✖ Εκκαθάριση πεδίων",
    "📤 Export DB": "📤 Εξαγωγή Β.Δ.",
    "📥 Import DB": "📥 Εισαγωγή Β.Δ.",
    "💾 Save to Database": "💾 Αποθήκευση στη Β.Δ.",
    "⟳ Calculate density": "⟳ Υπολογισμός πυκνότητας",
    "− Remove last": "− Αφαίρεση τελευταίου",
    "Apply": "Εφαρμογή",
    "Cancel": "Ακύρωση",
    "✔  OK": "✔  ΟΚ",
    "✕  Cancel": "✕  Ακύρωση",
    "✖ Cancel": "✖ Ακύρωση",
    "✔ Close": "✔ Κλείσιμο",
    "✕  Close": "✕  Κλείσιμο",
    "Restore Defaults": "Επαναφορά Προεπιλογών",
    "Component:": "Συστατικό:",
    "Input Mode:": "Τρόπος Εισόδου:",
    "Value:": "Τιμή:",
    "Reference:": "Αναφορά:",
    "Relationship:": "Σχέση:",
    "Primary mode:": "Κύρια Ποσότητα:",
    "Target:": "Στόχος:",
    "Density (g/cm³):": "Πυκνότητα (g/cm³):",
    "Acronym:": "Ακρωνύμιο:",
    "Full Name:": "Πλήρες Όνομα:",
    "RI:": "ΔΔ:",
    "MW (g/mol):": "ΜΒ (g/mol):",
    "Search:": "Αναζήτηση:",
    "Database file:": "Αρχείο Β.Δ.:",
    "Blend name:": "Όνομα Μίγματος:",
    "Blend density:": "Πυκνότητα Μίγματος:",
    "Material": "Υλικό",
    "⚙  Settings": "⚙  Ρυθμίσεις",
    "APPEARANCE": "ΕΜΦΑΝΙΣΗ",
    "BEHAVIOUR": "ΣΥΜΠΕΡΙΦΟΡΑ",
    "ABOUT": "ΠΛΗΡΟΦΟΡΙΕΣ",
    "Font size:": "Μέγεθος γραμματοσειράς:",
    "High contrast mode  (dark theme)": "Υψηλή αντίθεση  (σκοτεινό θέμα)",
    "Colour-blind safe palette  (swaps red/green → blue/orange)": "Παλέτα για χρωματοτυφλία  (μπλε/πορτοκαλί αντί κόκκινο/πράσινο)",
    "Ask for confirmation before removing or clearing components": "Επιβεβαίωση πριν την αφαίρεση ή εκκαθάριση",
    "Larger click targets  (increases button padding — easier to click)": "Μεγαλύτερα κουμπιά  (ευκολότερο κλικ)",
    "Help & User Guide": "Βοήθεια & Οδηγός Χρήστη",
    "Topics": "Θέματα",
    "Cleared.": "Εκκαθαρίστηκε.",
    "Click a row first.": "Επιλέξτε πρώτα μια γραμμή.",
    "No components.": "Δεν υπάρχουν συστατικά.",
    "Calculate first.": "Υπολογίστε πρώτα.",
    "Solve first.": "Επιλύστε πρώτα.",
    "Settings applied.": "Οι ρυθμίσεις εφαρμόστηκαν.",
    "Select a material first.": "Επιλέξτε πρώτα υλικό.",
    "Input": "Εισαγωγή",
    "Duplicate": "Διπλότυπο",
    "Duplicates": "Διπλότυπα",
    "Error": "Σφάλμα",
    "DB Error": "Σφάλμα Β.Δ.",
    "Load Error": "Σφάλμα Φόρτωσης",
    "PDF Error": "Σφάλμα PDF",
    "Settings Error": "Σφάλμα Ρυθμίσεων",
    "Solver Error": "Σφάλμα Επιλύτη",
    "Export": "Εξαγωγή",
    "Import": "Εισαγωγή",
    "Share": "Κοινοποίηση",
    "No Results": "Δεν υπάρχουν αποτελέσματα",
    "Saved": "Αποθηκεύτηκε",
    "Overwrite": "Αντικατάσταση",
    "Minimum": "Ελάχιστο",
    "Limit": "Όριο",
    "Create Blend": "Δημιουργία Μίγματος",
    "Materials Database": "Βάση Δεδομένων Υλικών",
    "The 3D Printing Formulator": "The 3D Printing Formulator",
    "Help & User Guide — The 3D Printing Formulator": "Βοήθεια — The 3D Printing Formulator",
    "Acronym cannot be empty.": "Το ακρωνύμιο δεν μπορεί να είναι κενό.",
    "Density must be a number.": "Η πυκνότητα πρέπει να είναι αριθμός.",
    "RI must be a number or blank.": "Ο ΔΔ πρέπει να είναι αριθμός ή κενός.",
    "MW must be a number or blank.": "Το ΜΒ πρέπει να είναι αριθμός ή κενό.",
    "Names must be unique.": "Τα ονόματα πρέπει να είναι μοναδικά.",
    "Values must be numbers.": "Οι τιμές πρέπει να είναι αριθμοί.",
    "A blend needs at least 2 components.": "Το μίγμα χρειάζεται τουλάχιστον 2 συστατικά.",
    "Please enter a name for the blend.": "Εισάγετε όνομα για το μίγμα.",
    "Remove all components?": "Αφαίρεση όλων των συστατικών;",
    "Remove all?": "Αφαίρεση όλων;",
    "Define a monomer blend. Enter wt.% for each component": "Ορίστε μίγμα μονομερών. Εισάγετε wt.% για κάθε συστατικό",
    "File does not appear to be a valid materials database.": "Το αρχείο δεν φαίνεται να είναι έγκυρη βάση δεδομένων.",
    "Exactly 1 Primary component required. Found {n}.": "Απαιτείται ακριβώς 1 Κύριο συστατικό. Βρέθηκαν: {n}.",
    "by Dr Thanos Goulas  ·  v1.0": "Copyright © 2026 Dr Thanos Goulas  ·  v1.0",
    "The 3D Printing": "The 3D Printing",
    "Formulator": "Formulator",
},

"fr": {  # French
    "Inverse Solver": "Solveur Inverse",
    "Forward Formulator": "Formulation Directe",
    "Materials DB": "Base Matériaux",
    "Settings": "Paramètres",
    "Help": "Aide",
    "Recipe / File Name:": "Nom de la Recette / Fichier :",
    "💾 Save": "💾 Enregistrer",
    "📂 Load": "📂 Charger",
    "📄 Export PDF": "📄 Exporter PDF",
    "📤 Share": "📤 Partager",
    "➕ Add": "➕ Ajouter",
    "✏ Update": "✏ Modifier",
    "🗑 Remove": "🗑 Supprimer",
    "▲ Up": "▲ Haut",
    "▼ Down": "▼ Bas",
    "✖ Clear All": "✖ Tout effacer",
    "⚙ SOLVE": "⚙ RÉSOUDRE",
    "⚙ CALCULATE": "⚙ CALCULER",
    "➕ Add / Update": "➕ Ajouter / Modifier",
    "🗑 Delete": "🗑 Supprimer",
    "⊕ Create Blend": "⊕ Créer un mélange",
    "✖ Clear fields": "✖ Vider les champs",
    "📤 Export DB": "📤 Exporter BD",
    "📥 Import DB": "📥 Importer BD",
    "💾 Save to Database": "💾 Enregistrer dans la BD",
    "⟳ Calculate density": "⟳ Calculer la densité",
    "− Remove last": "− Supprimer le dernier",
    "Apply": "Appliquer",
    "Cancel": "Annuler",
    "✔  OK": "✔  OK",
    "✕  Cancel": "✕  Annuler",
    "✖ Cancel": "✖ Annuler",
    "✔ Close": "✔ Fermer",
    "✕  Close": "✕  Fermer",
    "Restore Defaults": "Restaurer les défauts",
    "Component:": "Composant :",
    "Input Mode:": "Mode de saisie :",
    "Value:": "Valeur :",
    "Reference:": "Référence :",
    "Relationship:": "Relation :",
    "Primary mode:": "Quantité principale :",
    "Target:": "Cible :",
    "Density (g/cm³):": "Densité (g/cm³) :",
    "Acronym:": "Acronyme :",
    "Full Name:": "Nom complet :",
    "RI:": "IR :",
    "MW (g/mol):": "PM (g/mol) :",
    "Search:": "Recherche :",
    "Database file:": "Fichier de base de données :",
    "Blend name:": "Nom du mélange :",
    "Blend density:": "Densité du mélange :",
    "Material": "Matériau",
    "⚙  Settings": "⚙  Paramètres",
    "APPEARANCE": "APPARENCE",
    "BEHAVIOUR": "COMPORTEMENT",
    "ABOUT": "À PROPOS",
    "Font size:": "Taille de police :",
    "High contrast mode  (dark theme)": "Mode contraste élevé  (thème sombre)",
    "Colour-blind safe palette  (swaps red/green → blue/orange)": "Palette daltonien  (bleu/orange au lieu de rouge/vert)",
    "Ask for confirmation before removing or clearing components": "Confirmer avant de supprimer ou effacer des composants",
    "Larger click targets  (increases button padding — easier to click)": "Boutons plus grands  (plus faciles à cliquer)",
    "Help & User Guide": "Aide et Guide Utilisateur",
    "Topics": "Rubriques",
    "Cleared.": "Effacé.",
    "Click a row first.": "Sélectionnez d'abord une ligne.",
    "No components.": "Aucun composant.",
    "Calculate first.": "Calculez d'abord.",
    "Solve first.": "Résolvez d'abord.",
    "Settings applied.": "Paramètres appliqués.",
    "Select a material first.": "Sélectionnez d'abord un matériau.",
    "Input": "Saisie",
    "Duplicate": "Doublon",
    "Duplicates": "Doublons",
    "Error": "Erreur",
    "DB Error": "Erreur BD",
    "Load Error": "Erreur de chargement",
    "PDF Error": "Erreur PDF",
    "Settings Error": "Erreur de paramètres",
    "Solver Error": "Erreur du solveur",
    "Export": "Exporter",
    "Import": "Importer",
    "Share": "Partager",
    "No Results": "Aucun résultat",
    "Saved": "Enregistré",
    "Overwrite": "Écraser",
    "Minimum": "Minimum",
    "Limit": "Limite",
    "Create Blend": "Créer un mélange",
    "Materials Database": "Base de données des matériaux",
    "The 3D Printing Formulator": "The 3D Printing Formulator",
    "Help & User Guide — The 3D Printing Formulator": "Aide — The 3D Printing Formulator",
    "Acronym cannot be empty.": "L'acronyme ne peut pas être vide.",
    "Density must be a number.": "La densité doit être un nombre.",
    "RI must be a number or blank.": "L'IR doit être un nombre ou vide.",
    "MW must be a number or blank.": "Le PM doit être un nombre ou vide.",
    "Names must be unique.": "Les noms doivent être uniques.",
    "Values must be numbers.": "Les valeurs doivent être des nombres.",
    "A blend needs at least 2 components.": "Un mélange nécessite au moins 2 composants.",
    "Please enter a name for the blend.": "Veuillez saisir un nom pour le mélange.",
    "Remove all components?": "Supprimer tous les composants ?",
    "Remove all?": "Tout supprimer ?",
    "Define a monomer blend. Enter wt.% for each component": "Définir un mélange de monomères. Entrez wt.% pour chaque composant",
    "File does not appear to be a valid materials database.": "Le fichier ne semble pas être une base de données valide.",
    "Exactly 1 Primary component required. Found {n}.": "Exactement 1 composant Principal requis. Trouvé : {n}.",
    "by Dr Thanos Goulas  ·  v1.0": "Copyright © 2026 Dr Thanos Goulas  ·  v1.0",
    "The 3D Printing": "The 3D Printing",
    "Formulator": "Formulator",
},

"de": {  # German
    "Inverse Solver": "Inverser Löser",
    "Forward Formulator": "Vorwärtsberechnung",
    "Materials DB": "Materialdatenbank",
    "Settings": "Einstellungen",
    "Help": "Hilfe",
    "Recipe / File Name:": "Rezept- / Dateiname:",
    "💾 Save": "💾 Speichern",
    "📂 Load": "📂 Laden",
    "📄 Export PDF": "📄 PDF exportieren",
    "📤 Share": "📤 Teilen",
    "➕ Add": "➕ Hinzufügen",
    "✏ Update": "✏ Aktualisieren",
    "🗑 Remove": "🗑 Entfernen",
    "▲ Up": "▲ Hoch",
    "▼ Down": "▼ Runter",
    "✖ Clear All": "✖ Alle löschen",
    "⚙ SOLVE": "⚙ LÖSEN",
    "⚙ CALCULATE": "⚙ BERECHNEN",
    "➕ Add / Update": "➕ Hinzufügen / Aktualisieren",
    "🗑 Delete": "🗑 Löschen",
    "⊕ Create Blend": "⊕ Mischung erstellen",
    "✖ Clear fields": "✖ Felder leeren",
    "📤 Export DB": "📤 DB exportieren",
    "📥 Import DB": "📥 DB importieren",
    "💾 Save to Database": "💾 In DB speichern",
    "⟳ Calculate density": "⟳ Dichte berechnen",
    "− Remove last": "− Letzten entfernen",
    "Apply": "Übernehmen",
    "Cancel": "Abbrechen",
    "✔  OK": "✔  OK",
    "✕  Cancel": "✕  Abbrechen",
    "✖ Cancel": "✖ Abbrechen",
    "✔ Close": "✔ Schließen",
    "✕  Close": "✕  Schließen",
    "Restore Defaults": "Standard wiederherstellen",
    "Component:": "Komponente:",
    "Input Mode:": "Eingabemodus:",
    "Value:": "Wert:",
    "Reference:": "Referenz:",
    "Relationship:": "Beziehung:",
    "Primary mode:": "Primärmenge:",
    "Target:": "Ziel:",
    "Density (g/cm³):": "Dichte (g/cm³):",
    "Acronym:": "Abkürzung:",
    "Full Name:": "Vollständiger Name:",
    "RI:": "BI:",
    "MW (g/mol):": "MW (g/mol):",
    "Search:": "Suche:",
    "Database file:": "Datenbankdatei:",
    "Blend name:": "Mischungsname:",
    "Blend density:": "Mischungsdichte:",
    "Material": "Material",
    "⚙  Settings": "⚙  Einstellungen",
    "APPEARANCE": "ERSCHEINUNGSBILD",
    "BEHAVIOUR": "VERHALTEN",
    "ABOUT": "ÜBER",
    "Font size:": "Schriftgröße:",
    "High contrast mode  (dark theme)": "Hoher Kontrast  (dunkles Design)",
    "Colour-blind safe palette  (swaps red/green → blue/orange)": "Farbblinden-Palette  (Blau/Orange statt Rot/Grün)",
    "Ask for confirmation before removing or clearing components": "Bestätigung vor dem Löschen von Komponenten",
    "Larger click targets  (increases button padding — easier to click)": "Größere Schaltflächen  (einfacher zu klicken)",
    "Help & User Guide": "Hilfe & Benutzerhandbuch",
    "Topics": "Themen",
    "Cleared.": "Geleert.",
    "Click a row first.": "Wählen Sie zuerst eine Zeile aus.",
    "No components.": "Keine Komponenten.",
    "Calculate first.": "Zuerst berechnen.",
    "Solve first.": "Zuerst lösen.",
    "Settings applied.": "Einstellungen übernommen.",
    "Select a material first.": "Wählen Sie zuerst ein Material aus.",
    "Input": "Eingabe",
    "Duplicate": "Duplikat",
    "Duplicates": "Duplikate",
    "Error": "Fehler",
    "DB Error": "DB-Fehler",
    "Load Error": "Ladefehler",
    "PDF Error": "PDF-Fehler",
    "Settings Error": "Einstellungsfehler",
    "Solver Error": "Löserfehler",
    "Export": "Exportieren",
    "Import": "Importieren",
    "Share": "Teilen",
    "No Results": "Keine Ergebnisse",
    "Saved": "Gespeichert",
    "Overwrite": "Überschreiben",
    "Minimum": "Minimum",
    "Limit": "Limit",
    "Create Blend": "Mischung erstellen",
    "Materials Database": "Materialdatenbank",
    "The 3D Printing Formulator": "The 3D Printing Formulator",
    "Help & User Guide — The 3D Printing Formulator": "Hilfe — The 3D Printing Formulator",
    "Acronym cannot be empty.": "Die Abkürzung darf nicht leer sein.",
    "Density must be a number.": "Die Dichte muss eine Zahl sein.",
    "RI must be a number or blank.": "BI muss eine Zahl oder leer sein.",
    "MW must be a number or blank.": "MW muss eine Zahl oder leer sein.",
    "Names must be unique.": "Namen müssen eindeutig sein.",
    "Values must be numbers.": "Werte müssen Zahlen sein.",
    "A blend needs at least 2 components.": "Eine Mischung benötigt mindestens 2 Komponenten.",
    "Please enter a name for the blend.": "Bitte geben Sie einen Namen für die Mischung ein.",
    "Remove all components?": "Alle Komponenten entfernen?",
    "Remove all?": "Alle entfernen?",
    "Define a monomer blend. Enter wt.% for each component": "Monomermischung definieren. wt.% für jede Komponente eingeben",
    "File does not appear to be a valid materials database.": "Die Datei scheint keine gültige Datenbank zu sein.",
    "Exactly 1 Primary component required. Found {n}.": "Genau 1 Primärkomponente erforderlich. Gefunden: {n}.",
    "by Dr Thanos Goulas  ·  v1.0": "Copyright © 2026 Dr Thanos Goulas  ·  v1.0",
    "The 3D Printing": "The 3D Printing",
    "Formulator": "Formulator",
},

"es": {  # Spanish
    "Inverse Solver": "Solver Inverso",
    "Forward Formulator": "Formulación Directa",
    "Materials DB": "Base de Materiales",
    "Settings": "Configuración",
    "Help": "Ayuda",
    "Recipe / File Name:": "Nombre de Receta / Archivo:",
    "💾 Save": "💾 Guardar",
    "📂 Load": "📂 Cargar",
    "📄 Export PDF": "📄 Exportar PDF",
    "📤 Share": "📤 Compartir",
    "➕ Add": "➕ Añadir",
    "✏ Update": "✏ Actualizar",
    "🗑 Remove": "🗑 Eliminar",
    "▲ Up": "▲ Arriba",
    "▼ Down": "▼ Abajo",
    "✖ Clear All": "✖ Borrar todo",
    "⚙ SOLVE": "⚙ RESOLVER",
    "⚙ CALCULATE": "⚙ CALCULAR",
    "➕ Add / Update": "➕ Añadir / Actualizar",
    "🗑 Delete": "🗑 Eliminar",
    "⊕ Create Blend": "⊕ Crear mezcla",
    "✖ Clear fields": "✖ Borrar campos",
    "📤 Export DB": "📤 Exportar BD",
    "📥 Import DB": "📥 Importar BD",
    "💾 Save to Database": "💾 Guardar en BD",
    "⟳ Calculate density": "⟳ Calcular densidad",
    "− Remove last": "− Eliminar último",
    "Apply": "Aplicar",
    "Cancel": "Cancelar",
    "✔  OK": "✔  Aceptar",
    "✕  Cancel": "✕  Cancelar",
    "✖ Cancel": "✖ Cancelar",
    "✔ Close": "✔ Cerrar",
    "✕  Close": "✕  Cerrar",
    "Restore Defaults": "Restaurar valores",
    "Component:": "Componente:",
    "Input Mode:": "Modo de entrada:",
    "Value:": "Valor:",
    "Reference:": "Referencia:",
    "Relationship:": "Relación:",
    "Primary mode:": "Cantidad principal:",
    "Target:": "Objetivo:",
    "Density (g/cm³):": "Densidad (g/cm³):",
    "Acronym:": "Acrónimo:",
    "Full Name:": "Nombre completo:",
    "RI:": "IR:",
    "MW (g/mol):": "PM (g/mol):",
    "Search:": "Buscar:",
    "Database file:": "Archivo de base de datos:",
    "Blend name:": "Nombre de mezcla:",
    "Blend density:": "Densidad de mezcla:",
    "Material": "Material",
    "⚙  Settings": "⚙  Configuración",
    "APPEARANCE": "APARIENCIA",
    "BEHAVIOUR": "COMPORTAMIENTO",
    "ABOUT": "ACERCA DE",
    "Font size:": "Tamaño de fuente:",
    "High contrast mode  (dark theme)": "Alto contraste  (tema oscuro)",
    "Colour-blind safe palette  (swaps red/green → blue/orange)": "Paleta daltonismo  (azul/naranja en lugar de rojo/verde)",
    "Ask for confirmation before removing or clearing components": "Confirmar antes de eliminar o borrar componentes",
    "Larger click targets  (increases button padding — easier to click)": "Botones más grandes  (más fácil de pulsar)",
    "Help & User Guide": "Ayuda y Guía de Usuario",
    "Topics": "Temas",
    "Cleared.": "Borrado.",
    "Click a row first.": "Seleccione primero una fila.",
    "No components.": "Sin componentes.",
    "Calculate first.": "Calcule primero.",
    "Solve first.": "Resuelva primero.",
    "Settings applied.": "Configuración aplicada.",
    "Select a material first.": "Seleccione primero un material.",
    "Input": "Entrada",
    "Duplicate": "Duplicado",
    "Duplicates": "Duplicados",
    "Error": "Error",
    "DB Error": "Error de BD",
    "Load Error": "Error de carga",
    "PDF Error": "Error de PDF",
    "Settings Error": "Error de configuración",
    "Solver Error": "Error del solver",
    "Export": "Exportar",
    "Import": "Importar",
    "Share": "Compartir",
    "No Results": "Sin resultados",
    "Saved": "Guardado",
    "Overwrite": "Sobrescribir",
    "Minimum": "Mínimo",
    "Limit": "Límite",
    "Create Blend": "Crear mezcla",
    "Materials Database": "Base de datos de materiales",
    "The 3D Printing Formulator": "The 3D Printing Formulator",
    "Help & User Guide — The 3D Printing Formulator": "Ayuda — The 3D Printing Formulator",
    "Acronym cannot be empty.": "El acrónimo no puede estar vacío.",
    "Density must be a number.": "La densidad debe ser un número.",
    "RI must be a number or blank.": "El IR debe ser un número o estar vacío.",
    "MW must be a number or blank.": "El PM debe ser un número o estar vacío.",
    "Names must be unique.": "Los nombres deben ser únicos.",
    "Values must be numbers.": "Los valores deben ser números.",
    "A blend needs at least 2 components.": "Una mezcla necesita al menos 2 componentes.",
    "Please enter a name for the blend.": "Por favor introduzca un nombre para la mezcla.",
    "Remove all components?": "¿Eliminar todos los componentes?",
    "Remove all?": "¿Eliminar todo?",
    "Define a monomer blend. Enter wt.% for each component": "Definir mezcla de monómeros. Introducir wt.% para cada componente",
    "File does not appear to be a valid materials database.": "El archivo no parece ser una base de datos válida.",
    "Exactly 1 Primary component required. Found {n}.": "Se requiere exactamente 1 componente Principal. Encontrado: {n}.",
    "by Dr Thanos Goulas  ·  v1.0": "Copyright © 2026 Dr Thanos Goulas  ·  v1.0",
    "The 3D Printing": "The 3D Printing",
    "Formulator": "Formulator",
},

"it": {  # Italian
    "Inverse Solver": "Solutore Inverso",
    "Forward Formulator": "Formulazione Diretta",
    "Materials DB": "DB Materiali",
    "Settings": "Impostazioni",
    "Help": "Aiuto",
    "Recipe / File Name:": "Nome Ricetta / File:",
    "💾 Save": "💾 Salva",
    "📂 Load": "📂 Carica",
    "📄 Export PDF": "📄 Esporta PDF",
    "📤 Share": "📤 Condividi",
    "➕ Add": "➕ Aggiungi",
    "✏ Update": "✏ Aggiorna",
    "🗑 Remove": "🗑 Rimuovi",
    "▲ Up": "▲ Su",
    "▼ Down": "▼ Giù",
    "✖ Clear All": "✖ Cancella tutto",
    "⚙ SOLVE": "⚙ RISOLVI",
    "⚙ CALCULATE": "⚙ CALCOLA",
    "➕ Add / Update": "➕ Aggiungi / Aggiorna",
    "🗑 Delete": "🗑 Elimina",
    "⊕ Create Blend": "⊕ Crea miscela",
    "✖ Clear fields": "✖ Cancella campi",
    "📤 Export DB": "📤 Esporta DB",
    "📥 Import DB": "📥 Importa DB",
    "💾 Save to Database": "💾 Salva nel DB",
    "⟳ Calculate density": "⟳ Calcola densità",
    "− Remove last": "− Rimuovi ultimo",
    "Apply": "Applica",
    "Cancel": "Annulla",
    "✔  OK": "✔  OK",
    "✕  Cancel": "✕  Annulla",
    "✖ Cancel": "✖ Annulla",
    "✔ Close": "✔ Chiudi",
    "✕  Close": "✕  Chiudi",
    "Restore Defaults": "Ripristina predefiniti",
    "Component:": "Componente:",
    "Input Mode:": "Modalità di input:",
    "Value:": "Valore:",
    "Reference:": "Riferimento:",
    "Relationship:": "Relazione:",
    "Primary mode:": "Quantità principale:",
    "Target:": "Obiettivo:",
    "Density (g/cm³):": "Densità (g/cm³):",
    "Acronym:": "Acronimo:",
    "Full Name:": "Nome completo:",
    "RI:": "IR:",
    "MW (g/mol):": "PM (g/mol):",
    "Search:": "Cerca:",
    "Database file:": "File database:",
    "Blend name:": "Nome miscela:",
    "Blend density:": "Densità miscela:",
    "Material": "Materiale",
    "⚙  Settings": "⚙  Impostazioni",
    "APPEARANCE": "ASPETTO",
    "BEHAVIOUR": "COMPORTAMENTO",
    "ABOUT": "INFORMAZIONI",
    "Font size:": "Dimensione carattere:",
    "High contrast mode  (dark theme)": "Alto contrasto  (tema scuro)",
    "Colour-blind safe palette  (swaps red/green → blue/orange)": "Palette daltonismo  (blu/arancione al posto di rosso/verde)",
    "Ask for confirmation before removing or clearing components": "Chiedere conferma prima di rimuovere o cancellare componenti",
    "Larger click targets  (increases button padding — easier to click)": "Pulsanti più grandi  (più facili da cliccare)",
    "Help & User Guide": "Aiuto e Guida Utente",
    "Topics": "Argomenti",
    "Cleared.": "Cancellato.",
    "Click a row first.": "Seleziona prima una riga.",
    "No components.": "Nessun componente.",
    "Calculate first.": "Calcola prima.",
    "Solve first.": "Risolvi prima.",
    "Settings applied.": "Impostazioni applicate.",
    "Select a material first.": "Seleziona prima un materiale.",
    "Input": "Input",
    "Duplicate": "Duplicato",
    "Duplicates": "Duplicati",
    "Error": "Errore",
    "DB Error": "Errore DB",
    "Load Error": "Errore di caricamento",
    "PDF Error": "Errore PDF",
    "Settings Error": "Errore impostazioni",
    "Solver Error": "Errore solutore",
    "Export": "Esporta",
    "Import": "Importa",
    "Share": "Condividi",
    "No Results": "Nessun risultato",
    "Saved": "Salvato",
    "Overwrite": "Sovrascrivi",
    "Minimum": "Minimo",
    "Limit": "Limite",
    "Create Blend": "Crea miscela",
    "Materials Database": "Database dei materiali",
    "The 3D Printing Formulator": "The 3D Printing Formulator",
    "Help & User Guide — The 3D Printing Formulator": "Aiuto — The 3D Printing Formulator",
    "Acronym cannot be empty.": "L'acronimo non può essere vuoto.",
    "Density must be a number.": "La densità deve essere un numero.",
    "RI must be a number or blank.": "L'IR deve essere un numero o vuoto.",
    "MW must be a number or blank.": "Il PM deve essere un numero o vuoto.",
    "Names must be unique.": "I nomi devono essere unici.",
    "Values must be numbers.": "I valori devono essere numeri.",
    "A blend needs at least 2 components.": "Una miscela richiede almeno 2 componenti.",
    "Please enter a name for the blend.": "Inserire un nome per la miscela.",
    "Remove all components?": "Rimuovere tutti i componenti?",
    "Remove all?": "Rimuovere tutto?",
    "Define a monomer blend. Enter wt.% for each component": "Definire una miscela di monomeri. Inserire wt.% per ogni componente",
    "File does not appear to be a valid materials database.": "Il file non sembra essere un database valido.",
    "Exactly 1 Primary component required. Found {n}.": "È richiesto esattamente 1 componente Principale. Trovato: {n}.",
    "by Dr Thanos Goulas  ·  v1.0": "Copyright © 2026 Dr Thanos Goulas  ·  v1.0",
    "The 3D Printing": "The 3D Printing",
    "Formulator": "Formulator",
},

"nl": {  # Dutch
    "Inverse Solver": "Inverse Solver",
    "Forward Formulator": "Voorwaartse Formulering",
    "Materials DB": "Materialen DB",
    "Settings": "Instellingen",
    "Help": "Help",
    "Recipe / File Name:": "Recept- / Bestandsnaam:",
    "💾 Save": "💾 Opslaan",
    "📂 Load": "📂 Laden",
    "📄 Export PDF": "📄 PDF exporteren",
    "📤 Share": "📤 Delen",
    "➕ Add": "➕ Toevoegen",
    "✏ Update": "✏ Bijwerken",
    "🗑 Remove": "🗑 Verwijderen",
    "▲ Up": "▲ Omhoog",
    "▼ Down": "▼ Omlaag",
    "✖ Clear All": "✖ Alles wissen",
    "⚙ SOLVE": "⚙ OPLOSSEN",
    "⚙ CALCULATE": "⚙ BEREKENEN",
    "➕ Add / Update": "➕ Toevoegen / Bijwerken",
    "🗑 Delete": "🗑 Verwijderen",
    "⊕ Create Blend": "⊕ Mengsel maken",
    "✖ Clear fields": "✖ Velden wissen",
    "📤 Export DB": "📤 DB exporteren",
    "📥 Import DB": "📥 DB importeren",
    "💾 Save to Database": "💾 Opslaan in DB",
    "⟳ Calculate density": "⟳ Dichtheid berekenen",
    "− Remove last": "− Laatste verwijderen",
    "Apply": "Toepassen",
    "Cancel": "Annuleren",
    "✔  OK": "✔  OK",
    "✕  Cancel": "✕  Annuleren",
    "✖ Cancel": "✖ Annuleren",
    "✔ Close": "✔ Sluiten",
    "✕  Close": "✕  Sluiten",
    "Restore Defaults": "Standaard herstellen",
    "Component:": "Component:",
    "Input Mode:": "Invoermodus:",
    "Value:": "Waarde:",
    "Reference:": "Referentie:",
    "Relationship:": "Relatie:",
    "Primary mode:": "Primaire hoeveelheid:",
    "Target:": "Doel:",
    "Density (g/cm³):": "Dichtheid (g/cm³):",
    "Acronym:": "Afkorting:",
    "Full Name:": "Volledige naam:",
    "RI:": "BI:",
    "MW (g/mol):": "MW (g/mol):",
    "Search:": "Zoeken:",
    "Database file:": "Databasebestand:",
    "Blend name:": "Mengselnaam:",
    "Blend density:": "Mengsel dichtheid:",
    "Material": "Materiaal",
    "⚙  Settings": "⚙  Instellingen",
    "APPEARANCE": "UITERLIJK",
    "BEHAVIOUR": "GEDRAG",
    "ABOUT": "OVER",
    "Font size:": "Tekengrootte:",
    "High contrast mode  (dark theme)": "Hoog contrast  (donker thema)",
    "Colour-blind safe palette  (swaps red/green → blue/orange)": "Kleurenblind palette  (blauw/oranje i.p.v. rood/groen)",
    "Ask for confirmation before removing or clearing components": "Bevestiging vragen voor verwijderen of wissen",
    "Larger click targets  (increases button padding — easier to click)": "Grotere knoppen  (makkelijker te klikken)",
    "Help & User Guide": "Help en Gebruikershandleiding",
    "Topics": "Onderwerpen",
    "Cleared.": "Gewist.",
    "Click a row first.": "Selecteer eerst een rij.",
    "No components.": "Geen componenten.",
    "Calculate first.": "Bereken eerst.",
    "Solve first.": "Los eerst op.",
    "Settings applied.": "Instellingen toegepast.",
    "Select a material first.": "Selecteer eerst een materiaal.",
    "Input": "Invoer",
    "Duplicate": "Duplicaat",
    "Duplicates": "Duplicaten",
    "Error": "Fout",
    "DB Error": "DB-fout",
    "Load Error": "Laadfout",
    "PDF Error": "PDF-fout",
    "Settings Error": "Instellingsfout",
    "Solver Error": "Solverfout",
    "Export": "Exporteren",
    "Import": "Importeren",
    "Share": "Delen",
    "No Results": "Geen resultaten",
    "Saved": "Opgeslagen",
    "Overwrite": "Overschrijven",
    "Minimum": "Minimum",
    "Limit": "Limiet",
    "Create Blend": "Mengsel maken",
    "Materials Database": "Materialendatabase",
    "The 3D Printing Formulator": "The 3D Printing Formulator",
    "Help & User Guide — The 3D Printing Formulator": "Help — The 3D Printing Formulator",
    "Acronym cannot be empty.": "De afkorting mag niet leeg zijn.",
    "Density must be a number.": "De dichtheid moet een getal zijn.",
    "RI must be a number or blank.": "BI moet een getal of leeg zijn.",
    "MW must be a number or blank.": "MW moet een getal of leeg zijn.",
    "Names must be unique.": "Namen moeten uniek zijn.",
    "Values must be numbers.": "Waarden moeten getallen zijn.",
    "A blend needs at least 2 components.": "Een mengsel heeft minimaal 2 componenten nodig.",
    "Please enter a name for the blend.": "Voer een naam in voor het mengsel.",
    "Remove all components?": "Alle componenten verwijderen?",
    "Remove all?": "Alles verwijderen?",
    "Define a monomer blend. Enter wt.% for each component": "Monomeermensel definiëren. wt.% invoeren voor elk component",
    "File does not appear to be a valid materials database.": "Het bestand lijkt geen geldige database te zijn.",
    "Exactly 1 Primary component required. Found {n}.": "Precies 1 Primair component vereist. Gevonden: {n}.",
    "by Dr Thanos Goulas  ·  v1.0": "Copyright © 2026 Dr Thanos Goulas  ·  v1.0",
    "The 3D Printing": "The 3D Printing",
    "Formulator": "Formulator",
},

"zh": {  # Chinese Simplified
    "Inverse Solver": "反向求解器",
    "Forward Formulator": "正向计算",
    "Materials DB": "材料数据库",
    "Settings": "设置",
    "Help": "帮助",
    "Recipe / File Name:": "配方 / 文件名：",
    "💾 Save": "💾 保存",
    "📂 Load": "📂 加载",
    "📄 Export PDF": "📄 导出PDF",
    "📤 Share": "📤 分享",
    "➕ Add": "➕ 添加",
    "✏ Update": "✏ 更新",
    "🗑 Remove": "🗑 删除",
    "▲ Up": "▲ 上移",
    "▼ Down": "▼ 下移",
    "✖ Clear All": "✖ 全部清除",
    "⚙ SOLVE": "⚙ 求解",
    "⚙ CALCULATE": "⚙ 计算",
    "➕ Add / Update": "➕ 添加/更新",
    "🗑 Delete": "🗑 删除",
    "⊕ Create Blend": "⊕ 创建混合物",
    "✖ Clear fields": "✖ 清除字段",
    "📤 Export DB": "📤 导出数据库",
    "📥 Import DB": "📥 导入数据库",
    "💾 Save to Database": "💾 保存到数据库",
    "⟳ Calculate density": "⟳ 计算密度",
    "− Remove last": "− 删除最后一项",
    "Apply": "应用",
    "Cancel": "取消",
    "✔  OK": "✔  确定",
    "✕  Cancel": "✕  取消",
    "✖ Cancel": "✖ 取消",
    "✔ Close": "✔ 关闭",
    "✕  Close": "✕  关闭",
    "Restore Defaults": "恢复默认",
    "Component:": "组分：",
    "Input Mode:": "输入模式：",
    "Value:": "数值：",
    "Reference:": "参考：",
    "Relationship:": "关系：",
    "Primary mode:": "主要量：",
    "Target:": "目标：",
    "Density (g/cm³):": "密度 (g/cm³)：",
    "Acronym:": "缩写：",
    "Full Name:": "全名：",
    "RI:": "折射率：",
    "MW (g/mol):": "分子量 (g/mol)：",
    "Search:": "搜索：",
    "Database file:": "数据库文件：",
    "Blend name:": "混合物名称：",
    "Blend density:": "混合物密度：",
    "Material": "材料",
    "⚙  Settings": "⚙  设置",
    "APPEARANCE": "外观",
    "BEHAVIOUR": "行为",
    "ABOUT": "关于",
    "Font size:": "字体大小：",
    "High contrast mode  (dark theme)": "高对比度模式（深色主题）",
    "Colour-blind safe palette  (swaps red/green → blue/orange)": "色盲安全配色（蓝/橙代替红/绿）",
    "Ask for confirmation before removing or clearing components": "删除或清除组分前请求确认",
    "Larger click targets  (increases button padding — easier to click)": "更大的点击区域（按钮更易点击）",
    "Help & User Guide": "帮助与用户指南",
    "Topics": "主题",
    "Cleared.": "已清除。",
    "Click a row first.": "请先选择一行。",
    "No components.": "没有组分。",
    "Calculate first.": "请先计算。",
    "Solve first.": "请先求解。",
    "Settings applied.": "设置已应用。",
    "Select a material first.": "请先选择材料。",
    "Input": "输入",
    "Duplicate": "重复",
    "Duplicates": "重复项",
    "Error": "错误",
    "DB Error": "数据库错误",
    "Load Error": "加载错误",
    "PDF Error": "PDF错误",
    "Settings Error": "设置错误",
    "Solver Error": "求解错误",
    "Export": "导出",
    "Import": "导入",
    "Share": "分享",
    "No Results": "无结果",
    "Saved": "已保存",
    "Overwrite": "覆盖",
    "Minimum": "最小值",
    "Limit": "限制",
    "Create Blend": "创建混合物",
    "Materials Database": "材料数据库",
    "The 3D Printing Formulator": "The 3D Printing Formulator",
    "Help & User Guide — The 3D Printing Formulator": "帮助 — The 3D Printing Formulator",
    "Acronym cannot be empty.": "缩写不能为空。",
    "Density must be a number.": "密度必须是数字。",
    "RI must be a number or blank.": "折射率必须是数字或为空。",
    "MW must be a number or blank.": "分子量必须是数字或为空。",
    "Names must be unique.": "名称必须唯一。",
    "Values must be numbers.": "数值必须是数字。",
    "A blend needs at least 2 components.": "混合物至少需要2个组分。",
    "Please enter a name for the blend.": "请输入混合物名称。",
    "Remove all components?": "删除所有组分？",
    "Remove all?": "全部删除？",
    "Define a monomer blend. Enter wt.% for each component": "定义单体混合物。为每个组分输入wt.%",
    "File does not appear to be a valid materials database.": "该文件似乎不是有效的材料数据库。",
    "Exactly 1 Primary component required. Found {n}.": "恰好需要1个主要组分。找到：{n}。",
    "by Dr Thanos Goulas  ·  v1.0": "Copyright © 2026 Dr Thanos Goulas  ·  v1.0",
    "The 3D Printing": "3D打印",
    "Formulator": "配方计算器",
},

"ja": {  # Japanese
    "Inverse Solver": "逆算ソルバー",
    "Forward Formulator": "順方向計算",
    "Materials DB": "材料データベース",
    "Settings": "設定",
    "Help": "ヘルプ",
    "Recipe / File Name:": "レシピ名 / ファイル名：",
    "💾 Save": "💾 保存",
    "📂 Load": "📂 読込",
    "📄 Export PDF": "📄 PDFエクスポート",
    "📤 Share": "📤 共有",
    "➕ Add": "➕ 追加",
    "✏ Update": "✏ 更新",
    "🗑 Remove": "🗑 削除",
    "▲ Up": "▲ 上へ",
    "▼ Down": "▼ 下へ",
    "✖ Clear All": "✖ 全削除",
    "⚙ SOLVE": "⚙ 求解",
    "⚙ CALCULATE": "⚙ 計算",
    "➕ Add / Update": "➕ 追加/更新",
    "🗑 Delete": "🗑 削除",
    "⊕ Create Blend": "⊕ 混合物作成",
    "✖ Clear fields": "✖ フィールドをクリア",
    "📤 Export DB": "📤 DB エクスポート",
    "📥 Import DB": "📥 DB インポート",
    "💾 Save to Database": "💾 DBに保存",
    "⟳ Calculate density": "⟳ 密度を計算",
    "− Remove last": "− 最後を削除",
    "Apply": "適用",
    "Cancel": "キャンセル",
    "✔  OK": "✔  OK",
    "✕  Cancel": "✕  キャンセル",
    "✖ Cancel": "✖ キャンセル",
    "✔ Close": "✔ 閉じる",
    "✕  Close": "✕  閉じる",
    "Restore Defaults": "デフォルトに戻す",
    "Component:": "成分：",
    "Input Mode:": "入力モード：",
    "Value:": "値：",
    "Reference:": "参照：",
    "Relationship:": "関係：",
    "Primary mode:": "主要量：",
    "Target:": "目標：",
    "Density (g/cm³):": "密度 (g/cm³)：",
    "Acronym:": "略称：",
    "Full Name:": "フルネーム：",
    "RI:": "屈折率：",
    "MW (g/mol):": "分子量 (g/mol)：",
    "Search:": "検索：",
    "Database file:": "データベースファイル：",
    "Blend name:": "混合物名：",
    "Blend density:": "混合物密度：",
    "Material": "材料",
    "⚙  Settings": "⚙  設定",
    "APPEARANCE": "外観",
    "BEHAVIOUR": "動作",
    "ABOUT": "情報",
    "Font size:": "フォントサイズ：",
    "High contrast mode  (dark theme)": "高コントラスト（ダークテーマ）",
    "Colour-blind safe palette  (swaps red/green → blue/orange)": "色覚サポートパレット（青/橙に変更）",
    "Ask for confirmation before removing or clearing components": "削除前に確認を求める",
    "Larger click targets  (increases button padding — easier to click)": "大きなボタン（クリックしやすい）",
    "Help & User Guide": "ヘルプとユーザーガイド",
    "Topics": "トピック",
    "Cleared.": "クリアしました。",
    "Click a row first.": "先に行を選択してください。",
    "No components.": "成分がありません。",
    "Calculate first.": "先に計算してください。",
    "Solve first.": "先に求解してください。",
    "Settings applied.": "設定を適用しました。",
    "Select a material first.": "先に材料を選択してください。",
    "Input": "入力",
    "Duplicate": "重複",
    "Duplicates": "重複あり",
    "Error": "エラー",
    "DB Error": "DBエラー",
    "Load Error": "読込エラー",
    "PDF Error": "PDFエラー",
    "Settings Error": "設定エラー",
    "Solver Error": "ソルバーエラー",
    "Export": "エクスポート",
    "Import": "インポート",
    "Share": "共有",
    "No Results": "結果なし",
    "Saved": "保存済",
    "Overwrite": "上書き",
    "Minimum": "最小",
    "Limit": "上限",
    "Create Blend": "混合物作成",
    "Materials Database": "材料データベース",
    "The 3D Printing Formulator": "The 3D Printing Formulator",
    "Help & User Guide — The 3D Printing Formulator": "ヘルプ — The 3D Printing Formulator",
    "Acronym cannot be empty.": "略称を入力してください。",
    "Density must be a number.": "密度は数値で入力してください。",
    "RI must be a number or blank.": "屈折率は数値または空白にしてください。",
    "MW must be a number or blank.": "分子量は数値または空白にしてください。",
    "Names must be unique.": "名前は一意でなければなりません。",
    "Values must be numbers.": "値は数値でなければなりません。",
    "A blend needs at least 2 components.": "混合物には少なくとも2つの成分が必要です。",
    "Please enter a name for the blend.": "混合物の名前を入力してください。",
    "Remove all components?": "すべての成分を削除しますか？",
    "Remove all?": "すべて削除しますか？",
    "Define a monomer blend. Enter wt.% for each component": "モノマー混合物を定義します。各成分のwt.%を入力してください",
    "File does not appear to be a valid materials database.": "ファイルが有効な材料データベースではないようです。",
    "Exactly 1 Primary component required. Found {n}.": "主成分は1つだけ必要です。見つかった数：{n}。",
    "by Dr Thanos Goulas  ·  v1.0": "Copyright © 2026 Dr Thanos Goulas  ·  v1.0",
    "The 3D Printing": "3Dプリンティング",
    "Formulator": "フォーミュレーター",
},

"ko": {  # Korean
    "Inverse Solver": "역방향 솔버",
    "Forward Formulator": "순방향 계산",
    "Materials DB": "재료 데이터베이스",
    "Settings": "설정",
    "Help": "도움말",
    "Recipe / File Name:": "레시피 / 파일명:",
    "💾 Save": "💾 저장",
    "📂 Load": "📂 불러오기",
    "📄 Export PDF": "📄 PDF 내보내기",
    "📤 Share": "📤 공유",
    "➕ Add": "➕ 추가",
    "✏ Update": "✏ 업데이트",
    "🗑 Remove": "🗑 제거",
    "▲ Up": "▲ 위로",
    "▼ Down": "▼ 아래로",
    "✖ Clear All": "✖ 모두 지우기",
    "⚙ SOLVE": "⚙ 풀기",
    "⚙ CALCULATE": "⚙ 계산",
    "➕ Add / Update": "➕ 추가 / 업데이트",
    "🗑 Delete": "🗑 삭제",
    "⊕ Create Blend": "⊕ 혼합물 생성",
    "✖ Clear fields": "✖ 필드 지우기",
    "📤 Export DB": "📤 DB 내보내기",
    "📥 Import DB": "📥 DB 가져오기",
    "💾 Save to Database": "💾 DB에 저장",
    "⟳ Calculate density": "⟳ 밀도 계산",
    "− Remove last": "− 마지막 제거",
    "Apply": "적용",
    "Cancel": "취소",
    "✔  OK": "✔  확인",
    "✕  Cancel": "✕  취소",
    "✖ Cancel": "✖ 취소",
    "✔ Close": "✔ 닫기",
    "✕  Close": "✕  닫기",
    "Restore Defaults": "기본값 복원",
    "Component:": "성분:",
    "Input Mode:": "입력 모드:",
    "Value:": "값:",
    "Reference:": "참조:",
    "Relationship:": "관계:",
    "Primary mode:": "주요 양:",
    "Target:": "목표:",
    "Density (g/cm³):": "밀도 (g/cm³):",
    "Acronym:": "약어:",
    "Full Name:": "전체 이름:",
    "RI:": "굴절률:",
    "MW (g/mol):": "분자량 (g/mol):",
    "Search:": "검색:",
    "Database file:": "데이터베이스 파일:",
    "Blend name:": "혼합물 이름:",
    "Blend density:": "혼합물 밀도:",
    "Material": "재료",
    "⚙  Settings": "⚙  설정",
    "APPEARANCE": "외관",
    "BEHAVIOUR": "동작",
    "ABOUT": "정보",
    "Font size:": "글꼴 크기:",
    "High contrast mode  (dark theme)": "고대비 모드 (어두운 테마)",
    "Colour-blind safe palette  (swaps red/green → blue/orange)": "색맹 지원 팔레트 (파랑/주황으로 변경)",
    "Ask for confirmation before removing or clearing components": "성분 제거 또는 지우기 전 확인",
    "Larger click targets  (increases button padding — easier to click)": "더 큰 버튼 (클릭하기 쉬움)",
    "Help & User Guide": "도움말 및 사용자 가이드",
    "Topics": "주제",
    "Cleared.": "지워졌습니다.",
    "Click a row first.": "먼저 행을 선택하세요.",
    "No components.": "성분이 없습니다.",
    "Calculate first.": "먼저 계산하세요.",
    "Solve first.": "먼저 풀기를 실행하세요.",
    "Settings applied.": "설정이 적용되었습니다.",
    "Select a material first.": "먼저 재료를 선택하세요.",
    "Input": "입력",
    "Duplicate": "중복",
    "Duplicates": "중복 항목",
    "Error": "오류",
    "DB Error": "DB 오류",
    "Load Error": "로드 오류",
    "PDF Error": "PDF 오류",
    "Settings Error": "설정 오류",
    "Solver Error": "솔버 오류",
    "Export": "내보내기",
    "Import": "가져오기",
    "Share": "공유",
    "No Results": "결과 없음",
    "Saved": "저장됨",
    "Overwrite": "덮어쓰기",
    "Minimum": "최소",
    "Limit": "한도",
    "Create Blend": "혼합물 생성",
    "Materials Database": "재료 데이터베이스",
    "The 3D Printing Formulator": "The 3D Printing Formulator",
    "Help & User Guide — The 3D Printing Formulator": "도움말 — The 3D Printing Formulator",
    "Acronym cannot be empty.": "약어는 비어 있을 수 없습니다.",
    "Density must be a number.": "밀도는 숫자여야 합니다.",
    "RI must be a number or blank.": "굴절률은 숫자이거나 비어 있어야 합니다.",
    "MW must be a number or blank.": "분자량은 숫자이거나 비어 있어야 합니다.",
    "Names must be unique.": "이름은 고유해야 합니다.",
    "Values must be numbers.": "값은 숫자여야 합니다.",
    "A blend needs at least 2 components.": "혼합물에는 최소 2개의 성분이 필요합니다.",
    "Please enter a name for the blend.": "혼합물 이름을 입력해주세요.",
    "Remove all components?": "모든 성분을 제거하시겠습니까?",
    "Remove all?": "모두 제거하시겠습니까?",
    "Define a monomer blend. Enter wt.% for each component": "단량체 혼합물 정의. 각 성분의 wt.%를 입력하세요",
    "File does not appear to be a valid materials database.": "파일이 유효한 재료 데이터베이스가 아닌 것 같습니다.",
    "Exactly 1 Primary component required. Found {n}.": "정확히 1개의 주요 성분이 필요합니다. 발견됨: {n}.",
    "by Dr Thanos Goulas  ·  v1.0": "Copyright © 2026 Dr Thanos Goulas  ·  v1.0",
    "The 3D Printing": "3D 프린팅",
    "Formulator": "포뮬레이터",
},

"hi": {  # Hindi
    "Inverse Solver": "व्युत्क्रम सॉल्वर",
    "Forward Formulator": "अग्रवर्ती गणना",
    "Materials DB": "सामग्री डेटाबेस",
    "Settings": "सेटिंग्स",
    "Help": "सहायता",
    "Recipe / File Name:": "नुस्खा / फ़ाइल नाम:",
    "💾 Save": "💾 सहेजें",
    "📂 Load": "📂 लोड करें",
    "📄 Export PDF": "📄 PDF निर्यात",
    "📤 Share": "📤 साझा करें",
    "➕ Add": "➕ जोड़ें",
    "✏ Update": "✏ अपडेट",
    "🗑 Remove": "🗑 हटाएं",
    "▲ Up": "▲ ऊपर",
    "▼ Down": "▼ नीचे",
    "✖ Clear All": "✖ सब साफ करें",
    "⚙ SOLVE": "⚙ हल करें",
    "⚙ CALCULATE": "⚙ गणना करें",
    "➕ Add / Update": "➕ जोड़ें / अपडेट",
    "🗑 Delete": "🗑 हटाएं",
    "⊕ Create Blend": "⊕ मिश्रण बनाएं",
    "✖ Clear fields": "✖ फ़ील्ड साफ करें",
    "📤 Export DB": "📤 DB निर्यात",
    "📥 Import DB": "📥 DB आयात",
    "💾 Save to Database": "💾 DB में सहेजें",
    "⟳ Calculate density": "⟳ घनत्व गणना",
    "− Remove last": "− अंतिम हटाएं",
    "Apply": "लागू करें",
    "Cancel": "रद्द करें",
    "✔  OK": "✔  ठीक है",
    "✕  Cancel": "✕  रद्द करें",
    "✖ Cancel": "✖ रद्द करें",
    "✔ Close": "✔ बंद करें",
    "✕  Close": "✕  बंद करें",
    "Restore Defaults": "डिफ़ॉल्ट पुनर्स्थापित करें",
    "Component:": "घटक:",
    "Input Mode:": "इनपुट मोड:",
    "Value:": "मान:",
    "Reference:": "संदर्भ:",
    "Relationship:": "संबंध:",
    "Primary mode:": "प्राथमिक मात्रा:",
    "Target:": "लक्ष्य:",
    "Density (g/cm³):": "घनत्व (g/cm³):",
    "Acronym:": "संक्षिप्त नाम:",
    "Full Name:": "पूरा नाम:",
    "RI:": "RI:",
    "MW (g/mol):": "MW (g/mol):",
    "Search:": "खोजें:",
    "Database file:": "डेटाबेस फ़ाइल:",
    "Blend name:": "मिश्रण नाम:",
    "Blend density:": "मिश्रण घनत्व:",
    "Material": "सामग्री",
    "⚙  Settings": "⚙  सेटिंग्स",
    "APPEARANCE": "दिखावट",
    "BEHAVIOUR": "व्यवहार",
    "ABOUT": "जानकारी",
    "Font size:": "फ़ॉन्ट आकार:",
    "High contrast mode  (dark theme)": "उच्च कंट्रास्ट (डार्क थीम)",
    "Colour-blind safe palette  (swaps red/green → blue/orange)": "वर्णान्ध सुरक्षित पैलेट (नीला/नारंगी)",
    "Ask for confirmation before removing or clearing components": "घटक हटाने से पहले पुष्टि मांगें",
    "Larger click targets  (increases button padding — easier to click)": "बड़े बटन (क्लिक करने में आसान)",
    "Help & User Guide": "सहायता और उपयोगकर्ता मार्गदर्शिका",
    "Topics": "विषय",
    "Cleared.": "साफ हो गया।",
    "Click a row first.": "पहले एक पंक्ति चुनें।",
    "No components.": "कोई घटक नहीं।",
    "Calculate first.": "पहले गणना करें।",
    "Solve first.": "पहले हल करें।",
    "Settings applied.": "सेटिंग्स लागू हो गईं।",
    "Select a material first.": "पहले एक सामग्री चुनें।",
    "Input": "इनपुट",
    "Duplicate": "डुप्लिकेट",
    "Duplicates": "डुप्लिकेट",
    "Error": "त्रुटि",
    "DB Error": "DB त्रुटि",
    "Load Error": "लोड त्रुटि",
    "PDF Error": "PDF त्रुटि",
    "Settings Error": "सेटिंग त्रुटि",
    "Solver Error": "सॉल्वर त्रुटि",
    "Export": "निर्यात",
    "Import": "आयात",
    "Share": "साझा करें",
    "No Results": "कोई परिणाम नहीं",
    "Saved": "सहेजा गया",
    "Overwrite": "अधिलेखित करें",
    "Minimum": "न्यूनतम",
    "Limit": "सीमा",
    "Create Blend": "मिश्रण बनाएं",
    "Materials Database": "सामग्री डेटाबेस",
    "The 3D Printing Formulator": "The 3D Printing Formulator",
    "Help & User Guide — The 3D Printing Formulator": "सहायता — The 3D Printing Formulator",
    "Acronym cannot be empty.": "संक्षिप्त नाम खाली नहीं हो सकता।",
    "Density must be a number.": "घनत्व एक संख्या होनी चाहिए।",
    "RI must be a number or blank.": "RI एक संख्या या खाली होनी चाहिए।",
    "MW must be a number or blank.": "MW एक संख्या या खाली होनी चाहिए।",
    "Names must be unique.": "नाम अनोखे होने चाहिए।",
    "Values must be numbers.": "मान संख्याएं होनी चाहिए।",
    "A blend needs at least 2 components.": "मिश्रण में कम से कम 2 घटक चाहिए।",
    "Please enter a name for the blend.": "कृपया मिश्रण का नाम दर्ज करें।",
    "Remove all components?": "सभी घटक हटाएं?",
    "Remove all?": "सब हटाएं?",
    "Define a monomer blend. Enter wt.% for each component": "मोनोमर मिश्रण परिभाषित करें। प्रत्येक घटक के लिए wt.% दर्ज करें",
    "File does not appear to be a valid materials database.": "फ़ाइल एक वैध सामग्री डेटाबेस नहीं लगती।",
    "Exactly 1 Primary component required. Found {n}.": "बिल्कुल 1 प्राथमिक घटक आवश्यक है। पाया गया: {n}।",
    "by Dr Thanos Goulas  ·  v1.0": "Copyright © 2026 Dr Thanos Goulas  ·  v1.0",
    "The 3D Printing": "3D प्रिंटिंग",
    "Formulator": "फ़ॉर्मुलेटर",
},

}  # end TRANSLATIONS

# Current language code — updated by _T_set_lang()
_LANG = "en"

def _T_set_lang(code):
    global _LANG
    _LANG = code if code in TRANSLATIONS else "en"

def _T(s):
    """Return translation of s for the current language, fallback to English."""
    if _LANG == "en":
        return s
    return TRANSLATIONS.get(_LANG, {}).get(s, s)

# ─────────────────────────────────────────────
#  MATERIAL PICKER WIDGET
#  Entry + ▼ arrow button + 🗄 DB button inline
# ─────────────────────────────────────────────
class AutocompleteEntry(tk.Frame):
    """
    Name entry with:
      ▼  — opens a searchable dropdown of all materials in the DB
      🗄  — opens the Manage Materials dialog
    Selecting a material auto-fills the name and calls on_select(mat).
    """
    def __init__(self, parent, width, db_ref, on_select=None, open_db_cb=None, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._db        = db_ref
        self._on_select = on_select
        self._open_db   = open_db_cb
        self._popup     = None
        self._listbox   = None
        self._suppress  = False
        self._matches   = []

        self.var = tk.StringVar()
        self._entry = tk.Entry(self, width=width, bg=BG_WHITE, fg=TEXT,
            insertbackground=ACCENT, relief="flat", bd=1,
            highlightthickness=0, font=("Segoe UI", 9),
            textvariable=self.var)
        self._entry.pack(side="left")

        # ▼ arrow button — opens full list (filtered by what's in the entry)
        self._arrow = tk.Button(self, text="▼", command=self._toggle_popup,
            bg=BG_HDR, fg=ACCENT, activebackground=BG_ALT,
            relief="groove", bd=1, cursor="hand2",
            font=("Segoe UI", 8), padx=3, pady=0, width=2)
        self._arrow.pack(side="left", padx=(1, 2))

        # DB button removed — access via sidebar Materials DB link

        self._entry.bind("<Escape>", lambda e: self._close_popup())
        self._entry.bind("<Down>",   self._focus_list)
        self._entry.bind("<Return>", self._on_return)

    # ── public interface ──────────────────────
    def get(self):       return self.var.get()
    def set(self, v):
        self._suppress = True
        self.var.set(v)
        self._suppress = False
    def focus_set(self): self._entry.focus_set()

    # ── dropdown logic ────────────────────────
    def _toggle_popup(self):
        if self._popup:
            self._close_popup(); return
        # Filter by whatever is already typed; show all if empty
        typed = self.var.get().strip().lower()
        self._matches = [m for m in self._db
                         if not typed or typed in m["acronym"].lower() or typed in m["name"].lower()]
        if not self._matches:
            self._matches = list(self._db)   # fallback: show all
        self._show_popup()

    def _show_popup(self):
        self._close_popup()

        self._popup = tk.Toplevel(self._entry)
        self._popup.wm_overrideredirect(True)
        self._popup.attributes("-topmost", True)
        self._popup.configure(bg=BORDER)

        # Search bar inside popup
        sv = tk.StringVar()
        sf = tk.Frame(self._popup, bg=BG_HDR)
        sf.pack(fill="x", padx=1, pady=(1, 0))
        tk.Label(sf, text="Filter:", bg=BG_HDR, fg=TEXT_DIM,
                 font=("Segoe UI", 8)).pack(side="left", padx=(4, 2))
        se = tk.Entry(sf, textvariable=sv, width=20, bg=BG_WHITE, fg=TEXT,
                      relief="flat", bd=0, font=("Segoe UI", 9))
        se.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=2)
        sv.trace_add("write", lambda *_: self._filter_list(sv.get()))

        self._listbox = tk.Listbox(self._popup, font=("Segoe UI", 9),
            bg=BG_WHITE, fg=TEXT,
            selectbackground=SEL_BG, selectforeground=SEL_FG,
            relief="flat", bd=0, activestyle="none",
            highlightthickness=1, highlightcolor=ACCENT,
            exportselection=False)
        self._listbox.pack(fill="both", expand=True, padx=1, pady=(0, 1))

        self._populate_list(self._matches)

        # Position under the arrow button
        self._arrow.update_idletasks()
        x = self._arrow.winfo_rootx()
        y = self._arrow.winfo_rooty() + self._arrow.winfo_height()
        # align right edge with arrow button right edge
        w = 320
        x = max(0, x + self._arrow.winfo_width() - w)
        h = min(len(self._matches), 10) * 20 + 30   # +30 for filter bar
        self._popup.geometry(f"{w}x{h}+{x}+{y}")

        self._listbox.bind("<ButtonRelease-1>", self._pick)
        self._listbox.bind("<Return>",          self._pick)
        self._listbox.bind("<Escape>",          lambda e: self._close_popup())
        self._listbox.bind("<Up>",              self._list_up)
        self._listbox.bind("<FocusOut>",        self._on_focus_out)
        sf.bind("<FocusOut>",                   self._on_focus_out)
        se.bind("<FocusOut>",                   self._on_focus_out)
        se.bind("<Down>",                       lambda e: self._focus_list())
        se.bind("<Return>",                     lambda e: self._focus_list())
        se.focus_set()

    def _populate_list(self, items):
        self._listbox.delete(0, "end")
        self._matches = items
        for m in items:
            self._listbox.insert("end", f"{m['acronym']}   [{m['density']:.3f} g/cm³]")

    def _filter_list(self, text):
        t = text.strip().lower()
        filtered = [m for m in self._db if not t or t in m["acronym"].lower() or t in m["name"].lower()]
        self._populate_list(filtered)
        # Resize popup height to fit
        if self._popup:
            try:
                h = min(len(filtered), 10) * 20 + 30
                geo = self._popup.geometry()
                wh, pos = geo.split("+", 1) if "+" in geo else (geo, "0+0")
                w = wh.split("x")[0]
                self._popup.geometry(f"{w}x{h}+{pos}")
            except Exception:
                pass

    def _focus_list(self, _=None):
        if self._listbox and self._listbox.size() > 0:
            self._listbox.focus_set()
            self._listbox.selection_set(0)
            self._listbox.activate(0)

    def _list_up(self, _=None):
        if self._listbox:
            idx = self._listbox.curselection()
            if idx and idx[0] == 0:
                self._entry.focus_set()

    def _pick(self, _=None):
        if not self._listbox: return
        sel = self._listbox.curselection()
        if not sel: return
        mat = self._matches[sel[0]]
        self.set(mat["acronym"])
        self._close_popup()
        if self._on_select:
            self._on_select(mat)
        self._entry.focus_set()
        self._entry.icursor("end")

    def _on_return(self, _=None):
        if self._popup: self._focus_list()
        return "break"

    def _close_popup(self):
        if self._popup:
            try: self._popup.destroy()
            except Exception: pass
            self._popup = None
            self._listbox = None

    def _on_focus_out(self, _=None):
        self.after(200, self._close_popup)


# ─────────────────────────────────────────────
#  REFERENCE ENTRY WIDGET
#  Plain entry + ▼ button that suggests from
#  the components already in the current recipe
# ─────────────────────────────────────────────
class RefEntry(tk.Frame):
    """Entry with a ▼ dropdown that lists components already in the recipe.
    Accepts either a list reference OR a zero-argument callable that returns the list,
    so it always reflects the current state even after Load reassigns self.components."""
    def __init__(self, parent, width, components_ref, **kw):
        super().__init__(parent, bg=BG, **kw)
        # Accept a callable or a plain list; normalise to callable
        if callable(components_ref):
            self._get_components = components_ref
        else:
            self._get_components = lambda: components_ref
        self._popup   = None
        self._listbox = None
        self._matches = []

        self.var = tk.StringVar()
        self._entry = tk.Entry(self, width=width, bg=BG_WHITE, fg=TEXT,
            insertbackground=ACCENT, relief="flat", bd=1,
            highlightthickness=0, font=("Segoe UI", 9),
            textvariable=self.var)
        self._entry.pack(side="left")

        self._arrow = tk.Button(self, text="▼", command=self._toggle_popup,
            bg=BG_HDR, fg=ACCENT, activebackground=BG_ALT,
            relief="groove", bd=1, cursor="hand2",
            font=("Segoe UI", 8), padx=3, pady=0, width=2)
        self._arrow.pack(side="left", padx=(1, 0))

        self._entry.bind("<Escape>", lambda e: self._close_popup())
        self._entry.bind("<Down>",   self._focus_list)

    def get(self):       return self.var.get()
    def set(self, v):    self.var.set(v)
    def focus_set(self): self._entry.focus_set()

    def _toggle_popup(self):
        if self._popup:
            self._close_popup(); return
        names = [c["name"] for c in self._get_components()]
        if not names:
            return   # nothing to suggest yet
        typed = self.var.get().strip().lower()
        self._matches = [n for n in names if not typed or typed in n.lower()]
        if not self._matches:
            self._matches = names[:]
        self._show_popup()

    def _show_popup(self):
        self._close_popup()
        self._popup = tk.Toplevel(self._entry)
        self._popup.wm_overrideredirect(True)
        self._popup.attributes("-topmost", True)
        self._popup.configure(bg=BORDER)

        self._listbox = tk.Listbox(self._popup, font=("Segoe UI", 9),
            bg=BG_WHITE, fg=TEXT,
            selectbackground=SEL_BG, selectforeground=SEL_FG,
            relief="flat", bd=0, activestyle="none",
            highlightthickness=1, highlightcolor=ACCENT,
            exportselection=False)
        self._listbox.pack(fill="both", expand=True, padx=1, pady=1)
        for n in self._matches:
            self._listbox.insert("end", n)

        self._arrow.update_idletasks()
        x = self._arrow.winfo_rootx()
        y = self._arrow.winfo_rooty() + self._arrow.winfo_height()
        w = max(self._entry.winfo_width() + self._arrow.winfo_width(), 200)
        h = min(len(self._matches), 8) * 20 + 4
        self._popup.geometry(f"{w}x{h}+{x}+{y}")

        self._listbox.bind("<ButtonRelease-1>", self._pick)
        self._listbox.bind("<Return>",          self._pick)
        self._listbox.bind("<Escape>",          lambda e: self._close_popup())
        self._listbox.bind("<FocusOut>",        self._on_focus_out)
        self._entry.bind("<FocusOut>",          self._on_focus_out)

    def _focus_list(self, _=None):
        if self._listbox and self._listbox.size() > 0:
            self._listbox.focus_set()
            self._listbox.selection_set(0)
            self._listbox.activate(0)

    def _pick(self, _=None):
        if not self._listbox: return
        sel = self._listbox.curselection()
        if not sel: return
        self.var.set(self._matches[sel[0]])
        self._close_popup()
        self._entry.focus_set()
        self._entry.icursor("end")

    def _close_popup(self):
        if self._popup:
            try: self._popup.destroy()
            except Exception: pass
            self._popup = None
            self._listbox = None

    def _on_focus_out(self, _=None):
        self.after(200, self._close_popup)


class MaterialsDialog(tk.Toplevel):
    def __init__(self, parent, db_list, on_close=None):
        super().__init__(parent)
        self.title(_T("Materials Database")); _set_icon(self)
        self.configure(bg=BG)
        self.geometry("780x560")
        self.minsize(700, 460)
        self.grab_set()
        self._db = db_list          # mutable list shared with app
        self._on_close = on_close
        self._build()
        self._refresh()

    def _build(self):
        # ── Disclaimer banner ────────────────────────────────────────────
        db_frame = tk.Frame(self, bg="#EFF6FF", bd=1, relief="groove")
        db_frame.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(db_frame,
            text="⚠  Always verify density values against your material's own SDS or datasheet before use.",
            bg="#EFF6FF", fg="#1C4E8A", font=("Segoe UI", 8, "italic"),
            anchor="w", wraplength=520, padx=8, pady=4).pack(fill="x")

        # ── Search bar ───────────────────────────────────────────────────
        top = tk.Frame(self, bg=BG, pady=5, padx=8); top.pack(fill="x")
        _lbl(top, _T("Search:")).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh())
        tk.Entry(top, textvariable=self._search_var, width=28,
                 bg=BG_WHITE, fg=TEXT, relief="flat", bd=1,
                 font=("Segoe UI", 9)).pack(side="left", padx=(4, 0))

        # ── Treeview ─────────────────────────────────────────────────────
        tf = tk.Frame(self, bg=BG, bd=0, relief="flat", highlightthickness=1, highlightbackground=BORDER)
        tf.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        cols = [("acronym","Acronym",140,"w"),("name","Full Name",260,"w"),("density","Density (g/cm³)",110,"center"),("ri","RI",70,"center"),("mw","MW (g/mol)",90,"center")]
        self._tree = _make_tree(tf, cols)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y"); self._tree.pack(side="left", fill="both", expand=True)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # ── Edit fields ──────────────────────────────────────────────────
        sep1 = tk.Frame(self, bg=BORDER, height=1); sep1.pack(fill="x", padx=8, pady=(2,0))
        ef = tk.Frame(self, bg=BG, padx=8, pady=6); ef.pack(fill="x")
        # Row 0: Acronym + Full Name
        _lbl(ef, _T("Acronym:")).grid(row=0, column=0, sticky="e", padx=(0,4))
        self._var_acronym = tk.StringVar()
        tk.Entry(ef, textvariable=self._var_acronym, width=18,
                 bg=BG_WHITE, fg=TEXT, relief="flat", bd=1,
                 font=("Segoe UI", 9)).grid(row=0, column=1, sticky="w", padx=(0,12))
        _lbl(ef, _T("Full Name:")).grid(row=0, column=2, sticky="e", padx=(0,4))
        self._var_name = tk.StringVar()
        tk.Entry(ef, textvariable=self._var_name, width=34,
                 bg=BG_WHITE, fg=TEXT, relief="flat", bd=1,
                 font=("Segoe UI", 9)).grid(row=0, column=3, columnspan=3, sticky="w")
        # Row 1: Density + RI + MW
        _lbl(ef, "Density (g/cm³):").grid(row=1, column=0, sticky="e", padx=(0,4), pady=(4,0))
        self._var_density = tk.StringVar()
        tk.Entry(ef, textvariable=self._var_density, width=9, justify="right",
                 bg=BG_WHITE, fg=TEXT, relief="flat", bd=1,
                 font=("Segoe UI", 9)).grid(row=1, column=1, sticky="w", padx=(0,12), pady=(4,0))
        _lbl(ef, _T("RI:")).grid(row=1, column=2, sticky="e", padx=(0,4), pady=(4,0))
        self._var_ri = tk.StringVar()
        tk.Entry(ef, textvariable=self._var_ri, width=8, justify="right",
                 bg=BG_WHITE, fg=TEXT, relief="flat", bd=1,
                 font=("Segoe UI", 9)).grid(row=1, column=3, sticky="w", padx=(0,12), pady=(4,0))
        _lbl(ef, "MW (g/mol):").grid(row=1, column=4, sticky="e", padx=(0,4), pady=(4,0))
        self._var_mw = tk.StringVar()
        tk.Entry(ef, textvariable=self._var_mw, width=9, justify="right",
                 bg=BG_WHITE, fg=TEXT, relief="flat", bd=1,
                 font=("Segoe UI", 9)).grid(row=1, column=5, sticky="w", pady=(4,0))

        # ── Button row 1: edit actions ────────────────────────────────────
        sep2 = tk.Frame(self, bg=BORDER, height=1); sep2.pack(fill="x", padx=8, pady=(0,0))
        bf1 = tk.Frame(self, bg=BG, padx=8, pady=5); bf1.pack(fill="x")
        _btn(bf1, _T("➕ Add / Update"), self._add_update, "success").pack(side="left", padx=(0,4))
        _btn(bf1, _T("🗑 Delete"),        self._delete,     "danger" ).pack(side="left", padx=(0,4))
        _btn(bf1, _T("✖ Clear fields"),  self._clear_fields,"neutral").pack(side="left")
        _btn(bf1, _T("⊕ Create Blend"), self._create_blend, "neutral").pack(side="left", padx=(12, 0))

        # ── Button row 2: database actions + close ────────────────────────
        sep3 = tk.Frame(self, bg=BORDER, height=1); sep3.pack(fill="x", padx=8, pady=(0,0))
        bf2 = tk.Frame(self, bg=BG_ALT, padx=8, pady=5); bf2.pack(fill="x")
        _lbl(bf2, "Database file:", font=("Segoe UI", 8)).pack(side="left", padx=(0,6))
        _btn(bf2, _T("📤 Export DB"), self._export_db, "neutral").pack(side="left", padx=(0,4))
        _btn(bf2, _T("📥 Import DB"), self._import_db, "neutral").pack(side="left")
        _btn(bf2, _T("✔ Close"),      self._close,     "normal" ).pack(side="right")

    def _refresh(self):
        q = self._search_var.get().strip().lower()
        self._tree.delete(*self._tree.get_children())
        shown = [m for m in self._db if q in m["acronym"].lower() or q in m["name"].lower()] if q else self._db
        for i, m in enumerate(shown):
            tag = "even" if i % 2 == 0 else "odd"
            ri_str  = f"{m['ri']:.4f}"  if m.get("ri")  else ""
            mw_str  = f"{m['mw']:.1f}"  if m.get("mw")  else ""
            self._tree.insert("", "end", iid=m["acronym"], tags=(tag,),
                              values=(m["acronym"], m["name"], f"{m['density']:.3f}", ri_str, mw_str))

    def _on_select(self, _=None):
        sel = self._tree.selection()
        if not sel: return
        name = sel[0]
        mat = next((m for m in self._db if m["acronym"] == name), None)
        if mat:
            self._var_name.set(mat["name"])
            self._var_density.set(str(mat["density"]))

    def _add_update(self):
        acronym = self._var_acronym.get().strip()
        if not acronym: messagebox.showwarning(_T("Input"), _T("Acronym cannot be empty."), parent=self); return
        try: density = float(self._var_density.get())
        except ValueError: messagebox.showwarning(_T("Input"), _T("Density must be a number."), parent=self); return
        ri = None; mw = None
        try: ri = float(self._var_ri.get()) if self._var_ri.get().strip() else None
        except ValueError: messagebox.showwarning(_T("Input"), _T("RI must be a number or blank."), parent=self); return
        try: mw = float(self._var_mw.get()) if self._var_mw.get().strip() else None
        except ValueError: messagebox.showwarning(_T("Input"), _T("MW must be a number or blank."), parent=self); return
        fullname = self._var_name.get().strip()
        existing = next((m for m in self._db if m["acronym"] == acronym), None)
        if existing:
            existing.update({"name": fullname, "density": density, "ri": ri, "mw": mw})
        else:
            self._db.append({"acronym": acronym, "name": fullname, "density": density, "ri": ri, "mw": mw})
        self._db.sort(key=lambda m: m["acronym"].lower())
        save_materials_db(self._db)
        self._refresh()
        self._tree.selection_set(acronym) if acronym in [self._tree.item(i)["values"][0]
            for i in self._tree.get_children()] else None

    def _delete(self):
        sel = self._tree.selection()
        if not sel: messagebox.showinfo(_T("Input"), "Select a material first.", parent=self); return
        name = sel[0]
        if messagebox.askyesno(_T("🗑 Delete"), f"Delete '{name}'?", parent=self):
            self._db[:] = [m for m in self._db if m["acronym"] != name]
            save_materials_db(self._db)
            self._refresh()

    def _clear_fields(self):
        self._var_acronym.set(""); self._var_name.set(""); self._var_density.set(""); self._var_ri.set(""); self._var_mw.set("")

    def _export_db(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            parent=self, title="Export Materials Database",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="materials_db_export.json")
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._db, f, indent=2, ensure_ascii=False)
            messagebox.showinfo(_T("Export"), f"Database exported to:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror(_T("Export"), str(e), parent=self)

    def _import_db(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=self, title="Import Materials Database",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list) or not all(
                    isinstance(m, dict) and ("acronym" in m or "name" in m) and "density" in m for m in data):
                messagebox.showerror(_T("Import"),
                    _T("File does not appear to be a valid materials database."), parent=self)
                return
            n_new = sum(1 for m in data if not any(e["acronym"] == _migrate_entry(m)["acronym"] for e in self._db))
            n_upd = sum(1 for m in data if any(e["acronym"] == _migrate_entry(m)["acronym"] for e in self._db))
            msg = (f"Found {len(data)} materials in the file:\n"
                   f"  • {n_new} new entries will be added\n"
                   f"  • {n_upd} existing entries will be updated\n\n"
                   f"Proceed?")
            if not messagebox.askyesno("📥 Import Database", msg, parent=self): return
            for m in data:
                mm = _migrate_entry(m)
                existing = next((e for e in self._db if e["acronym"] == mm["acronym"]), None)
                if existing:
                    existing.update({"density": mm["density"], "name": mm["name"],
                                     "ri": mm.get("ri"), "mw": mm.get("mw")})
                else:
                    self._db.append(mm)
            self._db.sort(key=lambda m: m["acronym"].lower())
            save_materials_db(self._db)
            self._refresh()
            messagebox.showinfo("Import",
                f"Import complete: {n_new} added, {n_upd} updated.", parent=self)
        except Exception as e:
            messagebox.showerror(_T("Import"), str(e), parent=self)

    def _close(self):
        if self._on_close: self._on_close()
        self.destroy()

    def _create_blend(self):
        BlendDialog(self, self._db, on_created=self._refresh)


# ─────────────────────────────────────────────
#  BLEND DIALOG
# ─────────────────────────────────────────────
class BlendDialog(tk.Toplevel):
    """Dialog for creating a named blend of materials by wt.% with
    ideal-mixing density calculation. Saves result to the DB."""

    MAX_COMPONENTS = 6

    def __init__(self, parent, db_list, on_created=None):
        super().__init__(parent)
        self.title(_T("Create Blend")); _set_icon(self)
        self.configure(bg=BG)
        self.geometry(f"{_s(520)}x{_s(480)}")
        self.minsize(480, 400)
        self.grab_set()
        self._db      = db_list
        self._on_created = on_created
        self._names   = [tk.StringVar() for _ in range(self.MAX_COMPONENTS)]
        self._wts     = [tk.StringVar() for _ in range(self.MAX_COMPONENTS)]
        self._rows    = []          # list of (frame, ac_entry, wt_entry)
        self._n_rows  = tk.IntVar(value=2)
        self._result_density = tk.StringVar(value="")
        self._blend_name     = tk.StringVar(value="")
        self._build()

    def _build(self):
        # ── Info banner ───────────────────────────────────────────
        banner = tk.Frame(self, bg="#E8F5E9", bd=1, relief="groove")
        banner.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(banner,
            text="Define a monomer blend. Enter wt.% for each component "
                 "(must total 100). Density is calculated by ideal mixing.",
            bg="#F0FFF4", fg="#0D6B0D", font=("Segoe UI", 8, "italic"),
            anchor="w", wraplength=480, padx=8, pady=4).pack(fill="x")

        # ── Component rows header ─────────────────────────────────
        hdr = tk.Frame(self, bg=BG_ALT, padx=8, pady=3)
        hdr.pack(fill="x", padx=8)
        tk.Label(hdr, text="Material", bg=BG_ALT, fg=TEXT,
                 font=("Segoe UI", 8, "bold"), width=28, anchor="w").grid(
                 row=0, column=0, sticky="w")
        tk.Label(hdr, text="wt.%", bg=BG_ALT, fg=TEXT,
                 font=("Segoe UI", 8, "bold"), width=8, anchor="center").grid(
                 row=0, column=1, padx=(4, 0), sticky="w")

        # ── Scrollable component area ─────────────────────────────
        self._comp_frame = tk.Frame(self, bg=BG, padx=8)
        self._comp_frame.pack(fill="x")
        self._rebuild_rows()

        # ── Add/remove row buttons ────────────────────────────────
        rb = tk.Frame(self, bg=BG, padx=8, pady=2)
        rb.pack(fill="x")
        _btn(rb, _T("➕ Add"),    self._add_row,    "neutral",
             font=("Segoe UI", 8)).pack(side="left", padx=(0, 4))
        _btn(rb, _T("− Remove last"),      self._remove_row, "neutral",
             font=("Segoe UI", 8)).pack(side="left")

        # ── Calculate button + density result ─────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=8, pady=(6, 0))
        cf = tk.Frame(self, bg=BG, padx=8, pady=6)
        cf.pack(fill="x")
        _btn(cf, _T("⟳ Calculate density"), self._calculate, "normal").pack(
             side="left", padx=(0, 10))
        tk.Label(cf, text="Blend density:", bg=BG, fg=TEXT,
                 font=("Segoe UI", 9)).pack(side="left")
        tk.Label(cf, textvariable=self._result_density, bg=BG, fg=ACCENT,
                 font=("Segoe UI", 9, "bold"), width=12, anchor="w").pack(
                 side="left", padx=(4, 0))

        # ── Blend name + save ─────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=8, pady=(0, 0))
        nf = tk.Frame(self, bg=BG, padx=8, pady=6)
        nf.pack(fill="x")
        tk.Label(nf, text="Blend name:", bg=BG, fg=TEXT,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="e",
                 padx=(0, 6))
        tk.Entry(nf, textvariable=self._blend_name, width=32,
                 bg=BG_WHITE, fg=TEXT, relief="flat", bd=1,
                 font=("Segoe UI", 9)).grid(row=0, column=1, sticky="w")

        # ── Bottom buttons ────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=8, pady=(0, 0))
        bf = tk.Frame(self, bg=BG_ALT, padx=8, pady=5)
        bf.pack(fill="x")
        _btn(bf, _T("💾 Save to Database"), self._save,   "success").pack(side="left")
        _btn(bf, "✖ Cancel",            self.destroy, "neutral").pack(side="right")

    def _rebuild_rows(self):
        for w in self._comp_frame.winfo_children():
            w.destroy()
        self._rows.clear()
        n = self._n_rows.get()
        for i in range(n):
            row_bg = BG if i % 2 == 0 else BG_ALT
            rf = tk.Frame(self._comp_frame, bg=row_bg, pady=3, padx=4)
            rf.pack(fill="x")
            ac = AutocompleteEntry(rf, width=28, db_ref=self._db)
            ac.pack(side="left", padx=(0, 4))
            # restore existing text if re-building after add/remove row
            if self._names[i].get():
                ac.set(self._names[i].get())
            # keep names[i] in sync with whatever the user types/selects
            ac.var.trace_add("write", lambda *_, idx=i, v=ac.var:
                             self._names[idx].set(v.get()))
            wt_e = tk.Entry(rf, textvariable=self._wts[i], width=7,
                            justify="right", bg=BG_WHITE, fg=TEXT,
                            relief="flat", bd=1, font=("Segoe UI", 9))
            wt_e.pack(side="left", padx=(0, 4))
            tk.Label(rf, text="wt.%", bg=row_bg, fg=TEXT,
                     font=("Segoe UI", 8)).pack(side="left")
            self._rows.append((rf, ac, wt_e))

    def _add_row(self):
        n = self._n_rows.get()
        if n >= self.MAX_COMPONENTS:
            messagebox.showinfo("Limit",
                f"Maximum {self.MAX_COMPONENTS} components supported.",
                parent=self)
            return
        self._n_rows.set(n + 1)
        self._rebuild_rows()

    def _remove_row(self):
        n = self._n_rows.get()
        if n <= 2:
            messagebox.showinfo("Minimum", _T("A blend needs at least 2 components."),
                parent=self)
            return
        self._names[n - 1].set("")
        self._wts[n - 1].set("")
        self._n_rows.set(n - 1)
        self._rebuild_rows()

    def _parse_components(self):
        """Return list of (density, wt_fraction) or raise ValueError with message."""
        n = self._n_rows.get()
        components = []
        total_wt = 0.0
        for i in range(n):
            name = self._names[i].get().strip()
            wt_str = self._wts[i].get().strip()
            if not name and not wt_str:
                continue   # skip blank rows silently
            if not name:
                raise ValueError(f"Row {i+1}: material name is missing.")
            if not wt_str:
                raise ValueError(f"Row {i+1}: wt.% is missing for '{name}'.")
            mat = next((m for m in self._db if m["acronym"] == name), None)
            if mat is None:
                raise ValueError(
                    f"'{name}' not found in the database.\n"
                    "Please select a material from the dropdown.")
            try:
                wt = float(wt_str)
            except ValueError:
                raise ValueError(f"Row {i+1}: '{wt_str}' is not a valid number.")
            if wt <= 0:
                raise ValueError(f"Row {i+1}: wt.% must be greater than zero.")
            total_wt += wt
            components.append((mat["density"], wt))
        if len(components) < 2:
            raise ValueError("Please enter at least 2 components.")
        if abs(total_wt - 100.0) > 0.01:
            raise ValueError(
                f"wt.% values sum to {total_wt:.3f} — they must total 100.")
        return components

    def _calculate(self):
        try:
            components = self._parse_components()
        except ValueError as e:
            messagebox.showwarning("Input Error", str(e), parent=self)
            self._result_density.set("")
            return
        # Ideal mixing: 1/rho_blend = sum(wi/rho_i)  where wi = wt fraction
        inv_rho = sum(wt / 100.0 / rho for rho, wt in components)
        rho_blend = 1.0 / inv_rho
        self._result_density.set(f"{rho_blend:.2f} g/cm³")
        # Auto-suggest a name if blank
        if not self._blend_name.get().strip():
            n = self._n_rows.get()
            parts = []
            for i in range(n):
                nm = self._names[i].get().strip()
                wt = self._wts[i].get().strip()
                if nm and wt:
                    parts.append(f"{nm} {wt}%")
            self._blend_name.set(" / ".join(parts))
        return rho_blend

    def _save(self):
        try:
            components = self._parse_components()
        except ValueError as e:
            messagebox.showwarning("Input Error", str(e), parent=self)
            return
        inv_rho = sum(wt / 100.0 / rho for rho, wt in components)
        rho_blend = 1.0 / inv_rho
        self._result_density.set(f"{rho_blend:.2f} g/cm³")

        name = self._blend_name.get().strip()
        if not name:
            messagebox.showwarning("Input Error",
                _T("Please enter a name for the blend."), parent=self)
            return

        existing = next((m for m in self._db if m["acronym"] == name), None)
        if existing:
            if not messagebox.askyesno("Overwrite",
                    f"'{name}' already exists in the database.\nOverwrite it?",
                    parent=self):
                return
            existing["density"] = round(rho_blend, 4); existing.setdefault("acronym", name); existing.setdefault("ri", None); existing.setdefault("mw", None)
        else:
            self._db.append({"acronym": name, "name": "", "density": round(rho_blend, 4), "ri": None, "mw": None})
        self._db.sort(key=lambda m: m["acronym"].lower())
        save_materials_db(self._db)
        if self._on_created:
            self._on_created()
        messagebox.showinfo(_T("Saved"),
            f"'{name}' saved to database.\n"
            f"Density: {rho_blend:.2f} g/cm³", parent=self)
        self.destroy()


# ─────────────────────────────────────────────
#  DATA MODELS
# ─────────────────────────────────────────────
class Component:
    def __init__(self, name="", density=1.0,
                 input_mode="Mass (g)", value=0.0, ref_name=""):
        self.name=name; self.density=float(density)
        self.input_mode=input_mode; self.value=float(value); self.ref_name=ref_name
        self.mass=0.0; self.volume=0.0

class InvComponent:
    def __init__(self, name="", density=1.0,
                 rel_mode="wt.% to Reference", value=0.0, ref_name=""):
        self.name=name; self.density=float(density)
        self.rel_mode=rel_mode; self.value=float(value); self.ref_name=ref_name
        self.mass=0.0; self.volume=0.0

# ─────────────────────────────────────────────
#  FORWARD ENGINE
# ─────────────────────────────────────────────
def calculate_formulation(components):
    comps={c.name:c for c in components}
    for c in components:
        if c.input_mode=="Mass (g)":       c.mass=c.value;   c.volume=c.mass/c.density
        elif c.input_mode=="Volume (cm3)": c.volume=c.value; c.mass=c.volume*c.density
    for _ in range(20):
        for c in components:
            if c.input_mode in ("wt.% to Reference","vol.% to Reference"):
                ref=comps.get(c.ref_name)
                if ref is None: raise ValueError(f"Ref '{c.ref_name}' not found for '{c.name}'.")
                if not(ref.mass or ref.volume): continue
                if c.input_mode=="wt.% to Reference":
                    c.mass=(c.value/100)*ref.mass; c.volume=c.mass/c.density
                else:
                    c.volume=(c.value/100)*ref.volume; c.mass=c.volume*c.density
    pct_m=[c for c in components if c.input_mode=="wt.% of Total"]
    pct_v=[c for c in components if c.input_mode=="vol.% of Total"]
    abs_c=[c for c in components if c.input_mode not in("wt.% of Total","vol.% of Total")]
    if pct_m:
        am=sum(c.mass for c in abs_c); ps=sum(c.value for c in pct_m)
        if ps>=100: raise ValueError("Sum of 'wt.% of Total' >= 100%.")
        tm=am/(1-ps/100)
        for c in pct_m: c.mass=(c.value/100)*tm; c.volume=c.mass/c.density
    if pct_v:
        av=sum(c.volume for c in abs_c); ps=sum(c.value for c in pct_v)
        if ps>=100: raise ValueError("Sum of 'vol.% of Total' >= 100%.")
        tv=av/(1-ps/100)
        for c in pct_v: c.volume=(c.value/100)*tv; c.mass=c.volume*c.density
    tm=sum(c.mass for c in components); tv=sum(c.volume for c in components)
    if tm==0 or tv==0: raise ValueError("Total mass or volume is zero.")
    rows=[{"name":c.name,"density":c.density,"mass":c.mass,"volume":c.volume,
           "wt_pct":(c.mass/tm)*100,"vol_pct":(c.volume/tv)*100} for c in components]
    return {"rows":rows,"total_mass":tm,"total_volume":tv,"theoretical_density":tm/tv}

# ─────────────────────────────────────────────
#  INVERSE ENGINE
# ─────────────────────────────────────────────
def _dep_mass_factor(bal_name,all_comps):
    fac=0.0; q=[(bal_name,1.0)]; vis=set()
    while q:
        rn,m=q.pop(0)
        for c in all_comps:
            if c.rel_mode=="wt.% to Reference" and c.ref_name==rn and c.name not in vis:
                vis.add(c.name); cm=m*(c.value/100); fac+=cm; q.append((c.name,cm))
    return fac

def _dep_vol_factor(bal_name,all_comps):
    fac=0.0; q=[(bal_name,1.0)]; vis=set()
    while q:
        rn,m=q.pop(0)
        for c in all_comps:
            if c.rel_mode=="wt.% to Reference" and c.ref_name==rn and c.name not in vis:
                vis.add(c.name); cm=m*(c.value/100); fac+=cm/c.density; q.append((c.name,cm))
    return fac

def solve_inverse(inv_comps,target_mode,target_value,anchor_name,anchor_mode,anchor_value):
    comps={c.name:c for c in inv_comps}
    T=target_value/100.0
    if not(0<T<1): raise ValueError("Target must be 0–100.")
    balances=[c for c in inv_comps if c.rel_mode=="Balance"]
    if len(balances)>1: raise ValueError(f"Only one Balance allowed. Found {len(balances)}.")
    anchor=comps.get(anchor_name)
    if anchor is None: raise ValueError(f"Primary component '{anchor_name}' not found.")
    if anchor_mode=="Mass (g)":     anchor.mass=anchor_value; anchor.volume=anchor.mass/anchor.density
    else:                           anchor.volume=anchor_value; anchor.mass=anchor.volume*anchor.density
    for c in inv_comps:
        if c.rel_mode=="Independent Mass (g)":    c.mass=c.value;   c.volume=c.mass/c.density
        elif c.rel_mode=="Independent Vol (cm3)": c.volume=c.value; c.mass=c.volume*c.density
    for _ in range(30):
        for c in inv_comps:
            if c.rel_mode in("Balance","Independent Mass (g)","Independent Vol (cm3)",
                             "wt.% of Total Suspension","vol.% of Total Suspension"): continue
            if c.rel_mode=="wt.% to Reference":
                ref=comps.get(c.ref_name)
                if ref and(ref.mass or ref.volume): c.mass=(c.value/100)*ref.mass; c.volume=c.mass/c.density
            elif c.rel_mode=="vol.% to Reference":
                ref=comps.get(c.ref_name)
                if ref and(ref.mass or ref.volume): c.volume=(c.value/100)*ref.volume; c.mass=c.volume*c.density
    pg_m=[c for c in inv_comps if c.rel_mode=="wt.% of Total Suspension"]
    pg_v=[c for c in inv_comps if c.rel_mode=="vol.% of Total Suspension"]
    # Validate percentages early, but defer actual resolution until after Balance is solved
    if pg_m:
        ps=sum(c.value for c in pg_m)
        if ps>=100: raise ValueError("Sum of 'wt.% of Total Suspension' >= 100%.")
    if pg_v:
        ps=sum(c.value for c in pg_v)
        if ps>=100: raise ValueError("Sum of 'vol.% of Total Suspension' >= 100%.")
    dep_names=set()
    for bal in balances:
        q=[bal.name]
        while q:
            rn=q.pop()
            for c in inv_comps:
                if c.rel_mode in("wt.% to Reference","vol.% to Reference") and c.ref_name==rn and c.name not in dep_names:
                    dep_names.add(c.name); q.append(c.name)
    for c in inv_comps:
        if c.rel_mode in("Balance","Primary","wt.% of Total Suspension","vol.% of Total Suspension") or c.name in dep_names: continue
        if c.mass==0 and c.volume==0:
            raise ValueError(f"'{c.name}' could not be resolved. Check its Ref name.")
    if balances:
        bal=balances[0]
        F_m=_dep_mass_factor(bal.name,inv_comps); Fv=_dep_vol_factor(bal.name,inv_comps)
        known=[c for c in inv_comps if c.name!=bal.name and c.name not in dep_names
               and c.rel_mode not in("wt.% of Total Suspension","vol.% of Total Suspension")]
        b_sv=sum(c.volume for c in known if c.name==anchor_name)
        b_sm=sum(c.mass   for c in known if c.name==anchor_name)
        b_lv=sum(c.volume for c in known if c.name!=anchor_name)
        b_lm=sum(c.mass   for c in known if c.name!=anchor_name)
        a_lv=1.0/bal.density+Fv; a_lm=1.0+F_m
        # Suspension fractions: these components will be (f/100)*V_total or (f/100)*M_total
        # Their presence scales the total, so we correct the target equation:
        #   vol.%: V_primary*(1-F_pv) = T*(V_known + M_bal*a_lv)
        #   wt.%:  M_primary*(1-F_pm) = T*(M_known + M_bal*a_lm)
        F_pv=sum(c.value/100 for c in pg_v)
        F_pm=sum(c.value/100 for c in pg_m)
        if target_mode=="vol.%":
            # V_anchor*((1-F_pv)/T - 1) - V_others = M_bal*a_lv
            numer=b_sv*((1-F_pv)/T - 1) - b_lv; denom=a_lv
            if abs(denom)<1e-12: raise ValueError("Cannot solve: system already at target.")
            M_bal=numer/denom
        else:
            # M_anchor*((1-F_pm)/T - 1) - M_others = M_bal*a_lm
            numer=b_sm*((1-F_pm)/T - 1) - b_lm; denom=a_lm
            if abs(denom)<1e-12: raise ValueError("Cannot solve: system already at target.")
            M_bal=numer/denom
        if M_bal<=0: raise ValueError(f"No positive solution for '{bal.name}' (M={M_bal:.4f} g).")
        bal.mass=M_bal; bal.volume=M_bal/bal.density
        for _ in range(30):
            for c in inv_comps:
                if c.name not in dep_names: continue
                if c.rel_mode=="wt.% to Reference":
                    ref=comps.get(c.ref_name)
                    if ref and(ref.mass or ref.volume): c.mass=(c.value/100)*ref.mass; c.volume=c.mass/c.density
                elif c.rel_mode=="vol.% to Reference":
                    ref=comps.get(c.ref_name)
                    if ref and(ref.mass or ref.volume): c.volume=(c.value/100)*ref.volume; c.mass=c.volume*c.density
        k=1.0
    else:
        fixed=[c for c in inv_comps if c.rel_mode in("Independent Mass (g)","Independent Vol (cm3)")]
        scalable=[c for c in inv_comps if c not in fixed]
        anc=comps[anchor_name]
        if target_mode=="vol.%":
            A=anc.volume if anc in scalable else 0; B=sum(c.volume for c in scalable)
            C=anc.volume if anc in fixed else 0;    D=sum(c.volume for c in fixed)
        else:
            A=anc.mass if anc in scalable else 0; B=sum(c.mass for c in scalable)
            C=anc.mass if anc in fixed else 0;    D=sum(c.mass for c in fixed)
        denom=T*B-A
        if abs(denom)<1e-12: raise ValueError("Cannot solve: already at target.")
        k=(C-T*D)/denom
        if k<=0: raise ValueError(f"No positive solution (k={k:.4f}).")
        for c in scalable: c.mass*=k; c.volume*=k
    # ── Total Suspension components resolved last, against true full total ──
    # Non-suspension components are now all known; solve algebraically.
    if pg_m or pg_v:
        non_susp=[c for c in inv_comps if c.rel_mode not in
                  ("wt.% of Total Suspension","vol.% of Total Suspension")]
        if pg_m:
            am=sum(c.mass for c in non_susp)
            ps=sum(c.value for c in pg_m)
            gt=am/(1-ps/100)
            for c in pg_m: c.mass=(c.value/100)*gt; c.volume=c.mass/c.density
        if pg_v:
            av=sum(c.volume for c in non_susp)
            ps=sum(c.value for c in pg_v)
            gt=av/(1-ps/100)
            for c in pg_v: c.volume=(c.value/100)*gt; c.mass=c.volume*c.density
    tm=sum(c.mass for c in inv_comps); tv=sum(c.volume for c in inv_comps)
    anc=comps[anchor_name]
    rows=[{"name":c.name,"density":c.density,"mass":c.mass,"volume":c.volume,
           "wt_pct":(c.mass/tm)*100,"vol_pct":(c.volume/tv)*100} for c in inv_comps]
    return {"rows":rows,"total_mass":tm,"total_volume":tv,"theoretical_density":tm/tv,
            "solids_loading_wt":(anc.mass/tm)*100,"solids_loading_vol":(anc.volume/tv)*100,
            "scale_factor":k if not balances else 1.0}

# ─────────────────────────────────────────────
#  PDF EXPORT
# ─────────────────────────────────────────────
def export_pdf(result, recipe_name, filepath, extra_note=""):
    doc=SimpleDocTemplate(filepath,pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,
                          topMargin=20*mm,bottomMargin=20*mm)
    styles=getSampleStyleSheet()
    def ps(n,**kw): return ParagraphStyle(n,parent=styles["Normal"],**kw)
    story=[]
    story.append(Paragraph("The 3D Printing Formulator",
        ps("T",fontName="Helvetica-Bold",fontSize=18,
           textColor=colors.HexColor(ACCENT),spaceAfter=2*mm,alignment=TA_CENTER)))
    story.append(Paragraph("By Dr Thanos Goulas",
        ps("S",fontName="Helvetica",fontSize=9,
           textColor=colors.HexColor(TEXT_MUTED),alignment=TA_CENTER,spaceAfter=6*mm)))
    story.append(HRFlowable(width="100%",thickness=1,
                            color=colors.HexColor(ACCENT),spaceAfter=4*mm))
    if recipe_name:
        story.append(Paragraph(f"Recipe: {recipe_name}",
            ps("R",fontName="Helvetica-Bold",fontSize=13,
               textColor=colors.black,alignment=TA_CENTER,spaceAfter=1*mm)))
    if extra_note:
        story.append(Paragraph(extra_note,
            ps("N",fontName="Helvetica-Oblique",fontSize=9,
               textColor=colors.HexColor(ACCENT),alignment=TA_CENTER,spaceAfter=3*mm)))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d  %H:%M')}",
        ps("D",fontName="Helvetica",fontSize=8,
           textColor=colors.HexColor(TEXT_MUTED),alignment=TA_CENTER,spaceAfter=6*mm)))
    data=[["Component","Density (g/cm\u00b3)","Mass (g)","Volume (cm\u00b3)","wt.%","vol.%"]]
    for r in result["rows"]:
        data.append([r["name"],f"{r['density']:.3f}",f"{r['mass']:.2f}",
                     f"{r['volume']:.2f}",f"{r['wt_pct']:.2f}%",f"{r['vol_pct']:.2f}%"])
    data.append(["TOTAL","—",f"{result['total_mass']:.2f}",
                 f"{result['total_volume']:.2f}","100.00%","100.00%"])
    cw=[60*mm,28*mm,25*mm,28*mm,18*mm,18*mm]
    tbl=Table(data,colWidths=cw,repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor(ACCENT)),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),("ALIGN",(0,1),(0,-1),"LEFT"),
        ("ROWBACKGROUNDS",(0,1),(-1,-2),[colors.white,colors.HexColor(BG_ALT)]),
        ("TEXTCOLOR",(0,1),(-1,-2),colors.black),
        ("BACKGROUND",(0,-1),(-1,-1),colors.HexColor(TOTAL_BG)),
        ("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold"),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor(BORDER)),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story.append(tbl); story.append(Spacer(1,6*mm))
    story.append(HRFlowable(width="100%",thickness=0.5,
                            color=colors.HexColor(BORDER),spaceAfter=3*mm))
    sd=[["Theoretical Density",f"{result['theoretical_density']:.4f} g/cm\u00b3",
         "Total Mass",f"{result['total_mass']:.2f} g"],
        ["","","Total Volume",f"{result['total_volume']:.4f} cm\u00b3"]]
    if "solids_loading_wt" in result:
        sd.append(["Primary wt.%",f"{result['solids_loading_wt']:.2f} %",
                   "Primary vol.%",f"{result['solids_loading_vol']:.2f} %"])
    st=Table(sd,colWidths=[48*mm,38*mm,40*mm,34*mm])
    st.setStyle(TableStyle([("FONTSIZE",(0,0),(-1,-1),9),
        ("TEXTCOLOR",(0,0),(0,-1),colors.HexColor(TEXT_MUTED)),
        ("FONTNAME",(1,0),(1,-1),"Helvetica-Bold"),
        ("FONTNAME",(3,0),(3,-1),"Helvetica-Bold"),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    story.append(st)
    doc.build(story)

# ─────────────────────────────────────────────
#  UI HELPERS
# ─────────────────────────────────────────────
def _style_ttk(root):
    s=ttk.Style(root); s.theme_use("clam")
    # Combobox
    s.configure("TCombobox",fieldbackground=BG_WHITE,background=BG_WHITE,
        foreground=TEXT,bordercolor=BORDER_MED,arrowcolor=TEXT_DIM,
        selectbackground=SEL_BG,selectforeground=SEL_FG,relief="flat",padding=4)
    s.map("TCombobox",
        fieldbackground=[("readonly",BG_WHITE)],
        selectbackground=[("readonly",SEL_BG)],
        foreground=[("readonly",TEXT)],
        bordercolor=[("focus",ACCENT)])
    # Thin minimal scrollbar
    s.configure("Vertical.TScrollbar",
        troughcolor=BG,background=BORDER_MED,bordercolor=BG,
        arrowcolor=BG,arrowsize=0,width=5,relief="flat")
    s.map("Vertical.TScrollbar",
        background=[("active",TEXT_MUTED),("pressed",TEXT_DIM)])
    # (Notebook replaced by frame stack — no ttk.Notebook styling needed)
    # Treeview
    s.configure("App.Treeview",
        background=BG_WHITE,foreground=TEXT,fieldbackground=BG_WHITE,
        borderwidth=0,font=("Segoe UI",10),rowheight=28)
    s.configure("App.Treeview.Heading",
        background=BG_HDR,foreground=TEXT_DIM,
        font=("Segoe UI",9,"bold"),relief="flat",borderwidth=0)
    s.map("App.Treeview",
        background=[("selected",SEL_BG)],
        foreground=[("selected",SEL_FG)])
    s.map("App.Treeview.Heading",
        background=[("active",BORDER)],foreground=[("active",TEXT)])
    s.configure("TCheckbutton",background=BG,foreground=TEXT,font=("Segoe UI",9))

def _make_tree(parent, col_defs):
    cols = [c[0] for c in col_defs]
    tree = ttk.Treeview(parent, columns=cols, show="headings",
                        style="App.Treeview", selectmode="browse")
    for cid, heading, width, anchor in col_defs:
        tree.heading(cid, text=heading)
        # '#' (index) column is fixed; all others stretch to fill available space
        fixed = (cid == "idx")
        tree.column(cid, width=width, minwidth=max(_s(40), width//2),
                    anchor=anchor, stretch=not fixed)
    tree.tag_configure("even", background=BG_WHITE)
    tree.tag_configure("odd",  background=BG_ALT)
    tree.tag_configure("total", background=TOTAL_BG, font=("Segoe UI",10,"bold"), foreground=ACCENT)

    # Redistribute non-fixed column widths whenever the frame is resized
    def _on_resize(event, _tree=tree, _cols=col_defs):
        fixed_w = sum(w for cid, _, w, __ in _cols if cid == "idx")
        stretch_total = sum(w for cid, _, w, __ in _cols if cid != "idx")
        avail = event.width - fixed_w - 4   # 4 px for scrollbar/border
        if avail <= 0 or stretch_total <= 0:
            return
        scale = avail / stretch_total
        for cid, _, w, __ in _cols:
            if cid != "idx":
                _tree.column(cid, width=max(40, int(w * scale)))

    parent.bind("<Configure>", _on_resize, add="+")
    return tree

def _share_file(tab, parent_widget):
    """Share dialog — auto-generates a temp PDF or JSON if nothing saved yet."""
    recipe_name = tab.app.var_recipe_name.get() or "formulation"

    # ── Resolve share path: prefer last PDF, then last JSON, then generate ──
    path = getattr(tab, "_last_pdf", None) or getattr(tab, "_last_json", None)
    _tmp_files = []  # track temp files for cleanup

    if not path or not os.path.exists(path):
        # Auto-generate a temp PDF if results exist, else a temp JSON
        tmp_dir = tempfile.gettempdir()
        safe_name = recipe_name.replace(" ", "_")
        if getattr(tab, "last_result", None):
            path = os.path.join(tmp_dir, f"{safe_name}.pdf")
            try:
                export_pdf(tab.last_result, recipe_name, path)
                _tmp_files.append(path)
            except Exception as e:
                messagebox.showerror("Share", f"Could not generate PDF:\n{e}",
                                     parent=parent_widget); return
        elif getattr(tab, "components", None):
            path = os.path.join(tmp_dir, f"{safe_name}.json")
            try:
                with open(path, "w") as f:
                    json.dump({"recipe_name": recipe_name,
                               "components": tab.components}, f, indent=2)
                _tmp_files.append(path)
            except Exception as e:
                messagebox.showerror("Share", f"Could not generate file:\n{e}",
                                     parent=parent_widget); return
        else:
            messagebox.showinfo("Share",
                "Nothing to share yet.\nAdd some components first.",
                parent=parent_widget); return

    fname = os.path.basename(path)

    # ── Build share dialog ────────────────────────────────────────────
    win = tk.Toplevel(parent_widget)
    win.title("Share")
    win.configure(bg=BG_WHITE)
    _set_icon(win)
    win.resizable(False, False)
    win.grab_set()
    win.update_idletasks()
    px = parent_widget.winfo_rootx() + parent_widget.winfo_width()//2
    py = parent_widget.winfo_rooty() + parent_widget.winfo_height()//2
    win.geometry(f"340x210+{px-170}+{py-105}")

    tk.Frame(win, bg=ACCENT, height=3).pack(fill="x")
    tk.Label(win, text="Share", bg=BG_WHITE, fg=TEXT,
             font=("Segoe UI", 12, "bold"), pady=10).pack()
    tk.Label(win, text=fname, bg=BG_WHITE, fg=TEXT_MUTED,
             font=("Segoe UI", 8)).pack()
    tk.Frame(win, bg=BORDER, height=1).pack(fill="x", pady=8)

    btn_frame = tk.Frame(win, bg=BG_WHITE); btn_frame.pack(pady=4)

    def _cleanup():
        for f in _tmp_files:
            try: os.remove(f)
            except Exception: pass

    def _open_folder():
        """Open File Explorer at the file location so user can drag it anywhere."""
        try:
            # Select the file in Explorer (Windows)
            subprocess.Popen(["explorer", "/select,", path.replace("/", "\\")])
        except Exception:
            try: os.startfile(os.path.dirname(path))
            except Exception: pass

    def _email():
        """Create an Outlook email with the file attached via PowerShell COM."""
        ps_script = f"""
Add-Type -AssemblyName Microsoft.Office.Interop.Outlook -ErrorAction SilentlyContinue
try {{
    $outlook = New-Object -ComObject Outlook.Application
    $mail = $outlook.CreateItem(0)
    $mail.Subject = "3D Printing Formulator — {recipe_name}"
    $mail.Body = "Please find the formulation file attached."
    $mail.Attachments.Add("{path}")
    $mail.Display()
}} catch {{
    # Fallback: open mailto and show folder
    Start-Process "mailto:?subject=3D+Printing+Formulator&body=See+attached+file"
    explorer /select,"{path}"
}}
"""
        try:
            subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden",
                 "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )
            messagebox.showinfo("Share via Email",
                f"Outlook is opening with {fname} attached.\n\n"
                f"If Outlook is not installed, File Explorer will open "
                f"at the file location so you can attach it manually.",
                parent=win)
        except Exception as e:
            # Ultimate fallback — open folder
            _open_folder()
            messagebox.showinfo("Share via Email",
                f"Could not open Outlook automatically.\n\n"
                f"File Explorer has opened at the file location.\n"
                f"Drag {fname} into your email client to attach it.",
                parent=win)
        win.destroy()

    def _teams():
        """Copy file path to clipboard and open File Explorer so file can be dragged into Teams."""
        try:
            win.clipboard_clear(); win.clipboard_append(path)
            _open_folder()
            messagebox.showinfo("Share via Teams",
                f"File Explorer has opened with {fname} selected.\n\n"
                f"Drag the file into your Teams chat or channel,\n"
                f"or use the Teams attachment button (📎) and browse to:\n{path}",
                parent=win)
        except Exception as e:
            messagebox.showerror(_T("Error"), str(e), parent=win)
        win.destroy()

    def _cancel():
        _cleanup(); win.destroy()

    _btn(btn_frame, "✉  Email",  _email,  "normal").pack(side="left", padx=6)
    _btn(btn_frame, "💬  Teams", _teams,  "neutral").pack(side="left", padx=6)
    tk.Button(win, text="Cancel", command=_cancel,
              bg=BG_WHITE, fg=TEXT_MUTED, relief="flat", bd=0,
              font=("Segoe UI", 8), cursor="hand2").pack(pady=(4,0))
    win.protocol("WM_DELETE_WINDOW", _cancel)


def _safe_filename(name):
    """Convert recipe name to a safe filename — strip OS-invalid characters."""
    import re
    safe = re.sub(r'[\\/:*?"<>|]', '', name).strip()
    return safe or "formulation"

def _btn(parent,text,cmd,style="normal",width=None,font=("Segoe UI",9)):
    colors_map={
        "normal": (BTN_BLUE,   ACCENT_HOV,  BTN_FG),
        "danger": (BTN_RED,    "#B91C1C",   BTN_FG),
        "success":(BTN_GREEN,  "#15803D",   BTN_FG),
        "neutral":(BG_WHITE,   BG_ALT,      TEXT_DIM),
    }
    bg,hover,fg=colors_map.get(style,(BTN_BLUE,ACCENT_HOV,BTN_FG))
    bkw=({"highlightthickness":1,"highlightbackground":BORDER_MED}
         if style=="neutral" else {"highlightthickness":0})
    kw={"width":width} if width else {}
    b=tk.Button(parent,text=text,command=cmd,bg=bg,fg=fg,
        activebackground=hover,activeforeground=fg,
        relief="flat",bd=0,cursor="hand2",
        font=font,padx=_BTN_PADX,pady=_BTN_PADY,**kw,**bkw)
    b.bind("<Enter>",lambda e,w=b,h=hover:w.config(bg=h))
    b.bind("<Leave>",lambda e,w=b,o=bg:w.config(bg=o))
    return b

def _lbl(parent,text,fg=TEXT_DIM,font=("Segoe UI",9),**kw):
    return tk.Label(parent,text=text,bg=BG,fg=fg,font=font,**kw)

def _entry(parent,width,var=None,justify="left"):
    return tk.Entry(parent,width=width,bg=BG_WHITE,fg=TEXT,
        insertbackground=ACCENT,relief="flat",bd=1,
        highlightthickness=1,highlightbackground=BORDER_MED,
        highlightcolor=ACCENT,font=("Segoe UI",9),
        textvariable=var,justify=justify)

def _summary_block(parent,keys_captions_colors):
    labels={}
    for key,caption,color in keys_captions_colors:
        f=tk.Frame(parent,bg=BG_WHITE,highlightthickness=1,
                   highlightbackground=BORDER)
        f.pack(side="left",padx=_s(5),pady=3,ipadx=_s(10),ipady=_s(4))
        tk.Label(f,text=caption,bg=BG_WHITE,fg=TEXT_MUTED,
                 font=("Segoe UI",8)).pack()
        v=tk.Label(f,text="--",bg=BG_WHITE,fg=color,
                   font=("Segoe UI",12,"bold"))
        v.pack()
        labels[key]=v
    return labels

# ─────────────────────────────────────────────
#  FORWARD TAB
# ─────────────────────────────────────────────
def _fwd_cols():
    return [
        ("idx",     "#",                _s(42),  "center"),
        ("name",    "Component",        _s(175), "w"),
        ("density", "Density (g/cm³)",  _s(148), "center"),
        ("mode",    "Input Mode",       _s(175), "w"),
        ("value",   "Value",            _s(85),  "e"),
        ("ref",     "Reference",        _s(145), "w"),
        ("mass",    "Mass (g)",         _s(110), "e"),
        ("vol",     "Volume (cm³)",     _s(132), "e"),
        ("wt",      "wt.%",             _s(75),  "e"),
        ("volp",    "vol.%",            _s(75),  "e"),
    ]
FWD_COLS = _fwd_cols()

class ForwardTab(tk.Frame):
    def __init__(self,parent,app,**kw):
        super().__init__(parent,bg=BG,**kw)
        self.app=app; self.components=[]; self.last_result=None; self._build()

    def _build(self):
        # File buttons bar — top right
        fbar=tk.Frame(self,bg=BG_WHITE,pady=6,padx=12,
                      highlightthickness=1,highlightbackground=BORDER)
        fbar.pack(fill="x",padx=10,pady=(10,0))
        rhs2=tk.Frame(fbar,bg=BG_WHITE); rhs2.pack(side="right")
        b=_btn(rhs2,_T("📤 Share"),     lambda:_share_file(self,self),"neutral"); b.pack(side="right",padx=(2,0)); _tip(b,"Share this recipe via email or Teams. Generates a file automatically if needed.")
        b=_btn(rhs2,_T("📄 Export PDF"),self._export_pdf, "neutral"); b.pack(side="right",padx=(2,0)); _tip(b,"Export results as a PDF report.")
        b=_btn(rhs2,_T("📂 Load"),      self._load,       "neutral"); b.pack(side="right",padx=(2,0)); _tip(b,"Load a previously saved recipe.")
        b=_btn(rhs2,_T("💾 Save"),      self._save,       "neutral"); b.pack(side="right",padx=(2,0)); _tip(b,"Save recipe to a .json file.")

        tf=tk.Frame(self,bg=BG,bd=0, relief="flat", highlightthickness=1, highlightbackground=BORDER)
        tf.pack(fill="both",expand=True,padx=8,pady=(6,4))
        self.tree=_make_tree(tf,_fwd_cols())
        vsb=ttk.Scrollbar(tf,orient="vertical",command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right",fill="y"); self.tree.pack(side="left",fill="both",expand=True)
        self.tree.bind("<<TreeviewSelect>>",self._on_select)

        inp=tk.Frame(self,bg=BG_WHITE,pady=6,padx=12,
                     highlightthickness=1,highlightbackground=BORDER)
        inp.pack(fill="x",padx=10,pady=(4,0))
        r1=tk.Frame(inp,bg=BG_WHITE); r1.pack(fill="x",pady=(0,4))

        _lbl(r1,_T("Component:")).pack(side="left")
        self._ac_name = AutocompleteEntry(r1, width=16,
            db_ref=self.app.materials_db,
            on_select=lambda m: self.var_density.set(f"{m['density']:.3f}"),
            open_db_cb=self._open_db)
        self._ac_name.pack(side="left", padx=(2,12))
        _tip(self._ac_name,"Type the component name, or click ▼ to pick from the\nmaterials database. Density fills in automatically.")

        _lbl(r1,_T("Density (g/cm³):")).pack(side="left")
        self.var_density=tk.StringVar(value="1.000")
        fwd_den=_entry(r1,8,self.var_density,"right"); fwd_den.pack(side="left",padx=(2,12))
        _tip(fwd_den,"Density in g/cm3. Used to convert mass to volume and vice versa.")

        _lbl(r1,_T("Input Mode:")).pack(side="left")
        self.var_mode=tk.StringVar(value="Mass (g)")
        cb=ttk.Combobox(r1,textvariable=self.var_mode,values=FWD_MODES,
                        state="readonly",width=_s(22),font=("Segoe UI",9))
        cb.pack(side="left",padx=(2,12))
        _tip(cb,"How you specify this component:\nMass (g) = absolute grams\nVolume (cm3) = absolute cm3\nwt.% to Reference = % of another component mass\nvol.% to Reference = % of another component volume\nwt.% of Total = % of total batch mass\nvol.% of Total = % of total batch volume")
        self.var_mode.trace_add("write",lambda *_:self._update_ref_vis())

        _lbl(r1,_T("Value:")).pack(side="left")
        self.var_value=tk.StringVar(value="0")
        fwd_val=_entry(r1,10,self.var_value,"right"); fwd_val.pack(side="left",padx=(2,12))
        _tip(fwd_val,"The number for the selected Input Mode (grams, cm3, or %).")

        self._ref_lbl=_lbl(r1,_T("Reference:"))
        self.var_ref=tk.StringVar()
        self._ref_entry=RefEntry(r1,14,components_ref=lambda: self.components)
        self._ref_entry.var=self.var_ref  # share the same StringVar
        self._ref_entry._entry.config(textvariable=self.var_ref)
        self._update_ref_vis()

        r2=tk.Frame(inp,bg=BG_WHITE); r2.pack(fill="x",pady=(4,0))
        # ── Group 1: Edit ──
        b=_btn(r2,_T("➕ Add"),    self._add,       "neutral"); b.pack(side="left",padx=(0,2)); _tip(b,"Add this component to the list.")
        b=_btn(r2,_T("✏ Update"),  self._update,    "neutral");  b.pack(side="left",padx=(0,2)); _tip(b,"Select a row, edit the fields, then click Update.")
        b=_btn(r2,_T("🗑 Remove"),  self._remove,    "neutral");  b.pack(side="left",padx=(0,2)); _tip(b,"Remove the selected component.")
        b=_btn(r2,_T("▲ Up"),      self._move_up,   "neutral"); b.pack(side="left",padx=(0,2)); _tip(b,"Move selected row up.")
        b=_btn(r2,_T("▼ Down"),    self._move_down, "neutral"); b.pack(side="left",padx=(0,2)); _tip(b,"Move selected row down.")
        b=_btn(r2,_T("✖ Clear All"),self._clear_all,"neutral");  b.pack(side="left",padx=(0,0)); _tip(b,"Remove all components and reset the table.")
        b=_btn(r2,_T("⚙ CALCULATE"),self._calculate,"success",font=("Segoe UI",10,"bold")); b.pack(side="right",padx=(0,0),ipady=2); _tip(b,"Calculate mass, volume and percentages.")

        sum_bar=tk.Frame(self,bg=BG,pady=4,padx=10); sum_bar.pack(fill="x")
        self.sum_labels=_summary_block(sum_bar,[
            ("total_mass","Total Mass",   ACCENT),
            ("total_vol", "Total Volume", ACCENT),
            ("density",   "Density mix",  BTN_RED),
        ])

    def _update_ref_vis(self):
        if "to Reference" in self.var_mode.get():
            self._ref_lbl.pack(side="left"); self._ref_entry.pack(side="left",padx=(2,12))
        else:
            self._ref_lbl.pack_forget(); self._ref_entry.pack_forget(); self.var_ref.set("")

    def _refresh(self,result=None):
        self.tree.delete(*self.tree.get_children())
        res_map={r["name"]:r for r in result["rows"]} if result else {}
        for i,c in enumerate(self.components):
            tag="even" if i%2==0 else "odd"; r=res_map.get(c["name"])
            self.tree.insert("","end",iid=str(i),tags=(tag,),values=(
                f"{i+1:02d}",c["name"],f"{c['density']:.3f}",
                c["input_mode"],c["value"],c.get("ref_name",""),
                f"{r['mass']:.2f} g"     if r else "--",
                f"{r['volume']:.2f} cm³" if r else "--",
                f"{r['wt_pct']:.2f}%"    if r else "--",
                f"{r['vol_pct']:.2f}%"   if r else "--",
            ))
        if result:
            self.tree.insert("","end",iid="total",tags=("total",),values=(
                "Σ","TOTAL","—","—","—","—",
                f"{result['total_mass']:.2f} g",
                f"{result['total_volume']:.2f} cm³",
                "100.00%","100.00%",
            ))

    def _on_select(self,_=None):
        sel=self.tree.selection()
        if not sel or sel[0]=="total": return
        c=self.components[int(sel[0])]
        self._ac_name.set(c["name"]); self.var_density.set(str(c["density"]))
        self.var_mode.set(c["input_mode"]); self.var_value.set(str(c["value"]))
        self.var_ref.set(c.get("ref_name","")); self._update_ref_vis()

    def _read_form(self):
        name=self._ac_name.get().strip()
        if not name: raise ValueError("Component name cannot be empty.")
        return {"name":name,"density":float(self.var_density.get()),
                "input_mode":self.var_mode.get(),"value":float(self.var_value.get() or 0),
                "ref_name":self.var_ref.get().strip()}

    def _add(self):
        try: c=self._read_form()
        except ValueError as e: messagebox.showerror("Input Error",str(e)); return
        if c["name"] in [x["name"] for x in self.components]:
            messagebox.showwarning(_T("Duplicate"),f"'{c['name']}' already exists."); return
        self.components.append(c); self._refresh(); self.last_result=None; self._reset_summary()
        self.app.set_status(f"Added '{c['name']}'.")

    def _update(self):
        sel=self.tree.selection()
        if not sel or sel[0]=="total": messagebox.showinfo(_T("Input"),_T("Click a row first.")); return
        idx=int(sel[0])
        try: c=self._read_form()
        except ValueError as e: messagebox.showerror("Input Error",str(e)); return
        old=self.components[idx]["name"]
        if c["name"]!=old and c["name"] in [x["name"] for x in self.components]:
            messagebox.showwarning(_T("Duplicate"),f"'{c['name']}' exists."); return
        self.components[idx]=c; self._refresh(); self.last_result=None; self._reset_summary()
        self.app.set_status(f"Updated '{c['name']}'.")

    def _remove(self):
        sel=self.tree.selection()
        if not sel or sel[0]=="total": messagebox.showinfo(_T("Input"),_T("Click a row first.")); return
        idx=int(sel[0]); name=self.components[idx]["name"]
        do_remove = (
            not getattr(self.app,"settings",{}).get("confirm_destructive",True)
            or messagebox.askyesno(_T("🗑 Remove"),f"Remove '{name}'?")
        )
        if do_remove:
            self.components.pop(idx); self._refresh(); self.last_result=None; self._reset_summary()
            self.app.set_status(f"Removed '{name}'.")

    def _move_up(self):
        sel=self.tree.selection()
        if not sel or sel[0]=="total": return
        idx=int(sel[0])
        if idx==0: return
        self.components[idx],self.components[idx-1]=self.components[idx-1],self.components[idx]
        self._refresh(); self.tree.selection_set(str(idx-1))

    def _move_down(self):
        sel=self.tree.selection()
        if not sel or sel[0]=="total": return
        idx=int(sel[0])
        if idx>=len(self.components)-1: return
        self.components[idx],self.components[idx+1]=self.components[idx+1],self.components[idx]
        self._refresh(); self.tree.selection_set(str(idx+1))

    def _clear_all(self):
        if not self.components: return
        do_clear = (
            not getattr(self.app,"settings",{}).get("confirm_destructive",True)
            or messagebox.askyesno(_T("✖ Clear All"),_T("Remove all components?"))
        )
        if do_clear:
            self.components.clear(); self.last_result=None; self._refresh(); self._reset_summary()
            self.app.set_status(_T("Cleared."))

    def _calculate(self):
        if not self.components: self.app.set_status(_T("No components.")); return
        names=[c["name"] for c in self.components]
        if len(names)!=len(set(names)): messagebox.showwarning(_T("Duplicates"),_T("Names must be unique.")); return
        objs=[Component(**c) for c in self.components]
        try:
            result=calculate_formulation(objs)
            self.last_result=result; self._refresh(result)
            self.sum_labels["total_mass"].config(text=f"{result['total_mass']:.2f} g")
            self.sum_labels["total_vol"].config( text=f"{result['total_volume']:.2f} cm³")
            self.sum_labels["density"].config(   text=f"{result['theoretical_density']:.2f} g/cm³")
            self.app.set_status(
                f"Done.  {len(objs)} components  ·  "
                f"Total mass: {result['total_mass']:.2f} g  ·  "
                f"Total volume: {result['total_volume']:.2f} cm³  ·  "
                f"Density: {result['theoretical_density']:.2f} g/cm³")
        except ValueError as e: messagebox.showerror(_T("Error"),str(e)); self.app.set_status(f"Error: {e}")

    def _reset_summary(self):
        for l in self.sum_labels.values(): l.config(text="--")

    def _export_pdf(self):
        if not self.last_result: messagebox.showinfo(_T("No Results"),_T("Calculate first.")); return
        path=filedialog.asksaveasfilename(defaultextension=".pdf",filetypes=[("PDF","*.pdf")],
            initialfile=_safe_filename(self.app.var_recipe_name.get())+".pdf")
        if not path: return
        try:
            self._last_pdf = path
            export_pdf(self.last_result,self.app.var_recipe_name.get(),path)
            self.app.set_status(f"PDF saved: {os.path.basename(path)}")
            messagebox.showinfo(_T("Saved"),f"PDF saved:\n{path}")
        except Exception as e: messagebox.showerror(_T("PDF Error"),str(e))

    def _save(self):
        path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("Recipe","*.json")],
            initialfile=_safe_filename(self.app.var_recipe_name.get())+".json")
        if not path: return
        # Sync recipe name to the chosen filename
        file_stem = os.path.splitext(os.path.basename(path))[0]
        self.app.var_recipe_name.set(file_stem)
        with open(path,"w") as f:
            self._last_json = path
            json.dump({"recipe_name":file_stem,
                       "mode":"forward","components":self.components},f,indent=2)
        self.app.set_status(f"Saved: {os.path.basename(path)}")

    def _load(self):
        path=filedialog.askopenfilename(filetypes=[("Recipe","*.json"),("All","*.*")])
        if not path: return
        try:
            with open(path) as f: data=json.load(f)
            # Filename is authoritative; fall back to stored name only if stem is empty
            file_stem = os.path.splitext(os.path.basename(path))[0]
            self.app.var_recipe_name.set(file_stem or data.get("recipe_name",""))
            self.components=data.get("components",[]); self.last_result=None
            self._refresh(); self._reset_summary()
            self.app.set_status(f"Loaded: {os.path.basename(path)}")
        except Exception as e: messagebox.showerror(_T("Load Error"),str(e))

    def _open_db(self):
        MaterialsDialog(self.app, self.app.materials_db)

# ─────────────────────────────────────────────
#  INVERSE TAB
# ─────────────────────────────────────────────
def _inv_cols():
    return [
        ("idx",     "#",                _s(42),  "center"),
        ("name",    "Component",        _s(175), "w"),
        ("density", "Density (g/cm³)",  _s(148), "center"),
        ("mode",    "Relationship",     _s(195), "w"),
        ("value",   "Value",            _s(85),  "e"),
        ("ref",     "Reference",        _s(145), "w"),
        ("mass",    "Mass (g)",         _s(110), "e"),
        ("vol",     "Volume (cm³)",     _s(132), "e"),
        ("wt",      "wt.%",             _s(75),  "e"),
        ("volp",    "vol.%",            _s(75),  "e"),
    ]
INV_COLS = _inv_cols()

class InverseTab(tk.Frame):
    def __init__(self,parent,app,**kw):
        super().__init__(parent,bg=BG,**kw)
        self.app=app; self.components=[]; self.last_result=None; self._build()

    def _build(self):
        cfg=tk.Frame(self,bg=BG_WHITE,pady=6,padx=12,
                     highlightthickness=1,highlightbackground=BORDER)
        cfg.pack(fill="x",padx=10,pady=(10,0))

        _lbl(cfg,_T("Target:"),fg=ACCENT,font=("Segoe UI",9,"bold")).pack(side="left")
        self.var_target=tk.StringVar(value="45")
        tgt_e=_entry(cfg,7,self.var_target,"right"); tgt_e.pack(side="left",padx=(4,4))
        _tip(tgt_e,"The desired loading of your Primary component (0-100).")
        self.var_tmode=tk.StringVar(value="vol.%")
        tgt_cb=ttk.Combobox(cfg,textvariable=self.var_tmode,values=["vol.%","wt.%"],
            state="readonly",width=8,font=("Segoe UI",9))
        tgt_cb.pack(side="left",padx=(0,16))
        _tip(tgt_cb,"vol.% = Primary volume / total volume\nwt.% = Primary mass / total mass")
        self.lbl_k=_lbl(cfg,"",fg=ACCENT,font=("Segoe UI",9,"italic"))
        _tip(self.lbl_k,"Scale factor k (=1.0 when a Balance component is used).")
        self.lbl_k.pack(side="left")
        # File buttons — far right of config bar
        rhs=tk.Frame(cfg,bg=BG_WHITE); rhs.pack(side="right")
        b=_btn(rhs,_T("📤 Share"),     lambda:_share_file(self,self),"neutral"); b.pack(side="right",padx=(2,0)); _tip(b,"Share this recipe via email or Teams. Generates a file automatically if needed.")
        b=_btn(rhs,_T("📄 Export PDF"),self._export_pdf, "neutral"); b.pack(side="right",padx=(2,0)); _tip(b,"Export results as a PDF report.")
        b=_btn(rhs,_T("📂 Load"),      self._load,       "neutral"); b.pack(side="right",padx=(2,0)); _tip(b,"Load a previously saved recipe.")
        b=_btn(rhs,_T("💾 Save"),      self._save,       "neutral"); b.pack(side="right",padx=(2,0)); _tip(b,"Save recipe to a .json file.")

        tf=tk.Frame(self,bg=BG_WHITE,bd=0,relief="flat",
                    highlightthickness=1,highlightbackground=BORDER)
        tf.pack(fill="both",expand=True,padx=10,pady=(6,0))
        self.tree=_make_tree(tf,_inv_cols())
        vsb=ttk.Scrollbar(tf,orient="vertical",command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right",fill="y"); self.tree.pack(side="left",fill="both",expand=True)
        self.tree.bind("<<TreeviewSelect>>",self._on_select)

        inp=tk.Frame(self,bg=BG_WHITE,pady=6,padx=12,
                     highlightthickness=1,highlightbackground=BORDER)
        inp.pack(fill="x",padx=10,pady=(4,0))
        r1=tk.Frame(inp,bg=BG_WHITE); r1.pack(fill="x",pady=(0,4))

        _lbl(r1,_T("Component:")).pack(side="left")
        self._ac_name = AutocompleteEntry(r1, width=16,
            db_ref=self.app.materials_db,
            on_select=lambda m: self.var_density.set(f"{m['density']:.3f}"),
            open_db_cb=self._open_db)
        self._ac_name.pack(side="left", padx=(2,12))
        _tip(self._ac_name,"Type the component name, or click ▼ to pick from the\nmaterials database. Density fills in automatically.")

        _lbl(r1,_T("Density (g/cm³):")).pack(side="left")
        self.var_density=tk.StringVar(value="1.000")
        inv_den=_entry(r1,8,self.var_density,"right"); inv_den.pack(side="left",padx=(2,12))
        _tip(inv_den,"Density in g/cm3. Used to convert mass to volume.")

        _lbl(r1,_T("Relationship:")).pack(side="left")
        self.var_mode=tk.StringVar(value="wt.% to Reference")
        cb=ttk.Combobox(r1,textvariable=self.var_mode,values=INV_MODES,
                        state="readonly",width=_s(24),font=("Segoe UI",9))
        cb.pack(side="left",padx=(2,12))
        _tip(cb,"How this component relates to others:\nPrimary = the component whose loading you are targeting (exactly 1 required)\nBalance = quantity calculated by solver to hit the target (max 1 allowed)\nwt.% to Reference = % of another component mass\nvol.% to Reference = % of another component volume\nwt.% of Total Suspension = % of entire batch mass\nvol.% of Total Suspension = % of entire batch volume\nIndependent Mass (g) = fixed absolute mass, does not scale\nIndependent Vol (cm3) = fixed absolute volume, does not scale")
        self.var_mode.trace_add("write",lambda *_:self._update_ref_vis())

        _lbl(r1,_T("Value:")).pack(side="left")
        self.var_value=tk.StringVar(value="0")
        self.e_val=_entry(r1,10,self.var_value,"right")
        self.e_val.pack(side="left",padx=(2,12))
        _tip(self.e_val,"Primary: absolute amount (g or cm3).\nBalance: leave as 0, solver calculates it.\nPercentage modes: enter the % value (e.g. 3 for 3%).")

        # Primary mode fields — only visible when Relationship = Primary
        self._anc_lbl=_lbl(r1,_T("Primary mode:"))
        self.var_amode=tk.StringVar(value="Mass (g)")
        self._anc_cb=ttk.Combobox(r1,textvariable=self.var_amode,
            values=["Mass (g)","Volume (cm3)"],state="readonly",width=13,font=("Segoe UI",9))

        self._ref_lbl2=_lbl(r1,_T("Reference:"))
        self.var_ref=tk.StringVar()
        self._ref_entry2=RefEntry(r1,14,components_ref=lambda: self.components)
        self._ref_entry2.var=self.var_ref
        self._ref_entry2._entry.config(textvariable=self.var_ref)
        self._update_ref_vis()

        r2=tk.Frame(inp,bg=BG_WHITE); r2.pack(fill="x",pady=(4,0))
        # ── Group 1: Edit ──
        b=_btn(r2,_T("➕ Add"),    self._add,       "neutral"); b.pack(side="left",padx=(0,2)); _tip(b,"Add this component to the list.")
        b=_btn(r2,_T("✏ Update"),  self._update,    "neutral");  b.pack(side="left",padx=(0,2)); _tip(b,"Select a row, edit the fields, then click Update.")
        b=_btn(r2,_T("🗑 Remove"),  self._remove,    "neutral");  b.pack(side="left",padx=(0,2)); _tip(b,"Remove the selected component.")
        b=_btn(r2,_T("▲ Up"),      self._move_up,   "neutral"); b.pack(side="left",padx=(0,2)); _tip(b,"Move selected row up.")
        b=_btn(r2,_T("▼ Down"),    self._move_down, "neutral"); b.pack(side="left",padx=(0,2)); _tip(b,"Move selected row down.")
        b=_btn(r2,_T("✖ Clear All"),self._clear_all,"neutral");  b.pack(side="left",padx=(0,0)); _tip(b,"Remove all components and reset the table.")
        b=_btn(r2,_T("⚙ SOLVE"),self._solve,"success",font=("Segoe UI",10,"bold")); b.pack(side="right",padx=(0,0),ipady=2); _tip(b,"Run the solver.")

        sum_bar2=tk.Frame(self,bg=BG,padx=10,pady=4)
        sum_bar2.pack(fill="x")
        self.sum_labels=_summary_block(sum_bar2,[
            ("total_mass","Total Mass",   ACCENT),
            ("total_vol", "Total Volume", ACCENT),
            ("density",   "Density mix",  BTN_RED),
            ("sl_wt",     "Primary wt.%",  BTN_GREEN),
            ("sl_vol",    "Primary vol.%", BTN_GREEN),
        ])

    def _update_ref_vis(self):
        mode=self.var_mode.get()
        is_anchor= mode=="Primary"
        no_val=mode=="Balance"
        no_ref="to Reference" not in mode
        self.e_val.config(state="disabled" if no_val else "normal",
                          bg="#E0E0E0" if no_val else BG_WHITE)
        # Primary mode fields
        if is_anchor:
            self._anc_lbl.pack(side="left",padx=(0,2))
            self._anc_cb.pack(side="left",padx=(0,8))
        else:
            self._anc_lbl.pack_forget(); self._anc_cb.pack_forget()
        # Reference field
        if not no_ref:
            self._ref_lbl2.pack(side="left"); self._ref_entry2.pack(side="left",padx=(2,12))
        else:
            self._ref_lbl2.pack_forget(); self._ref_entry2.pack_forget(); self.var_ref.set("")

    def _refresh(self,result=None):
        self.tree.delete(*self.tree.get_children())
        fmt_mv = "{:.2f}"
        res_map={r["name"]:r for r in result["rows"]} if result else {}
        for i,c in enumerate(self.components):
            tag="even" if i%2==0 else "odd"; r=res_map.get(c["name"])
            self.tree.insert("","end",iid=str(i),tags=(tag,),values=(
                f"{i+1:02d}",c["name"],f"{c['density']:.3f}",c["rel_mode"],c["value"],c.get("ref_name",""),
                (fmt_mv.format(r['mass'])   + " g")   if r else "--",
                (fmt_mv.format(r['volume']) + " cm³") if r else "--",
                f"{r['wt_pct']:.2f}%"    if r else "--",
                f"{r['vol_pct']:.2f}%"   if r else "--",
            ))
        if result:
            self.tree.insert("","end",iid="total",tags=("total",),values=(
                "Σ","TOTAL","—","—","—","—",
                fmt_mv.format(result['total_mass'])   + " g",
                fmt_mv.format(result['total_volume']) + " cm³",
                "100.00%","100.00%",
            ))

    def _on_select(self,_=None):
        sel=self.tree.selection()
        if not sel or sel[0]=="total": return
        c=self.components[int(sel[0])]
        self._ac_name.set(c["name"]); self.var_density.set(str(c["density"]))
        self.var_mode.set(c["rel_mode"]); self.var_value.set(str(c["value"]))
        self.var_ref.set(c.get("ref_name",""))
        if c["rel_mode"]=="Primary":
            self.var_amode.set(c.get("anchor_mode","Mass (g)"))
        self._update_ref_vis()

    def _read_form(self):
        name=self._ac_name.get().strip()
        if not name: raise ValueError("Component name cannot be empty.")
        d={"name":name,"density":float(self.var_density.get()),
           "rel_mode":self.var_mode.get(),"value":float(self.var_value.get() or 0),
           "ref_name":self.var_ref.get().strip()}
        if self.var_mode.get()=="Primary":
            d["anchor_mode"]=self.var_amode.get()
        return d

    def _add(self):
        try: c=self._read_form()
        except ValueError as e: messagebox.showerror("Input Error",str(e)); return
        if c["name"] in [x["name"] for x in self.components]:
            messagebox.showwarning(_T("Duplicate"),f"'{c['name']}' already exists."); return
        self.components.append(c); self._refresh(); self.app.set_status(f"Added '{c['name']}'.")

    def _update(self):
        sel=self.tree.selection()
        if not sel or sel[0]=="total": messagebox.showinfo(_T("Input"),_T("Click a row first.")); return
        idx=int(sel[0])
        try: c=self._read_form()
        except ValueError as e: messagebox.showerror("Input Error",str(e)); return
        old=self.components[idx]["name"]
        if c["name"]!=old and c["name"] in [x["name"] for x in self.components]:
            messagebox.showwarning(_T("Duplicate"),f"'{c['name']}' exists."); return
        self.components[idx]=c; self._refresh(); self.app.set_status(f"Updated '{c['name']}'.")

    def _remove(self):
        sel=self.tree.selection()
        if not sel or sel[0]=="total": messagebox.showinfo(_T("Input"),_T("Click a row first.")); return
        idx=int(sel[0]); name=self.components[idx]["name"]
        do_remove = (
            not getattr(self.app,"settings",{}).get("confirm_destructive",True)
            or messagebox.askyesno(_T("🗑 Remove"),f"Remove '{name}'?")
        )
        if do_remove:
            self.components.pop(idx); self._refresh(); self.app.set_status(f"Removed '{name}'.")

    def _move_up(self):
        sel=self.tree.selection()
        if not sel or sel[0]=="total": return
        idx=int(sel[0])
        if idx==0: return
        self.components[idx],self.components[idx-1]=self.components[idx-1],self.components[idx]
        self._refresh(); self.tree.selection_set(str(idx-1))

    def _move_down(self):
        sel=self.tree.selection()
        if not sel or sel[0]=="total": return
        idx=int(sel[0])
        if idx>=len(self.components)-1: return
        self.components[idx],self.components[idx+1]=self.components[idx+1],self.components[idx]
        self._refresh(); self.tree.selection_set(str(idx+1))

    def _clear_all(self):
        if not self.components: return
        do_clear = (
            not getattr(self.app,"settings",{}).get("confirm_destructive",True)
            or messagebox.askyesno(_T("✖ Clear All"),_T("Remove all?"))
        )
        if do_clear:
            self.components.clear(); self.last_result=None; self._refresh()
            for l in self.sum_labels.values(): l.config(text="--")
            self.lbl_k.config(text=""); self.app.set_status(_T("Cleared."))

    def _solve(self):
        if not self.components: self.app.set_status(_T("No components.")); return
        names=[c["name"] for c in self.components]
        if len(names)!=len(set(names)): messagebox.showwarning(_T("Duplicates"),_T("Names must be unique.")); return
        anchors=[c for c in self.components if c["rel_mode"]=="Primary"]
        if len(anchors)!=1:
            messagebox.showwarning(_T("Input"),f"Exactly 1 Primary component required. Found {len(anchors)}."); return
        anc=anchors[0]
        try: tv=float(self.var_target.get()); av=float(anc["value"])
        except ValueError: messagebox.showerror("Input",_T("Values must be numbers.")); return
        aname=anc["name"]
        amode=anc.get("anchor_mode","Mass (g)")
        objs=[InvComponent(**{k:v for k,v in c.items() if k in
              ("name","density","rel_mode","value","ref_name")}) for c in self.components]
        try:
            result=solve_inverse(objs,self.var_tmode.get(),tv,aname,amode,av)
            self.last_result=result; self._refresh(result)
            self.sum_labels["total_mass"].config(text=f"{result['total_mass']:.2f} g")
            self.sum_labels["total_vol"].config( text=f"{result['total_volume']:.2f} cm³")
            self.sum_labels["density"].config(   text=f"{result['theoretical_density']:.2f} g/cm³")
            self.sum_labels["sl_wt"].config(     text=f"{result['solids_loading_wt']:.2f}%")
            self.sum_labels["sl_vol"].config(    text=f"{result['solids_loading_vol']:.2f}%")
            k=result.get("scale_factor",1.0); self.lbl_k.config(text=f"  k = {k:.4f}")
            self.app.set_status(
                f"Solved.  Target: {tv} {self.var_tmode.get()}  ·  "
                f"Primary: {result['solids_loading_wt']:.2f} wt.% / {result['solids_loading_vol']:.2f} vol.%  ·  "
                f"Total: {result['total_mass']:.2f} g / {result['total_volume']:.2f} cm³")
        except ValueError as e: messagebox.showerror(_T("Solver Error"),str(e)); self.app.set_status(f"Error: {e}")

    def _export_pdf(self):
        if not self.last_result: messagebox.showinfo(_T("No Results"),_T("Solve first.")); return
        path=filedialog.asksaveasfilename(defaultextension=".pdf",filetypes=[("PDF","*.pdf")],
            initialfile=_safe_filename(self.app.var_recipe_name.get())+".pdf")
        if not path: return
        try:
            note=(f"Inverse Solver  —  Target: {self.var_target.get()} {self.var_tmode.get()}  |  "
                  f"Primary: {self.last_result['solids_loading_wt']:.2f} wt.% / "
                  f"{self.last_result['solids_loading_vol']:.2f} vol.%")
            export_pdf(self.last_result,self.app.var_recipe_name.get(),path,extra_note=note)
            self.app.set_status(f"PDF saved: {os.path.basename(path)}")
            messagebox.showinfo(_T("Saved"),f"PDF saved:\n{path}")
        except Exception as e: messagebox.showerror(_T("PDF Error"),str(e))

    def _save(self):
        path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("Recipe","*.json")],
            initialfile=_safe_filename(self.app.var_recipe_name.get())+".json")
        if not path: return
        # Sync recipe name to the chosen filename
        file_stem = os.path.splitext(os.path.basename(path))[0]
        self.app.var_recipe_name.set(file_stem)
        with open(path,"w") as f:
            json.dump({"recipe_name":file_stem,"mode":"inverse",
                "target_mode":self.var_tmode.get(),"target_value":self.var_target.get(),
                "components":self.components},f,indent=2)
        self.app.set_status(f"Saved: {os.path.basename(path)}")

    def _load(self):
        path=filedialog.askopenfilename(filetypes=[("Recipe","*.json"),("All","*.*")])
        if not path: return
        try:
            with open(path) as f: data=json.load(f)
            # Filename is authoritative; fall back to stored name only if stem is empty
            file_stem = os.path.splitext(os.path.basename(path))[0]
            self.app.var_recipe_name.set(file_stem or data.get("recipe_name",""))
            self.var_tmode.set(data.get("target_mode","vol.%"))
            self.var_target.set(data.get("target_value","45"))
            self.components=data.get("components",[])
            self.last_result=None; self._refresh()
            for l in self.sum_labels.values(): l.config(text="--")
            self.lbl_k.config(text="")
            self.app.set_status(f"Loaded: {os.path.basename(path)}")
        except Exception as e: messagebox.showerror(_T("Load Error"),str(e))

    def _open_db(self):
        MaterialsDialog(self.app, self.app.materials_db)

# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
class FormulatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("The 3D Printing Formulator")
        self.configure(bg=BG)
        self.geometry(f"{_s(1400)}x{_s(645)}"); self.minsize(_s(1100), _s(490))
        self.var_recipe_name=tk.StringVar(value="My Formulation")
        self.var_status=tk.StringVar(value="Ready.  Add components and press Calculate / Solve.")
        self.materials_db = load_materials_db()
        self.settings = load_settings()
        _apply_font_scale(self, self.settings["font_scale"])
        _apply_colorblind(self.settings["colorblind_mode"])
        _apply_high_contrast(self, self.settings["high_contrast"])
        _apply_large_targets(self.settings.get("large_targets", False))
        _T_set_lang(self.settings.get("language", "en"))
        _apply_cjk_font(self.settings.get("language", "en"))
        _style_ttk(self); self._build_ui(); _set_icon(self)

    def _build_ui(self):
        # ── Root split: sidebar | main content ───────────────────────
        root_frame = tk.Frame(self, bg=BG)
        root_frame.pack(fill="both", expand=True)

        # ══ LEFT SIDEBAR ═════════════════════════════════════════════
        sidebar = tk.Frame(root_frame, bg=SIDEBAR, width=_s(220))
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo = tk.Frame(sidebar, bg=SIDEBAR)
        logo.pack(fill="x")
        tk.Frame(logo, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(logo, text=_T("The 3D Printing"), bg=SIDEBAR, fg="#FFFFFF",
                 font=("Segoe UI", 13, "bold"), anchor="w",
                 padx=20, pady=0).pack(fill="x", pady=(16,0))
        tk.Label(logo, text=_T("Formulator"), bg=SIDEBAR, fg="#FFFFFF",
                 font=("Segoe UI", 13, "bold"), anchor="w",
                 padx=20, pady=0).pack(fill="x", pady=(0,14))

        tk.Frame(sidebar, bg=SIDEBAR_HOV, height=1).pack(fill="x")

        nav_items = []
        def _make_nav(label, icon, idx):
            bg0=SIDEBAR; bgS=SIDEBAR_SEL; bgH=SIDEBAR_HOV
            f = tk.Frame(sidebar, bg=bg0, cursor="hand2")
            f.pack(fill="x", padx=8, pady=2)
            lb = tk.Label(f, text=f"  {icon}   {label}", bg=bg0,
                          fg=SIDEBAR_FG, font=("Segoe UI", 10),
                          anchor="w", padx=10, pady=10)
            lb.pack(fill="x")
            def _click(e=None):
                for t in self._tabs: t.lower()
                self._tabs[idx].lift()
                for i,(fi,li) in enumerate(nav_items):
                    c=bgS if i==idx else bg0
                    fi.config(bg=c); li.config(bg=c)
            def _ent(e):
                if f.cget("bg")!=bgS: f.config(bg=bgH); lb.config(bg=bgH)
            def _lea(e):
                if f.cget("bg")!=bgS: f.config(bg=bg0); lb.config(bg=bg0)
            for w in (f,lb):
                w.bind("<Button-1>",_click)
                w.bind("<Enter>",_ent)
                w.bind("<Leave>",_lea)
            nav_items.append((f,lb))

        _make_nav(_T("Inverse Solver"),    "⊕", 0)
        _make_nav(_T("Forward Formulator"),"→", 1)
        nav_items[0][0].config(bg=SIDEBAR_SEL)
        nav_items[0][1].config(bg=SIDEBAR_SEL)

        tk.Frame(sidebar, bg=SIDEBAR_HOV, height=1).pack(fill="x", side="bottom")
        for utxt, uicon, ucmd in [
            (_T("Help"),              "❓", lambda: HelpDialog(self)),
            (_T("Materials DB"),      "🗃", lambda: MaterialsDialog(self, self.materials_db)),
            (_T("Settings"),          "⚙",  lambda: SettingsDialog(self)),
            ("Register for Updates",  "📧", lambda: RegisterDialog(self)),
        ]:
            uf = tk.Frame(sidebar, bg=SIDEBAR, cursor="hand2")
            uf.pack(side="bottom", fill="x", padx=8, pady=1)
            font_ulb = ("Segoe UI", 9, "bold") if utxt == "Materials DB" else ("Segoe UI", 9)
            fg_ulb   = SIDEBAR_FG if utxt == "Materials DB" else SIDEBAR_FG2
            ulb = tk.Label(uf, text=f"  {uicon}   {utxt}", bg=SIDEBAR,
                           fg=fg_ulb, font=font_ulb,
                           anchor="w", padx=10, pady=8)
            ulb.pack(fill="x")
            def _uent(e,fr=uf,lb=ulb): fr.config(bg=SIDEBAR_HOV); lb.config(bg=SIDEBAR_HOV)
            def _ulea(e,fr=uf,lb=ulb): fr.config(bg=SIDEBAR); lb.config(bg=SIDEBAR)
            for w in (uf,ulb):
                w.bind("<Button-1>", lambda e,c=ucmd: c())
                w.bind("<Enter>", _uent)
                w.bind("<Leave>", _ulea)

        # ══ MAIN CONTENT AREA ════════════════════════════════════════
        main = tk.Frame(root_frame, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        topbar = tk.Frame(main, bg=BG_WHITE)
        topbar.pack(fill="x")
        tk.Frame(topbar, bg=BORDER, height=1).pack(fill="x", side="bottom")
        tb = tk.Frame(topbar, bg=BG_WHITE)
        tb.pack(fill="x", padx=16, pady=(6,6))
        tk.Label(tb, text=_T("Recipe / File Name:"), bg=BG_WHITE, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).pack(side="left")
        _entry(tb, 36, self.var_recipe_name).pack(side="left", padx=(6,0))

        # Frame-based tab switcher — no ttk.Notebook, no stray tab bar
        self._tab_container = tk.Frame(main, bg=BG)
        self._tab_container.pack(fill="both", expand=True)
        self.inv_tab = InverseTab(self._tab_container, app=self)
        self.fwd_tab = ForwardTab(self._tab_container, app=self)
        self._tabs = [self.inv_tab, self.fwd_tab]
        for t in self._tabs:
            t.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.inv_tab.lift()   # show first tab

        tk.Frame(main, bg=BORDER, height=1).pack(fill="x", side="bottom")
        sb = tk.Frame(main, bg=BG_WHITE)
        sb.pack(fill="x", side="bottom")
        tk.Label(sb, text="Copyright © 2026 Dr Thanos Goulas  ·  v1.0", bg=BG_WHITE, fg=TEXT_MUTED,
                 font=("Segoe UI", 8, "italic"), anchor="e", padx=14, pady=5
                 ).pack(side="right")
        tk.Label(sb, textvariable=self.var_status, bg=BG_WHITE, fg=TEXT_MUTED,
                 font=("Segoe UI", 9), anchor="w", padx=14, pady=5).pack(side="left", fill="x", expand=True)

    def set_status(self,msg): self.var_status.set(msg)

    def _snapshot_state(self):
        """Capture everything needed to survive a UI rebuild."""
        snap = {
            "recipe_name": self.var_recipe_name.get(),
            "active_tab":  0 if self.inv_tab.winfo_ismapped() else 1,
        }
        # Inverse tab
        it = self.inv_tab
        snap["inv"] = {
            "components":   list(it.components),
            "target_mode":  it.var_tmode.get(),
            "target_value": it.var_target.get(),
        }
        # Forward tab
        ft = self.fwd_tab
        snap["fwd"] = {
            "components": list(ft.components),
        }
        return snap

    def _restore_state(self, snap):
        """Push a snapshot back into the freshly-built tabs."""
        self.var_recipe_name.set(snap["recipe_name"])
        # Inverse
        it = self.inv_tab
        it.components = snap["inv"]["components"]
        it.var_tmode.set(snap["inv"]["target_mode"])
        it.var_target.set(snap["inv"]["target_value"])
        it.last_result = None
        it._refresh()
        it._reset_summary()
        # Forward
        ft = self.fwd_tab
        ft.components = snap["fwd"]["components"]
        ft.last_result = None
        ft._refresh()
        ft._reset_summary()
        # Restore active tab
        if snap["active_tab"] == 1:
            self.fwd_tab.lift()
        else:
            self.inv_tab.lift()

    def live_apply_settings(self):
        """Apply all settings live — no restart required."""
        snap = self._snapshot_state()
        s = self.settings
        # Apply global colour / scale changes first (these mutate module globals)
        _apply_colorblind(s["colorblind_mode"])
        _apply_high_contrast(self, s["high_contrast"])
        _apply_large_targets(s.get("large_targets", False))
        _apply_font_scale(self, s["font_scale"])
        _T_set_lang(s.get("language", "en"))
        _apply_cjk_font(s.get("language", "en"))
        _style_ttk(self)
        # Recompute scaled column widths with new _SF before rebuilding
        global FWD_COLS, INV_COLS
        FWD_COLS = _fwd_cols()
        INV_COLS = _inv_cols()
        # Destroy and rebuild all UI widgets so every font/colour takes effect
        for child in self.winfo_children():
            child.destroy()
        self._build_ui()
        _set_icon(self)
        # Restore recipe state
        self._restore_state(snap)
        self.set_status(_T("Settings applied."))

# ─────────────────────────────────────────────
#  TOOLTIP
# ─────────────────────────────────────────────
class Tooltip:
    """Show a small balloon when hovering over a widget."""
    def __init__(self, widget, text):
        self._widget = widget
        self._text   = text
        self._tip    = None
        widget.bind("<Enter>",  self._show, add="+")
        widget.bind("<Leave>",  self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _show(self, _=None):
        if self._tip: return
        try:
            x = self._widget.winfo_rootx() + 20
            y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        except Exception: return
        self._tip = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.attributes("-topmost", True)
        tw.configure(bg=BORDER_MED)
        lbl = tk.Label(tw, text=self._text, bg=BG_WHITE, fg=TEXT_DIM,
            font=("Segoe UI", 9), relief="flat", bd=0,
            wraplength=300, justify="left", padx=10, pady=6)
        lbl.pack()
        tw.geometry(f"+{x}+{y}")

    def _hide(self, _=None):
        if self._tip:
            try: self._tip.destroy()
            except Exception: pass
            self._tip = None

def _tip(widget, text):
    """Convenience: attach a tooltip to any widget."""
    Tooltip(widget, text)


# ─────────────────────────────────────────────
#  HELP DIALOG  (injected at end, called from header)
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
#  HELP TEXT TRANSLATIONS
#  Each key is a language code; value is a dict
#  mapping English section title → translated text.
#  Falls back to English (HELP_SECTIONS) if a
#  section or language is missing.
# ─────────────────────────────────────────────
HELP_TRANSLATIONS = {
    "el": {'About': '\nTHE 3D PRINTING FORMULATOR  —  v1.0\nΑπό τον Dr Thanos Goulas\n📧  thanosgoulas@outlook.com\n\n─────────────────────────────────────────────────────\n\nΤΙ ΚΑΝΕΙ Η ΕΦΑΡΜΟΓΗ;\n\nΥπολογίζει τις ακριβείς ποσότητες κάθε υλικού σε μια κεραμική\nρητίνη ή πάστα — σε γραμμάρια και cm³ — ώστε να ζυγίσετε\nμε ακρίβεια τον κάθε κύκλο στον πάγκο εργασίας.\n\nΜπορείτε να εργαστείτε με δύο τρόπους:\n\n  ΑΜΕΣΟΣ  →  Εσείς ορίζετε τις ποσότητες. Η εφαρμογή\n               υπολογίζει τη σύσταση (wt.%, vol.%, πυκνότητα\n               μίγματος).\n\n  ΑΝΤΙΣΤΡΟΦΟΣ  →  Εσείς ορίζετε τη σύσταση που θέλετε (π.χ.\n               45 vol.% αλούμινα). Η εφαρμογή υπολογίζει τις\n               ποσότητες για εσάς.\n\n─────────────────────────────────────────────────────\n\nΠΛΟΗΓΗΣΗ ΣΤΗΝ ΕΦΑΡΜΟΓΗ\n\nΗ αριστερή πλαϊνή μπάρα περιέχει:\n  • Αντίστροφος Επιλύτης  — εναλλαγή στην καρτέλα Αντίστροφος\n  • Άμεσος Υπολογισμός    — εναλλαγή στην καρτέλα Άμεσος\n  • Β.Δ. Υλικών            — άνοιγμα επεξεργαστή βάσης δεδομένων\n  • Βοήθεια               — άνοιγμα αυτού του οδηγού\n  • Ρυθμίσεις             — άνοιγμα παραθύρου ρυθμίσεων\n\nΗ μπάρα κορυφής κάθε καρτέλας περιέχει:\n  • Όνομα Συνταγής / Αρχείου — το τρέχον όνομα\n  • 💾 Αποθήκευση          — αποθήκευση σε αρχείο .json\n  • 📂 Φόρτωση             — φόρτωση αποθηκευμένης συνταγής\n  • 📄 Εξαγωγή PDF         — εξαγωγή αναφοράς PDF\n  • 📤 Κοινοποίηση         — αποστολή μέσω email ή Teams\n\n─────────────────────────────────────────────────────\n\nΒΑΣΗ ΔΕΔΟΜΕΝΩΝ ΥΛΙΚΩΝ\n\nΗ βάση δεδομένων περιέχει ~200 υλικά (κεραμικά, μονομερή,\nφωτοεκκινητές, διασκορπιστές, διαλύτες κ.ά.) — με πυκνότητα,\nδείκτη διάθλασης και μοριακό βάρος.\n\n─────────────────────────────────────────────────────\n\nΑΠΟΠΟΙΗΣΗ ΕΥΘΥΝΗΣ\n\nΟι τιμές πυκνότητας προέρχονται από Sigma-Aldrich, PubChem,\nNIST, CRC Handbook και φύλλα τεχνικών δεδομένων κατασκευαστών.\n\n⚠  Η πυκνότητα μπορεί να διαφέρει ανάλογα με βαθμό, καθαρότητα,\n   θερμοκρασία και προμηθευτή. Πάντα επαληθεύετε με το SDS του\n   υλικού σας πριν τη χρήση σε κρίσιμες εφαρμογές.\n\n─────────────────────────────────────────────────────\n\nΣΧΟΛΙΑ & ΑΝΑΦΟΡΕΣ ΣΦΑΛΜΑΤΩΝ\n\n📧  thanosgoulas@outlook.com\n', 'Quick Start Guide': '\nΝΕΟΣ ΧΡΗΣΤΗΣ; ΞΕΚΙΝΗΣΤΕ ΕΔΩ.\n\nΑυτός ο οδηγός σας καθοδηγεί μέσα από ένα πλήρες παράδειγμα\nχρησιμοποιώντας τον Αντίστροφο Επιλύτη.\n\n─────────────────────────────────────────────────────\n\nΠΑΡΑΔΕΙΓΜΑ ΣΥΝΤΑΓΗΣ\n\n  Στόχος:    45 vol.% Al₂O₃ σε μονομερές HDDA\n  Παρτίδα:   200 g αλούμινας\n  Πρόσθετο:  1 wt.% BAPO φωτοεκκινητής επί του συνόλου\n\n─────────────────────────────────────────────────────\n\nΒΗΜΑ 1 — Ονομάστε τη συνταγή σας\n\nΣτην κορυφή του παραθύρου, κάντε κλικ στο πεδίο\n«Όνομα Συνταγής / Αρχείου» και πληκτρολογήστε ένα όνομα, π.χ.:\n\n  Al2O3 45vol% HDDA\n\n─────────────────────────────────────────────────────\n\nΒΗΜΑ 2 — Ανοίξτε τον Αντίστροφο Επιλύτη\n\nΚάντε κλικ στο «Αντίστροφος Επιλύτης» στην αριστερή πλαϊνή μπάρα.\n\n─────────────────────────────────────────────────────\n\nΒΗΜΑ 3 — Ορίστε τον στόχο\n\nΣτη γραμμή ΣΤΟΧΟΣ στην κορυφή:\n  • Πληκτρολογήστε  45  στο πεδίο αριθμού.\n  • Επιλέξτε  vol.%  από το αναπτυσσόμενο μενού.\n\n─────────────────────────────────────────────────────\n\nΒΗΜΑ 4 — Προσθέστε το κεραμικό ως ΚΥΡΙΟ ΣΥΣΤΑΤΙΚΟ\n\nΣτη γραμμή εισόδου:\n  • Συστατικό:      κάντε κλικ ▼, πληκτρολογήστε "Al2O3", επιλέξτε το.\n                    Η πυκνότητα συμπληρώνεται αυτόματα (3.987 g/cm³).\n  • Σχέση:          επιλέξτε  Κύριο Συστατικό (Primary)\n  • Κύρια Ποσότητα: επιλέξτε  Μάζα (g)\n  • Τιμή:           πληκτρολογήστε  200\n\nΚάντε κλικ ➕ Προσθήκη.\n\n─────────────────────────────────────────────────────\n\nΒΗΜΑ 5 — Προσθέστε το μονομερές ως ΙΣΟΡΡΟΠΙΑ (Balance)\n\n  • Συστατικό:  κάντε κλικ ▼, πληκτρολογήστε "HDDA", επιλέξτε το.\n  • Σχέση:      επιλέξτε  Balance\n  • Τιμή:       αφήστε  0  (ο επιλύτης το υπολογίζει)\n\nΚάντε κλικ ➕ Προσθήκη.\n\n─────────────────────────────────────────────────────\n\nΒΗΜΑ 6 — Προσθέστε τον φωτοεκκινητή\n\n  • Συστατικό:  κάντε κλικ ▼, πληκτρολογήστε "BAPO", επιλέξτε το.\n  • Σχέση:      επιλέξτε  wt.% of Total Suspension\n  • Τιμή:       πληκτρολογήστε  1\n\nΚάντε κλικ ➕ Προσθήκη.\n\n─────────────────────────────────────────────────────\n\nΒΗΜΑ 7 — Επιλύστε\n\nΚάντε κλικ ⚙ ΕΠΙΛΥΣΗ.\n\nΟ πίνακας συμπληρώνεται με τη μάζα και τον όγκο κάθε συστατικού.\n\n─────────────────────────────────────────────────────\n\nΒΗΜΑ 8 — Αποθηκεύστε και εξάγετε\n\n  💾 Αποθήκευση    →  αποθήκευση συνταγής για μελλοντική χρήση.\n  📄 Εξαγωγή PDF  →  αναφορά Α4 για το εργαστηριακό σας ημερολόγιο.\n  📤 Κοινοποίηση  →  αποστολή μέσω email ή Teams.\n\n─────────────────────────────────────────────────────\n\nΤΕΛΟΣ!\n\nΔιαβάστε τις άλλες ενότητες αυτού του οδηγού για να μάθετε\nγια όλους τους τρόπους εισόδου, τον Άμεσο Υπολογισμό,\nτη Βάση Δεδομένων Υλικών και πολλά άλλα.\n', 'The Materials Database': '\nΗ ΒΑΣΗ ΔΕΔΟΜΕΝΩΝ ΥΛΙΚΩΝ\n\nΗ βάση δεδομένων αποθηκεύει τις φυσικές ιδιότητες κάθε υλικού:\nπυκνότητα (g/cm³), δείκτης διάθλασης (ΔΔ) και μοριακό βάρος\n(g/mol).\n\n─────────────────────────────────────────────────────\n\nΑΝΑΖΗΤΗΣΗ ΥΛΙΚΟΥ\n\nΣτο πεδίο Συστατικό, κάντε κλικ στο κουμπί ▼. Εμφανίζεται\nαναπτυσσόμενος πίνακας με όλα τα υλικά.\n\n  • Κάντε κύλιση, Ή\n  • Αρχίστε να πληκτρολογείτε για φιλτράρισμα — αναζήτηση\n    στο ακρωνύμιο ΚΑΙ στο χημικό όνομα ταυτόχρονα.\n\n─────────────────────────────────────────────────────\n\nΑΝΟΙΓΜΑ ΕΠΕΞΕΡΓΑΣΤΗ ΒΑΣΗΣ ΔΕΔΟΜΕΝΩΝ\n\nΚάντε κλικ στο «🗃 Β.Δ. Υλικών» στο κάτω μέρος\nτης αριστερής πλαϊνής μπάρας.\n\n─────────────────────────────────────────────────────\n\nΠΡΟΣΘΗΚΗ ΝΕΟΥ ΥΛΙΚΟΥ\n\n1. Πληκτρολογήστε το ακρωνύμιο στο πεδίο «Ακρωνύμιο»\n2. Πληκτρολογήστε το πλήρες χημικό όνομα (προαιρετικό)\n3. Εισάγετε την πυκνότητα σε g/cm³  ← ΥΠΟΧΡΕΩΤΙΚΟ\n4. Προαιρετικά εισάγετε τον ΔΔ\n5. Προαιρετικά εισάγετε το μοριακό βάρος\n6. Κάντε κλικ ➕ Προσθήκη / Ενημέρωση\n\n─────────────────────────────────────────────────────\n\nΕΠΕΞΕΡΓΑΣΙΑ ΥΠΑΡΧΟΝΤΟΣ ΥΛΙΚΟΥ\n\n1. Κάντε κλικ στη γραμμή του υλικού.\n2. Αλλάξτε τα πεδία που θέλετε.\n3. Κάντε κλικ ➕ Προσθήκη / Ενημέρωση για αποθήκευση.\n\n─────────────────────────────────────────────────────\n\nΔΙΑΓΡΑΦΗ ΥΛΙΚΟΥ\n\n1. Κάντε κλικ στη γραμμή.\n2. Κάντε κλικ 🗑 Διαγραφή.\n3. Επιβεβαιώστε στο παράθυρο.\n\n─────────────────────────────────────────────────────\n\nΔΗΜΙΟΥΡΓΙΑ ΜΙΓΜΑΤΟΣ\n\nΑν χρησιμοποιείτε τακτικά μείγμα μονομερών, μπορείτε να το\nαποθηκεύσετε ως μία καταχώρηση με προ-υπολογισμένη πυκνότητα.\n\n1. Κάντε κλικ ⊕ Δημιουργία Μίγματος.\n2. Επιλέξτε κάθε συστατικό και εισάγετε το wt.% (σύνολο = 100).\n3. Κάντε κλικ ⟳ Υπολογισμός πυκνότητας.\n4. Δώστε ένα όνομα στο μίγμα.\n5. Κάντε κλικ 💾 Αποθήκευση στη Β.Δ.\n\n─────────────────────────────────────────────────────\n\nΕΞΑΓΩΓΗ ΚΑΙ ΕΙΣΑΓΩΓΗ ΒΑΣΗΣ ΔΕΔΟΜΕΝΩΝ\n\n  Εξαγωγή:  Στον επεξεργαστή → 📤 Εξαγωγή Β.Δ.\n             Αποθηκεύει την πλήρη βάση σε αρχείο .json.\n\n  Εισαγωγή: Στον επεξεργαστή → 📥 Εισαγωγή Β.Δ.\n             Προσθέτει ή ενημερώνει καταχωρήσεις.\n             Δεν διαγράφει ποτέ υπάρχουσες εγγραφές.\n\n─────────────────────────────────────────────────────\n\nΠΟΥ ΑΠΟΘΗΚΕΥΕΤΑΙ ΤΟ ΑΡΧΕΙΟ ΒΑΣΗΣ ΔΕΔΟΜΕΝΩΝ;\n\nΩς μεταγλωττισμένο .exe:\n  %APPDATA%\\3DPrintingFormulator\\3dpformulator_materialsdatabase.json\n\nΩς πηγαίος κώδικας Python:\n  Στον ίδιο φάκελο με το formulator.py\n\n⚠  Αν διαγράψετε το αρχείο, η βάση επανέρχεται στις\n   εργοστασιακές προεπιλογές. Πάντα εξάγετε αντίγραφο πρώτα.\n', 'Forward Formulator': '\nΟ ΑΜΕΣΟΣ ΥΠΟΛΟΓΙΣΜΟΣ\n\nΧρησιμοποιήστε αυτή την καρτέλα όταν ΕΣΕΙΣ αποφασίζετε πόσο\nχρησιμοποιείτε από κάθε υλικό, και θέλετε η εφαρμογή να\nυπολογίσει τη σύσταση.\n\n─────────────────────────────────────────────────────\n\nΡΟΗΕΡΓΑΣΙΑΣ\n\n1. Εισάγετε όνομα συστατικού (χρησιμοποιήστε ▼ για αυτόματη\n   συμπλήρωση και πυκνότητα).\n2. Επιλέξτε Τρόπο Εισόδου (βλ. παρακάτω).\n3. Εισάγετε την Τιμή (και Αναφορά αν απαιτείται).\n4. Κάντε κλικ ➕ Προσθήκη.\n5. Επαναλάβετε για όλα τα συστατικά.\n6. Κάντε κλικ ⚙ ΥΠΟΛΟΓΙΣΜΟΣ.\n\n─────────────────────────────────────────────────────\n\nΟΙ ΕΞΙ ΤΡΟΠΟΙ ΕΙΣΟΔΟΥ\n\n────────────────────────────────────────\nΤΡΟΠΟΣ 1:  Μάζα (g)\n────────────────────────────────────────\n  Εισάγετε την ακριβή μάζα σε γραμμάρια.\n  Η εφαρμογή μετατρέπει σε όγκο: V = μάζα / πυκνότητα\n\n  Χρήση:  Όταν γνωρίζετε ακριβώς πόσα γραμμάρια θέλετε.\n\n  Παράδειγμα:  Al₂O₃  →  Μάζα (g)  →  200\n\n────────────────────────────────────────\nΤΡΟΠΟΣ 2:  Όγκος (cm³)\n────────────────────────────────────────\n  Εισάγετε τον ακριβή όγκο σε cm³ (= mL).\n  Η εφαρμογή μετατρέπει σε μάζα: m = V × πυκνότητα\n\n  Χρήση:  Μέτρηση υγρού με πιπέτα ή ογκομετρικό κύλινδρο.\n\n────────────────────────────────────────\nΤΡΟΠΟΣ 3:  wt.% ως προς Αναφορά\n────────────────────────────────────────\n  Η μάζα αυτού του συστατικού είναι ποσοστό της μάζας ενός άλλου.\n  Πρέπει να ορίσετε και το πεδίο Αναφορά.\n\n  Τύπος:  μάζα_αυτό = (Τιμή / 100) × μάζα_αναφοράς\n\n  Παράδειγμα:  Διασκορπιστής  →  2 wt.% ως προς Al₂O₃\n               Αν Al₂O₃ = 200 g → Διασκορπιστής = 4 g\n\n────────────────────────────────────────\nΤΡΟΠΟΣ 4:  vol.% ως προς Αναφορά\n────────────────────────────────────────\n  Ίδιο με Τρόπο 3 αλλά το ποσοστό είναι σε ΟΓΚΟ.\n\n────────────────────────────────────────\nΤΡΟΠΟΣ 5:  wt.% επί του Συνόλου\n────────────────────────────────────────\n  Το συστατικό είναι σταθερό ποσοστό της ΣΥΝΟΛΙΚΗΣ μάζας.\n\n  Χρήση:  Φωτοεκκινητές που δοσολογούνται σε σχέση με το\n           συνολικό ρητίνη.\n\n  ⚠  Το άθροισμα όλων των wt.% επί Συνόλου < 100%.\n\n────────────────────────────────────────\nΤΡΟΠΟΣ 6:  vol.% επί του Συνόλου\n────────────────────────────────────────\n  Ίδιο με Τρόπο 5 αλλά σε ποσοστό όγκου.\n\n  ⚠  Το άθροισμα όλων των vol.% επί Συνόλου < 100%.\n\n─────────────────────────────────────────────────────\n\nΣΥΜΒΟΥΛΕΣ\n\n  ✓  Μπορείτε να συνδυάσετε ελεύθερα και τους έξι τρόπους.\n  ✓  Χρησιμοποιήστε ▼ στο πεδίο Αναφορά για επιλογή από τα\n     ήδη υπάρχοντα συστατικά — αποφεύγετε ορθογραφικά λάθη.\n  ✓  Η σειρά των συστατικών δεν επηρεάζει τους υπολογισμούς.\n', 'Inverse Solver': "\nΟ ΑΝΤΙΣΤΡΟΦΟΣ ΕΠΙΛΥΤΗΣ\n\nΧρησιμοποιήστε αυτή την καρτέλα όταν έχετε ένα ΣΤΟΧΟ\nΦΟΡΤΙΣΗΣ ΣΤΕΡΕΩΝ και θέλετε η εφαρμογή να υπολογίσει\nτις ποσότητες για εσάς.\n\n«Θέλω 45 vol.% αλούμινα» → η εφαρμογή σας λέει πόσο HDDA.\n\n─────────────────────────────────────────────────────\n\nΓΡΑΜΜΗ ΣΤΟΧΟΥ (κορυφή της καρτέλας)\n\n  • Τιμή στόχου:  το επιθυμητό ποσοστό φόρτισης (π.χ. 45)\n  • Τρόπος:       vol.% ή wt.%\n\n  vol.%  →  Κύριο Συστατικό = αυτό το % του ΣΥΝΟΛΙΚΟΥ ΟΓΚΟΥ.\n  wt.%   →  Κύριο Συστατικό = αυτό το % της ΣΥΝΟΛΙΚΗΣ ΜΑΖΑΣ.\n\n─────────────────────────────────────────────────────\n\nΟΙ ΕΠΤΑ ΤΥΠΟΙ ΣΧΕΣΗΣ\n\n────────────────────────────────────────\nΣΧΕΣΗ 1:  Κύριο Συστατικό (Primary)\n────────────────────────────────────────\n  Το ΚΕΡΑΜΙΚΟ ή κύριο πληρωτικό — το συστατικό η φόρτιση\n  του οποίου αποτελεί τον στόχο.\n\n  Κανόνες:  ΑΚΡΙΒΩΣ 1 Κύριο Συστατικό ανά συνταγή.\n\n  Παράδειγμα:  Al₂O₃  →  Primary  →  Μάζα (g)  →  200\n\n────────────────────────────────────────\nΣΧΕΣΗ 2:  Ισορροπία (Balance)\n────────────────────────────────────────\n  Ο ΔΙΑΛΥΤΗΣ ή ΜΟΝΟΜΕΡΕΣ που ο επιλύτης υπολογίζει ώστε\n  να επιτευχθεί ο στόχος φόρτισης.\n\n  Κανόνες:  Κατ' ανώτατο 1 Balance. Αφήστε Τιμή = 0.\n\n  ⚠  Χωρίς Balance; Ο επιλύτης βρίσκει ένα συντελεστή\n     κλίμακας k που πολλαπλασιάζει όλα τα κλιμακούμενα\n     συστατικά.\n\n────────────────────────────────────────\nΣΧΕΣΗ 3:  wt.% ως προς Αναφορά\n────────────────────────────────────────\n  Η μάζα αυτού του συστατικού είναι ποσοστό μάζας άλλου.\n\n  Παράδειγμα:  DISPERBYK-111  →  2 wt.% ως προς Al₂O₃\n\n────────────────────────────────────────\nΣΧΕΣΗ 4:  vol.% ως προς Αναφορά\n────────────────────────────────────────\n  Ίδιο αλλά ποσοστό σε όγκο.\n\n────────────────────────────────────────\nΣΧΕΣΗ 5:  wt.% του Συνολικού Αιωρήματος\n────────────────────────────────────────\n  Σταθερό wt.% της ΤΕΛΙΚΗΣ παρτίδας.\n  Επιλύεται ΜΕΤΑ τον υπολογισμό του Balance.\n\n  ⚠  Άθροισμα όλων των wt.% Συνολικού Αιωρήματος < 100%.\n\n────────────────────────────────────────\nΣΧΕΣΗ 6:  vol.% του Συνολικού Αιωρήματος\n────────────────────────────────────────\n  Ίδιο αλλά ποσοστό σε όγκο.\n\n────────────────────────────────────────\nΣΧΕΣΗ 7:  Ανεξάρτητη Μάζα / Όγκος\n────────────────────────────────────────\n  Σταθερή ποσότητα που δεν κλιμακώνεται με τίποτα.\n\n  Χρήση:  Μικρά σταθερά πρόσθετα ανεξάρτητα μεγέθους\n           παρτίδας.\n\n─────────────────────────────────────────────────────\n\nΣΥΝΟΨΗ ΚΑΝΟΝΩΝ\n\n  ✓  Απαιτείται ακριβώς 1 Κύριο Συστατικό.\n  ✓  Κατ' ανώτατο 1 Balance. Αφήστε Τιμή = 0.\n  ✓  Όλα τα ονόματα συστατικών μοναδικά.\n  ✓  Τα ονόματα Αναφοράς πρέπει να ταιριάζουν ακριβώς.\n  ✓  Ποσοστά Συνολικού Αιωρήματος < 100% συνολικά.\n\n─────────────────────────────────────────────────────\n\nΑΝAΓΝΩΣΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ\n\nΜετά το ⚙ ΕΠΙΛΥΣΗ:\n\n  Πίνακας:       Μάζα (g) · Όγκος (cm³) · wt.% · vol.%\n  Σύνοψη:        Συνολική Μάζα · Συνολικός Όγκος · Πυκνότητα\n                 Επιτευχθείσα φόρτιση wt.% και vol.%\n\n─────────────────────────────────────────────────────\n\nΤΥΠΙΚΟ ΠΑΡΑΔΕΙΓΜΑ ΣΥΝΤΑΓΗΣ\n\n  Συστατικό         Σχέση                        Τιμή   Αναφορά\n  ──────────────    ──────────────────────────   ─────  ──────────\n  Al₂O₃             Primary (Μάζα g)              200\n  HDDA               Balance                        0\n  TMP(EO)3TA         wt.% ως προς                  50    HDDA\n  DISPERBYK-111      wt.% ως προς                   2    Al₂O₃\n  BAPO               wt.% Συνολικού Αιωρήματος      1\n  CQ                 wt.% Συνολικού Αιωρήματος      0.5\n\n  Στόχος: 45 vol.%\n", 'Editing & Managing Components': '\nΕΠΕΞΕΡΓΑΣΙΑ ΣΥΣΤΑΤΙΚΟΥ\n\n1. Κάντε κλικ στη γραμμή του συστατικού (επισημαίνεται μπλε).\n   Τα στοιχεία του φορτώνονται στα πεδία εισόδου.\n2. Κάντε τις αλλαγές σας.\n3. Κάντε κλικ ✏ Ενημέρωση για αποθήκευση.\n\n⚠  ΜΗΝ κάνετε κλικ ➕ Προσθήκη κατά την επεξεργασία — αυτό\n   θα δημιουργήσει διπλότυπο. Χρησιμοποιείτε ΠΑΝΤΑ\n   ✏ Ενημέρωση για υπάρχοντα συστατικά.\n\n─────────────────────────────────────────────────────\n\nΑΦΑΙΡΕΣΗ ΣΥΣΤΑΤΙΚΟΥ\n\n1. Κάντε κλικ στη γραμμή για επιλογή.\n2. Κάντε κλικ 🗑 Αφαίρεση.\n\n─────────────────────────────────────────────────────\n\nΑΛΛΑΓΗ ΣΕΙΡΑΣ ΣΥΣΤΑΤΙΚΩΝ\n\n1. Κάντε κλικ στη γραμμή που θέλετε να μετακινήσετε.\n2. Κάντε κλικ ▲ Πάνω ή ▼ Κάτω.\n\nΗ σειρά επηρεάζει την εμφάνιση στον πίνακα και στην αναφορά PDF.\nΔΕΝ επηρεάζει τους υπολογισμούς.\n\n─────────────────────────────────────────────────────\n\nΕΚΚΑΘΑΡΙΣΗ ΟΛΗΣ ΤΗΣ ΣΥΝΤΑΓΗΣ\n\nΚάντε κλικ ✖ Εκκαθάριση για αφαίρεση όλων. Θα ζητηθεί\nεπιβεβαίωση.\n\n⚠  Δεν μπορεί να αναιρεθεί — αποθηκεύστε πρώτα αν θέλετε\n   να κρατήσετε την τρέχουσα συνταγή.\n\n─────────────────────────────────────────────────────\n\nΑΛΛΑΓΗ ΟΝΟΜΑΤΟΣ ΣΥΝΤΑΓΗΣ\n\nΤο πεδίο «Όνομα Συνταγής / Αρχείου» βρίσκεται στην κορυφή\nτου παραθύρου. Κάντε κλικ και πληκτρολογήστε νέο όνομα.\n\nΤο όνομα ενημερώνεται αυτόματα κατά Αποθήκευση / Φόρτωση.\n', 'Save, Load & PDF Export': '\nΑΠΟΘΗΚΕΥΣΗ ΣΥΝΤΑΓΗΣ\n\nΚάντε κλικ 💾 Αποθήκευση (πάνω δεξιά κάθε καρτέλας).\n\nΑνοίγει παράθυρο αρχείου με το Όνομα Συνταγής προσυμπληρωμένο.\nΤο αρχείο αποθηκεύεται σε μορφή .json.\n\nΤι ΑΠΟΘΗΚΕΥΕΤΑΙ:\n  ✓  Όνομα συνταγής\n  ✓  Όλα τα συστατικά, πυκνότητες, τρόποι, τιμές, αναφορές\n  ✓  Ποια καρτέλα ήταν ενεργή\n  ✓  Τιμή και τρόπος στόχου (Αντίστροφος Επιλύτης)\n\nΤι ΔΕΝ ΑΠΟΘΗΚΕΥΕΤΑΙ:\n  ✗  Υπολογισμένα αποτελέσματα (επανυπολογίστε μετά τη φόρτωση)\n\n─────────────────────────────────────────────────────\n\nΦΟΡΤΩΣΗ ΣΥΝΤΑΓΗΣ\n\nΚάντε κλικ 📂 Φόρτωση.\n\nΕπιλέξτε ένα αρχείο .json. Όλα τα συστατικά αποκαθίστανται.\nΤο Όνομα Συνταγής ενημερώνεται από το όνομα αρχείου.\n\n⚠  Μετά τη φόρτωση, πατήστε ⚙ ΥΠΟΛΟΓΙΣΜΟΣ ή ⚙ ΕΠΙΛΥΣΗ\n   για επανάληψη των αποτελεσμάτων.\n\n─────────────────────────────────────────────────────\n\nΕΞΑΓΩΓΗ ΣΕ PDF\n\nΚάντε κλικ 📄 Εξαγωγή PDF.\n\nΠρέπει πρώτα να υπολογίσετε/επιλύσετε. Αν δεν υπάρχουν\nαποτελέσματα, η εφαρμογή σας ειδοποιεί.\n\nΗ αναφορά PDF περιλαμβάνει:\n  • Όνομα συνταγής, ημερομηνία, στοιχεία προγραμματιστή\n  • Πλήρη πίνακα συστατικών\n  • Στατιστικά σύνοψης: Συνολική Μάζα · Συνολικός Όγκος ·\n    Θεωρητική Πυκνότητα\n  • Για Αντίστροφο Επιλύτη: Στόχος · Επιτευχθείσα φόρτιση\n\nΜορφοποίηση για εκτύπωση σε χαρτί A4.\n\n─────────────────────────────────────────────────────\n\nΚΟΙΝΟΠΟΙΗΣΗ ΑΡΧΕΙΟΥ\n\nΚάντε κλικ 📤 Κοινοποίηση.\n\nΔεν χρειάζεται να αποθηκεύσετε πρώτα — το κουμπί δημιουργεί\nαυτόματα αρχείο αν δεν υπάρχει.\n\n  ✉ Email  →  Ανοίγει το Outlook με συνημμένο αρχείο.\n  💬 Teams →  Ανοίγει την Εξερεύνηση αρχείων με επισημασμένο\n               το αρχείο για σύρσιμο στο Teams.\n', 'Tips & Troubleshooting': '\n─────────────────────────────────────────────────────\nΣΥΝΗΘΗ ΛΑΘΗ ΚΑΙ ΠΩΣ ΝΑ ΤΑ ΔΙΟΡΘΩΣΕΤΕ\n─────────────────────────────────────────────────────\n\nΠΡΟΒΛΗΜΑ:  Σφάλμα επιλύτη ή λανθασμένοι όγκοι\n────────────────────────────────────────\n  Αιτία:  Λανθασμένη ή ελλείπουσα τιμή πυκνότητας.\n  Λύση:   Ελέγξτε κάθε πυκνότητα. Πρέπει να είναι σε g/cm³.\n          Χρησιμοποιήστε ▼ για επιλογή από τη βάση δεδομένων.\n\n─────────────────────────────────────────────────────\n\nΠΡΟΒΛΗΜΑ:  Σφάλμα «Αναφορά δεν βρέθηκε»\n──────────────────────────────────────\n  Αιτία:  Το όνομα αναφοράς δεν ταιριάζει ακριβώς.\n          Ακόμα και ένα επιπλέον κενό προκαλεί το σφάλμα.\n  Λύση:   Χρησιμοποιήστε ▼ στο πεδίο Αναφορά για επιλογή\n          από τα συστατικά της συνταγής.\n\n─────────────────────────────────────────────────────\n\nΠΡΟΒΛΗΜΑ:  Σφάλμα «Δεν βρέθηκε Primary»\n──────────────────────────────────────────\n  Αιτία:  Κανένα συστατικό δεν έχει Σχέση = Primary.\n  Λύση:   Επιλέξτε το κεραμικό → αλλάξτε σε Primary\n          → κάντε κλικ ✏ Ενημέρωση.\n\n─────────────────────────────────────────────────────\n\nΠΡΟΒΛΗΜΑ:  Σφάλμα «Πολλαπλά Primary»\n──────────────────────────────────────────\n  Αιτία:  Περισσότερα του ενός συστατικά έχουν Primary.\n  Λύση:   Αφήστε μόνο ένα ως Primary.\n\n─────────────────────────────────────────────────────\n\nΠΡΟΒΛΗΜΑ:  Αρνητικό ή τεράστιο αποτέλεσμα Balance\n──────────────────────────────────────────\n  Αιτία:  Ο στόχος φόρτισης μπορεί να είναι γεωμετρικά\n          αδύνατος.\n  Λύση:   Μειώστε τον στόχο % ή μειώστε τις τιμές των\n          άλλων συστατικών.\n\n─────────────────────────────────────────────────────\n\nΠΡΟΒΛΗΜΑ:  wt.% και vol.% δεν αθροίζουν 100%\n────────────────────────────────────────────────────\n  Αυτό είναι ΦΥΣΙΟΛΟΓΙΚΟ αν κάποια συστατικά ορίζονται\n  σε απόλυτες ποσότητες (g ή cm³).\n\n─────────────────────────────────────────────────────\n\nΠΡΟΒΛΗΜΑ:  Δύο συστατικά με το ίδιο όνομα\n────────────────────────────────────────────\n  Λύση:   Μετονομάστε το ένα (π.χ. «HDDA-1» και «HDDA-2»).\n\n─────────────────────────────────────────────────────\n\nΠΡΟΒΛΗΜΑ:  Φόρτωσα συνταγή αλλά τα αποτελέσματα είναι κενά\n────────────────────────────────────────────────────\n  Λύση:   Πατήστε ⚙ ΥΠΟΛΟΓΙΣΜΟΣ ή ⚙ ΕΠΙΛΥΣΗ μετά τη φόρτωση.\n\n─────────────────────────────────────────────────────\nΣΥΜΒΟΥΛΕΣ ΓΙΑ ΑΠΟΤΕΛΕΣΜΑΤΙΚΗ ΧΡΗΣΗ\n─────────────────────────────────────────────────────\n\n  ✓  Χρησιμοποιείτε πάντα ▼ στο πεδίο Συστατικό.\n  ✓  Χρησιμοποιείτε πάντα ▼ στο πεδίο Αναφορά.\n  ✓  Αποθηκεύετε τη συνταγή ΠΡΙΝ πειραματιστείτε με τιμές.\n  ✓  Δημιουργήστε μίγμα μονομερών με ⊕ Δημιουργία Μίγματος\n     αν το χρησιμοποιείτε τακτικά.\n  ✓  Εξάγετε PDF μετά από κάθε επιτυχημένη σύνθεση.\n  ✓  Η μπάρα κατάστασης στο κάτω μέρος δείχνει πάντα τι\n     έκανε τελευταία η εφαρμογή.\n  ✓  Τοποθετήστε το ποντίκι πάνω από οποιοδήποτε κουμπί\n     για να δείτε επεξήγηση.\n', 'Settings & Accessibility': '\nΠΑΡΑΘΥΡΟ ΡΥΘΜΙΣΕΩΝ\n\nΑνοίξτε το μέσω του κουμπιού ⚙ Ρυθμίσεις στο κάτω μέρος\nτης αριστερής πλαϊνής μπάρας.\n\n─────────────────────────────────────────────────────\n\nΕΜΦΑΝΙΣΗ\n\n────────────────────────────────────────\nΓλώσσα\n────────────────────────────────────────\n  Επιλέξτε γλώσσα UI από το αναπτυσσόμενο μενού.\n\n  ✓  Ισχύει αμέσως με κλικ Εφαρμογή ή ΟΚ.\n\n  Διαθέσιμες γλώσσες: Αγγλικά, Ελληνικά, Γαλλικά, Γερμανικά,\n  Ισπανικά, Ιταλικά, Ολλανδικά, Κινεζικά, Ιαπωνικά, Κορεατικά,\n  Χίντι.\n\n  Σημείωση: το κείμενο Βοήθειας, η βάση δεδομένων υλικών και\n  η επιστημονική σημειογραφία (wt.%, vol.%, g/cm³) παραμένουν\n  στα Αγγλικά σε όλες τις γλώσσες.\n\n────────────────────────────────────────\nΜέγεθος γραμματοσειράς\n────────────────────────────────────────\n  Μικρό / Κανονικό / Μεγάλο / Πολύ Μεγάλο\n\n  ✓  Ισχύει αμέσως με κλικ Εφαρμογή ή ΟΚ.\n\n────────────────────────────────────────\nΛειτουργία υψηλής αντίθεσης\n────────────────────────────────────────\n  Εναλλαγή σε σκοτεινό θέμα με μεγαλύτερη αντίθεση.\n\n  ✓  Ισχύει αμέσως με κλικ Εφαρμογή ή ΟΚ.\n\n────────────────────────────────────────\nΠαλέτα για χρωματοτυφλία\n────────────────────────────────────────\n  Αντικαθιστά κόκκινο/πράσινο με μπλε/πορτοκαλί.\n\n  ✓  Ισχύει αμέσως.\n\n─────────────────────────────────────────────────────\n\nΣΥΜΠΕΡΙΦΟΡΑ\n\n────────────────────────────────────────\nΕπιβεβαίωση πριν αφαίρεση/εκκαθάριση\n────────────────────────────────────────\n  Ενεργοποιημένο (προεπιλογή): η εφαρμογή ρωτά πριν\n  αφαιρέσει συστατικό ή εκκαθαρίσει τη λίστα.\n\n────────────────────────────────────────\nΜεγαλύτερα κουμπιά\n────────────────────────────────────────\n  Αυξάνει το padding των κουμπιών για ευκολότερο κλικ\n  σε οθόνες αφής ή για χρήστες με δυσκολία στην κίνηση.\n\n  ✓  Ισχύει αμέσως με κλικ Εφαρμογή ή ΟΚ.\n\n─────────────────────────────────────────────────────\n\nΕΠΑΝΑΦΟΡΑ ΠΡΟΕΠΙΛΟΓΩΝ\n\nΚάντε κλικ «Επαναφορά Προεπιλογών» κάτω αριστερά στο\nπαράθυρο Ρυθμίσεων. Θα ζητηθεί επιβεβαίωση.\n\n─────────────────────────────────────────────────────\n\nΠΟΥ ΑΠΟΘΗΚΕΥΟΝΤΑΙ ΟΙ ΡΥΘΜΙΣΕΙΣ;\n\nΩς μεταγλωττισμένο .exe:\n  %APPDATA%\\3DPrintingFormulator\\3dpformulator_usersettings.json\n\nΩς πηγαίος κώδικας Python:\n  Στον ίδιο φάκελο με το formulator.py\n', 'Formulae & Theory': '\nΑυτή η ενότητα εξηγεί τα μαθηματικά που χρησιμοποιεί η εφαρμογή.\nΧρήσιμο για χειροκίνητη επαλήθευση αποτελεσμάτων ή κατανόηση\nτης λειτουργίας του επιλύτη.\n\n─────────────────────────────────────────────────────\nΣΥΜΒΟΛΙΣΜΟΣ\n─────────────────────────────────────────────────────\n\n  mᵢ         μάζα συστατικού i  [g]\n  Vᵢ         όγκος συστατικού i  [cm³]\n  ρᵢ         πυκνότητα συστατικού i  [g/cm³]\n  M_tot      συνολική μάζα παρτίδας  [g]\n  V_tot      συνολικός όγκος παρτίδας  [cm³]\n  T          στόχος φόρτισης ως κλάσμα  (π.χ. 45% → T = 0.45)\n  n          αριθμός συστατικών\n\n─────────────────────────────────────────────────────\nΒΑΣΙΚΕΣ ΜΕΤΑΤΡΟΠΕΣ\n─────────────────────────────────────────────────────\n\n  Όγκος από μάζα:        Vᵢ = mᵢ / ρᵢ\n  Μάζα από όγκο:         mᵢ = Vᵢ · ρᵢ\n\n─────────────────────────────────────────────────────\nΣΥΝΟΛΑ ΠΑΡΤΙΔΑΣ ΚΑΙ ΣΥΣΤΑΣΗ\n─────────────────────────────────────────────────────\n\n  Συνολική μάζα:         M_tot = m₁ + m₂ + ... + mₙ\n  Συνολικός όγκος:       V_tot = V₁ + V₂ + ... + Vₙ\n\n  Θεωρητική πυκνότητα:   ρ_mix = M_tot / V_tot\n\n  Κλάσμα βάρους (wt.%):  wt.%ᵢ  = 100 · mᵢ / M_tot\n  Κλάσμα όγκου (vol.%): vol.%ᵢ = 100 · Vᵢ / V_tot\n\n─────────────────────────────────────────────────────\nΑΜΕΣΟΣ ΥΠΟΛΟΓΙΣΜΟΣ — ΕΠΙΛΥΣΗ ΤΡΟΠΩΝ ΕΙΣΟΔΟΥ\n─────────────────────────────────────────────────────\n\n  Μάζα (g):\n    mᵢ = εισαχθείσα τιμή\n    Vᵢ = mᵢ / ρᵢ\n\n  Όγκος (cm³):\n    Vᵢ = εισαχθείσα τιμή\n    mᵢ = Vᵢ · ρᵢ\n\n  wt.% ως προς Αναφορά (συστατικό αναφοράς = r):\n    mᵢ = (τιμή / 100) · m_r\n    Vᵢ = mᵢ / ρᵢ\n\n  vol.% ως προς Αναφορά:\n    Vᵢ = (τιμή / 100) · V_r\n    mᵢ = Vᵢ · ρᵢ\n\n  wt.% επί Συνόλου (αλγεβρική λύση):\n    Έστω S = (άθροισμα όλων των wt.% επί Συνόλου) / 100\n    Έστω M_abs = άθροισμα μαζών όλων των άλλων συστατικών\n    M_tot = M_abs / (1 − S)\n    mᵢ = (τιμή / 100) · M_tot\n\n  vol.% επί Συνόλου (ανάλογο):\n    Έστω S = (άθροισμα vol.% επί Συνόλου) / 100\n    Έστω V_abs = άθροισμα όγκων όλων των άλλων\n    V_tot = V_abs / (1 − S)\n    Vᵢ = (τιμή / 100) · V_tot\n\n─────────────────────────────────────────────────────\nΑΝΤΙΣΤΡΟΦΟΣ ΕΠΙΛΥΤΗΣ — ΕΠΙΛΥΣΗ ΣΧΕΣΕΩΝ\n─────────────────────────────────────────────────────\n\n  wt.% ως προς Αναφορά:\n    mᵢ = (τιμή / 100) · m_r  (ίδιο με Άμεσο)\n\n  vol.% ως προς Αναφορά:\n    Vᵢ = (τιμή / 100) · V_r  (ίδιο με Άμεσο)\n\n  wt.% Συνολικού Αιωρήματος (μετά Balance):\n    Έστω F_pm = άθροισμα κλασμάτων wt.% Συνολικού\n    Έστω M_non = άθροισμα μαζών μη-αιωρηματικών\n    M_tot = M_non / (1 − F_pm)\n    mᵢ = (τιμή / 100) · M_tot\n\n  Ανεξάρτητη Μάζα (g):   mᵢ = τιμή  (σταθερό, δεν κλιμακώνεται)\n  Ανεξάρτητος Όγκος (cm³): Vᵢ = τιμή\n\n─────────────────────────────────────────────────────\nΑΝΤΙΣΤΡΟΦΟΣ ΕΠΙΛΥΤΗΣ — ΥΠΟΛΟΓΙΣΜΟΣ BALANCE\n─────────────────────────────────────────────────────\n\nΟ επιλύτης βρίσκει τη μάζα Balance (m_B) ώστε το Κύριο\nΣυστατικό να φτάσει ακριβώς τον στόχο T.\n\n  Για στόχο vol.%:\n    V_B = V_anc · (1 − F_pv) / T − V_anc − V_kn\n    m_B = V_B · ρ_B\n\n  Για στόχο wt.%:\n    m_B = M_anc · (1 − F_pm) / T − M_anc − M_kn\n\n  Όπου:\n    V_anc, M_anc  = όγκος και μάζα του Κύριου Συστατικού\n    V_kn, M_kn    = συνολικός όγκος και μάζα άλλων γνωστών\n    F_pv, F_pm    = άθροισμα κλασμάτων vol.%/wt.% Αιωρήματος\n    ρ_B           = πυκνότητα Balance\n\n─────────────────────────────────────────────────────\nΑΝΤΙΣΤΡΟΦΟΣ ΕΠΙΛΥΤΗΣ — ΣΥΝΤΕΛΕΣΤΗΣ ΚΛΙΜΑΚΑΣ k\n─────────────────────────────────────────────────────\n\nΌταν δεν υπάρχει Balance, ο επιλύτης βρίσκει k ώστε όλα\nτα κλιμακούμενα συστατικά × k να ικανοποιούν τον στόχο.\n\n  Για στόχο vol.%:\n    k = (V_anc_fixed − T · V_fixed_total)\n        / (T · V_scalable_total − V_anc_scalable)\n\n  Τελικές ποσότητες: mᵢ_final = k · mᵢ,  Vᵢ_final = k · Vᵢ\n\n─────────────────────────────────────────────────────\nΙΔΕΩΔΗΣ ΑΝΑΜΕΙΞΗ (χρησιμοποιείται στη Δημιουργία Μίγματος)\n─────────────────────────────────────────────────────\n\n  1 / ρ_blend = Σ (wᵢ / ρᵢ)\n\n  όπου wᵢ = κλάσμα βάρους συστατικού i.\n\n  Προϋποθέτει πρόσθετους όγκους (χωρίς αλλαγή όγκου).\n\n─────────────────────────────────────────────────────\nΠΑΡΑΔΕΙΓΜΑ ΥΠΟΛΟΓΙΣΜΟΥ — ΠΛΗΡΗΣ ΑΝΤΙΣΤΡΟΦΗ ΕΠΙΛΥΣΗ\n─────────────────────────────────────────────────────\n\nΣυνταγή:  200 g Al₂O₃ (ρ = 3.987),  στόχος = 45 vol.%\n          Balance: HDDA (ρ = 1.010)\n          BAPO: 1 wt.% Συνολικού Αιωρήματος\n\nΒήμα 1 — Όγκος Κύριου Συστατικού:\n  V_anc = 200 / 3.987 = 50.16 cm³\n\nΒήμα 2 — F_pm = 0.01,  F_pv = 0\n\nΒήμα 3 — Απαιτούμενος όγκος Balance:\n  V_B = 50.16 · (1/0.45 − 1) = 61.31 cm³\n  m_B = 61.31 × 1.010 = 61.92 g\n\nΒήμα 4 — BAPO (wt.% Αιωρήματος):\n  M_non = 200 + 61.92 = 261.92 g\n  M_tot = 261.92 / 0.99 = 264.57 g\n  m_BAPO = 0.01 × 264.57 = 2.65 g\n\nΒήμα 5 — Τελικός έλεγχος:\n  V_tot = 50.16 + 61.31 + 2.23 = 113.70 cm³\n  vol.% Al₂O₃ = 50.16 / 113.70 × 100 = 44.1%\n  (Μικρή απόκλιση λόγω όγκου BAPO· ο επιλύτης επαναλαμβάνει\n   για ακριβή λύση.)\n'},
    "fr": {'About': "\nTHE 3D PRINTING FORMULATOR  —  v1.0\nPar Dr Thanos Goulas\n📧  thanosgoulas@outlook.com\n\n─────────────────────────────────────────────────────\n\nQUE FAIT CETTE APPLICATION ?\n\nElle calcule les quantités exactes de chaque matériau dans une\nformulation de résine ou de pâte céramique — en grammes et cm³ —\nafin de peser précisément chaque lot au laboratoire.\n\nVous pouvez travailler dans deux directions :\n\n  DIRECT  →  Vous décidez des quantités. L'application calcule\n              la composition finale (wt.%, vol.%, densité).\n\n  INVERSE →  Vous décidez de la composition souhaitée (ex. 45\n              vol.% d'alumine). L'application calcule les\n              quantités pour vous.\n\n─────────────────────────────────────────────────────\n\nNAVIGATION\n\nLa barre latérale gauche contient :\n  • Solveur Inverse      — basculer vers l'onglet Solveur Inverse\n  • Formulation Directe  — basculer vers l'onglet Direct\n  • Base Matériaux       — ouvrir l'éditeur de base de données\n  • Aide                 — ouvrir ce guide\n  • Paramètres           — ouvrir les paramètres\n\nLa barre supérieure de chaque onglet contient :\n  • Nom de la Recette / Fichier\n  • 💾 Enregistrer · 📂 Charger · 📄 Exporter PDF · 📤 Partager\n\n─────────────────────────────────────────────────────\n\nBASE DE DONNÉES DES MATÉRIAUX\n\nLa base de données contient ~200 matériaux (céramiques, monomères,\nphotoamorceurs, dispersants, solvants, etc.) — avec densité,\nindice de réfraction et masse molaire.\n\n─────────────────────────────────────────────────────\n\nAVERTISSEMENT\n\nLes valeurs de densité proviennent de Sigma-Aldrich, PubChem,\nNIST, CRC Handbook et fiches techniques des fabricants.\n\n⚠  La densité peut varier selon la qualité, la pureté, la\n   température et le fournisseur. Vérifiez toujours avec la\n   FDS de votre matériau avant utilisation critique.\n\n─────────────────────────────────────────────────────\n\nRETOURS & SIGNALEMENT D'ERREURS\n\n📧  thanosgoulas@outlook.com\n", 'Quick Start Guide': "\nNOUVEAU ? COMMENCEZ ICI.\n\nCe guide vous accompagne à travers un exemple complet en utilisant\nle Solveur Inverse.\n\n─────────────────────────────────────────────────────\n\nEXEMPLE DE RECETTE\n\n  Cible :    45 vol.% Al₂O₃ dans un monomère HDDA\n  Lot :      200 g d'alumine\n  Additif :  1 wt.% de photoamorceur BAPO sur le lot total\n\n─────────────────────────────────────────────────────\n\nÉTAPE 1 — Nommez votre recette\n\nEn haut de la fenêtre, cliquez sur «Nom de la Recette / Fichier»\net tapez un nom, par exemple :  Al2O3 45vol% HDDA\n\n─────────────────────────────────────────────────────\n\nÉTAPE 2 — Ouvrez le Solveur Inverse\n\nCliquez sur «Solveur Inverse» dans la barre latérale gauche.\n\n─────────────────────────────────────────────────────\n\nÉTAPE 3 — Définissez la cible\n\nDans la ligne CIBLE en haut :\n  • Tapez  45  dans la case.\n  • Sélectionnez  vol.%  dans la liste déroulante.\n\n─────────────────────────────────────────────────────\n\nÉTAPE 4 — Ajoutez la céramique comme COMPOSANT PRINCIPAL\n\nDans la ligne de saisie :\n  • Composant :   cliquez ▼, tapez «Al2O3», sélectionnez.\n                  La densité se remplit automatiquement.\n  • Relation :    choisissez  Primary\n  • Quantité :    choisissez  Masse (g)\n  • Valeur :      tapez  200\n\nCliquez ➕ Ajouter.\n\n─────────────────────────────────────────────────────\n\nÉTAPE 5 — Ajoutez le monomère comme BALANCE\n\n  • Composant :  cliquez ▼, tapez «HDDA», sélectionnez.\n  • Relation :   choisissez  Balance\n  • Valeur :     laissez  0  (le solveur calcule)\n\nCliquez ➕ Ajouter.\n\n─────────────────────────────────────────────────────\n\nÉTAPE 6 — Ajoutez le photoamorceur\n\n  • Composant :  cliquez ▼, tapez «BAPO», sélectionnez.\n  • Relation :   choisissez  wt.% of Total Suspension\n  • Valeur :     tapez  1\n\nCliquez ➕ Ajouter.\n\n─────────────────────────────────────────────────────\n\nÉTAPE 7 — Résolvez\n\nCliquez ⚙ RÉSOUDRE.\n\nLe tableau se remplit avec la masse et le volume de chaque\ncomposant.\n\n─────────────────────────────────────────────────────\n\nÉTAPE 8 — Enregistrez et exportez\n\n  💾 Enregistrer   →  sauvegarde la recette.\n  📄 Exporter PDF  →  rapport A4 pour votre cahier de laboratoire.\n  📤 Partager      →  envoi par e-mail ou Teams.\n", 'The Materials Database': "\nLA BASE DE DONNÉES DES MATÉRIAUX\n\nLa base stocke les propriétés physiques de chaque matériau :\ndensité (g/cm³), indice de réfraction (IR) et masse molaire\n(g/mol).\n\n─────────────────────────────────────────────────────\n\nRECHERCHER UN MATÉRIAU\n\nDans le champ Composant, cliquez sur ▼. Un panneau déroulant\naffiche tous les matériaux.\n\n  • Faites défiler, OU\n  • Commencez à taper pour filtrer — la recherche porte sur\n    l'acronyme ET le nom chimique simultanément.\n\n─────────────────────────────────────────────────────\n\nOUVRIR L'ÉDITEUR DE BASE DE DONNÉES\n\nCliquez sur «🗃 Base Matériaux» en bas de la barre latérale.\n\n─────────────────────────────────────────────────────\n\nAJOUTER UN NOUVEAU MATÉRIAU\n\n1. Saisissez l'acronyme dans «Acronyme»\n2. Saisissez le nom chimique complet (optionnel)\n3. Entrez la densité en g/cm³  ← OBLIGATOIRE\n4. Entrez l'IR (optionnel)\n5. Entrez la masse molaire (optionnel)\n6. Cliquez ➕ Ajouter / Modifier\n\n─────────────────────────────────────────────────────\n\nMODIFIER UN MATÉRIAU EXISTANT\n\n1. Cliquez sur la ligne du matériau.\n2. Modifiez les champs souhaités.\n3. Cliquez ➕ Ajouter / Modifier pour sauvegarder.\n\n─────────────────────────────────────────────────────\n\nSUPPRIMER UN MATÉRIAU\n\n1. Cliquez sur la ligne.\n2. Cliquez 🗑 Supprimer.\n3. Confirmez.\n\n─────────────────────────────────────────────────────\n\nCRÉER UN MÉLANGE\n\nSi vous utilisez régulièrement un mélange de monomères, vous\npouvez l'enregistrer comme une entrée unique avec densité\npré-calculée.\n\n1. Cliquez ⊕ Créer un mélange.\n2. Sélectionnez chaque composant et entrez son wt.% (total = 100).\n3. Cliquez ⟳ Calculer la densité.\n4. Donnez un nom au mélange.\n5. Cliquez 💾 Enregistrer dans la BD.\n\n─────────────────────────────────────────────────────\n\nEXPORTER ET IMPORTER LA BASE DE DONNÉES\n\n  Export :  Dans l'éditeur → 📤 Exporter BD\n  Import :  Dans l'éditeur → 📥 Importer BD\n            Ajoute ou met à jour les entrées. Ne supprime jamais\n            les entrées existantes.\n\n─────────────────────────────────────────────────────\n\nOÙ EST STOCKÉ LE FICHIER ?\n\nEn .exe compilé :\n  %APPDATA%\\3DPrintingFormulator\\3dpformulator_materialsdatabase.json\n\nEn source Python :\n  Dans le même dossier que formulator.py\n", 'Forward Formulator': "\nLA FORMULATION DIRECTE\n\nUtilisez cet onglet lorsque VOUS décidez des quantités de chaque\nmatériau, et souhaitez que l'application calcule la composition.\n\n─────────────────────────────────────────────────────\n\nFLUX DE TRAVAIL\n\n1. Saisissez un composant (utilisez ▼ pour l'auto-complétion).\n2. Choisissez le Mode de saisie.\n3. Entrez la Valeur (et la Référence si nécessaire).\n4. Cliquez ➕ Ajouter.\n5. Répétez pour tous les composants.\n6. Cliquez ⚙ CALCULER.\n\n─────────────────────────────────────────────────────\n\nLES SIX MODES DE SAISIE\n\n────────────────────────────────────────\nMODE 1 :  Masse (g)\n────────────────────────────────────────\n  Entrez la masse exacte en grammes.\n  V = masse / densité\n\n  Exemple :  Al₂O₃  →  Masse (g)  →  200\n\n────────────────────────────────────────\nMODE 2 :  Volume (cm³)\n────────────────────────────────────────\n  Entrez le volume exact en cm³ (= mL).\n  m = V × densité\n\n────────────────────────────────────────\nMODE 3 :  wt.% par rapport à Référence\n────────────────────────────────────────\n  La masse de ce composant est un % de la masse d'un autre.\n  Spécifiez la Référence.\n\n  Formule :  masse_i = (valeur / 100) × masse_référence\n\n  Exemple :  Dispersant  →  2 wt.% par rapport à Al₂O₃\n             Si Al₂O₃ = 200 g → Dispersant = 4 g\n\n────────────────────────────────────────\nMODE 4 :  vol.% par rapport à Référence\n────────────────────────────────────────\n  Idem Mode 3 mais le pourcentage est en VOLUME.\n\n────────────────────────────────────────\nMODE 5 :  wt.% du Total\n────────────────────────────────────────\n  Ce composant est un % fixe de la masse TOTALE du lot.\n\n  ⚠  La somme de tous les wt.% du Total doit être < 100%.\n\n────────────────────────────────────────\nMODE 6 :  vol.% du Total\n────────────────────────────────────────\n  Idem Mode 5 en pourcentage de volume.\n\n  ⚠  La somme de tous les vol.% du Total doit être < 100%.\n\n─────────────────────────────────────────────────────\n\nCONSEILS\n\n  ✓  Vous pouvez librement combiner les six modes.\n  ✓  Utilisez ▼ pour le champ Référence — évite les fautes.\n  ✓  L'ordre des composants n'affecte pas les calculs.\n", 'Inverse Solver': "\nLE SOLVEUR INVERSE\n\nUtilisez cet onglet lorsque vous avez une CHARGE EN SOLIDES CIBLE\net souhaitez que l'application calcule les quantités.\n\n«Je veux 45 vol.% d'alumine» → l'appli vous dit combien de HDDA.\n\n─────────────────────────────────────────────────────\n\nBARRE CIBLE (haut de l'onglet)\n\n  • Valeur cible :  le pourcentage de charge souhaité (ex. 45)\n  • Mode :          vol.% ou wt.%\n\n  vol.%  →  Le Composant Principal = ce % du VOLUME TOTAL.\n  wt.%   →  Le Composant Principal = ce % de la MASSE TOTALE.\n\n─────────────────────────────────────────────────────\n\nLES SEPT TYPES DE RELATION\n\n────────────────────────────────────────\nRELATION 1 :  Principal (Primary)\n────────────────────────────────────────\n  La CÉRAMIQUE ou charge principale — le composant dont la charge\n  est ciblée. EXACTEMENT 1 par recette.\n\n  Exemple :  Al₂O₃  →  Primary  →  Masse (g)  →  200\n\n────────────────────────────────────────\nRELATION 2 :  Balance\n────────────────────────────────────────\n  Le SOLVANT ou MONOMÈRE dont la quantité est calculée par le\n  solveur. Au plus 1. Laissez Valeur = 0.\n\n────────────────────────────────────────\nRELATION 3 :  wt.% par rapport à Référence\n────────────────────────────────────────\n  La masse de ce composant est un % de la masse d'un autre.\n\n────────────────────────────────────────\nRELATION 4 :  vol.% par rapport à Référence\n────────────────────────────────────────\n  Idem en pourcentage de volume.\n\n────────────────────────────────────────\nRELATION 5 :  wt.% de la Suspension Totale\n────────────────────────────────────────\n  % fixe en masse du lot final total.\n  Résolu APRÈS le calcul de la Balance.\n\n  ⚠  Somme de tous les wt.% Suspension Totale < 100%.\n\n────────────────────────────────────────\nRELATION 6 :  vol.% de la Suspension Totale\n────────────────────────────────────────\n  Idem en pourcentage de volume.\n\n────────────────────────────────────────\nRELATION 7 :  Masse / Volume Indépendant\n────────────────────────────────────────\n  Quantité fixe qui ne se redimensionne pas.\n  Utile pour les petits additifs fixes.\n\n─────────────────────────────────────────────────────\n\nRÉSUMÉ DES RÈGLES\n\n  ✓  Exactement 1 Composant Principal requis.\n  ✓  Au plus 1 Balance. Laissez Valeur = 0.\n  ✓  Tous les noms de composants doivent être uniques.\n  ✓  Les noms de Référence doivent correspondre exactement.\n  ✓  wt.%/vol.% Suspension Totale < 100% en tout.\n\n─────────────────────────────────────────────────────\n\nEXEMPLE DE RECETTE TYPIQUE\n\n  Composant          Relation                       Valeur  Référence\n  ──────────────     ──────────────────────────     ─────   ──────────\n  Al₂O₃              Primary (Masse g)               200\n  HDDA               Balance                           0\n  TMP(EO)3TA         wt.% par rapport à               50    HDDA\n  DISPERBYK-111      wt.% par rapport à                2    Al₂O₃\n  BAPO               wt.% Suspension Totale            1\n  CQ                 wt.% Suspension Totale            0.5\n\n  Cible : 45 vol.%\n", 'Editing & Managing Components': "\nMODIFIER UN COMPOSANT\n\n1. Cliquez sur la ligne du composant (elle s'illumine en bleu).\n   Ses détails se chargent dans les champs de saisie.\n2. Effectuez vos modifications.\n3. Cliquez ✏ Modifier pour sauvegarder.\n\n⚠  Ne cliquez PAS sur ➕ Ajouter lors d'une modification —\n   cela créerait un doublon. Utilisez TOUJOURS ✏ Modifier.\n\n─────────────────────────────────────────────────────\n\nSUPPRIMER UN COMPOSANT\n\n1. Cliquez sur la ligne pour la sélectionner.\n2. Cliquez 🗑 Supprimer.\n\n─────────────────────────────────────────────────────\n\nRÉORGANISER LES COMPOSANTS\n\n1. Cliquez sur la ligne à déplacer.\n2. Cliquez ▲ Haut ou ▼ Bas.\n\nL'ordre affecte l'affichage dans le tableau et le rapport PDF.\nIl N'affecte PAS les calculs.\n\n─────────────────────────────────────────────────────\n\nEFFACER TOUTE LA RECETTE\n\nCliquez ✖ Tout effacer. Une confirmation sera demandée.\n\n⚠  Cette action est irréversible — enregistrez d'abord si\n   vous souhaitez conserver la recette actuelle.\n\n─────────────────────────────────────────────────────\n\nMODIFIER LE NOM DE LA RECETTE\n\nLe champ «Nom de la Recette / Fichier» se trouve en haut de\nla fenêtre. Cliquez et tapez un nouveau nom.\n\nIl se met à jour automatiquement lors d'un enregistrement\nou d'un chargement.\n", 'Save, Load & PDF Export': "\nENREGISTRER UNE RECETTE\n\nCliquez 💾 Enregistrer (en haut à droite de chaque onglet).\n\nLe fichier est enregistré au format .json.\n\nCe QUI EST enregistré :\n  ✓  Nom de la recette\n  ✓  Tous les composants, densités, modes, valeurs, références\n  ✓  Onglet actif\n  ✓  Valeur et mode cible (Solveur Inverse)\n\nCe QUI N'EST PAS enregistré :\n  ✗  Résultats calculés (recalculez après chargement)\n\n─────────────────────────────────────────────────────\n\nCHARGER UNE RECETTE\n\nCliquez 📂 Charger.\n\nSélectionnez un fichier .json. Tous les composants sont\nrestaurés. Le Nom de la Recette se met à jour depuis le\nnom du fichier.\n\n⚠  Après le chargement, appuyez sur ⚙ CALCULER ou\n   ⚙ RÉSOUDRE pour régénérer les résultats.\n\n─────────────────────────────────────────────────────\n\nEXPORTER EN PDF\n\nCliquez 📄 Exporter PDF.\n\nVous devez d'abord calculer/résoudre.\n\nLe rapport PDF comprend :\n  • Nom de la recette, date, informations développeur\n  • Tableau complet des composants\n  • Statistiques : Masse Totale · Volume Total · Densité\n  • Pour le Solveur Inverse : Cible · Charge atteinte\n\nFormaté pour impression sur papier A4.\n\n─────────────────────────────────────────────────────\n\nPARTAGER UN FICHIER\n\nCliquez 📤 Partager. Pas besoin d'enregistrer au préalable.\n\n  ✉ E-mail →  Ouvre Outlook avec le fichier en pièce jointe.\n  💬 Teams →  Ouvre l'Explorateur avec le fichier sélectionné.\n", 'Tips & Troubleshooting': "\n─────────────────────────────────────────────────────\nERREURS COURANTES ET COMMENT LES CORRIGER\n─────────────────────────────────────────────────────\n\nPROBLÈME :  Erreur du solveur ou volumes incorrects\n────────────────────────────────────────\n  Cause :  Valeur de densité incorrecte ou manquante.\n  Solution : Vérifiez chaque densité. Elle doit être en g/cm³.\n             Utilisez ▼ pour sélectionner depuis la base.\n\n─────────────────────────────────────────────────────\n\nPROBLÈME :  Erreur «Référence introuvable»\n──────────────────────────────────────\n  Cause :  Le nom de référence ne correspond à aucun composant.\n           Même un espace supplémentaire cause cette erreur.\n  Solution : Utilisez ▼ dans le champ Référence.\n\n─────────────────────────────────────────────────────\n\nPROBLÈME :  Erreur «Primary non trouvé»\n──────────────────────────────────────────\n  Cause :  Aucun composant n'a la Relation = Primary.\n  Solution : Sélectionnez la céramique → définissez Primary\n             → cliquez ✏ Modifier.\n\n─────────────────────────────────────────────────────\n\nPROBLÈME :  Résultat Balance négatif ou très grand\n──────────────────────────────────────────\n  Cause :  La charge cible peut être géométriquement impossible.\n  Solution : Réduisez le % cible ou les valeurs des autres\n             composants.\n\n─────────────────────────────────────────────────────\n\nPROBLÈME :  wt.% et vol.% ne totalisent pas 100%\n────────────────────────────────────────────────────\n  C'est NORMAL si certains composants sont en quantités\n  absolues (g ou cm³).\n\n─────────────────────────────────────────────────────\n\nPROBLÈME :  Chargé une recette mais résultats vides\n────────────────────────────────────────────────────\n  Solution : Appuyez sur ⚙ CALCULER ou ⚙ RÉSOUDRE après\n             le chargement.\n\n─────────────────────────────────────────────────────\nCONSEILS POUR UNE UTILISATION EFFICACE\n─────────────────────────────────────────────────────\n\n  ✓  Utilisez toujours ▼ pour le champ Composant.\n  ✓  Utilisez toujours ▼ pour le champ Référence.\n  ✓  Enregistrez avant d'expérimenter avec les valeurs.\n  ✓  Utilisez ⊕ Créer un mélange pour vos mélanges habituels.\n  ✓  Exportez un PDF après chaque formulation réussie.\n  ✓  La barre d'état en bas montre toujours la dernière action.\n  ✓  Survolez un bouton pour voir son info-bulle.\n", 'Settings & Accessibility': "\nPARAMÈTRES\n\nOuvrez-les via ⚙ Paramètres en bas de la barre latérale gauche.\n\n─────────────────────────────────────────────────────\n\nAPPARENCE\n\n────────────────────────────────────────\nLangue\n────────────────────────────────────────\n  Sélectionnez la langue de l'interface.\n  ✓  Prend effet immédiatement.\n\n────────────────────────────────────────\nTaille de police\n────────────────────────────────────────\n  Petit / Normal / Grand / Très Grand\n  ✓  Prend effet immédiatement.\n\n────────────────────────────────────────\nMode contraste élevé\n────────────────────────────────────────\n  Bascule vers un thème sombre.\n  ✓  Prend effet immédiatement.\n\n────────────────────────────────────────\nPalette daltonisme\n────────────────────────────────────────\n  Remplace rouge/vert par bleu/orange.\n  ✓  Prend effet immédiatement.\n\n─────────────────────────────────────────────────────\n\nCOMPORTEMENT\n\n────────────────────────────────────────\nConfirmation avant suppression\n────────────────────────────────────────\n  L'application demande confirmation avant de supprimer ou\n  d'effacer des composants.\n\n────────────────────────────────────────\nBoutons plus grands\n────────────────────────────────────────\n  Augmente le padding des boutons pour faciliter les clics.\n  ✓  Prend effet immédiatement.\n\n─────────────────────────────────────────────────────\n\nRESTAURER LES VALEURS PAR DÉFAUT\n\nCliquez «Restaurer les défauts» en bas à gauche.\n\n─────────────────────────────────────────────────────\n\nOÙ SONT STOCKÉS LES PARAMÈTRES ?\n\nEn .exe compilé :  %APPDATA%\\3DPrintingFormulator\\3dpformulator_usersettings.json\nEn source Python : Dans le même dossier que formulator.py\n", 'Formulae & Theory': "\nCette section explique les mathématiques utilisées par l'application.\nUtile pour vérifier manuellement les résultats.\n\n─────────────────────────────────────────────────────\nNOTATION\n─────────────────────────────────────────────────────\n\n  mᵢ         masse du composant i  [g]\n  Vᵢ         volume du composant i  [cm³]\n  ρᵢ         densité du composant i  [g/cm³]\n  M_tot      masse totale du lot  [g]\n  V_tot      volume total du lot  [cm³]\n  T          charge cible en fraction  (ex. 45% → T = 0.45)\n\n─────────────────────────────────────────────────────\nCONVERSIONS FONDAMENTALES\n─────────────────────────────────────────────────────\n\n  Volume depuis masse :    Vᵢ = mᵢ / ρᵢ\n  Masse depuis volume :    mᵢ = Vᵢ · ρᵢ\n\n─────────────────────────────────────────────────────\nTOTAUX ET COMPOSITION DU LOT\n─────────────────────────────────────────────────────\n\n  Masse totale :           M_tot = m₁ + m₂ + ... + mₙ\n  Volume total :           V_tot = V₁ + V₂ + ... + Vₙ\n  Densité théorique :      ρ_mix = M_tot / V_tot\n  Fraction massique :      wt.%ᵢ  = 100 · mᵢ / M_tot\n  Fraction volumique :     vol.%ᵢ = 100 · Vᵢ / V_tot\n\n─────────────────────────────────────────────────────\nFORMULATION DIRECTE — RÉSOLUTION DES MODES\n─────────────────────────────────────────────────────\n\n  Masse (g) :            mᵢ = valeur saisie\n  Volume (cm³) :         Vᵢ = valeur saisie\n  wt.% / Référence :     mᵢ = (valeur/100) · m_r\n  vol.% / Référence :    Vᵢ = (valeur/100) · V_r\n  wt.% du Total :        M_tot = M_abs / (1 − S),  mᵢ = (v/100)·M_tot\n  vol.% du Total :       V_tot = V_abs / (1 − S),  Vᵢ = (v/100)·V_tot\n\n─────────────────────────────────────────────────────\nSOLVEUR INVERSE — CALCUL DE LA BALANCE\n─────────────────────────────────────────────────────\n\n  Pour cible vol.% :\n    V_B = V_anc · (1 − F_pv) / T − V_anc − V_kn\n    m_B = V_B · ρ_B\n\n  Pour cible wt.% :\n    m_B = M_anc · (1 − F_pm) / T − M_anc − M_kn\n\n─────────────────────────────────────────────────────\nMÉLANGE IDÉAL (Créer un mélange)\n─────────────────────────────────────────────────────\n\n  1 / ρ_blend = Σ (wᵢ / ρᵢ)\n\n─────────────────────────────────────────────────────\nEXEMPLE COMPLET — RÉSOLUTION INVERSE\n─────────────────────────────────────────────────────\n\nRecette :  200 g Al₂O₃ (ρ = 3.987),  cible = 45 vol.%\n           Balance : HDDA (ρ = 1.010)\n           BAPO : 1 wt.% Suspension Totale\n\nÉtape 1 — Volume du Composant Principal :\n  V_anc = 200 / 3.987 = 50.16 cm³\n\nÉtape 2 — Balance :\n  V_B = 50.16 · (1/0.45 − 1) = 61.31 cm³\n  m_B = 61.31 × 1.010 = 61.92 g\n\nÉtape 3 — BAPO :\n  M_tot = 261.92 / 0.99 = 264.57 g\n  m_BAPO = 0.01 × 264.57 = 2.65 g\n\nÉtape 4 — Vérification :\n  V_tot = 50.16 + 61.31 + 2.23 = 113.70 cm³\n  vol.% Al₂O₃ = 50.16 / 113.70 × 100 = 44.1%\n"},
    "de": {'About': '\nTHE 3D PRINTING FORMULATOR  —  v1.0\nVon Dr. Thanos Goulas\n📧  thanosgoulas@outlook.com\n\n─────────────────────────────────────────────────────\n\nWAS MACHT DIESE ANWENDUNG?\n\nSie berechnet die genauen Mengen jedes Materials in einer\nkeramischen Harz- oder Pastenformulierung — in Gramm und cm³ —\ndamit Sie Ihre Charge am Labortisch präzise abwiegen können.\n\nSie können in zwei Richtungen arbeiten:\n\n  VORWÄRTS →  Sie legen die Mengen fest. Die Anwendung berechnet\n               die endgültige Zusammensetzung (wt.%, vol.%,\n               Mischungsdichte).\n\n  INVERS   →  Sie legen die gewünschte Zusammensetzung fest\n               (z.B. 45 vol.% Aluminiumoxid). Die Anwendung\n               berechnet die Mengen für Sie.\n\n─────────────────────────────────────────────────────\n\nNAVIGATION\n\nDie linke Seitenleiste enthält:\n  • Inverser Löser       — zur Registerkarte wechseln\n  • Vorwärtsberechnung   — zur Registerkarte wechseln\n  • Materialdatenbank    — Datenbankassistent öffnen\n  • Hilfe                — dieses Handbuch öffnen\n  • Einstellungen        — Einstellungsfenster öffnen\n\nDie obere Leiste jeder Registerkarte enthält:\n  • Rezept- / Dateiname\n  • 💾 Speichern · 📂 Laden · 📄 PDF exportieren · 📤 Teilen\n\n─────────────────────────────────────────────────────\n\nMATERIALDATENBANK\n\nDie Datenbank enthält ~200 Materialien (Keramiken, Monomere,\nPhotoinitiatoren, Dispergiermittel, Lösungsmittel usw.) —\nmit Dichte, Brechungsindex und Molmasse.\n\n─────────────────────────────────────────────────────\n\nHAFTUNGSAUSSCHLUSS\n\nDichtewerte stammen aus Sigma-Aldrich, PubChem, NIST, CRC\nHandbook und Herstellerdatenblättern.\n\n⚠  Die Dichte kann je nach Reinheitsgrad, Temperatur und\n   Lieferanten variieren. Überprüfen Sie stets das SDB Ihres\n   Materials vor dem Einsatz in kritischen Formulierungen.\n\n─────────────────────────────────────────────────────\n\nFEEDBACK & FEHLERMELDUNGEN\n\n📧  thanosgoulas@outlook.com\n', 'Quick Start Guide': '\nNEU? BEGINNEN SIE HIER.\n\nDiese Anleitung führt Sie durch ein vollständiges Beispiel mit\ndem Inversen Löser.\n\n─────────────────────────────────────────────────────\n\nBEISPIELREZEPT\n\n  Ziel :     45 vol.% Al₂O₃ in HDDA-Monomer\n  Charge :   200 g Aluminiumoxid\n  Additiv :  1 wt.% BAPO-Photoinitiator auf die Gesamtcharge\n\n─────────────────────────────────────────────────────\n\nSCHRITT 1 — Benennen Sie Ihr Rezept\n\nKlicken Sie oben im Fenster auf «Rezept- / Dateiname» und geben\nSie einen Namen ein, z.B.:  Al2O3 45vol% HDDA\n\n─────────────────────────────────────────────────────\n\nSCHRITT 2 — Öffnen Sie den Inversen Löser\n\nKlicken Sie in der linken Seitenleiste auf «Inverser Löser».\n\n─────────────────────────────────────────────────────\n\nSCHRITT 3 — Ziel festlegen\n\nIn der ZIEL-Zeile oben:\n  • Geben Sie  45  in das Zahlenfeld ein.\n  • Wählen Sie  vol.%  aus der Dropdown-Liste.\n\n─────────────────────────────────────────────────────\n\nSCHRITT 4 — Keramik als PRIMÄRKOMPONENTE hinzufügen\n\nIn der Eingabezeile:\n  • Komponente :   ▼ klicken, «Al2O3» eingeben, auswählen.\n                   Dichte wird automatisch eingetragen.\n  • Beziehung :    Primary wählen\n  • Primärmenge :  Masse (g) wählen\n  • Wert :         200 eingeben\n\nKlicken Sie ➕ Hinzufügen.\n\n─────────────────────────────────────────────────────\n\nSCHRITT 5 — Monomer als BALANCE hinzufügen\n\n  • Komponente :  ▼ klicken, «HDDA» eingeben, auswählen.\n  • Beziehung :   Balance wählen\n  • Wert :        0 lassen (Löser berechnet den Wert)\n\nKlicken Sie ➕ Hinzufügen.\n\n─────────────────────────────────────────────────────\n\nSCHRITT 6 — Photoinitiator hinzufügen\n\n  • Komponente :  ▼ klicken, «BAPO» eingeben, auswählen.\n  • Beziehung :   wt.% of Total Suspension wählen\n  • Wert :        1 eingeben\n\nKlicken Sie ➕ Hinzufügen.\n\n─────────────────────────────────────────────────────\n\nSCHRITT 7 — Lösen\n\nKlicken Sie ⚙ LÖSEN.\n\nDie Tabelle wird mit Masse und Volumen jeder Komponente gefüllt.\n\n─────────────────────────────────────────────────────\n\nSCHRITT 8 — Speichern und exportieren\n\n  💾 Speichern      →  Rezept für spätere Verwendung speichern.\n  📄 PDF exportieren →  A4-Bericht für das Laborbuch.\n  📤 Teilen         →  Per E-Mail oder Teams senden.\n', 'The Materials Database': '\nDIE MATERIALDATENBANK\n\nDie Datenbank speichert die physikalischen Eigenschaften jedes\nMaterials: Dichte (g/cm³), Brechungsindex (BI) und Molmasse\n(g/mol).\n\n─────────────────────────────────────────────────────\n\nMATERIAL SUCHEN\n\nIm Feld Komponente auf ▼ klicken. Ein Dropdown-Bereich zeigt\nalle Materialien.\n\n  • Liste durchscrollen, ODER\n  • Tippen, um zu filtern — Suche im Akronym UND vollständigen\n    Namen gleichzeitig.\n\n─────────────────────────────────────────────────────\n\nDATENBANKASSISTENT ÖFFNEN\n\nKlicken Sie auf «🗃 Materialdatenbank» unten in der Seitenleiste.\n\n─────────────────────────────────────────────────────\n\nNEUES MATERIAL HINZUFÜGEN\n\n1. Akronym eingeben\n2. Vollständigen Namen eingeben (optional)\n3. Dichte in g/cm³ eingeben  ← PFLICHTFELD\n4. BI eingeben (optional)\n5. Molmasse eingeben (optional)\n6. Klicken ➕ Hinzufügen / Aktualisieren\n\n─────────────────────────────────────────────────────\n\nBESTEHENDES MATERIAL BEARBEITEN\n\n1. Auf die Zeile des Materials klicken.\n2. Gewünschte Felder ändern.\n3. ➕ Hinzufügen / Aktualisieren klicken.\n\n─────────────────────────────────────────────────────\n\nMATERIAL LÖSCHEN\n\n1. Zeile anklicken.\n2. 🗑 Löschen klicken.\n3. Bestätigen.\n\n─────────────────────────────────────────────────────\n\nMISCHUNG ERSTELLEN\n\nWenn Sie regelmäßig ein Monomergemisch verwenden, können Sie es\nals einzelnen Eintrag mit vorberechneter Dichte speichern.\n\n1. ⊕ Mischung erstellen klicken.\n2. Jede Komponente und deren wt.% eingeben (Summe = 100).\n3. ⟳ Dichte berechnen klicken.\n4. Namen für die Mischung vergeben.\n5. 💾 In DB speichern klicken.\n\n─────────────────────────────────────────────────────\n\nDATENBANK EXPORTIEREN UND IMPORTIEREN\n\n  Export :  Im Editor → 📤 DB exportieren\n  Import :  Im Editor → 📥 DB importieren\n            Fügt Einträge hinzu oder aktualisiert sie.\n            Löscht nie bestehende Einträge.\n\n─────────────────────────────────────────────────────\n\nWO WIRD DIE DATENBANKDATEI GESPEICHERT?\n\nAls kompilierte .exe :\n  %APPDATA%\\3DPrintingFormulator\\3dpformulator_materialsdatabase.json\n\nAls Python-Quellcode :\n  Im gleichen Ordner wie formulator.py\n', 'Forward Formulator': '\nDIE VORWÄRTSBERECHNUNG\n\nVerwenden Sie diese Registerkarte, wenn SIE entscheiden, wie\nviel von jedem Material Sie verwenden möchten, und die Anwendung\ndie Zusammensetzung berechnen soll.\n\n─────────────────────────────────────────────────────\n\nARBEITSABLAUF\n\n1. Komponentenname eingeben (▼ für Autovervollständigung).\n2. Eingabemodus wählen.\n3. Wert eingeben (und Referenz falls erforderlich).\n4. ➕ Hinzufügen klicken.\n5. Für alle Komponenten wiederholen.\n6. ⚙ BERECHNEN klicken.\n\n─────────────────────────────────────────────────────\n\nDIE SECHS EINGABEMODI\n\n────────────────────────────────────────\nMODUS 1 :  Masse (g)\n────────────────────────────────────────\n  Exakte Masse in Gramm eingeben.\n  V = Masse / Dichte\n\n  Beispiel :  Al₂O₃  →  Masse (g)  →  200\n\n────────────────────────────────────────\nMODUS 2 :  Volumen (cm³)\n────────────────────────────────────────\n  Exaktes Volumen in cm³ eingeben.\n  m = V × Dichte\n\n────────────────────────────────────────\nMODUS 3 :  wt.% zur Referenz\n────────────────────────────────────────\n  Masse dieser Komponente ist ein % der Masse einer anderen.\n  Referenzfeld ausfüllen.\n\n  Formel :  Masse_i = (Wert / 100) × Masse_Referenz\n\n────────────────────────────────────────\nMODUS 4 :  vol.% zur Referenz\n────────────────────────────────────────\n  Wie Modus 3, aber Prozentsatz in VOLUMEN.\n\n────────────────────────────────────────\nMODUS 5 :  wt.% des Gesamtgewichts\n────────────────────────────────────────\n  Fester % der GESAMTMASSE des Batches.\n\n  ⚠  Summe aller wt.% Gesamtgewicht muss < 100% sein.\n\n────────────────────────────────────────\nMODUS 6 :  vol.% des Gesamtvolumens\n────────────────────────────────────────\n  Wie Modus 5 als Volumenprozent.\n\n  ⚠  Summe aller vol.% Gesamtvolumen muss < 100% sein.\n\n─────────────────────────────────────────────────────\n\nTIPPS\n\n  ✓  Alle sechs Modi können frei kombiniert werden.\n  ✓  ▼ im Referenzfeld nutzen — vermeidet Tippfehler.\n  ✓  Die Reihenfolge der Komponenten beeinflusst keine\n     Berechnungen.\n', 'Inverse Solver': '\nDER INVERSE LÖSER\n\nVerwenden Sie diese Registerkarte, wenn Sie eine ZIEL-FESTSTOFF-\nBELADUNG haben und die Anwendung die Mengen berechnen soll.\n\n«Ich möchte 45 vol.% Aluminiumoxid» → die App sagt Ihnen,\nwie viel HDDA benötigt wird.\n\n─────────────────────────────────────────────────────\n\nZIEL-LEISTE (oben auf der Registerkarte)\n\n  • Zielwert :  gewünschter Beladungsprozentsatz (z.B. 45)\n  • Modus :     vol.% oder wt.%\n\n  vol.%  →  Primärkomponente = dieser % des GESAMTVOLUMENS.\n  wt.%   →  Primärkomponente = dieser % der GESAMTMASSE.\n\n─────────────────────────────────────────────────────\n\nDIE SIEBEN BEZIEHUNGSTYPEN\n\n────────────────────────────────────────\nBEZIEHUNG 1 :  Primär (Primary)\n────────────────────────────────────────\n  Die KERAMIK oder Hauptfüllstoff. GENAU 1 pro Rezept.\n\n  Beispiel :  Al₂O₃  →  Primary  →  Masse (g)  →  200\n\n────────────────────────────────────────\nBEZIEHUNG 2 :  Balance\n────────────────────────────────────────\n  Das LÖSUNGSMITTEL oder MONOMER, dessen Menge der Löser\n  berechnet. Höchstens 1. Wert = 0 lassen.\n\n────────────────────────────────────────\nBEZIEHUNG 3 :  wt.% zur Referenz\n────────────────────────────────────────\n  Masse dieser Komponente = % der Masse einer anderen.\n\n────────────────────────────────────────\nBEZIEHUNG 4 :  vol.% zur Referenz\n────────────────────────────────────────\n  Wie oben, als Volumenprozent.\n\n────────────────────────────────────────\nBEZIEHUNG 5 :  wt.% der Gesamtsuspension\n────────────────────────────────────────\n  Fester Massenprozentsatz der gesamten Endsuspension.\n  Wird NACH der Balance berechnet.\n\n  ⚠  Summe aller wt.% Gesamtsuspension < 100%.\n\n────────────────────────────────────────\nBEZIEHUNG 6 :  vol.% der Gesamtsuspension\n────────────────────────────────────────\n  Wie oben, als Volumenprozent.\n\n────────────────────────────────────────\nBEZIEHUNG 7 :  Unabhängige Masse / Volumen\n────────────────────────────────────────\n  Feste Menge, die sich nicht skaliert.\n  Nützlich für kleine feste Additive.\n\n─────────────────────────────────────────────────────\n\nREGELÜBERSICHT\n\n  ✓  Genau 1 Primärkomponente erforderlich.\n  ✓  Höchstens 1 Balance. Wert = 0 lassen.\n  ✓  Alle Komponentennamen müssen eindeutig sein.\n  ✓  Referenznamen müssen exakt übereinstimmen.\n  ✓  wt.%/vol.% Gesamtsuspension zusammen < 100%.\n\n─────────────────────────────────────────────────────\n\nTYPISCHES REZEPTBEISPIEL\n\n  Komponente         Beziehung                      Wert   Referenz\n  ──────────────     ──────────────────────────     ─────  ──────────\n  Al₂O₃              Primary (Masse g)               200\n  HDDA               Balance                           0\n  TMP(EO)3TA         wt.% zur                          50   HDDA\n  DISPERBYK-111      wt.% zur                           2   Al₂O₃\n  BAPO               wt.% Gesamtsuspension              1\n  CQ                 wt.% Gesamtsuspension              0.5\n\n  Ziel: 45 vol.%\n', 'Editing & Managing Components': '\nKOMPONENTE BEARBEITEN\n\n1. Auf die Komponentenzeile klicken (blau hervorgehoben).\n   Details werden in den Eingabefeldern geladen.\n2. Änderungen vornehmen.\n3. ✏ Aktualisieren klicken.\n\n⚠  Beim Bearbeiten NICHT auf ➕ Hinzufügen klicken — das würde\n   ein Duplikat erstellen. Immer ✏ Aktualisieren verwenden.\n\n─────────────────────────────────────────────────────\n\nKOMPONENTE ENTFERNEN\n\n1. Zeile anklicken.\n2. 🗑 Entfernen klicken.\n\n─────────────────────────────────────────────────────\n\nKOMPONENTEN NEU ANORDNEN\n\n1. Zeile anklicken.\n2. ▲ Hoch oder ▼ Runter klicken.\n\nDie Reihenfolge beeinflusst Tabelle und PDF-Bericht.\nBerechnungen werden NICHT beeinflusst.\n\n─────────────────────────────────────────────────────\n\nGESAMTES REZEPT LÖSCHEN\n\n✖ Alle löschen klicken. Bestätigung wird angefragt.\n\n⚠  Kann nicht rückgängig gemacht werden — vorher speichern.\n\n─────────────────────────────────────────────────────\n\nREZEPTNAME ÄNDERN\n\nDas Feld «Rezept- / Dateiname» befindet sich oben im Fenster.\nKlicken und neuen Namen eingeben.\n\nEs wird beim Speichern/Laden automatisch aktualisiert.\n', 'Save, Load & PDF Export': '\nREZEPT SPEICHERN\n\n💾 Speichern klicken (oben rechts auf jeder Registerkarte).\n\nDatei wird im .json-Format gespeichert.\n\nWas GESPEICHERT wird :\n  ✓  Rezeptname\n  ✓  Alle Komponenten, Dichten, Modi, Werte, Referenzen\n  ✓  Aktive Registerkarte\n  ✓  Zielwert und -modus (Inverser Löser)\n\nWas NICHT gespeichert wird :\n  ✗  Berechnete Ergebnisse (nach dem Laden neu berechnen)\n\n─────────────────────────────────────────────────────\n\nREZEPT LADEN\n\n📂 Laden klicken. .json-Datei auswählen.\n\n⚠  Nach dem Laden ⚙ BERECHNEN oder ⚙ LÖSEN drücken.\n\n─────────────────────────────────────────────────────\n\nALS PDF EXPORTIEREN\n\n📄 PDF exportieren klicken.\n\nZuerst berechnen/lösen.\n\nDer PDF-Bericht enthält :\n  • Rezeptname, Datum, Entwicklerinformationen\n  • Vollständige Komponententabelle\n  • Zusammenfassung : Gesamtmasse · Gesamtvolumen · Dichte\n  • Für Inversen Löser : Ziel · Erreichte Beladung\n\nFormatiert für A4-Ausdruck.\n\n─────────────────────────────────────────────────────\n\nDATEI TEILEN\n\n📤 Teilen klicken. Kein vorheriges Speichern erforderlich.\n\n  ✉ E-Mail →  Öffnet Outlook mit angehängter Datei.\n  💬 Teams →  Öffnet Explorer mit ausgewählter Datei.\n', 'Tips & Troubleshooting': '\n─────────────────────────────────────────────────────\nHÄUFIGE FEHLER UND LÖSUNGEN\n─────────────────────────────────────────────────────\n\nPROBLEM :  Löserfehler oder falsche Volumen\n────────────────────────────────────────\n  Ursache :  Falscher oder fehlender Dichtewert.\n  Lösung :   Jede Dichte prüfen. Muss in g/cm³ sein.\n             ▼ zum Auswählen aus der Datenbank verwenden.\n\n─────────────────────────────────────────────────────\n\nPROBLEM :  Fehler «Referenz nicht gefunden»\n──────────────────────────────────────\n  Ursache :  Referenzname stimmt mit keiner Komponente überein.\n  Lösung :   ▼ im Referenzfeld verwenden.\n\n─────────────────────────────────────────────────────\n\nPROBLEM :  Fehler «Primary nicht gefunden»\n──────────────────────────────────────────\n  Ursache :  Keine Komponente hat Beziehung = Primary.\n  Lösung :   Keramik auswählen → Primary setzen →\n             ✏ Aktualisieren klicken.\n\n─────────────────────────────────────────────────────\n\nPROBLEM :  Balance-Ergebnis negativ oder sehr groß\n──────────────────────────────────────────\n  Ursache :  Zielbeladung geometrisch unmöglich.\n  Lösung :   Ziel-% reduzieren oder Werte anderer\n             Komponenten verringern.\n\n─────────────────────────────────────────────────────\n\nPROBLEM :  wt.% und vol.% summieren nicht zu 100%\n────────────────────────────────────────────────────\n  NORMAL, wenn Komponenten in absoluten Mengen angegeben sind.\n\n─────────────────────────────────────────────────────\n\nPROBLEM :  Rezept geladen, aber Ergebnisse leer\n────────────────────────────────────────────────\n  Lösung :   ⚙ BERECHNEN oder ⚙ LÖSEN nach dem Laden drücken.\n\n─────────────────────────────────────────────────────\nTIPPS FÜR EFFIZIENTE NUTZUNG\n─────────────────────────────────────────────────────\n\n  ✓  Immer ▼ im Komponentenfeld verwenden.\n  ✓  Immer ▼ im Referenzfeld verwenden.\n  ✓  Rezept speichern, bevor Sie mit Werten experimentieren.\n  ✓  ⊕ Mischung erstellen für regelmäßig verwendete Mischungen.\n  ✓  Nach jeder erfolgreichen Formulierung PDF exportieren.\n  ✓  Statusleiste unten zeigt immer die letzte Aktion.\n  ✓  Maus über Schaltflächen für Tooltip-Beschreibung halten.\n', 'Settings & Accessibility': '\nEINSTELLUNGEN\n\nÖffnen über ⚙ Einstellungen unten in der linken Seitenleiste.\n\n─────────────────────────────────────────────────────\n\nERSCHEINUNGSBILD\n\n────────────────────────────────────────\nSprache\n────────────────────────────────────────\n  UI-Sprache aus dem Dropdown wählen.\n  ✓  Wirkt sofort.\n\n────────────────────────────────────────\nSchriftgröße\n────────────────────────────────────────\n  Klein / Normal / Groß / Sehr Groß\n  ✓  Wirkt sofort.\n\n────────────────────────────────────────\nHoher Kontrast\n────────────────────────────────────────\n  Dunkles Design aktivieren.\n  ✓  Wirkt sofort.\n\n────────────────────────────────────────\nFarbblinden-Palette\n────────────────────────────────────────\n  Ersetzt Rot/Grün durch Blau/Orange.\n  ✓  Wirkt sofort.\n\n─────────────────────────────────────────────────────\n\nVERHALTEN\n\n────────────────────────────────────────\nBestätigung vor dem Löschen\n────────────────────────────────────────\n  Anwendung fragt vor dem Entfernen oder Leeren.\n\n────────────────────────────────────────\nGrößere Schaltflächen\n────────────────────────────────────────\n  Mehr Abstand in Schaltflächen für einfacheres Klicken.\n  ✓  Wirkt sofort.\n\n─────────────────────────────────────────────────────\n\nSTANDARD WIEDERHERSTELLEN\n\n«Standard wiederherstellen» unten links im Einstellungsfenster.\n\n─────────────────────────────────────────────────────\n\nWO WERDEN EINSTELLUNGEN GESPEICHERT?\n\nAls .exe :      %APPDATA%\\3DPrintingFormulator\\3dpformulator_usersettings.json\nAls Quellcode : Im gleichen Ordner wie formulator.py\n', 'Formulae & Theory': '\nDieser Abschnitt erläutert die von der Anwendung verwendete\nMathematik. Nützlich zur manuellen Überprüfung der Ergebnisse.\n\n─────────────────────────────────────────────────────\nNOTATION\n─────────────────────────────────────────────────────\n\n  mᵢ         Masse der Komponente i  [g]\n  Vᵢ         Volumen der Komponente i  [cm³]\n  ρᵢ         Dichte der Komponente i  [g/cm³]\n  M_tot      Gesamtmasse des Batches  [g]\n  V_tot      Gesamtvolumen des Batches  [cm³]\n  T          Zielbeladung als Bruch  (z.B. 45% → T = 0.45)\n\n─────────────────────────────────────────────────────\nGRUNDLEGENDE UMRECHNUNGEN\n─────────────────────────────────────────────────────\n\n  Volumen aus Masse :    Vᵢ = mᵢ / ρᵢ\n  Masse aus Volumen :    mᵢ = Vᵢ · ρᵢ\n\n─────────────────────────────────────────────────────\nBATCH-SUMMEN UND ZUSAMMENSETZUNG\n─────────────────────────────────────────────────────\n\n  Gesamtmasse :          M_tot = m₁ + m₂ + ... + mₙ\n  Gesamtvolumen :        V_tot = V₁ + V₂ + ... + Vₙ\n  Theoretische Dichte :  ρ_mix = M_tot / V_tot\n  Massenanteil :         wt.%ᵢ  = 100 · mᵢ / M_tot\n  Volumenanteil :        vol.%ᵢ = 100 · Vᵢ / V_tot\n\n─────────────────────────────────────────────────────\nVORWÄRTSBERECHNUNG — AUFLÖSUNG DER MODI\n─────────────────────────────────────────────────────\n\n  Masse (g) :          mᵢ = eingegebener Wert\n  Volumen (cm³) :      Vᵢ = eingegebener Wert\n  wt.% zur Referenz :  mᵢ = (Wert/100) · m_r\n  vol.% zur Referenz : Vᵢ = (Wert/100) · V_r\n  wt.% Gesamt :        M_tot = M_abs/(1−S),  mᵢ = (W/100)·M_tot\n  vol.% Gesamt :       V_tot = V_abs/(1−S),  Vᵢ = (W/100)·V_tot\n\n─────────────────────────────────────────────────────\nINVERSER LÖSER — BALANCE-BERECHNUNG\n─────────────────────────────────────────────────────\n\n  Für vol.%-Ziel :\n    V_B = V_anc · (1 − F_pv) / T − V_anc − V_kn\n    m_B = V_B · ρ_B\n\n  Für wt.%-Ziel :\n    m_B = M_anc · (1 − F_pm) / T − M_anc − M_kn\n\n─────────────────────────────────────────────────────\nIDEALE MISCHUNG (Mischung erstellen)\n─────────────────────────────────────────────────────\n\n  1 / ρ_blend = Σ (wᵢ / ρᵢ)\n\n─────────────────────────────────────────────────────\nVOLLSTÄNDIGES BERECHNUNGSBEISPIEL\n─────────────────────────────────────────────────────\n\nRezept :  200 g Al₂O₃ (ρ = 3.987),  Ziel = 45 vol.%\n          Balance : HDDA (ρ = 1.010)\n          BAPO : 1 wt.% Gesamtsuspension\n\nSchritt 1 — Volumen Primärkomponente :\n  V_anc = 200 / 3.987 = 50.16 cm³\n\nSchritt 2 — Balance :\n  V_B = 50.16 · (1/0.45 − 1) = 61.31 cm³\n  m_B = 61.31 × 1.010 = 61.92 g\n\nSchritt 3 — BAPO :\n  M_tot = 261.92 / 0.99 = 264.57 g\n  m_BAPO = 0.01 × 264.57 = 2.65 g\n\nSchritt 4 — Prüfung :\n  V_tot = 50.16 + 61.31 + 2.23 = 113.70 cm³\n  vol.% Al₂O₃ = 50.16 / 113.70 × 100 = 44.1%\n'},
    "es": {'About': '\nTHE 3D PRINTING FORMULATOR  —  v1.0\nPor Dr. Thanos Goulas\n📧  thanosgoulas@outlook.com\n\n─────────────────────────────────────────────────────\n\n¿QUÉ HACE ESTA APLICACIÓN?\n\nCalcula las cantidades exactas de cada material en una formulación\nde resina o pasta cerámica — en gramos y cm³ — para pesar\ncon precisión cada lote en el laboratorio.\n\nPuede trabajar en dos direcciones:\n\n  DIRECTO  →  Usted decide las cantidades. La aplicación calcula\n               la composición final (wt.%, vol.%, densidad).\n\n  INVERSO  →  Usted decide la composición deseada (p.ej. 45 vol.%\n               alúmina). La aplicación calcula las cantidades.\n\n─────────────────────────────────────────────────────\n\nNAVEGACIÓN\n\nLa barra lateral izquierda contiene:\n  • Solver Inverso       — cambiar a la pestaña Inverso\n  • Formulación Directa  — cambiar a la pestaña Directa\n  • Base de Materiales   — abrir el editor de base de datos\n  • Ayuda                — abrir esta guía\n  • Configuración        — abrir ajustes\n\nLa barra superior de cada pestaña contiene:\n  • Nombre de Receta / Archivo\n  • 💾 Guardar · 📂 Cargar · 📄 Exportar PDF · 📤 Compartir\n\n─────────────────────────────────────────────────────\n\nBASE DE DATOS DE MATERIALES\n\nLa base de datos contiene ~200 materiales (cerámicas, monómeros,\nfotoiniciadores, dispersantes, disolventes, etc.) con densidad,\níndice de refracción y peso molecular.\n\n─────────────────────────────────────────────────────\n\nAVISO LEGAL\n\nLos valores de densidad provienen de Sigma-Aldrich, PubChem,\nNIST, CRC Handbook y fichas técnicas de fabricantes.\n\n⚠  La densidad puede variar según la calidad, pureza, temperatura\n   y proveedor. Verifique siempre con la FDS de su material.\n\n─────────────────────────────────────────────────────\n\nCOMENTARIOS Y ERRORES\n\n📧  thanosgoulas@outlook.com\n', 'Quick Start Guide': '\n¿NUEVO? EMPIECE AQUÍ.\n\nEsta guía le lleva a través de un ejemplo completo usando el\nSolver Inverso.\n\n─────────────────────────────────────────────────────\n\nRECETA DE EJEMPLO\n\n  Objetivo:  45 vol.% Al₂O₃ en monómero HDDA\n  Lote:      200 g de alúmina\n  Aditivo:   1 wt.% de fotoiniciador BAPO sobre el lote total\n\n─────────────────────────────────────────────────────\n\nPASO 1 — Nombre su receta\n\nHaga clic en «Nombre de Receta / Archivo» y escriba un nombre,\npor ejemplo:  Al2O3 45vol% HDDA\n\n─────────────────────────────────────────────────────\n\nPASO 2 — Abra el Solver Inverso\n\nHaga clic en «Solver Inverso» en la barra lateral izquierda.\n\n─────────────────────────────────────────────────────\n\nPASO 3 — Establezca el objetivo\n\nEn la fila OBJETIVO arriba:\n  • Escriba  45  en el campo.\n  • Seleccione  vol.%  en el desplegable.\n\n─────────────────────────────────────────────────────\n\nPASO 4 — Añada la cerámica como COMPONENTE PRINCIPAL\n\n  • Componente:   clic ▼, escriba «Al2O3», seleccione.\n                  La densidad se rellena automáticamente.\n  • Relación:     elija  Primary\n  • Cantidad:     elija  Masa (g)\n  • Valor:        escriba  200\n\nHaga clic ➕ Añadir.\n\n─────────────────────────────────────────────────────\n\nPASO 5 — Añada el monómero como BALANCE\n\n  • Componente:  clic ▼, escriba «HDDA», seleccione.\n  • Relación:    elija  Balance\n  • Valor:       deje  0  (el solver lo calcula)\n\nHaga clic ➕ Añadir.\n\n─────────────────────────────────────────────────────\n\nPASO 6 — Añada el fotoiniciador\n\n  • Componente:  clic ▼, escriba «BAPO», seleccione.\n  • Relación:    elija  wt.% of Total Suspension\n  • Valor:       escriba  1\n\nHaga clic ➕ Añadir.\n\n─────────────────────────────────────────────────────\n\nPASO 7 — Resolver\n\nHaga clic ⚙ RESOLVER.\n\nLa tabla se rellena con la masa y el volumen de cada componente.\n\n─────────────────────────────────────────────────────\n\nPASO 8 — Guardar y exportar\n\n  💾 Guardar      →  guarda la receta para uso futuro.\n  📄 Exportar PDF →  informe A4 para su cuaderno de laboratorio.\n  📤 Compartir    →  enviar por e-mail o Teams.\n', 'The Materials Database': '\nLA BASE DE DATOS DE MATERIALES\n\nAlmacena densidad (g/cm³), índice de refracción (IR) y peso\nmolecular (g/mol) de cada material.\n\n─────────────────────────────────────────────────────\n\nBUSCAR UN MATERIAL\n\nEn el campo Componente, haga clic en ▼.\n\n  • Desplácese por la lista, O\n  • Empiece a escribir para filtrar — busca en el acrónimo\n    Y el nombre completo simultáneamente.\n\n─────────────────────────────────────────────────────\n\nABRIR EL EDITOR\n\nHaga clic en «🗃 Base de Materiales» en la barra lateral.\n\n─────────────────────────────────────────────────────\n\nAÑADIR NUEVO MATERIAL\n\n1. Escriba el acrónimo\n2. Escriba el nombre completo (opcional)\n3. Introduzca la densidad en g/cm³  ← OBLIGATORIO\n4. Introduzca IR (opcional)\n5. Introduzca PM (opcional)\n6. Haga clic ➕ Añadir / Actualizar\n\n─────────────────────────────────────────────────────\n\nEDITAR MATERIAL EXISTENTE\n\n1. Haga clic en la fila del material.\n2. Modifique los campos deseados.\n3. Haga clic ➕ Añadir / Actualizar.\n\n─────────────────────────────────────────────────────\n\nELIMINAR MATERIAL\n\n1. Haga clic en la fila.\n2. Haga clic 🗑 Eliminar.\n3. Confirme.\n\n─────────────────────────────────────────────────────\n\nCREAR MEZCLA\n\n1. Haga clic ⊕ Crear mezcla.\n2. Seleccione cada componente e introduzca su wt.% (suma = 100).\n3. Haga clic ⟳ Calcular densidad.\n4. Dé nombre a la mezcla.\n5. Haga clic 💾 Guardar en BD.\n\n─────────────────────────────────────────────────────\n\nEXPORTAR E IMPORTAR\n\n  Exportar:  En el editor → 📤 Exportar BD\n  Importar:  En el editor → 📥 Importar BD\n             Añade o actualiza entradas. Nunca elimina existentes.\n', 'Forward Formulator': '\nFORMULACIÓN DIRECTA\n\nUse esta pestaña cuando USTED decide las cantidades de cada\nmaterial y quiere que la aplicación calcule la composición.\n\n─────────────────────────────────────────────────────\n\nFLUJO DE TRABAJO\n\n1. Introduzca un componente (use ▼ para autocompletar).\n2. Elija el Modo de entrada.\n3. Introduzca el Valor (y Referencia si es necesario).\n4. Haga clic ➕ Añadir.\n5. Repita para todos los componentes.\n6. Haga clic ⚙ CALCULAR.\n\n─────────────────────────────────────────────────────\n\nLOS SEIS MODOS DE ENTRADA\n\n────────────────────────────────────────\nMODO 1:  Masa (g)\n────────────────────────────────────────\n  Introduzca la masa exacta en gramos.\n  V = masa / densidad\n\n────────────────────────────────────────\nMODO 2:  Volumen (cm³)\n────────────────────────────────────────\n  Introduzca el volumen exacto en cm³.\n  m = V × densidad\n\n────────────────────────────────────────\nMODO 3:  wt.% respecto a Referencia\n────────────────────────────────────────\n  masa_i = (valor/100) × masa_referencia\n\n────────────────────────────────────────\nMODO 4:  vol.% respecto a Referencia\n────────────────────────────────────────\n  Igual que Modo 3 pero en VOLUMEN.\n\n────────────────────────────────────────\nMODO 5:  wt.% del Total\n────────────────────────────────────────\n  % fijo de la MASA TOTAL del lote.\n  ⚠  Suma de todos los wt.% del Total < 100%.\n\n────────────────────────────────────────\nMODO 6:  vol.% del Total\n────────────────────────────────────────\n  Igual que Modo 5 en porcentaje de volumen.\n  ⚠  Suma de todos los vol.% del Total < 100%.\n\n─────────────────────────────────────────────────────\n\nCONSEJOS\n\n  ✓  Puede combinar libremente los seis modos.\n  ✓  Use ▼ en el campo Referencia para evitar errores.\n  ✓  El orden de los componentes no afecta los cálculos.\n', 'Inverse Solver': '\nEL SOLVER INVERSO\n\nUse esta pestaña cuando tiene una CARGA DE SÓLIDOS OBJETIVO\ny quiere que la aplicación calcule las cantidades.\n\n«Quiero 45 vol.% de alúmina» → la app le dice cuánto HDDA.\n\n─────────────────────────────────────────────────────\n\nBARRA DE OBJETIVO\n\n  • Valor objetivo:  porcentaje de carga deseado (p.ej. 45)\n  • Modo:            vol.% o wt.%\n\n─────────────────────────────────────────────────────\n\nLOS SIETE TIPOS DE RELACIÓN\n\n────────────────────────────────────────\nRELACIÓN 1:  Principal (Primary)\n────────────────────────────────────────\n  La CERÁMICA o carga principal. EXACTAMENTE 1 por receta.\n\n────────────────────────────────────────\nRELACIÓN 2:  Balance\n────────────────────────────────────────\n  El DISOLVENTE o MONÓMERO cuya cantidad calcula el solver.\n  Como máximo 1. Deje Valor = 0.\n\n────────────────────────────────────────\nRELACIÓN 3:  wt.% respecto a Referencia\n────────────────────────────────────────\n  masa_i = (valor/100) × masa_referencia\n\n────────────────────────────────────────\nRELACIÓN 4:  vol.% respecto a Referencia\n────────────────────────────────────────\n  En porcentaje de volumen.\n\n────────────────────────────────────────\nRELACIÓN 5:  wt.% de la Suspensión Total\n────────────────────────────────────────\n  % fijo en masa del lote final.\n  ⚠  Suma < 100%.\n\n────────────────────────────────────────\nRELACIÓN 6:  vol.% de la Suspensión Total\n────────────────────────────────────────\n  En porcentaje de volumen.\n\n────────────────────────────────────────\nRELACIÓN 7:  Masa / Volumen Independiente\n────────────────────────────────────────\n  Cantidad fija que no se escala.\n\n─────────────────────────────────────────────────────\n\nRESUMEN DE REGLAS\n\n  ✓  Exactamente 1 Componente Principal requerido.\n  ✓  Como máximo 1 Balance. Valor = 0.\n  ✓  Todos los nombres de componentes únicos.\n  ✓  Nombres de Referencia deben coincidir exactamente.\n  ✓  wt.%/vol.% Suspensión Total < 100%.\n', 'Editing & Managing Components': '\nEDITAR UN COMPONENTE\n\n1. Haga clic en la fila del componente (resaltada en azul).\n2. Realice sus cambios.\n3. Haga clic ✏ Actualizar para guardar.\n\n⚠  NO haga clic en ➕ Añadir al editar — crearía un duplicado.\n   Use SIEMPRE ✏ Actualizar.\n\n─────────────────────────────────────────────────────\n\nELIMINAR UN COMPONENTE\n\n1. Haga clic en la fila.\n2. Haga clic 🗑 Eliminar.\n\n─────────────────────────────────────────────────────\n\nREORDENAR COMPONENTES\n\n1. Haga clic en la fila a mover.\n2. Haga clic ▲ Arriba o ▼ Abajo.\n\nEl orden afecta la tabla y el informe PDF.\nNO afecta los cálculos.\n\n─────────────────────────────────────────────────────\n\nBORRAR TODA LA RECETA\n\nHaga clic ✖ Borrar todo. Se pedirá confirmación.\n\n⚠  No se puede deshacer — guarde antes si quiere conservarla.\n\n─────────────────────────────────────────────────────\n\nCAMBIAR EL NOMBRE DE LA RECETA\n\nEl campo «Nombre de Receta / Archivo» está en la parte superior.\nSe actualiza automáticamente al guardar o cargar.\n', 'Save, Load & PDF Export': '\nGUARDAR UNA RECETA\n\nHaga clic 💾 Guardar (arriba a la derecha de cada pestaña).\nFormato .json.\n\nQué SE guarda:\n  ✓  Nombre de receta, componentes, densidades, modos, valores\n  ✓  Pestaña activa y objetivo (Solver Inverso)\n\nQué NO se guarda:\n  ✗  Resultados calculados (recalcule tras cargar)\n\n─────────────────────────────────────────────────────\n\nCARGAR UNA RECETA\n\nHaga clic 📂 Cargar. Seleccione un archivo .json.\n\n⚠  Pulse ⚙ CALCULAR o ⚙ RESOLVER después de cargar.\n\n─────────────────────────────────────────────────────\n\nEXPORTAR A PDF\n\nHaga clic 📄 Exportar PDF. Calcule/resuelva primero.\n\nEl informe incluye tabla completa, resumen y carga alcanzada.\nFormato A4.\n\n─────────────────────────────────────────────────────\n\nCOMPARTIR\n\nHaga clic 📤 Compartir. No es necesario guardar previamente.\n\n  ✉ E-mail →  Abre Outlook con el archivo adjunto.\n  💬 Teams  →  Abre el Explorador con el archivo seleccionado.\n', 'Tips & Troubleshooting': '\n─────────────────────────────────────────────────────\nERRORES COMUNES Y CÓMO RESOLVERLOS\n─────────────────────────────────────────────────────\n\nPROBLEMA:  Error del solver o volúmenes incorrectos\n  Causa:   Densidad incorrecta o ausente.\n  Solución: Use ▼ para seleccionar desde la base de datos.\n\n─────────────────────────────────────────────────────\n\nPROBLEMA:  «Referencia no encontrada»\n  Causa:   El nombre de referencia no coincide exactamente.\n  Solución: Use ▼ en el campo Referencia.\n\n─────────────────────────────────────────────────────\n\nPROBLEMA:  «Primary no encontrado»\n  Causa:   Ningún componente tiene Relación = Primary.\n  Solución: Seleccione la cerámica → establezca Primary\n            → haga clic ✏ Actualizar.\n\n─────────────────────────────────────────────────────\n\nPROBLEMA:  Resultado Balance negativo o muy grande\n  Causa:   La carga objetivo puede ser geométricamente imposible.\n  Solución: Reduzca el % objetivo o los valores de otros.\n\n─────────────────────────────────────────────────────\n\nPROBLEMA:  wt.% y vol.% no suman 100%\n  Normal si algunos componentes están en cantidades absolutas.\n\n─────────────────────────────────────────────────────\n\nPROBLEMA:  Cargué receta pero resultados vacíos\n  Solución: Pulse ⚙ CALCULAR o ⚙ RESOLVER tras cargar.\n\n─────────────────────────────────────────────────────\nCONSEJOS PARA USO EFICIENTE\n─────────────────────────────────────────────────────\n\n  ✓  Use siempre ▼ en el campo Componente.\n  ✓  Use siempre ▼ en el campo Referencia.\n  ✓  Guarde antes de experimentar con valores.\n  ✓  Use ⊕ Crear mezcla para mezclas habituales.\n  ✓  Exporte PDF tras cada formulación exitosa.\n  ✓  La barra de estado siempre muestra la última acción.\n', 'Settings & Accessibility': '\nCONFIGURACIÓN\n\nAbra mediante ⚙ Configuración en la barra lateral izquierda.\n\n─────────────────────────────────────────────────────\n\nAPARIENCIA\n\nIdioma — seleccione el idioma de la interfaz. ✓ Efecto inmediato.\nTamaño de fuente — Pequeño / Normal / Grande / Muy Grande.\nAlto contraste — tema oscuro. ✓ Efecto inmediato.\nPaleta daltonismo — azul/naranja en lugar de rojo/verde.\n\n─────────────────────────────────────────────────────\n\nCOMPORTAMIENTO\n\nConfirmación antes de eliminar — activa por defecto.\nBotones más grandes — para pantallas táctiles. ✓ Efecto inmediato.\n\n─────────────────────────────────────────────────────\n\nRESTAURAR VALORES PREDETERMINADOS\n\nHaga clic «Restaurar valores» abajo a la izquierda.\n\n─────────────────────────────────────────────────────\n\nDÓNDE SE GUARDAN LOS AJUSTES\n\n.exe:          %APPDATA%\\3DPrintingFormulator\\3dpformulator_usersettings.json\nPython fuente: En el mismo directorio que formulator.py\n', 'Formulae & Theory': '\nEsta sección explica las matemáticas usadas por la aplicación.\n\n─────────────────────────────────────────────────────\nNOTACIÓN\n─────────────────────────────────────────────────────\n\n  mᵢ    masa del componente i  [g]\n  Vᵢ    volumen del componente i  [cm³]\n  ρᵢ    densidad del componente i  [g/cm³]\n  M_tot masa total del lote  [g]\n  V_tot volumen total del lote  [cm³]\n  T     carga objetivo como fracción  (45% → T = 0.45)\n\n─────────────────────────────────────────────────────\nCONVERSIONES FUNDAMENTALES\n─────────────────────────────────────────────────────\n\n  Volumen desde masa:    Vᵢ = mᵢ / ρᵢ\n  Masa desde volumen:    mᵢ = Vᵢ · ρᵢ\n\n─────────────────────────────────────────────────────\nTOTALES Y COMPOSICIÓN\n─────────────────────────────────────────────────────\n\n  Masa total:       M_tot = m₁ + ... + mₙ\n  Volumen total:    V_tot = V₁ + ... + Vₙ\n  Densidad teórica: ρ_mix = M_tot / V_tot\n  Fracción másica:  wt.%ᵢ  = 100 · mᵢ / M_tot\n  Fracción vol.:    vol.%ᵢ = 100 · Vᵢ / V_tot\n\n─────────────────────────────────────────────────────\nSOLVER INVERSO — CÁLCULO DE BALANCE\n─────────────────────────────────────────────────────\n\n  Para vol.%:   V_B = V_anc·(1−F_pv)/T − V_anc − V_kn;  m_B = V_B·ρ_B\n  Para wt.%:    m_B = M_anc·(1−F_pm)/T − M_anc − M_kn\n\n─────────────────────────────────────────────────────\nMEZCLA IDEAL\n─────────────────────────────────────────────────────\n\n  1 / ρ_blend = Σ (wᵢ / ρᵢ)\n'},
    "it": {'About': "\nTHE 3D PRINTING FORMULATOR  —  v1.0\nDi Dr. Thanos Goulas\n📧  thanosgoulas@outlook.com\n\n─────────────────────────────────────────────────────\n\nCOSA FA QUESTA APPLICAZIONE?\n\nCalcola le quantità esatte di ogni materiale in una formulazione\ndi resina o pasta ceramica — in grammi e cm³ — per pesare con\nprecisione ogni lotto in laboratorio.\n\nSi può lavorare in due direzioni:\n\n  DIRETTO  →  Si decidono le quantità. L'applicazione calcola\n               la composizione finale (wt.%, vol.%, densità).\n\n  INVERSO  →  Si decide la composizione desiderata (es. 45 vol.%\n               allumina). L'applicazione calcola le quantità.\n\n─────────────────────────────────────────────────────\n\nNAVIGAZIONE\n\nLa barra laterale sinistra contiene:\n  • Solutore Inverso     — passare alla scheda Inverso\n  • Formulazione Diretta — passare alla scheda Diretta\n  • DB Materiali         — aprire l'editor del database\n  • Aiuto                — aprire questa guida\n  • Impostazioni         — aprire le impostazioni\n\nLa barra superiore di ogni scheda contiene:\n  • Nome Ricetta / File\n  • 💾 Salva · 📂 Carica · 📄 Esporta PDF · 📤 Condividi\n\n─────────────────────────────────────────────────────\n\nDATABASE DEI MATERIALI\n\nIl database contiene ~200 materiali (ceramiche, monomeri,\nfotoiniziatori, disperdenti, solventi, ecc.) con densità,\nindice di rifrazione e peso molecolare.\n\n─────────────────────────────────────────────────────\n\nAVVERTENZA\n\nI valori di densità provengono da Sigma-Aldrich, PubChem,\nNIST, CRC Handbook e schede tecniche dei produttori.\n\n⚠  La densità può variare in base a qualità, purezza, temperatura\n   e fornitore. Verificare sempre con la SDS del proprio materiale.\n\n─────────────────────────────────────────────────────\n\nFEEDBACK ED ERRORI\n\n📧  thanosgoulas@outlook.com\n", 'Quick Start Guide': "\nNUOVO? INIZIA QUI.\n\nQuesta guida ti accompagna attraverso un esempio completo usando\nil Solutore Inverso.\n\n─────────────────────────────────────────────────────\n\nRICETTA DI ESEMPIO\n\n  Obiettivo: 45 vol.% Al₂O₃ in monomero HDDA\n  Lotto:     200 g di allumina\n  Additivo:  1 wt.% di fotoiniziatore BAPO sul lotto totale\n\n─────────────────────────────────────────────────────\n\nPASSO 1 — Assegnare un nome alla ricetta\n\nFare clic su «Nome Ricetta / File» e digitare un nome,\nes.:  Al2O3 45vol% HDDA\n\n─────────────────────────────────────────────────────\n\nPASSO 2 — Aprire il Solutore Inverso\n\nFare clic su «Solutore Inverso» nella barra laterale.\n\n─────────────────────────────────────────────────────\n\nPASSO 3 — Impostare l'obiettivo\n\nNella riga OBIETTIVO in alto:\n  • Digitare  45  nel campo.\n  • Selezionare  vol.%  dall'elenco a discesa.\n\n─────────────────────────────────────────────────────\n\nPASSO 4 — Aggiungere la ceramica come COMPONENTE PRINCIPALE\n\n  • Componente:  clic ▼, digitare «Al2O3», selezionare.\n                 La densità si compila automaticamente.\n  • Relazione:   scegliere  Primary\n  • Quantità:    scegliere  Massa (g)\n  • Valore:      digitare  200\n\nFare clic ➕ Aggiungi.\n\n─────────────────────────────────────────────────────\n\nPASSO 5 — Aggiungere il monomero come BALANCE\n\n  • Componente:  clic ▼, digitare «HDDA», selezionare.\n  • Relazione:   scegliere  Balance\n  • Valore:      lasciare  0  (il solutore lo calcola)\n\nFare clic ➕ Aggiungi.\n\n─────────────────────────────────────────────────────\n\nPASSO 6 — Aggiungere il fotoiniziatore\n\n  • Componente:  clic ▼, digitare «BAPO», selezionare.\n  • Relazione:   scegliere  wt.% of Total Suspension\n  • Valore:      digitare  1\n\nFare clic ➕ Aggiungi.\n\n─────────────────────────────────────────────────────\n\nPASSO 7 — Risolvere\n\nFare clic ⚙ RISOLVI.\n\nLa tabella si popola con massa e volume di ogni componente.\n\n─────────────────────────────────────────────────────\n\nPASSO 8 — Salvare ed esportare\n\n  💾 Salva       →  salva la ricetta per uso futuro.\n  📄 Esporta PDF →  report A4 per il quaderno di laboratorio.\n  📤 Condividi   →  inviare via e-mail o Teams.\n", 'The Materials Database': "\nIL DATABASE DEI MATERIALI\n\nConserva densità (g/cm³), indice di rifrazione (IR) e peso\nmolecolare (g/mol) di ogni materiale.\n\n─────────────────────────────────────────────────────\n\nCERCARE UN MATERIALE\n\nNel campo Componente, fare clic su ▼.\n\n  • Scorrere la lista, OPPURE\n  • Iniziare a digitare per filtrare — cerca nell'acronimo\n    E nel nome completo contemporaneamente.\n\n─────────────────────────────────────────────────────\n\nAPRIRE L'EDITOR\n\nFare clic su «🗃 DB Materiali» nella barra laterale.\n\n─────────────────────────────────────────────────────\n\nAGGIUNGERE UN NUOVO MATERIALE\n\n1. Digitare l'acronimo\n2. Digitare il nome completo (opzionale)\n3. Inserire la densità in g/cm³  ← OBBLIGATORIO\n4. Inserire IR (opzionale)\n5. Inserire PM (opzionale)\n6. Fare clic ➕ Aggiungi / Aggiorna\n\n─────────────────────────────────────────────────────\n\nCREARE UNA MISCELA\n\n1. Fare clic ⊕ Crea miscela.\n2. Selezionare ogni componente e inserire il suo wt.% (totale = 100).\n3. Fare clic ⟳ Calcola densità.\n4. Assegnare un nome alla miscela.\n5. Fare clic 💾 Salva nel DB.\n", 'Forward Formulator': "\nFORMULAZIONE DIRETTA\n\nUsare questa scheda quando SI decide le quantità e si vuole\nche l'applicazione calcoli la composizione.\n\n─────────────────────────────────────────────────────\n\nFLUSSO DI LAVORO\n\n1. Inserire un componente (usare ▼ per il completamento).\n2. Scegliere la Modalità di input.\n3. Inserire il Valore (e il Riferimento se necessario).\n4. Fare clic ➕ Aggiungi.\n5. Ripetere per tutti i componenti.\n6. Fare clic ⚙ CALCOLA.\n\n─────────────────────────────────────────────────────\n\nLE SEI MODALITÀ DI INPUT\n\nMODO 1:  Massa (g) — massa esatta in grammi.\nMODO 2:  Volume (cm³) — volume esatto in cm³.\nMODO 3:  wt.% rispetto a Riferimento — massa_i = (val/100)·m_r\nMODO 4:  vol.% rispetto a Riferimento — volume.\nMODO 5:  wt.% del Totale — % fisso della massa totale.\n         ⚠  Somma < 100%.\nMODO 6:  vol.% del Totale — % fisso del volume totale.\n         ⚠  Somma < 100%.\n\n─────────────────────────────────────────────────────\n\nSUGGERIMENTI\n\n  ✓  Combinare liberamente tutti e sei i modi.\n  ✓  Usare ▼ nel campo Riferimento.\n  ✓  L'ordine dei componenti non influenza i calcoli.\n", 'Inverse Solver': "\nIL SOLUTORE INVERSO\n\nUsare questa scheda quando si ha un CARICO DI SOLIDI OBIETTIVO\ne si vuole che l'applicazione calcoli le quantità.\n\n«Voglio 45 vol.% di allumina» → l'app dice quanto HDDA serve.\n\n─────────────────────────────────────────────────────\n\nBARRA OBIETTIVO\n\n  • Valore obiettivo:  percentuale di carico desiderata (es. 45)\n  • Modo:              vol.% o wt.%\n\n─────────────────────────────────────────────────────\n\nI SETTE TIPI DI RELAZIONE\n\nRELAZIONE 1:  Principale (Primary) — CERAMICA o carica.\n              ESATTAMENTE 1 per ricetta.\nRELAZIONE 2:  Balance — solvente/monomero calcolato dal solutore.\n              Al massimo 1. Lasciare Valore = 0.\nRELAZIONE 3:  wt.% rispetto a Riferimento\nRELAZIONE 4:  vol.% rispetto a Riferimento\nRELAZIONE 5:  wt.% della Sospensione Totale  ⚠ Somma < 100%.\nRELAZIONE 6:  vol.% della Sospensione Totale  ⚠ Somma < 100%.\nRELAZIONE 7:  Massa / Volume Indipendente — quantità fissa.\n\n─────────────────────────────────────────────────────\n\nRIEPILOGO REGOLE\n\n  ✓  Esattamente 1 Componente Principale.\n  ✓  Al massimo 1 Balance. Valore = 0.\n  ✓  Nomi componenti unici.\n  ✓  Nomi Riferimento corrispondenza esatta.\n  ✓  wt.%/vol.% Sospensione Totale < 100%.\n", 'Editing & Managing Components': "\nMODIFICARE UN COMPONENTE\n\n1. Fare clic sulla riga (evidenziata in blu).\n2. Effettuare le modifiche.\n3. Fare clic ✏ Aggiorna per salvare.\n\n⚠  NON fare clic su ➕ Aggiungi durante la modifica.\n   Usare SEMPRE ✏ Aggiorna.\n\n─────────────────────────────────────────────────────\n\nRIMUOVERE UN COMPONENTE\n\n1. Fare clic sulla riga.\n2. Fare clic 🗑 Rimuovi.\n\n─────────────────────────────────────────────────────\n\nRIORDINARE I COMPONENTI\n\n1. Fare clic sulla riga da spostare.\n2. Fare clic ▲ Su o ▼ Giù.\n\nL'ordine influenza tabella e report PDF. NON i calcoli.\n\n─────────────────────────────────────────────────────\n\nCANCELLARE TUTTA LA RICETTA\n\nFare clic ✖ Cancella tutto. Verrà chiesta conferma.\n⚠  Irreversibile — salvare prima se necessario.\n", 'Save, Load & PDF Export': '\nSALVARE UNA RICETTA\n\nFare clic 💾 Salva. Formato .json.\n\nCosa VIENE salvato: nome, componenti, densità, modi, valori,\nscheda attiva, obiettivo.\nCosa NON viene salvato: risultati calcolati.\n\n─────────────────────────────────────────────────────\n\nCARICARE UNA RICETTA\n\nFare clic 📂 Carica. Selezionare un file .json.\n⚠  Premere ⚙ CALCOLA o ⚙ RISOLVI dopo il caricamento.\n\n─────────────────────────────────────────────────────\n\nESPORTARE IN PDF\n\nFare clic 📄 Esporta PDF. Calcolare/risolvere prima.\nReport include tabella completa, statistiche, carico raggiunto.\nFormato A4.\n\n─────────────────────────────────────────────────────\n\nCONDIVIDERE\n\nFare clic 📤 Condividi. Non è necessario salvare prima.\n  ✉ E-mail →  Apre Outlook con file allegato.\n  💬 Teams  →  Apre Esplora file con file selezionato.\n', 'Tips & Troubleshooting': "\n─────────────────────────────────────────────────────\nERRORI COMUNI E SOLUZIONI\n─────────────────────────────────────────────────────\n\nPROBLEMA:  Errore del solutore o volumi errati\n  Causa:   Valore di densità errato o mancante.\n  Soluzione: Usare ▼ per selezionare dalla base dati.\n\nPROBLEMA:  «Riferimento non trovato»\n  Soluzione: Usare ▼ nel campo Riferimento.\n\nPROBLEMA:  «Primary non trovato»\n  Soluzione: Selezionare la ceramica → impostare Primary\n             → fare clic ✏ Aggiorna.\n\nPROBLEMA:  Risultato Balance negativo o molto grande\n  Soluzione: Ridurre % obiettivo o valori degli altri componenti.\n\nPROBLEMA:  wt.% e vol.% non sommano 100%\n  Normale se alcuni componenti sono in quantità assolute.\n\nPROBLEMA:  Caricata ricetta ma risultati vuoti\n  Soluzione: Premere ⚙ CALCOLA o ⚙ RISOLVI dopo il caricamento.\n\n─────────────────────────────────────────────────────\nCONSIGLI PER L'USO EFFICIENTE\n─────────────────────────────────────────────────────\n\n  ✓  Usare sempre ▼ nel campo Componente.\n  ✓  Usare sempre ▼ nel campo Riferimento.\n  ✓  Salvare prima di sperimentare con i valori.\n  ✓  Usare ⊕ Crea miscela per miscele abituali.\n  ✓  Esportare PDF dopo ogni formulazione riuscita.\n  ✓  La barra di stato mostra sempre l'ultima azione.\n", 'Settings & Accessibility': '\nIMPOSTAZIONI\n\nAprire tramite ⚙ Impostazioni nella barra laterale.\n\n─────────────────────────────────────────────────────\n\nASPETTO\n\nLingua — selezionare la lingua interfaccia. ✓ Effetto immediato.\nDimensione carattere — Piccolo / Normale / Grande / Molto Grande.\nAlto contrasto — tema scuro. ✓ Effetto immediato.\nPalette daltonismo — blu/arancione invece di rosso/verde.\n\n─────────────────────────────────────────────────────\n\nCOMPORTAMENTO\n\nConferma prima di rimuovere — attivo per default.\nPulsanti più grandi — per schermi touch. ✓ Effetto immediato.\n\n─────────────────────────────────────────────────────\n\nRIPRISTINARE PREDEFINITI\n\nFare clic «Ripristina predefiniti» in basso a sinistra.\n', 'Formulae & Theory': "\nQuesta sezione spiega la matematica utilizzata dall'applicazione.\n\n─────────────────────────────────────────────────────\nNOTAZIONE\n─────────────────────────────────────────────────────\n\n  mᵢ    massa del componente i  [g]\n  Vᵢ    volume del componente i  [cm³]\n  ρᵢ    densità del componente i  [g/cm³]\n  M_tot massa totale del lotto  [g]\n  V_tot volume totale del lotto  [cm³]\n  T     carico obiettivo come frazione (45% → T = 0.45)\n\n─────────────────────────────────────────────────────\nCONVERSIONI\n\n  Vᵢ = mᵢ / ρᵢ     mᵢ = Vᵢ · ρᵢ\n\n─────────────────────────────────────────────────────\nTOTALI E COMPOSIZIONE\n\n  M_tot = Σmᵢ     V_tot = ΣVᵢ     ρ_mix = M_tot/V_tot\n  wt.%ᵢ = 100·mᵢ/M_tot     vol.%ᵢ = 100·Vᵢ/V_tot\n\n─────────────────────────────────────────────────────\nSOLUTORE INVERSO — CALCOLO BALANCE\n\n  vol.%:  V_B = V_anc·(1−F_pv)/T − V_anc − V_kn;  m_B = V_B·ρ_B\n  wt.%:   m_B = M_anc·(1−F_pm)/T − M_anc − M_kn\n\n─────────────────────────────────────────────────────\nMISCELA IDEALE\n\n  1/ρ_blend = Σ(wᵢ/ρᵢ)\n"},
    "nl": {'About': '\nTHE 3D PRINTING FORMULATOR  —  v1.0\nDoor Dr. Thanos Goulas\n📧  thanosgoulas@outlook.com\n\n─────────────────────────────────────────────────────\n\nWAT DOET DEZE APPLICATIE?\n\nBerekent de exacte hoeveelheden van elk materiaal in een\nkeramische hars- of pastenformulering — in grammen en cm³ —\nzodat u elke batch nauwkeurig kunt afwegen in het laboratorium.\n\nU kunt in twee richtingen werken:\n\n  VOORWAARTS →  U bepaalt de hoeveelheden. De applicatie berekent\n                 de eindsamenstelling (wt.%, vol.%, dichtheid).\n\n  INVERS     →  U bepaalt de gewenste samenstelling (bijv. 45\n                 vol.% aluminiumoxide). De applicatie berekent\n                 de hoeveelheden voor u.\n\n─────────────────────────────────────────────────────\n\nNAVIGATIE\n\nDe linker zijbalk bevat:\n  • Inverse Solver       — wisselen naar de Inverse tab\n  • Voorwaartse Form.    — wisselen naar de Voorwaartse tab\n  • Materialen DB        — database-editor openen\n  • Help                 — deze handleiding openen\n  • Instellingen         — instellingen openen\n\nDe bovenste balk van elke tab bevat:\n  • Recept- / Bestandsnaam\n  • 💾 Opslaan · 📂 Laden · 📄 PDF exporteren · 📤 Delen\n\n─────────────────────────────────────────────────────\n\nMATERIALENDATABASE\n\nDe database bevat ~200 materialen (keramieken, monomeren,\nfotoinitiatoren, dispergeermiddelen, oplosmiddelen, enz.)\nmet dichtheid, brekingsindex en molecuulgewicht.\n\n─────────────────────────────────────────────────────\n\nDISCLAIMER\n\nDichtheidswaarden zijn afkomstig van Sigma-Aldrich, PubChem,\nNIST, CRC Handbook en technische datasheets van fabrikanten.\n\n⚠  Dichtheid kan variëren met kwaliteit, zuiverheid, temperatuur\n   en leverancier. Verifieer altijd met het VIB van uw materiaal.\n\n─────────────────────────────────────────────────────\n\nFEEDBACK & FOUTMELDINGEN\n\n📧  thanosgoulas@outlook.com\n', 'Quick Start Guide': '\nNIEUW? BEGIN HIER.\n\nDeze handleiding begeleidt u door een volledig voorbeeld met\nde Inverse Solver.\n\n─────────────────────────────────────────────────────\n\nVOORBEELDRECEPT\n\n  Doel:    45 vol.% Al₂O₃ in HDDA-monomeer\n  Batch:   200 g aluminiumoxide\n  Additief: 1 wt.% BAPO foto-initiator op de totale batch\n\n─────────────────────────────────────────────────────\n\nSTAP 1 — Geef uw recept een naam\n\nKlik op «Recept- / Bestandsnaam» en typ een naam,\nbijv.:  Al2O3 45vol% HDDA\n\n─────────────────────────────────────────────────────\n\nSTAP 2 — Open de Inverse Solver\n\nKlik op «Inverse Solver» in de linker zijbalk.\n\n─────────────────────────────────────────────────────\n\nSTAP 3 — Stel het doel in\n\nIn de DOEL-rij bovenaan:\n  • Typ  45  in het veld.\n  • Selecteer  vol.%  uit de keuzelijst.\n\n─────────────────────────────────────────────────────\n\nSTAP 4 — Voeg de keramiek toe als PRIMAIR COMPONENT\n\n  • Component:  klik ▼, typ «Al2O3», selecteer.\n                Dichtheid wordt automatisch ingevuld.\n  • Relatie:    kies  Primary\n  • Hoeveelheid: kies  Massa (g)\n  • Waarde:     typ  200\n\nKlik ➕ Toevoegen.\n\n─────────────────────────────────────────────────────\n\nSTAP 5 — Voeg het monomeer toe als BALANCE\n\n  • Component:  klik ▼, typ «HDDA», selecteer.\n  • Relatie:    kies  Balance\n  • Waarde:     laat  0  staan (de solver berekent het)\n\nKlik ➕ Toevoegen.\n\n─────────────────────────────────────────────────────\n\nSTAP 6 — Voeg de foto-initiator toe\n\n  • Component:  klik ▼, typ «BAPO», selecteer.\n  • Relatie:    kies  wt.% of Total Suspension\n  • Waarde:     typ  1\n\nKlik ➕ Toevoegen.\n\n─────────────────────────────────────────────────────\n\nSTAP 7 — Oplossen\n\nKlik ⚙ OPLOSSEN.\n\nDe tabel wordt gevuld met massa en volume van elk component.\n\n─────────────────────────────────────────────────────\n\nSTAP 8 — Opslaan en exporteren\n\n  💾 Opslaan       →  recept bewaren voor later gebruik.\n  📄 PDF exporteren →  A4-rapport voor uw labjournal.\n  📤 Delen         →  versturen via e-mail of Teams.\n', 'The Materials Database': '\nDE MATERIALENDATABASE\n\nSlaat dichtheid (g/cm³), brekingsindex (BI) en molecuulgewicht\n(g/mol) op van elk materiaal.\n\n─────────────────────────────────────────────────────\n\nEEN MATERIAAL ZOEKEN\n\nIn het veld Component op ▼ klikken.\n\n  • Scrol door de lijst, OF\n  • Begin te typen om te filteren — zoekt in acroniem\n    EN volledige naam tegelijk.\n\n─────────────────────────────────────────────────────\n\nDE EDITOR OPENEN\n\nKlik op «🗃 Materialen DB» in de zijbalk.\n\n─────────────────────────────────────────────────────\n\nNIEUW MATERIAAL TOEVOEGEN\n\n1. Afkorting invoeren\n2. Volledige naam invoeren (optioneel)\n3. Dichtheid in g/cm³ invoeren  ← VERPLICHT\n4. BI invoeren (optioneel)\n5. Molecuulgewicht invoeren (optioneel)\n6. Klik ➕ Toevoegen / Bijwerken\n\n─────────────────────────────────────────────────────\n\nEEN MENGSEL MAKEN\n\n1. Klik ⊕ Mengsel maken.\n2. Selecteer elk component en voer wt.% in (totaal = 100).\n3. Klik ⟳ Dichtheid berekenen.\n4. Geef het mengsel een naam.\n5. Klik 💾 Opslaan in DB.\n', 'Forward Formulator': '\nVOORWAARTSE FORMULERING\n\nGebruik dit tabblad wanneer U de hoeveelheden bepaalt en de\napplicatie de samenstelling moet berekenen.\n\n─────────────────────────────────────────────────────\n\nWERKSTROOM\n\n1. Voer een component in (gebruik ▼ voor automatisch aanvullen).\n2. Kies de Invoermodus.\n3. Voer de Waarde in (en Referentie indien nodig).\n4. Klik ➕ Toevoegen.\n5. Herhaal voor alle componenten.\n6. Klik ⚙ BEREKENEN.\n\n─────────────────────────────────────────────────────\n\nDE ZES INVOERMODI\n\nMODUS 1:  Massa (g) — exacte massa in grammen.\nMODUS 2:  Volume (cm³) — exact volume in cm³.\nMODUS 3:  wt.% t.o.v. Referentie — massa_i = (waarde/100)·m_r\nMODUS 4:  vol.% t.o.v. Referentie — in volume.\nMODUS 5:  wt.% van Totaal — vast % van totale massa.\n          ⚠  Som < 100%.\nMODUS 6:  vol.% van Totaal — vast % van totaal volume.\n          ⚠  Som < 100%.\n\n─────────────────────────────────────────────────────\n\nTIPS\n\n  ✓  Combineer de zes modi vrij.\n  ✓  Gebruik ▼ in het Referentieveld.\n  ✓  Volgorde componenten beïnvloedt berekeningen niet.\n', 'Inverse Solver': '\nDE INVERSE SOLVER\n\nGebruik dit tabblad wanneer u een DOEL-VASTE-STOFBELADING\nheeft en de applicatie de hoeveelheden moet berekenen.\n\n«Ik wil 45 vol.% aluminiumoxide» → de app vertelt hoeveel HDDA.\n\n─────────────────────────────────────────────────────\n\nDOELBALK\n\n  • Doelwaarde:  gewenst belastingspercentage (bijv. 45)\n  • Modus:       vol.% of wt.%\n\n─────────────────────────────────────────────────────\n\nDE ZEVEN RELATIETYPEN\n\nRELATIE 1:  Primair (Primary) — KERAMIEK. PRECIES 1 per recept.\nRELATIE 2:  Balance — oplosmiddel/monomeer. Max 1. Waarde = 0.\nRELATIE 3:  wt.% t.o.v. Referentie\nRELATIE 4:  vol.% t.o.v. Referentie\nRELATIE 5:  wt.% van Totale Suspensie  ⚠ Som < 100%.\nRELATIE 6:  vol.% van Totale Suspensie  ⚠ Som < 100%.\nRELATIE 7:  Onafhankelijke Massa/Volume — vaste hoeveelheid.\n\n─────────────────────────────────────────────────────\n\nREGELOVERZICHT\n\n  ✓  Precies 1 Primair component vereist.\n  ✓  Maximaal 1 Balance. Waarde = 0.\n  ✓  Alle componentnamen uniek.\n  ✓  Referentienamen moeten exact overeenkomen.\n  ✓  wt.%/vol.% Totale Suspensie < 100%.\n', 'Editing & Managing Components': '\nEEN COMPONENT BEWERKEN\n\n1. Klik op de componentrij (blauw gemarkeerd).\n2. Breng uw wijzigingen aan.\n3. Klik ✏ Bijwerken om op te slaan.\n\n⚠  Klik NIET op ➕ Toevoegen bij bewerken — dat maakt een\n   duplicaat. Gebruik ALTIJD ✏ Bijwerken.\n\n─────────────────────────────────────────────────────\n\nEEN COMPONENT VERWIJDEREN\n\n1. Klik op de rij.\n2. Klik 🗑 Verwijderen.\n\n─────────────────────────────────────────────────────\n\nCOMPONENTEN HERORDENEN\n\n1. Klik op de te verplaatsen rij.\n2. Klik ▲ Omhoog of ▼ Omlaag.\n\nVolgorde beïnvloedt tabel en PDF. NIET de berekeningen.\n\n─────────────────────────────────────────────────────\n\nHET RECEPT WISSEN\n\nKlik ✖ Alles wissen. Bevestiging vereist.\n⚠  Onherstelbaar — sla eerst op indien gewenst.\n', 'Save, Load & PDF Export': '\nEEN RECEPT OPSLAAN\n\nKlik 💾 Opslaan. .json-formaat.\n\nWat WEL wordt opgeslagen: naam, componenten, dichtheden, modi,\nwaarden, actief tabblad, doel.\nWat NIET wordt opgeslagen: berekende resultaten.\n\n─────────────────────────────────────────────────────\n\nEEN RECEPT LADEN\n\nKlik 📂 Laden. Selecteer een .json-bestand.\n⚠  Druk na laden op ⚙ BEREKENEN of ⚙ OPLOSSEN.\n\n─────────────────────────────────────────────────────\n\nEXPORTEREN NAAR PDF\n\nKlik 📄 PDF exporteren. Eerst berekenen/oplossen.\nRapport bevat volledige tabel, samenvatting, bereikte belading.\nA4-formaat.\n\n─────────────────────────────────────────────────────\n\nDELEN\n\nKlik 📤 Delen. Niet eerst opslaan nodig.\n  ✉ E-mail →  Opent Outlook met bijgevoegd bestand.\n  💬 Teams  →  Opent Verkenner met geselecteerd bestand.\n', 'Tips & Troubleshooting': '\n─────────────────────────────────────────────────────\nVEELVOORKOMENDE FOUTEN EN OPLOSSINGEN\n─────────────────────────────────────────────────────\n\nPROBLEEM:  Solver-fout of onjuiste volumes\n  Oorzaak:  Onjuiste of ontbrekende dichtheidswaarde.\n  Oplossing: Gebruik ▼ om uit de database te selecteren.\n\nPROBLEEM:  «Referentie niet gevonden»\n  Oplossing: Gebruik ▼ in het Referentieveld.\n\nPROBLEEM:  «Primary niet gevonden»\n  Oplossing: Selecteer keramiek → stel Primary in →\n             klik ✏ Bijwerken.\n\nPROBLEEM:  Balance-resultaat negatief of zeer groot\n  Oplossing: Verlaag doel-% of waarden van andere componenten.\n\nPROBLEEM:  wt.% en vol.% tellen niet op tot 100%\n  Normaal als sommige componenten in absolute hoeveelheden zijn.\n\nPROBLEEM:  Recept geladen maar resultaten leeg\n  Oplossing: Druk op ⚙ BEREKENEN of ⚙ OPLOSSEN na laden.\n\n─────────────────────────────────────────────────────\nTIPS VOOR EFFICIËNT GEBRUIK\n─────────────────────────────────────────────────────\n\n  ✓  Gebruik altijd ▼ in het Componentveld.\n  ✓  Gebruik altijd ▼ in het Referentieveld.\n  ✓  Sla op vóór u met waarden experimenteert.\n  ✓  Gebruik ⊕ Mengsel maken voor regelmatig gebruikte mengsels.\n  ✓  Exporteer PDF na elke geslaagde formulering.\n  ✓  De statusbalk toont altijd de laatste actie.\n', 'Settings & Accessibility': '\nINSTELLINGEN\n\nOpenen via ⚙ Instellingen in de linker zijbalk.\n\n─────────────────────────────────────────────────────\n\nUITERLIJK\n\nTaal — selecteer de interfacetaal. ✓ Direct van kracht.\nTekengrootte — Klein / Normaal / Groot / Extra Groot.\nHoog contrast — donker thema. ✓ Direct van kracht.\nKleurenblind palette — blauw/oranje i.p.v. rood/groen.\n\n─────────────────────────────────────────────────────\n\nGEDRAG\n\nBevestiging voor verwijderen — standaard ingeschakeld.\nGrotere knoppen — voor touchscreens. ✓ Direct van kracht.\n\n─────────────────────────────────────────────────────\n\nSTANDAARD HERSTELLEN\n\nKlik «Standaard herstellen» linksonder in Instellingen.\n', 'Formulae & Theory': '\nDeze sectie legt de wiskunde uit die de applicatie gebruikt.\n\n─────────────────────────────────────────────────────\nNOTATIE\n\n  mᵢ    massa component i  [g]\n  Vᵢ    volume component i  [cm³]\n  ρᵢ    dichtheid component i  [g/cm³]\n  M_tot totale batchmassa  [g]\n  V_tot totaal batchvolume  [cm³]\n  T     doelbelading als breuk (45% → T = 0.45)\n\n─────────────────────────────────────────────────────\nCONVERSIES\n\n  Vᵢ = mᵢ / ρᵢ     mᵢ = Vᵢ · ρᵢ\n\n─────────────────────────────────────────────────────\nBATCH-TOTALEN\n\n  M_tot = Σmᵢ     V_tot = ΣVᵢ     ρ_mix = M_tot/V_tot\n  wt.%ᵢ = 100·mᵢ/M_tot     vol.%ᵢ = 100·Vᵢ/V_tot\n\n─────────────────────────────────────────────────────\nINVERSE SOLVER — BALANCE-BEREKENING\n\n  vol.%:  V_B = V_anc·(1−F_pv)/T − V_anc − V_kn;  m_B = V_B·ρ_B\n  wt.%:   m_B = M_anc·(1−F_pm)/T − M_anc − M_kn\n\n─────────────────────────────────────────────────────\nIDEAAL MENGEN\n\n  1/ρ_blend = Σ(wᵢ/ρᵢ)\n'},
    "zh": {
        'About': '\nTHE 3D PRINTING FORMULATOR  —  v1.0\n作者：Dr Thanos Goulas\n📧  thanosgoulas@outlook.com\n\n─────────────────────────────────────────────────────\n\n本软件能做什么？\n\n计算陶瓷树脂或浆料配方中每种材料的精确用量——以克和cm³表示——\n方便在实验台上准确称量。\n\n  FORWARD  →  您决定用量，软件计算最终组成（wt.%、vol.%、密度）。\n  INVERSE  →  您决定目标组成（如45 vol.% 氧化铝），软件计算用量。\n\n─────────────────────────────────────────────────────\n\n免责声明\n\n⚠  密度值可能因等级、纯度、温度和供应商而异。\n   使用前请对照您材料的SDS进行验证。\n\n📧  thanosgoulas@outlook.com\n',
        'Quick Start Guide': '\n新用户？从这里开始。\n\n─────────────────────────────────────────────────────\n\n示例配方\n\n  目标：45 vol.% Al₂O₃ 在HDDA树脂中\n  批次：200 g氧化铝\n  添加剂：1 wt.% BAPO光引发剂（基于总批次）\n\n─────────────────────────────────────────────────────\n\n步骤1 — 命名配方\n点击"配方/文件名"框，输入名称，如：Al2O3 45vol% HDDA\n\n步骤2 — 打开反向求解器\n在左侧边栏点击"Inverse Solver"。\n\n步骤3 — 设置目标\n在TARGET栏：输入45，选择vol.%。\n\n步骤4 — 添加陶瓷为PRIMARY\n  组分：Al2O3 · 关系：Primary · 模式：Mass (g) · 值：200\n  点击 ➕ 添加。\n\n步骤5 — 添加单体为BALANCE\n  组分：HDDA · 关系：Balance · 值：0\n  点击 ➕ 添加。\n\n步骤6 — 添加光引发剂\n  组分：BAPO · 关系：wt.% of Total Suspension · 值：1\n  点击 ➕ 添加。\n\n步骤7 — 求解\n点击 ⚙ 求解。\n\n步骤8 — 保存和导出\n  💾 保存 · 📄 导出PDF · 📤 分享\n',
        'The Materials Database': '\n材料数据库\n\n存储密度（g/cm³）、折射率（RI）和分子量（MW）。\n\n─────────────────────────────────────────────────────\n\n搜索材料\n\n在组分字段中点击 ▼。通过输入过滤——同时搜索缩写和化学名称。\n\n─────────────────────────────────────────────────────\n\n添加新材料\n\n1. 缩写  2. 全名（可选）\n3. 密度 g/cm³  ← 必填\n4. RI（可选）  5. MW g/mol（可选）\n6. 点击 ➕ 添加/更新\n\n─────────────────────────────────────────────────────\n\n创建混合物\n\n1. 点击 ⊕ 创建混合物。\n2. 选择组分并输入wt.%（总和=100%）。\n3. 点击 ⟳ 计算密度。\n4. 输入名称。\n5. 点击 💾 保存到数据库。\n',
        'Forward Formulator': '\n正向计算\n\n─────────────────────────────────────────────────────\n\n六种输入模式\n\n模式1：质量(g)           — 直接输入克数\n模式2：体积(cm³)         — 直接输入cm³\n模式3：相对参考的wt.%    — m_i = (值/100) × m_参考\n模式4：相对参考的vol.%   — V_i = (值/100) × V_参考\n模式5：占总量的wt.%      — 占总质量的固定%  ⚠ 总和 < 100%\n模式6：占总量的vol.%     — 占总体积的固定%  ⚠ 总和 < 100%\n\n  ✓  可以自由混合所有模式。\n  ✓  在参考字段使用 ▼ 避免拼写错误。\n',
        'Inverse Solver': '\n反向求解器\n\n─────────────────────────────────────────────────────\n\n关系类型\n\nPrimary   — 陶瓷/填料。每个配方恰好1个。\nBalance   — 计算所得的溶剂/单体。最多1个。值=0。\nwt.%/vol.% 参考   — 占另一组分的百分比。\nwt.%/vol.% 总悬浮液 — 占总批次的固定%。  ⚠ 总和 < 100%\n独立质量/体积     — 固定量，不随比例变化。\n\n─────────────────────────────────────────────────────\n\n规则\n\n  ✓  恰好需要1个Primary。\n  ✓  最多1个Balance，值=0。\n  ✓  所有组分名称必须唯一。\n',
        'Editing & Managing Components': '\n编辑组分\n\n1. 点击该行（蓝色高亮）。\n2. 进行修改。\n3. 点击 ✏ 更新 保存。\n⚠  编辑时不要点击 ➕ 添加——会创建重复项。\n\n─────────────────────────────────────────────────────\n\n删除 · 重排 · 全部清除\n\n🗑 删除 — 删除选中的组分。\n▲/▼ — 重排（仅影响显示，不影响计算）。\n✖ 全部清除 — 删除所有（需确认）。\n',
        'Save, Load & PDF Export': '\n保存 · 加载 · 导出PDF\n\n💾 保存    — 保存为.json（结果不保存）。\n📂 加载    — 加载.json（加载后重新计算）。\n📄 导出    — 含完整表格和摘要的A4 PDF。\n📤 分享    — 自动生成文件并打开邮件/Teams。\n',
        'Tips & Troubleshooting': '\n常见问题\n\n求解器错误/体积不正确\n  → 检查密度值。使用 ▼ 从数据库选择。\n\n"未找到参考"\n  → 在参考字段使用 ▼。\n\n"未找到Primary"（反向求解器）\n  → 选择陶瓷 → Primary → ✏ 更新。\n\nBalance为负数或异常大\n  → 降低目标值或减少其他组分的值。\n\n─────────────────────────────────────────────────────\n\n使用技巧\n\n  ✓  始终在组分字段使用 ▼。\n  ✓  实验之前先保存。\n  ✓  使用 ⊕ 创建混合物处理常用单体混合物。\n  ✓  每次成功配方后导出PDF。\n',
        'Settings & Accessibility': '\n设置\n\n通过左侧边栏的 ⚙ 设置 打开。\n\n语言 · 字体大小 · 高对比度 · 色盲配色\n  ✓  点击应用或确定后立即生效。\n\n删除前确认 — 删除或清除前询问确认。\n更大的点击区域 — 增大按钮以便触摸使用。\n\n恢复默认 — 设置对话框左下角按钮。\n',
        'Formulae & Theory': '\n符号说明\n\n  mᵢ/Vᵢ/ρᵢ    质量[g] / 体积[cm³] / 密度[g/cm³]\n  M_tot/V_tot  批次总质量 / 总体积\n  T            目标固含量（分数形式，45%→0.45）\n\n─────────────────────────────────────────────────────\n\n基本换算\n\n  Vᵢ = mᵢ/ρᵢ    mᵢ = Vᵢ·ρᵢ\n  ρ_mix = M_tot/V_tot\n  wt.%ᵢ = 100·mᵢ/M_tot    vol.%ᵢ = 100·Vᵢ/V_tot\n\n─────────────────────────────────────────────────────\n\n正向计算 — 输入模式\n  wt.%/vol.% 参考：  mᵢ=(W/100)·m_r  /  Vᵢ=(W/100)·V_r\n  wt.%/vol.% 总量：  M_tot=M_abs/(1−S)\n\n反向求解器 — Balance计算\n  vol.%: V_B = V_anc·(1−F_pv)/T − V_anc − V_kn; m_B = V_B·ρ_B\n  wt.%:  m_B = M_anc·(1−F_pm)/T − M_anc − M_kn\n\n理想混合：  1/ρ_blend = Σ(wᵢ/ρᵢ)\n',
    },
    "ja": {
        'About': '\nTHE 3D PRINTING FORMULATOR  —  v1.0\n制作：Dr Thanos Goulas\n📧  thanosgoulas@outlook.com\n\n─────────────────────────────────────────────────────\n\nこのアプリの機能\n\nセラミック樹脂またはペーストのレシピにおける各材料の正確な量を\nグラムおよびcm³で計算し、実験台での正確な計量を支援します。\n\n  FORWARD  →  量を決める。組成（wt.%、vol.%、密度）を計算。\n  INVERSE  →  組成を決める（例：45 vol.% アルミナ）。量を計算。\n\n─────────────────────────────────────────────────────\n\n免責事項\n\n⚠  密度値はグレード、純度、温度、サプライヤーにより異なる場合があります。\n   使用前に必ずご使用材料のSDSで確認してください。\n\n📧  thanosgoulas@outlook.com\n',
        'Quick Start Guide': '\n初めてお使いの方へ — ここから始めましょう\n\n─────────────────────────────────────────────────────\n\nレシピ例\n\n  目標：45 vol.% Al₂O₃ (HDDA樹脂中)\n  バッチ：アルミナ 200 g\n  添加剤：1 wt.% BAPO 光開始剤（全バッチ基準）\n\n─────────────────────────────────────────────────────\n\nステップ1 — レシピ名の入力\n「レシピ名/ファイル名」欄に名前を入力します。\n\nステップ2 — 逆算ソルバーを開く\n左のサイドバーで「Inverse Solver」をクリック。\n\nステップ3 — 目標を設定\nTARGET欄に 45 と入力し、vol.% を選択。\n\nステップ4 — セラミックをPRIMARYとして追加\n  成分：Al2O3 · 関係：Primary · モード：Mass (g) · 値：200\n  ➕ 追加 をクリック。\n\nステップ5 — モノマーをBALANCEとして追加\n  成分：HDDA · 関係：Balance · 値：0\n  ➕ 追加 をクリック。\n\nステップ6 — 光開始剤を追加\n  成分：BAPO · 関係：wt.% of Total Suspension · 値：1\n  ➕ 追加 をクリック。\n\nステップ7 — 求解\n⚙ 求解 をクリック。\n\nステップ8 — 保存とエクスポート\n  💾 保存 · 📄 PDFエクスポート · 📤 共有\n',
        'The Materials Database': '\n材料データベース\n\n密度（g/cm³）、屈折率（RI）、分子量（MW）を保存します。\n\n─────────────────────────────────────────────────────\n\n材料の検索\n\n成分フィールドで ▼ をクリック。入力でフィルタリング—\n略称と化学名の両方を検索します。\n\n─────────────────────────────────────────────────────\n\n新しい材料の追加\n\n1. 略称  2. フルネーム（任意）\n3. 密度 g/cm³  ← 必須\n4. RI（任意）  5. MW g/mol（任意）\n6. ➕ 追加/更新 をクリック\n\n─────────────────────────────────────────────────────\n\nブレンドの作成\n\n1. ⊕ 混合物作成 をクリック。\n2. 成分と wt.% を入力（合計100%）。\n3. ⟳ 密度を計算 をクリック。\n4. 名前を付ける。\n5. 💾 DBに保存 をクリック。\n',
        'Forward Formulator': '\n順方向計算\n\n─────────────────────────────────────────────────────\n\n6つの入力モード\n\nモード1：質量(g)         — グラムで直接入力\nモード2：体積(cm³)       — cm³で直接入力\nモード3：参照へのwt.%    — m_i = (値/100) × m_参照\nモード4：参照へのvol.%   — V_i = (値/100) × V_参照\nモード5：全体のwt.%      — 全質量の固定%  ⚠ 合計 < 100%\nモード6：全体のvol.%     — 全体積の固定%  ⚠ 合計 < 100%\n\n  ✓  すべてのモードを自由に組み合わせられます。\n  ✓  参照フィールドで ▼ を使用してタイプミスを防ぎます。\n',
        'Inverse Solver': '\n逆算ソルバー\n\n─────────────────────────────────────────────────────\n\n関係タイプ\n\nPrimary   — セラミック/フィラー。1レシピにちょうど1つ。\nBalance   — 計算されるソルベント/モノマー。最大1つ。値=0。\nwt.%/vol.% 参照   — 別成分のパーセンテージ。\nwt.%/vol.% 全懸濁液 — 全バッチの固定%。  ⚠ 合計 < 100%\n独立質量/体積     — 固定量。スケールしない。\n\n─────────────────────────────────────────────────────\n\nルール\n\n  ✓  Primaryはちょうど1つ必要。\n  ✓  Balanceは最大1つ。値=0。\n  ✓  すべての成分名は一意であること。\n',
        'Editing & Managing Components': '\n成分の編集\n\n1. 行をクリック（青くハイライト）。\n2. 変更を加える。\n3. ✏ 更新 をクリックして保存。\n⚠  編集中に ➕ 追加 を使わないこと—重複を作成します。\n\n─────────────────────────────────────────────────────\n\n削除 · 並べ替え · 全削除\n\n🗑 削除 — 選択した成分を削除。\n▲/▼ — 並べ替え（表示のみ、計算に影響なし）。\n✖ 全削除 — すべてを削除（確認が必要）。\n',
        'Save, Load & PDF Export': '\n保存 · 読込 · PDFエクスポート\n\n💾 保存    — .jsonに保存（結果は保存されません）。\n📂 読込    — .jsonを読み込む（読み込み後に再計算）。\n📄 エクスポート — 完全な表とサマリーのA4 PDF。\n📤 共有    — ファイルを生成してメール/Teamsを開く。\n',
        'Tips & Troubleshooting': '\nよくある問題\n\nソルバーエラー / 体積が正しくない\n  → 密度を確認。▼ を使ってデータベースから選択。\n\n「参照が見つかりません」\n  → 参照フィールドで ▼ を使用。\n\n「Primaryが見つかりません」（逆算ソルバー）\n  → セラミックを選択 → Primary → ✏ 更新。\n\nBalanceが負または非常に大きい\n  → 目標値または他の成分の値を下げる。\n\n─────────────────────────────────────────────────────\n\n使用のヒント\n\n  ✓  成分フィールドでは常に ▼ を使用。\n  ✓  値を実験する前に保存。\n  ✓  ⊕ 混合物作成で頻繁に使うモノマーブレンドを登録。\n  ✓  成功した配方ごとにPDFをエクスポート。\n',
        'Settings & Accessibility': '\n設定\n\n左サイドバーの ⚙ 設定 から開きます。\n\n言語 · フォントサイズ · 高コントラスト · 色覚サポートパレット\n  ✓  適用またはOKをクリックすると即座に反映。\n\n削除前の確認 — 削除またはクリア前に確認を求める。\n大きなボタン — タッチスクリーンや運動障害のある方向け。\n\nデフォルトに戻す — ダイアログ左下のボタン。\n',
        'Formulae & Theory': '\n記号\n\n  mᵢ/Vᵢ/ρᵢ    質量[g] / 体積[cm³] / 密度[g/cm³]\n  M_tot/V_tot  バッチ総質量 / 総体積\n  T            目標充填率（分数、45%→0.45）\n\n─────────────────────────────────────────────────────\n\n基本換算\n\n  Vᵢ = mᵢ/ρᵢ    mᵢ = Vᵢ·ρᵢ\n  ρ_mix = M_tot/V_tot\n  wt.%ᵢ = 100·mᵢ/M_tot    vol.%ᵢ = 100·Vᵢ/V_tot\n\n─────────────────────────────────────────────────────\n\n順方向 — 入力モード\n  wt.%/vol.% 参照：  mᵢ=(W/100)·m_r  /  Vᵢ=(W/100)·V_r\n  wt.%/vol.% 全体：  M_tot=M_abs/(1−S)\n\n逆算 — Balance計算\n  vol.%: V_B = V_anc·(1−F_pv)/T − V_anc − V_kn; m_B = V_B·ρ_B\n  wt.%:  m_B = M_anc·(1−F_pm)/T − M_anc − M_kn\n\n理想混合：  1/ρ_blend = Σ(wᵢ/ρᵢ)\n',
    },
    "ko": {
        'About': '\nTHE 3D PRINTING FORMULATOR  —  v1.0\n제작: Dr Thanos Goulas\n📧  thanosgoulas@outlook.com\n\n─────────────────────────────────────────────────────\n\n이 앱의 기능\n\n세라믹 수지 또는 페이스트 배합에서 각 재료의 정확한 양을\n그램 및 cm³으로 계산하여 실험실에서 정확하게 계량할 수 있도록\n도와줍니다.\n\n  FORWARD  →  양을 결정하면 조성(wt.%, vol.%, 밀도)을 계산합니다.\n  INVERSE  →  조성을 결정하면(예: 45 vol.% 알루미나) 양을 계산합니다.\n\n─────────────────────────────────────────────────────\n\n면책 조항\n\n⚠  밀도는 등급, 순도, 온도 및 공급업체에 따라 다를 수 있습니다.\n   사용 전 반드시 재료의 SDS를 확인하세요.\n\n📧  thanosgoulas@outlook.com\n',
        'Quick Start Guide': '\n처음 사용하시나요? 여기서 시작하세요.\n\n─────────────────────────────────────────────────────\n\n예제 배합\n\n  목표: 45 vol.% Al₂O₃ (HDDA 수지 중)\n  배치: 알루미나 200 g\n  첨가제: 1 wt.% BAPO 광개시제 (전체 배치 기준)\n\n─────────────────────────────────────────────────────\n\n단계 1 — 배합 이름 지정\n"레시피/파일명" 입력란을 클릭하고 이름을 입력합니다.\n\n단계 2 — 역방향 솔버 열기\n왼쪽 사이드바에서 "Inverse Solver"를 클릭합니다.\n\n단계 3 — 목표 설정\nTARGET 표시줄: 45 입력, vol.% 선택.\n\n단계 4 — 세라믹을 PRIMARY로 추가\n  성분: Al2O3 · 관계: Primary · 모드: Mass (g) · 값: 200\n  ➕ 추가 클릭.\n\n단계 5 — 단량체를 BALANCE로 추가\n  성분: HDDA · 관계: Balance · 값: 0\n  ➕ 추가 클릭.\n\n단계 6 — 광개시제 추가\n  성분: BAPO · 관계: wt.% of Total Suspension · 값: 1\n  ➕ 추가 클릭.\n\n단계 7 — 풀기\n⚙ 풀기 클릭.\n\n단계 8 — 저장 및 내보내기\n  💾 저장 · 📄 PDF 내보내기 · 📤 공유\n',
        'The Materials Database': '\n재료 데이터베이스\n\n밀도 (g/cm³), 굴절률 (RI), 분자량 (MW)을 저장합니다.\n\n─────────────────────────────────────────────────────\n\n재료 검색\n\n성분 필드에서 ▼를 클릭합니다. 입력하여 필터링—\n약어와 화학명 모두 검색합니다.\n\n─────────────────────────────────────────────────────\n\n새 재료 추가\n\n1. 약어  2. 전체 이름(선택)\n3. 밀도 g/cm³  ← 필수\n4. RI(선택)  5. MW g/mol(선택)\n6. ➕ 추가/업데이트 클릭\n\n─────────────────────────────────────────────────────\n\n혼합물 만들기\n\n1. ⊕ 혼합물 생성 클릭.\n2. 성분과 wt.% 입력 (합계=100%).\n3. ⟳ 밀도 계산 클릭.\n4. 이름 지정.\n5. 💾 DB에 저장 클릭.\n',
        'Forward Formulator': '\n순방향 계산\n\n─────────────────────────────────────────────────────\n\n여섯 가지 입력 모드\n\n모드1: 질량(g)             — 그램으로 직접 입력\n모드2: 체적(cm³)           — cm³로 직접 입력\n모드3: 참조 대비 wt.%      — m_i = (값/100) × m_참조\n모드4: 참조 대비 vol.%     — V_i = (값/100) × V_참조\n모드5: 전체의 wt.%         — 총 질량의 고정 %  ⚠ 합계 < 100%\n모드6: 전체의 vol.%        — 총 체적의 고정 %  ⚠ 합계 < 100%\n\n  ✓  모든 모드를 자유롭게 조합할 수 있습니다.\n  ✓  참조 필드에서 ▼를 사용하여 오타를 방지하세요.\n',
        'Inverse Solver': '\n역방향 솔버\n\n─────────────────────────────────────────────────────\n\n관계 유형\n\nPrimary   — 세라믹/필러. 배합당 정확히 1개.\nBalance   — 계산되는 용매/단량체. 최대 1개. 값=0.\nwt.%/vol.% 참조   — 다른 성분의 백분율.\nwt.%/vol.% 전체 현탁액 — 전체 배치의 고정 %.  ⚠ 합계 < 100%\n독립 질량/체적     — 고정 양. 비례하지 않음.\n\n─────────────────────────────────────────────────────\n\n규칙\n\n  ✓  Primary는 정확히 1개 필요.\n  ✓  Balance는 최대 1개. 값=0.\n  ✓  모든 성분 이름은 고유해야 합니다.\n',
        'Editing & Managing Components': '\n성분 편집\n\n1. 행 클릭 (파란색 강조 표시).\n2. 변경 사항 적용.\n3. ✏ 업데이트 클릭하여 저장.\n⚠  편집 시 ➕ 추가를 클릭하지 마세요 — 중복이 생성됩니다.\n\n─────────────────────────────────────────────────────\n\n제거 · 재정렬 · 모두 지우기\n\n🗑 제거 — 선택한 성분 제거.\n▲/▼ — 재정렬 (표시만, 계산에 영향 없음).\n✖ 모두 지우기 — 전체 삭제 (확인 필요).\n',
        'Save, Load & PDF Export': '\n저장 · 불러오기 · PDF 내보내기\n\n💾 저장      — .json으로 저장 (결과는 저장 안 됨).\n📂 불러오기  — .json 불러오기 (불러온 후 재계산).\n📄 내보내기  — 전체 표와 요약이 포함된 A4 PDF.\n📤 공유      — 파일을 생성하고 이메일/Teams 열기.\n',
        'Tips & Troubleshooting': '\n자주 발생하는 문제\n\n솔버 오류 / 잘못된 체적\n  → 밀도 확인. ▼를 사용하여 데이터베이스에서 선택.\n\n"참조를 찾을 수 없음"\n  → 참조 필드에서 ▼ 사용.\n\n"Primary를 찾을 수 없음" (역방향 솔버)\n  → 세라믹 선택 → Primary → ✏ 업데이트.\n\nBalance가 음수이거나 매우 큼\n  → 목표값 또는 다른 성분의 값 줄이기.\n\n─────────────────────────────────────────────────────\n\n사용 팁\n\n  ✓  항상 성분 필드에서 ▼ 사용.\n  ✓  값 실험 전에 저장.\n  ✓  ⊕ 혼합물 생성으로 자주 사용하는 단량체 혼합물 등록.\n  ✓  성공적인 배합마다 PDF 내보내기.\n',
        'Settings & Accessibility': '\n설정\n\n왼쪽 사이드바의 ⚙ 설정에서 열기.\n\n언어 · 글꼴 크기 · 고대비 · 색맹 지원 팔레트\n  ✓  적용 또는 확인 클릭 시 즉시 적용.\n\n제거 전 확인 — 제거 또는 지우기 전 확인 요청.\n더 큰 버튼 — 터치스크린 또는 운동 장애가 있는 분들을 위해.\n\n기본값 복원 — 다이얼로그 왼쪽 하단 버튼.\n',
        'Formulae & Theory': '\n기호\n\n  mᵢ/Vᵢ/ρᵢ    질량[g] / 체적[cm³] / 밀도[g/cm³]\n  M_tot/V_tot  배치 총 질량 / 총 체적\n  T            목표 충전율 (분수, 45%→0.45)\n\n─────────────────────────────────────────────────────\n\n기본 변환\n\n  Vᵢ = mᵢ/ρᵢ    mᵢ = Vᵢ·ρᵢ\n  ρ_mix = M_tot/V_tot\n  wt.%ᵢ = 100·mᵢ/M_tot    vol.%ᵢ = 100·Vᵢ/V_tot\n\n─────────────────────────────────────────────────────\n\n순방향 — 입력 모드\n  wt.%/vol.% 참조:  mᵢ=(W/100)·m_r  /  Vᵢ=(W/100)·V_r\n  wt.%/vol.% 전체:  M_tot=M_abs/(1−S)\n\n역방향 솔버 — Balance 계산\n  vol.%: V_B = V_anc·(1−F_pv)/T − V_anc − V_kn; m_B = V_B·ρ_B\n  wt.%:  m_B = M_anc·(1−F_pm)/T − M_anc − M_kn\n\n이상 혼합:  1/ρ_blend = Σ(wᵢ/ρᵢ)\n',
    },
    "hi": {
        'About': '\nTHE 3D PRINTING FORMULATOR  —  v1.0\nद्वारा: Dr Thanos Goulas\n📧  thanosgoulas@outlook.com\n\n─────────────────────────────────────────────────────\n\nयह ऐप क्या करता है?\n\nयह सिरेमिक रेज़िन या पेस्ट फॉर्मूलेशन में प्रत्येक सामग्री की\nसटीक मात्रा — ग्राम और cm³ में — की गणना करता है।\n\n  FORWARD  →  आप मात्रा तय करें। ऐप संरचना (wt.%, vol.%, घनत्व)\n               की गणना करता है।\n  INVERSE  →  आप संरचना तय करें (जैसे 45 vol.% एल्युमिना)।\n               ऐप मात्रा की गणना करता है।\n\n─────────────────────────────────────────────────────\n\nअस्वीकरण\n\n⚠  घनत्व मान ग्रेड, शुद्धता, तापमान और आपूर्तिकर्ता के अनुसार\n   भिन्न हो सकते हैं। उपयोग से पहले अपनी सामग्री के SDS से सत्यापित करें।\n\n📧  thanosgoulas@outlook.com\n',
        'Quick Start Guide': '\nनए उपयोगकर्ता? यहाँ से शुरू करें।\n\n─────────────────────────────────────────────────────\n\nउदाहरण फॉर्मूलेशन\n\n  लक्ष्य: 45 vol.% Al₂O₃ HDDA रेज़िन में\n  बैच: 200 g एल्युमिना\n  योजक: 1 wt.% BAPO फोटोइनिशिएटर (कुल बैच पर)\n\n─────────────────────────────────────────────────────\n\nचरण 1 — फॉर्मूलेशन का नाम दें\n"रेसिपी/फ़ाइल नाम" पर क्लिक करें और नाम टाइप करें।\n\nचरण 2 — Inverse Solver खोलें\nबाएं साइडबार में "Inverse Solver" पर क्लिक करें।\n\nचरण 3 — लक्ष्य सेट करें\nTARGET बार में: 45 टाइप करें, vol.% चुनें।\n\nचरण 4 — सिरेमिक को PRIMARY के रूप में जोड़ें\n  घटक: Al2O3 · संबंध: Primary · मोड: Mass (g) · मान: 200\n  ➕ जोड़ें पर क्लिक करें।\n\nचरण 5 — मोनोमर को BALANCE के रूप में जोड़ें\n  घटक: HDDA · संबंध: Balance · मान: 0\n  ➕ जोड़ें पर क्लिक करें।\n\nचरण 6 — फोटोइनिशिएटर जोड़ें\n  घटक: BAPO · संबंध: wt.% of Total Suspension · मान: 1\n  ➕ जोड़ें पर क्लिक करें।\n\nचरण 7 — हल करें\n⚙ हल करें पर क्लिक करें।\n\nचरण 8 — सहेजें और निर्यात करें\n  💾 सहेजें · 📄 PDF निर्यात · 📤 साझा करें\n',
        'The Materials Database': '\nसामग्री डेटाबेस\n\nघनत्व (g/cm³), अपवर्तनांक (RI) और आणविक भार (MW) संग्रहीत करता है।\n\n─────────────────────────────────────────────────────\n\nसामग्री खोजें\n\nघटक फ़ील्ड में ▼ पर क्लिक करें। टाइप करके फ़िल्टर करें —\nसंक्षिप्त नाम और रासायनिक नाम दोनों खोजता है।\n\n─────────────────────────────────────────────────────\n\nनई सामग्री जोड़ें\n\n1. संक्षिप्त नाम  2. पूरा नाम (वैकल्पिक)\n3. घनत्व g/cm³  ← अनिवार्य\n4. RI (वैकल्पिक)  5. MW g/mol (वैकल्पिक)\n6. ➕ जोड़ें/अपडेट पर क्लिक करें\n\n─────────────────────────────────────────────────────\n\nमिश्रण बनाएं\n\n1. ⊕ मिश्रण बनाएं पर क्लिक करें।\n2. घटक और wt.% दर्ज करें (कुल=100%)।\n3. ⟳ घनत्व गणना पर क्लिक करें।\n4. नाम दें।\n5. 💾 DB में सहेजें पर क्लिक करें।\n',
        'Forward Formulator': '\nअग्रवर्ती गणना\n\n─────────────────────────────────────────────────────\n\nछह इनपुट मोड\n\nमोड 1: द्रव्यमान (g)           — ग्राम में सीधे दर्ज करें\nमोड 2: आयतन (cm³)              — cm³ में सीधे दर्ज करें\nमोड 3: संदर्भ का wt.%          — m_i = (मान/100) × m_संदर्भ\nमोड 4: संदर्भ का vol.%         — V_i = (मान/100) × V_संदर्भ\nमोड 5: कुल का wt.%             — कुल द्रव्यमान का %  ⚠ योग < 100%\nमोड 6: कुल का vol.%            — कुल आयतन का %   ⚠ योग < 100%\n\n  ✓  सभी मोड स्वतंत्र रूप से मिला सकते हैं।\n  ✓  त्रुटियों से बचने के लिए संदर्भ फ़ील्ड में ▼ का उपयोग करें।\n',
        'Inverse Solver': '\nव्युत्क्रम सॉल्वर\n\n─────────────────────────────────────────────────────\n\nसंबंध प्रकार\n\nPrimary   — सिरेमिक/भराव। प्रति रेसिपी बिल्कुल 1।\nBalance   — गणना किया गया विलायक/मोनोमर। अधिकतम 1। मान=0।\nwt.%/vol.% संदर्भ   — किसी अन्य घटक का प्रतिशत।\nwt.%/vol.% कुल निलंबन — कुल बैच का %।  ⚠ योग < 100%\nस्वतंत्र द्रव्यमान/आयतन — निश्चित मात्रा, स्केल नहीं।\n\n─────────────────────────────────────────────────────\n\nनियम\n\n  ✓  बिल्कुल 1 Primary आवश्यक।\n  ✓  अधिकतम 1 Balance। मान=0।\n  ✓  सभी घटक नाम अद्वितीय होने चाहिए।\n',
        'Editing & Managing Components': '\nघटक संपादित करें\n\n1. पंक्ति पर क्लिक करें (नीले रंग में हाइलाइट)।\n2. बदलाव करें।\n3. सहेजने के लिए ✏ अपडेट पर क्लिक करें।\n⚠  संपादन के दौरान ➕ जोड़ें पर क्लिक न करें — डुप्लिकेट बनेगा।\n\n─────────────────────────────────────────────────────\n\nहटाएं · पुनः क्रमित करें · सब साफ करें\n\n🗑 हटाएं — चुने गए घटक को हटाएं।\n▲/▼ — पुनः क्रमित करें (केवल प्रदर्शन, गणना पर कोई प्रभाव नहीं)।\n✖ सब साफ करें — सब हटाएं (पुष्टि आवश्यक)।\n',
        'Save, Load & PDF Export': '\nसहेजें · लोड करें · PDF निर्यात\n\n💾 सहेजें    — .json में सहेजें (परिणाम नहीं)।\n📂 लोड करें  — .json लोड करें (बाद में पुनः गणना करें)।\n📄 निर्यात   — पूर्ण तालिका और सारांश के साथ A4 PDF।\n📤 साझा करें — फ़ाइल बनाएं और ईमेल/Teams खोलें।\n',
        'Tips & Troubleshooting': '\nसामान्य समस्याएं\n\nसॉल्वर त्रुटि / गलत आयतन\n  → घनत्व जांचें। डेटाबेस से चुनने के लिए ▼ का उपयोग करें।\n\n"संदर्भ नहीं मिला"\n  → संदर्भ फ़ील्ड में ▼ उपयोग करें।\n\n"Primary नहीं मिला" (व्युत्क्रम सॉल्वर)\n  → सिरेमिक चुनें → Primary → ✏ अपडेट।\n\nBalance ऋणात्मक या बहुत बड़ा\n  → लक्ष्य मान या अन्य घटकों के मान घटाएं।\n\n─────────────────────────────────────────────────────\n\nउपयोग के सुझाव\n\n  ✓  हमेशा घटक फ़ील्ड में ▼ का उपयोग करें।\n  ✓  मान के साथ प्रयोग से पहले सहेजें।\n  ✓  अक्सर उपयोग किए जाने वाले मोनोमर मिश्रणों के लिए ⊕ उपयोग करें।\n  ✓  हर सफल फॉर्मूलेशन के बाद PDF निर्यात करें।\n',
        'Settings & Accessibility': '\nसेटिंग्स\n\nबाएं साइडबार में ⚙ सेटिंग्स से खोलें।\n\nभाषा · फ़ॉन्ट आकार · उच्च कंट्रास्ट · वर्णान्ध पैलेट\n  ✓  लागू करें या ठीक है क्लिक करते ही तुरंत प्रभावी।\n\nहटाने से पहले पुष्टि — हटाने या साफ करने से पहले पुष्टि मांगें।\nबड़े बटन — टच स्क्रीन या मोटर अक्षमता के लिए।\n\nडिफ़ॉल्ट पुनर्स्थापित करें — डायलॉग के नीचे बाईं ओर बटन।\n',
        'Formulae & Theory': '\nसंकेतन\n\n  mᵢ/Vᵢ/ρᵢ    द्रव्यमान[g] / आयतन[cm³] / घनत्व[g/cm³]\n  M_tot/V_tot  बैच कुल द्रव्यमान / कुल आयतन\n  T            लक्ष्य लोडिंग (भिन्न रूप में, 45%→0.45)\n\n─────────────────────────────────────────────────────\n\nमूल रूपांतरण\n\n  Vᵢ = mᵢ/ρᵢ    mᵢ = Vᵢ·ρᵢ\n  ρ_mix = M_tot/V_tot\n  wt.%ᵢ = 100·mᵢ/M_tot    vol.%ᵢ = 100·Vᵢ/V_tot\n\n─────────────────────────────────────────────────────\n\nअग्रवर्ती — इनपुट मोड\n  wt.%/vol.% संदर्भ:  mᵢ=(W/100)·m_r  /  Vᵢ=(W/100)·V_r\n  wt.%/vol.% कुल:     M_tot=M_abs/(1−S)\n\nव्युत्क्रम — Balance गणना\n  vol.%: V_B = V_anc·(1−F_pv)/T − V_anc − V_kn; m_B = V_B·ρ_B\n  wt.%:  m_B = M_anc·(1−F_pm)/T − M_anc − M_kn\n\nआदर्श मिश्रण:  1/ρ_blend = Σ(wᵢ/ρᵢ)\n',
    },

}

# Translated nav titles for the Help dialog sidebar
HELP_TITLE_TRANSLATIONS = {'el': {'About': 'Σχετικά', 'Quick Start Guide': 'Οδηγός Γρήγορης Εκκίνησης', 'The Materials Database': 'Βάση Δεδομένων Υλικών', 'Forward Formulator': 'Άμεσος Υπολογισμός', 'Inverse Solver': 'Αντίστροφος Επιλύτης', 'Editing & Managing Components': 'Επεξεργασία Συστατικών', 'Save, Load & PDF Export': 'Αποθήκευση & Εξαγωγή', 'Tips & Troubleshooting': 'Συμβουλές & Αντιμετώπιση', 'Settings & Accessibility': 'Ρυθμίσεις & Προσβασιμότητα', 'Formulae & Theory': 'Τύποι & Θεωρία'}, 'fr': {'About': 'À propos', 'Quick Start Guide': 'Guide de démarrage rapide', 'The Materials Database': 'Base de données matériaux', 'Forward Formulator': 'Formulation directe', 'Inverse Solver': 'Solveur inverse', 'Editing & Managing Components': 'Gestion des composants', 'Save, Load & PDF Export': 'Sauvegarder & Exporter', 'Tips & Troubleshooting': 'Conseils & Dépannage', 'Settings & Accessibility': 'Paramètres & Accessibilité', 'Formulae & Theory': 'Formules & Théorie'}, 'de': {'About': 'Über', 'Quick Start Guide': 'Schnellstartanleitung', 'The Materials Database': 'Materialdatenbank', 'Forward Formulator': 'Vorwärtsberechnung', 'Inverse Solver': 'Inverser Löser', 'Editing & Managing Components': 'Komponenten verwalten', 'Save, Load & PDF Export': 'Speichern & Exportieren', 'Tips & Troubleshooting': 'Tipps & Fehlersuche', 'Settings & Accessibility': 'Einstellungen', 'Formulae & Theory': 'Formeln & Theorie'}, 'es': {'About': 'Acerca de', 'Quick Start Guide': 'Guía de inicio rápido', 'The Materials Database': 'Base de datos de materiales', 'Forward Formulator': 'Formulación directa', 'Inverse Solver': 'Solver inverso', 'Editing & Managing Components': 'Gestión de componentes', 'Save, Load & PDF Export': 'Guardar & Exportar', 'Tips & Troubleshooting': 'Consejos & Solución', 'Settings & Accessibility': 'Configuración', 'Formulae & Theory': 'Fórmulas & Teoría'}, 'it': {'About': 'Informazioni', 'Quick Start Guide': 'Guida rapida', 'The Materials Database': 'Database dei materiali', 'Forward Formulator': 'Formulazione diretta', 'Inverse Solver': 'Solutore inverso', 'Editing & Managing Components': 'Gestione componenti', 'Save, Load & PDF Export': 'Salva & Esporta', 'Tips & Troubleshooting': 'Consigli & Risoluzione', 'Settings & Accessibility': 'Impostazioni', 'Formulae & Theory': 'Formule & Teoria'}, 'nl': {'About': 'Over', 'Quick Start Guide': 'Snelstartgids', 'The Materials Database': 'Materialendatabase', 'Forward Formulator': 'Voorwaartse formulering', 'Inverse Solver': 'Inverse solver', 'Editing & Managing Components': 'Componenten beheren', 'Save, Load & PDF Export': 'Opslaan & Exporteren', 'Tips & Troubleshooting': 'Tips & Problemen', 'Settings & Accessibility': 'Instellingen', 'Formulae & Theory': 'Formules & Theorie'}, 'zh': {'About': '关于', 'Quick Start Guide': '快速入门', 'The Materials Database': '材料数据库', 'Forward Formulator': '正向计算', 'Inverse Solver': '反向求解器', 'Editing & Managing Components': '编辑组分', 'Save, Load & PDF Export': '保存与导出', 'Tips & Troubleshooting': '技巧与故障排除', 'Settings & Accessibility': '设置', 'Formulae & Theory': '公式与理论'}, 'ja': {'About': '概要', 'Quick Start Guide': 'クイックスタート', 'The Materials Database': '材料データベース', 'Forward Formulator': '順方向計算', 'Inverse Solver': '逆算ソルバー', 'Editing & Managing Components': '成分の編集', 'Save, Load & PDF Export': '保存とエクスポート', 'Tips & Troubleshooting': 'ヒントとトラブル', 'Settings & Accessibility': '設定', 'Formulae & Theory': '数式と理論'}, 'ko': {'About': '정보', 'Quick Start Guide': '빠른 시작', 'The Materials Database': '재료 데이터베이스', 'Forward Formulator': '순방향 계산', 'Inverse Solver': '역방향 솔버', 'Editing & Managing Components': '성분 편집', 'Save, Load & PDF Export': '저장 및 내보내기', 'Tips & Troubleshooting': '팁 및 문제 해결', 'Settings & Accessibility': '설정', 'Formulae & Theory': '공식 및 이론'}, 'hi': {'About': 'जानकारी', 'Quick Start Guide': 'त्वरित शुरुआत', 'The Materials Database': 'सामग्री डेटाबेस', 'Forward Formulator': 'अग्रवर्ती गणना', 'Inverse Solver': 'व्युत्क्रम सॉल्वर', 'Editing & Managing Components': 'घटक संपादन', 'Save, Load & PDF Export': 'सहेजें और निर्यात', 'Tips & Troubleshooting': 'सुझाव और समस्या', 'Settings & Accessibility': 'सेटिंग्स', 'Formulae & Theory': 'सूत्र और सिद्धांत'}}

def _get_help_sections(lang):
    """Return HELP_SECTIONS with titles and text replaced by translation."""
    if lang == "en":
        return HELP_SECTIONS
    titles = HELP_TITLE_TRANSLATIONS.get(lang, {})
    texts  = HELP_TRANSLATIONS.get(lang, {})
    if not titles and not texts:
        return HELP_SECTIONS
    return [
        (titles.get(title, title), texts.get(title, text))
        for title, text in HELP_SECTIONS
    ]

HELP_SECTIONS = [

    ("About", """
THE 3D PRINTING FORMULATOR  —  v1.0
Copyright (c) 2026 Dr Thanos Goulas. All rights reserved.

📧  thanosgoulas@outlook.com

─────────────────────────────────────────────────────

WHAT DOES THIS APP DO?

It calculates the exact amounts of every material in a ceramic
resin or paste recipe — in grams and cm³ — so you can weigh out
your batch accurately at the bench.

You can work in two directions:

  FORWARD  →  You decide the amounts. The app calculates the final
               composition (wt.%, vol.%, mixture density).

  INVERSE  →  You decide the composition you want (e.g. 45 vol.%
               alumina). The app calculates the amounts for you.

─────────────────────────────────────────────────────

NAVIGATING THE APP

The left sidebar contains:
  • Inverse Solver      — switch to the Inverse Solver tab
  • Forward Formulator  — switch to the Forward Formulator tab
  • Materials DB        — open the Materials Database editor
  • Help                — open this guide

The top bar on each tab contains:
  • Recipe / File Name  — the name of your current recipe
  • 💾 Save             — save the recipe to a .json file
  • 📂 Load             — load a previously saved recipe
  • 📄 Export PDF       — export results to a PDF report
  • 📤 Share            — share the file via email or Teams

The bottom strip shows the summary results (total mass, volume,
density, solids loading) and the status bar shows what the app
just did.

─────────────────────────────────────────────────────

MATERIALS DATABASE

The database contains ~200 materials (ceramics, monomers,
photoinitiators, dispersants, solvents and more) — each with
density, refractive index, and molecular weight.

Selecting a material from the dropdown fills in its density
automatically, saving time and preventing errors.

You can add, edit, or delete materials at any time. Your database
is saved automatically and persists between sessions.

─────────────────────────────────────────────────────

DISCLAIMER

Density values have been sourced from Sigma-Aldrich, PubChem,
NIST, CRC Handbook, and manufacturer datasheets, and cross-
checked where possible.

⚠  Density can vary with grade, purity, temperature, and
   supplier. Always verify against your material's SDS before
   use in critical formulations. The developer accepts no
   responsibility for errors arising from unverified values.

─────────────────────────────────────────────────────

FEEDBACK & BUG REPORTS

If you find an error, have a suggestion, or would like a material
added to the database, please contact:
📧  thanosgoulas@outlook.com
"""),


    ("Quick Start Guide", """
NEW TO THE APP? START HERE.

This guide walks you through a complete worked example from scratch
using the Inverse Solver — the most commonly used tab.

─────────────────────────────────────────────────────

EXAMPLE FORMULATIONS

Two real recipe files from published research are available
as a free download alongside this app on GitHub:

  📦  Example Formulations.zip

Download, extract, and open the .json files using the
📂 Load button in the top bar of any tab. These examples
are taken from the following publications:

  • Goulas et al. (2025). Enabling accessible additive manufacturing
    of alumina ceramics through formulation design.
    Materials & Design, 114601.
    https://doi.org/10.1016/j.matdes.2025.114601

  • Goulas et al. (2025). Formulation-driven additive manufacturing
    of 3YSZ advanced ceramics via digital light processing.
    Open Ceramics, 100785.
    https://doi.org/10.1016/j.oceram.2025.100785

If you use these formulations in your work, please cite
the original publications as well as this software.

─────────────────────────────────────────────────────

EXAMPLE RECIPE

  Target:   45 vol.% Al₂O₃ in an HDDA monomer resin
  Batch:    200 g of alumina
  Additive: 1 wt.% BAPO photoinitiator on the total batch

─────────────────────────────────────────────────────

STEP 1 — Name your recipe

At the top of the window, click the "Recipe / File Name" box
and type a name, for example:

  Al2O3 45vol% HDDA

This name will appear in the PDF report and will be used as
the filename when you save.

─────────────────────────────────────────────────────

STEP 2 — Open the Inverse Solver

Click "Inverse Solver" in the left sidebar.
(Use this tab whenever you have a target solids loading in mind.)

─────────────────────────────────────────────────────

STEP 3 — Set the target

In the TARGET row at the top of the tab:
  • Type  45  in the number box.
  • Select  vol.%  from the dropdown.

This tells the app: "I want alumina to be 45% of the total volume."

─────────────────────────────────────────────────────

STEP 4 — Add the ceramic as the ANCHOR

In the input row below the table:
  • Component:      click ▼, type "Al2O3", select it.
                    Density fills in automatically (3.987 g/cm³).
  • Relationship:   choose  Primary
  • Primary mode:   choose  Mass (g)
  • Value:          type  200

Click ➕ Add.

  → "I am using 200 g of alumina. Scale everything else so that
    alumina ends up at exactly 45 vol.% of the total."

─────────────────────────────────────────────────────

STEP 5 — Add the monomer as the BALANCE

  • Component:      click ▼, type "HDDA", select it.
  • Relationship:   choose  Balance
  • Value:          leave at  0  (the solver calculates this)

Click ➕ Add.

  → "Calculate how much HDDA is needed to hit the target."

─────────────────────────────────────────────────────

STEP 6 — Add the photoinitiator

  • Component:      click ▼, type "BAPO", select it.
  • Relationship:   choose  wt.% of Total Suspension
  • Value:          type  1

Click ➕ Add.

  → "BAPO makes up 1 wt.% of the total final batch mass."

─────────────────────────────────────────────────────

STEP 7 — Solve

Click ⚙ SOLVE (far right of the button row).

The table fills in immediately with the mass and volume of
every component. The summary strip at the bottom shows:
  • Total Mass (g) and Total Volume (cm³)
  • Mixture Density (g/cm³)
  • Achieved Primary loading in wt.% and vol.%

─────────────────────────────────────────────────────

STEP 8 — Save and export

  💾 Save        →  saves the recipe so you can reload it later.
                    The filename is taken from the Recipe Name.
  📄 Export PDF  →  saves a formatted A4 report for your lab notebook.
  📤 Share       →  send the file via email or Microsoft Teams.

─────────────────────────────────────────────────────

THAT'S IT!

Read the other sections of this guide to learn about all the
input modes, the Forward Formulator, the Materials Database,
and tips for efficient use.
"""),


    ("The Materials Database", """
THE MATERIALS DATABASE

The database stores the physical properties of every material
the app knows about: density (g/cm³), refractive index (RI),
and molecular weight (MW g/mol).

Whenever you select a material in the recipe builder, its
density is filled in automatically.

─────────────────────────────────────────────────────

HOW TO SEARCH FOR A MATERIAL

In the Component field, click the ▼ arrow button. A panel drops
down showing all materials.

  • Scroll through the list, OR
  • Start typing to filter results — the search looks at both
    the acronym AND the full chemical name.
    Example: typing "acrylate" shows all acrylate monomers.

Click a material to select it. Its name and density fill in
automatically.

─────────────────────────────────────────────────────

HOW TO OPEN THE DATABASE EDITOR

Click "🗃 Materials DB" in the bottom-left of the sidebar.

The editor shows all materials in a table with five columns:
  Acronym · Full Name · Density (g/cm³) · RI · MW (g/mol)

You can search by typing in the Search box at the top.

─────────────────────────────────────────────────────

HOW TO ADD A NEW MATERIAL

1. Type the acronym in the "Acronym" field  (e.g. TCDDA, BaTiO3)
2. Type the full chemical name in "Full Name"  (optional)
3. Enter the density in g/cm³ in "Density"  ← REQUIRED
4. Optionally enter the refractive index in "RI"
5. Optionally enter the molecular weight in "MW (g/mol)"
6. Click ➕ Add / Update

The material is saved and sorted alphabetically.

─────────────────────────────────────────────────────

HOW TO EDIT AN EXISTING MATERIAL

1. Click the material's row in the table.
   Its details load into the edit fields below.
2. Change any field.
3. Click ➕ Add / Update to save.

─────────────────────────────────────────────────────

HOW TO DELETE A MATERIAL

1. Click the material's row.
2. Click 🗑 Delete.
3. Confirm when prompted.

─────────────────────────────────────────────────────

HOW TO CREATE A BLEND

If you regularly use a mixture of monomers (e.g. 50 wt.% HDDA
+ 50 wt.% TMP(EO)3TA), save it as a single named blend entry
with a pre-calculated effective density.

1. Click ⊕ Create Blend.
2. Select each component from the dropdowns and enter its wt.%.
   Values must total exactly 100%.
3. Click ⟳ Calculate Density — the app uses ideal mixing.
4. Give the blend a name (auto-suggested from components).
5. Click 💾 Save to Database.

The blend appears in the database like any other material.

─────────────────────────────────────────────────────

EXPORTING AND IMPORTING THE DATABASE

To back up or share your database:

  Export:  In the database editor → click 📤 Export DB.
           Saves your entire database to a .json file.

  Import:  In the database editor → click 📥 Import DB.
           Adds or updates entries from the imported file.
           Existing entries are NEVER deleted.

─────────────────────────────────────────────────────

WHERE IS THE DATABASE FILE STORED?

When running as a compiled .exe:
  %APPDATA%\\3DPrintingFormulator\\3dpformulator_materialsdatabase.json

When running from Python source:
  In the same folder as formulator.py

The file updates automatically whenever you add, edit, or delete
a material. No manual saving is needed.

⚠  If you delete the database file, it resets to factory
   defaults on the next launch. Always export a backup first.
"""),


    ("Forward Formulator", """
THE FORWARD FORMULATOR

Use this tab when YOU decide how much of each material to use,
and you want the app to calculate the resulting composition.

─────────────────────────────────────────────────────

WORKFLOW

1. Enter a component name (use ▼ for autocomplete and density).
2. Choose the Input Mode (see below).
3. Enter the Value (and Reference if needed).
4. Click ➕ Add.
5. Repeat for all components.
6. Click ⚙ CALCULATE (far right of the button row).

Results appear in the table: Mass · Volume · wt.% · vol.%
Summary boxes show the totals and mixture density.

─────────────────────────────────────────────────────

THE SIX INPUT MODES

────────────────────────────────────────
MODE 1:  Mass (g)
────────────────────────────────────────
  You enter the exact mass in grams.
  App converts to volume:  V = mass / density

  Use when:  you know exactly how many grams you want.

  Example:  Al₂O₃  →  Mass (g)  →  200
            → 200 g of alumina added to the batch.

────────────────────────────────────────
MODE 2:  Volume (cm³)
────────────────────────────────────────
  You enter the exact volume in cm³ (= mL).
  App converts to mass:  m = volume × density

  Use when:  measuring a liquid by pipette or cylinder.

  Example:  HDDA  →  Volume (cm³)  →  50
            → 50 cm³ of HDDA added.

────────────────────────────────────────
MODE 3:  wt.% to Reference
────────────────────────────────────────
  This component's mass is a % of another component's mass.
  You must specify the Reference component.

  Formula:  mass_this = (Value / 100) × mass_of_Reference

  Use when:  dosing dispersants as % of ceramic mass.

  Example:  Dispersant  →  wt.% to Reference  →  2  →  Ref: Al₂O₃
            If Al₂O₃ = 200 g → Dispersant = 2% × 200 = 4 g

────────────────────────────────────────
MODE 4:  vol.% to Reference
────────────────────────────────────────
  Same as Mode 3 but the percentage is of VOLUME.

  Formula:  volume_this = (Value / 100) × volume_of_Reference

  Example:  Plasticiser  →  vol.% to Reference  →  5  →  Ref: HDDA
            If HDDA = 50 cm³ → Plasticiser = 5% × 50 = 2.5 cm³

────────────────────────────────────────
MODE 5:  wt.% of Total
────────────────────────────────────────
  This component is a fixed % of the TOTAL batch mass.
  The app solves the algebra to make the total consistent.

  Use when:  photoinitiators dosed relative to total resin.

  Example:  BAPO  →  wt.% of Total  →  1
            If total batch = 250 g → BAPO = 1% × 250 = 2.5 g

  ⚠  The sum of ALL wt.% of Total values must be less than 100%.

────────────────────────────────────────
MODE 6:  vol.% of Total
────────────────────────────────────────
  Same as Mode 5 but as a volume percentage of the total.

  ⚠  The sum of ALL vol.% of Total values must be less than 100%.

─────────────────────────────────────────────────────

TIPS

  ✓  You can freely mix all six modes in the same recipe.
  ✓  Use the ▼ button on the Reference field to pick from
     components already in the recipe — avoids spelling errors.
  ✓  Component order does not affect calculations.
     Use ▲ Up / ▼ Down to reorder for presentation only.
"""),


    ("Inverse Solver", """
THE INVERSE SOLVER

Use this tab when you have a target solids loading in mind and
want the app to calculate the amounts for you.

"I want 45 vol.% alumina" → the app tells you how much HDDA.

─────────────────────────────────────────────────────

THE TARGET BAR  (top of the tab)

  • Target value:  the desired loading percentage (e.g. 45)
  • Target mode:   vol.% or wt.%

  vol.%  →  Primary will be that % of the TOTAL VOLUME.
  wt.%   →  Primary will be that % of the TOTAL MASS.

─────────────────────────────────────────────────────

THE SEVEN RELATIONSHIP TYPES

────────────────────────────────────────
RELATIONSHIP 1:  Primary
────────────────────────────────────────
  The CERAMIC or main filler — the component whose loading
  you are targeting.

  Rules:  EXACTLY 1 Primary per recipe. No more, no less.

  You specify:
    • Primary mode:  Mass (g) or Volume (cm³)
    • Value:        the absolute amount of the Primary

  Example:  Al₂O₃  →  Primary  →  Mass (g)  →  200
            "I am using 200 g of alumina."

────────────────────────────────────────
RELATIONSHIP 2:  Balance
────────────────────────────────────────
  The SOLVENT or MONOMER whose amount the solver calculates
  to hit the target loading.

  Rules:  At most 1 Balance. Leave Value = 0.

  Example:  HDDA  →  Balance  →  0
            "Calculate how much HDDA I need."

  ⚠  No Balance? The solver finds a scale factor k that
     multiplies all scalable components to hit the target.
     (see the Formulae & Theory section for details)

────────────────────────────────────────
RELATIONSHIP 3:  wt.% to Reference
────────────────────────────────────────
  This component's mass is a % of another component's mass.

  Formula:  mass_this = (Value / 100) × mass_of_Reference

  Example:  DISPERBYK-111  →  wt.% to Reference  →  2  →  Ref: Al₂O₃
            If Al₂O₃ = 200 g → Dispersant = 2% × 200 = 4 g

────────────────────────────────────────
RELATIONSHIP 4:  vol.% to Reference
────────────────────────────────────────
  Same but as a volume percentage.

  Example:  Additive  →  vol.% to Reference  →  5  →  Ref: HDDA
            Additive volume = 5% × HDDA volume

────────────────────────────────────────
RELATIONSHIP 5:  wt.% of Total Suspension
────────────────────────────────────────
  This component is a fixed wt.% of the entire final batch.
  It is resolved AFTER the Balance is calculated.

  Example:  BAPO  →  wt.% of Total Suspension  →  1
            BAPO = 1 wt.% of the total batch mass.

  ⚠  Sum of all wt.% of Total Suspension values must be < 100%.

────────────────────────────────────────
RELATIONSHIP 6:  vol.% of Total Suspension
────────────────────────────────────────
  Same but as a volume percentage of the final batch.

  ⚠  Sum of all vol.% of Total Suspension values must be < 100%.

────────────────────────────────────────
RELATIONSHIP 7:  Independent Mass / Vol
────────────────────────────────────────
  A fixed amount that does NOT scale with anything.

  Independent Mass (g):   always adds exactly Value grams.
  Independent Vol (cm³):  always adds exactly Value cm³.

  Use when:  a small fixed additive is always the same amount
             regardless of batch size.

─────────────────────────────────────────────────────

RULES SUMMARY

  ✓  Exactly 1 Primary required.
  ✓  At most 1 Balance allowed. Leave its Value = 0.
  ✓  All component names must be unique.
  ✓  Reference names must exactly match another component.
  ✓  wt.%/vol.% of Total Suspension must sum to less than 100%.

─────────────────────────────────────────────────────

READING THE RESULTS

After clicking ⚙ SOLVE:

  Table:          Mass (g) · Volume (cm³) · wt.% · vol.%
  Summary strip:  Total Mass · Total Volume · Mixture Density
                  Achieved Primary wt.% and vol.%

  The achieved loadings should match your target.

  k value (top bar):  scale factor used when there is no Balance.
                      When a Balance is present, k = 1.0000.

─────────────────────────────────────────────────────

TYPICAL RECIPE EXAMPLE

  Component         Relationship                Value   Reference
  ─────────────     ───────────────────────     ─────   ─────────
  Al₂O₃             Primary (Mass g)             200
  HDDA               Balance                       0
  TMP(EO)3TA         wt.% to Reference            50     HDDA
  DISPERBYK-111      wt.% to Reference             2     Al₂O₃
  BAPO               wt.% of Total Suspension      1
  CQ                 wt.% of Total Suspension      0.5

  Target: 45 vol.%
"""),


    ("Editing & Managing Components", """
EDITING A COMPONENT

1. Click the component's row in the table (it highlights blue).
   Its details load into the input fields below.
2. Make your changes.
3. Click ✏ Update to save.

⚠  Do NOT click ➕ Add when editing — that would create a
   duplicate. Always use ✏ Update for existing components.

─────────────────────────────────────────────────────

REMOVING A COMPONENT

1. Click the row to select it.
2. Click 🗑 Remove.

─────────────────────────────────────────────────────

REORDERING COMPONENTS

1. Click the row you want to move.
2. Click ▲ Up or ▼ Down in the button bar.

Order affects the table and PDF report appearance only.
It has NO effect on calculations.

─────────────────────────────────────────────────────

CLEARING THE ENTIRE RECIPE

Click ✖ Clear All to remove everything and reset the table.
You will be asked to confirm first.

⚠  This cannot be undone — save your recipe before clearing
   if you might want to keep it.

─────────────────────────────────────────────────────

DUPLICATING A COMPONENT

There is no dedicated duplicate button, but you can:
1. Click a row to load it into the input fields.
2. Change the component name to something new.
3. Click ➕ Add.

─────────────────────────────────────────────────────

CHANGING THE RECIPE NAME

The "Recipe / File Name" box is at the top of the window.
Click it and type a new name at any time.

The name is used:
  • In the PDF report header
  • As the default filename when you Save or Export PDF

When you Save or Load a file, the Recipe Name automatically
updates to match the filename — so they stay in sync.
"""),


    ("Save, Load & PDF Export", """
SAVING A RECIPE

Click 💾 Save  (top-right of each tab).

A file dialog opens with the Recipe Name pre-filled as the
filename. Choose a location and click Save.

The file is saved as .json format.

What IS saved:
  ✓  Recipe name
  ✓  All component names, densities, modes, values, references
  ✓  Which tab was active (Forward or Inverse)
  ✓  Target value and mode (Inverse Solver)

What is NOT saved:
  ✗  Calculated results  (press CALCULATE/SOLVE after loading)

After saving, the "Recipe / File Name" field updates to match
the filename you chose.

─────────────────────────────────────────────────────

LOADING A RECIPE

Click 📂 Load  (top-right of each tab).

Select a previously saved .json file. All components are
restored exactly as saved. The Recipe Name updates to match
the filename automatically.

⚠  After loading, press ⚙ CALCULATE or ⚙ SOLVE to regenerate
   the results — they are not stored in the file.

─────────────────────────────────────────────────────

EXPORTING TO PDF

Click 📄 Export PDF  (top-right of each tab).

You must calculate/solve first. If no results exist, the app
will remind you to calculate before exporting.

The PDF report includes:
  • Recipe name, date, and developer information
  • Full component table:
    Component · Density · Mass (g) · Volume (cm³) · wt.% · vol.%
  • Summary: Total Mass · Total Volume · Theoretical Density
  • For Inverse Solver:
    Target mode and value · Achieved Primary wt.% and vol.%

Formatted for printing on A4 paper.

─────────────────────────────────────────────────────

SHARING A FILE

Click 📤 Share  (top-right of each tab, rightmost button).

You do not need to save the file first — the Share button
generates a file automatically if needed:
  • If results exist → generates a PDF
  • If no results yet → generates a .json recipe file

A dialog then opens with two options:

  ✉ Email  →  Opens Outlook with the file already attached,
               subject line pre-filled. Ready to send.

  💬 Teams →  Opens File Explorer with the file highlighted.
               Drag it into a Teams chat or channel, or use
               the Teams attachment button (📎) to browse to it.

─────────────────────────────────────────────────────

FILE FORMAT NOTES

  Recipe files (.json):  can be saved anywhere on your computer.
  PDF reports:           standard PDF, opens in any PDF viewer.
  Materials database:    auto-saved — see the Materials Database
                         section for its location.

  Recipe .json files can be opened in any text editor.
  Do not manually edit them unless you know what you are doing.
"""),


    ("Tips & Troubleshooting", """
─────────────────────────────────────────────────────
COMMON MISTAKES AND HOW TO FIX THEM
─────────────────────────────────────────────────────

PROBLEM:  Solver error or wrong volumes
────────────────────────────────────────
  Cause:  A density value is wrong, missing, or set to zero.
  Fix:    Check every component's density. It must be in g/cm³.
          Use the ▼ dropdown to select from the database —
          this fills in the correct density automatically.

─────────────────────────────────────────────────────

PROBLEM:  "Reference not found" error
──────────────────────────────────────
  Cause:  The reference name does not exactly match any
          component in the recipe. Even one extra space
          or a different capitalisation will cause this.
  Fix:    Use the ▼ dropdown on the Reference field to pick
          directly from the components already in the recipe.
          This guarantees an exact match every time.

─────────────────────────────────────────────────────

PROBLEM:  "No Primary found" error  (Inverse Solver only)
──────────────────────────────────────────────────────────
  Cause:  No component has Relationship = Primary.
  Fix:    Select the ceramic/filler row → change its
          Relationship to "Primary" → click ✏ Update.

─────────────────────────────────────────────────────

PROBLEM:  "Multiple Primary" error  (Inverse Solver only)
──────────────────────────────────────────────────────────
  Cause:  More than one component is set to Primary.
  Fix:    Set all but one back to a different relationship.

─────────────────────────────────────────────────────

PROBLEM:  Balance result is negative or enormous
──────────────────────────────────────────────────
  Cause:  The target loading may be geometrically impossible.
          For example: if dispersant + photoinitiator already
          occupy 60 vol.% of the suspension, you cannot also
          target 55 vol.% ceramic.
  Fix:    Reduce the target %, or reduce other components'
          values.

─────────────────────────────────────────────────────

PROBLEM:  wt.% and vol.% columns don't sum to 100%
────────────────────────────────────────────────────
  This is NORMAL — it is expected if any component is
  specified in absolute amounts (g or cm³) rather than
  percentages. The wt.% and vol.% columns always show
  the correct proportion of each component in the final
  mixture.

─────────────────────────────────────────────────────

PROBLEM:  Two components with the same name
────────────────────────────────────────────
  Cause:  All component names must be unique in a recipe.
  Fix:    Rename one (e.g. "HDDA-1" and "HDDA-2").

─────────────────────────────────────────────────────

PROBLEM:  Loaded a recipe but results are blank
────────────────────────────────────────────────
  Cause:  Calculated results are not saved in the .json file.
  Fix:    Press ⚙ CALCULATE or ⚙ SOLVE after loading.

─────────────────────────────────────────────────────

PROBLEM:  Recipe name still shows "My Formulation"
────────────────────────────────────────────────────
  Fix:    Click the "Recipe / File Name" box at the top
          and type your recipe name before saving.
          The name updates automatically when you Save
          or Load a file.

─────────────────────────────────────────────────────
TIPS FOR EFFICIENT USE
─────────────────────────────────────────────────────

  ✓  Always use the ▼ dropdown on the Component field.
     It auto-fills the density and prevents spelling errors.

  ✓  Always use the ▼ dropdown on the Reference field.
     It shows only components already in your recipe.

  ✓  Save your recipe BEFORE experimenting with values.
     Use 📂 Load to return to the saved version if needed.

  ✓  Use ⊕ Create Blend in the Materials Database for
     monomer mixtures you use regularly — then treat the
     blend as a single material in your recipes.

  ✓  Export a PDF after each successful formulation for
     your lab records.

  ✓  The status bar at the bottom always shows what the
     app just did — check it after every action.

  ✓  Hover the mouse over any button to see a tooltip
     describing what it does.

  ✓  The window is fully resizable and columns adjust
     automatically with the window width.
"""),


    ("Settings & Accessibility", """
SETTINGS DIALOG

Open it via the ⚙ Settings button at the bottom of the left sidebar.
Changes are saved automatically to a settings.json file next to your
materials database and are restored every time the app starts.

─────────────────────────────────────────────────────

APPEARANCE

────────────────────────────────────────
Font size
────────────────────────────────────────
  Controls how large all text and controls appear.

  Small         — compact layout, fits more on screen
  Normal        — default (recommended)
  Large         — easier to read on high-DPI screens
  Extra Large   — for presentations or low-vision use

  ✓  Takes effect immediately when you click Apply or OK.

────────────────────────────────────────
High contrast mode
────────────────────────────────────────
  Switches the app to a dark blue theme with higher contrast between
  text and background. Useful for:
    • Users with visual impairments
    • Working in a dark lab environment

  ✓  Takes effect immediately when you click Apply or OK.

────────────────────────────────────────
Colour-blind safe palette
────────────────────────────────────────
  Replaces the red and green colours used for warnings and results
  with blue and orange — distinguishable under the most common forms
  of colour blindness (deuteranopia, protanopia).

  ✓  This change takes effect immediately without a restart.

─────────────────────────────────────────────────────

BEHAVIOUR

────────────────────────────────────────
Confirm before removing or clearing
────────────────────────────────────────
  When enabled (default), the app asks "Are you sure?" before:
    • Removing a component from the recipe
    • Clearing all components

  Turn this off if you find the prompts unnecessary and prefer
  faster editing. Accidental changes can always be undone by
  reloading your saved recipe with 📂 Load.

────────────────────────────────────────
Larger click targets
────────────────────────────────────────
  Increases the padding inside all buttons, making them taller
  and easier to click. Useful for:
    • Touch-screen laptops or tablets
    • Users with reduced motor precision

  ✓  Takes effect immediately when you click Apply or OK.

─────────────────────────────────────────────────────

LANGUAGE

Select the UI language from the Language dropdown at the top of
the Appearance section in Settings.

  ✓  Takes effect immediately when you click Apply or OK.

Available languages: English, Greek, French, German, Spanish,
Italian, Dutch, Chinese (Simplified), Japanese, Korean, Hindi.

Note: the Help text, materials database, and scientific notation
(wt.%, vol.%, g/cm³) remain in English in all languages — these
are internationally standardised scientific terms.

─────────────────────────────────────────────────────

RESTORE DEFAULTS

Click the _T("Restore Defaults") button at the bottom-left of the
Settings dialog to reset all settings to their factory values.
A confirmation prompt will appear before anything is changed.

─────────────────────────────────────────────────────

WHERE ARE SETTINGS STORED?

When running as a compiled .exe:
  %APPDATA%\\3DPrintingFormulator\\3dpformulator_usersettings.json

When running from Python source:
  In the same folder as formulator.py

The file is plain JSON and can be opened in any text editor.
Delete it to reset all settings to defaults.
"""),

        ("Formulae & Theory", """
This section covers the mathematics used by the app.
Useful for manually verifying results or understanding
how the solver works.

─────────────────────────────────────────────────────
NOTATION
─────────────────────────────────────────────────────

  mᵢ         mass of component i  [g]
  Vᵢ         volume of component i  [cm³]
  ρᵢ         density of component i  [g/cm³]
  M_tot      total batch mass  [g]
  V_tot      total batch volume  [cm³]
  T          target loading as a fraction  (45% → T = 0.45)
  n          number of components

─────────────────────────────────────────────────────
FUNDAMENTAL CONVERSIONS
─────────────────────────────────────────────────────

  Volume from mass:        Vᵢ = mᵢ / ρᵢ
  Mass from volume:        mᵢ = Vᵢ · ρᵢ

─────────────────────────────────────────────────────
BATCH TOTALS AND COMPOSITION
─────────────────────────────────────────────────────

  Total mass:              M_tot = m₁ + m₂ + ... + mₙ
  Total volume:            V_tot = V₁ + V₂ + ... + Vₙ

  Theoretical density:     ρ_mix = M_tot / V_tot

  Weight fraction (wt.%):  wt.%ᵢ  = 100 · mᵢ / M_tot
  Volume fraction (vol.%): vol.%ᵢ = 100 · Vᵢ / V_tot

─────────────────────────────────────────────────────
FORWARD FORMULATOR — HOW EACH INPUT MODE IS RESOLVED
─────────────────────────────────────────────────────

  Mass (g):
    mᵢ = value entered
    Vᵢ = mᵢ / ρᵢ

  Volume (cm³):
    Vᵢ = value entered
    mᵢ = Vᵢ · ρᵢ

  wt.% to Reference  (reference component = r):
    mᵢ = (value / 100) · m_r
    Vᵢ = mᵢ / ρᵢ
    Example: Dispersant 2 wt.% to Al₂O₃ (200 g)
             → mᵢ = 0.02 × 200 = 4 g

  vol.% to Reference  (reference component = r):
    Vᵢ = (value / 100) · V_r
    mᵢ = Vᵢ · ρᵢ

  wt.% of Total  (algebraic solution):
    Let S = (sum of all wt.%-of-Total values) / 100
    Let M_abs = sum of masses of all other components
    M_tot = M_abs / (1 − S)
    mᵢ = (value / 100) · M_tot

    Example: BAPO at 1 wt.% of Total, other components = 247.5 g
             S = 0.01
             M_tot = 247.5 / 0.99 = 250 g
             m_BAPO = 0.01 × 250 = 2.5 g

  vol.% of Total  (analogous to wt.% of Total):
    Let S = (sum of all vol.%-of-Total values) / 100
    Let V_abs = sum of volumes of all other components
    V_tot = V_abs / (1 − S)
    Vᵢ = (value / 100) · V_tot

─────────────────────────────────────────────────────
INVERSE SOLVER — RELATIONSHIP RESOLUTION
─────────────────────────────────────────────────────

  wt.% to Reference:
    mᵢ = (value / 100) · m_r  (same as Forward)

  vol.% to Reference:
    Vᵢ = (value / 100) · V_r  (same as Forward)

  wt.% of Total Suspension  (resolved after Balance):
    Let F_pm = sum of all wt.%-of-Total fractions
    Let M_non = sum of masses of all non-suspension components
    M_tot = M_non / (1 − F_pm)
    mᵢ = (value / 100) · M_tot

  vol.% of Total Suspension  (analogous):
    Let F_pv = sum of all vol.%-of-Total fractions
    Let V_non = sum of volumes of all non-suspension components
    V_tot = V_non / (1 − F_pv)
    Vᵢ = (value / 100) · V_tot

  Independent Mass (g):   mᵢ = value  (fixed, does not scale)
  Independent Vol (cm³):  Vᵢ = value  (fixed, does not scale)

─────────────────────────────────────────────────────
INVERSE SOLVER — BALANCE CALCULATION
─────────────────────────────────────────────────────

The solver finds the Balance mass (m_B) such that the Primary
reaches exactly the target loading T.

  For a vol.% target:
    V_B = V_anc · (1 − F_pv) / T − V_anc − V_kn
    m_B = V_B · ρ_B

  For a wt.% target:
    m_B = M_anc · (1 − F_pm) / T − M_anc − M_kn

  Where:
    V_anc, M_anc  = volume and mass of the Primary
    V_kn, M_kn    = total volume and mass of all other known
                    components (not Primary, not Balance)
    F_pv, F_pm    = sum of vol.%/wt.%-of-Total fractions
    ρ_B           = density of the Balance

─────────────────────────────────────────────────────
INVERSE SOLVER — SCALE FACTOR  (no Balance component)
─────────────────────────────────────────────────────

When there is no Balance, the solver finds k such that all
scalable components are multiplied by k to hit the target.

  For a vol.% target:
    k = (V_anc_fixed − T · V_fixed_total)
        / (T · V_scalable_total − V_anc_scalable)

  For a wt.% target  (same form, with masses):
    k = (M_anc_fixed − T · M_fixed_total)
        / (T · M_scalable_total − M_anc_scalable)

  "fixed"    = components with Independent Mass/Vol
  "scalable" = all other components

  Final quantities: mᵢ_final = k · mᵢ , Vᵢ_final = k · Vᵢ

─────────────────────────────────────────────────────
IDEAL MIXING  (used in Create Blend)
─────────────────────────────────────────────────────

  1 / ρ_blend = Σ (wᵢ / ρᵢ)

  where wᵢ = weight fraction of component i.

  Assumes volumes are additive (no volume change on mixing).
  A good approximation for organic monomer systems.

─────────────────────────────────────────────────────
WORKED EXAMPLE — FULL INVERSE SOLVE
─────────────────────────────────────────────────────

Recipe:   200 g Al₂O₃ (ρ = 3.987),  target = 45 vol.%
          Balance: HDDA (ρ = 1.010)
          BAPO: 1 wt.% of Total Suspension

Step 1 — Primary volume:
  V_anc = 200 / 3.987 = 50.16 cm³

Step 2 — F_pm = 0.01  (BAPO is wt.%-of-Total, not vol.%)
         F_pv = 0

Step 3 — Balance volume needed:
  V_B = 50.16 · (1 − 0) / 0.45 − 50.16 = 61.31 cm³
  m_B = 61.31 × 1.010 = 61.92 g

Step 4 — BAPO  (wt.% of Total):
  M_non = 200 + 61.92 = 261.92 g
  M_tot = 261.92 / (1 − 0.01) = 264.57 g
  m_BAPO = 0.01 × 264.57 = 2.65 g

Step 5 — Final check:
  V_BAPO = 2.65 / 1.190 = 2.23 cm³
  V_tot  = 50.16 + 61.31 + 2.23 = 113.70 cm³
  vol.% Al₂O₃ = 50.16 / 113.70 × 100 = 44.1%
  (Small deviation because BAPO occupies volume;
   solver iterates to exact solution.)
"""),

]



# ─────────────────────────────────────────────
#  SETTINGS DIALOG
# ─────────────────────────────────────────────
class SettingsDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title(_T("Settings"))
        _set_icon(self)
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(480, 420)
        self.grab_set()
        self._s = dict(app.settings)
        self._build()
        # Let tkinter calculate the natural height after all widgets are packed,
        # then set that as the window size — works correctly at any font scale.
        self.update_idletasks()
        w = max(500, self.winfo_reqwidth())
        h = max(440, self.winfo_reqheight())
        self.geometry(f"{w}x{h}")

    def _build(self):
        tk.Frame(self, bg=ACCENT, height=3).pack(fill="x")

        hdr = tk.Frame(self, bg=BG_WHITE)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=BORDER, height=1).pack(fill="x", side="bottom")
        tk.Label(hdr, text=_T("⚙  Settings"), bg=BG_WHITE, fg=TEXT,
                 font=("Segoe UI", 13, "bold"),
                 anchor="w", padx=20, pady=12).pack(fill="x")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=12)

        def _section(title):
            tk.Label(body, text=title, bg=BG, fg=ACCENT,
                     font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", pady=(14,4))
            tk.Frame(body, bg=BORDER, height=1).pack(fill="x")

        def _row():
            r = tk.Frame(body, bg=BG); r.pack(fill="x", pady=5); return r

        # ── APPEARANCE ──────────────────────────────────────────────
        _section(_T("APPEARANCE"))

        r = _row()
        tk.Label(r, text="Language:", bg=BG, fg=TEXT,
                 font=("Segoe UI", 9), width=24, anchor="w").pack(side="left")
        self._var_lang = tk.StringVar(
            value=LANGUAGES.get(self._s.get("language", "en"), "English"))
        ttk.Combobox(r, textvariable=self._var_lang,
                     values=list(LANGUAGES.values()),
                     state="readonly", width=22,
                     font=("Segoe UI", 9)).pack(side="left")

        r = _row()
        tk.Label(r, text=_T("Font size:"), bg=BG, fg=TEXT,
                 font=("Segoe UI", 9), width=24, anchor="w").pack(side="left")
        self._var_font = tk.StringVar(value=self._s["font_scale"])
        ttk.Combobox(r, textvariable=self._var_font,
                     values=list(FONT_SCALE_MAP.keys()),
                     state="readonly", width=16,
                     font=("Segoe UI", 9)).pack(side="left")
        r = _row()
        self._var_hc = tk.BooleanVar(value=self._s["high_contrast"])
        tk.Checkbutton(r, text=_T("High contrast mode  (dark theme)"),
                       variable=self._var_hc, bg=BG, fg=TEXT,
                       activebackground=BG, selectcolor=BG_WHITE,
                       font=("Segoe UI", 9)).pack(side="left")
        r = _row()
        self._var_cb = tk.BooleanVar(value=self._s["colorblind_mode"])
        tk.Checkbutton(r, text=_T("Colour-blind safe palette  (swaps red/green → blue/orange)"),
                       variable=self._var_cb, bg=BG, fg=TEXT,
                       activebackground=BG, selectcolor=BG_WHITE,
                       font=("Segoe UI", 9)).pack(side="left")

        # ── BEHAVIOUR ───────────────────────────────────────────────
        _section(_T("BEHAVIOUR"))

        r = _row()
        self._var_confirm = tk.BooleanVar(value=self._s["confirm_destructive"])
        tk.Checkbutton(r,
                       text=_T("Ask for confirmation before removing or clearing components"),
                       variable=self._var_confirm, bg=BG, fg=TEXT,
                       activebackground=BG, selectcolor=BG_WHITE,
                       font=("Segoe UI", 9),
                       wraplength=420, justify="left").pack(side="left", anchor="w")

        r = _row()
        self._var_lt = tk.BooleanVar(value=self._s.get("large_targets", False))
        tk.Checkbutton(r,
                       text=_T("Larger click targets  (increases button padding — easier to click)"),
                       variable=self._var_lt, bg=BG, fg=TEXT,
                       activebackground=BG, selectcolor=BG_WHITE,
                       font=("Segoe UI", 9)).pack(side="left")

        # ── ABOUT ───────────────────────────────────────────────────
        _section(_T("ABOUT"))
        info = tk.Frame(body, bg=ACCENT_SOFT)
        info.pack(fill="x", pady=(4,0))
        tk.Label(info,
                 text="The 3D Printing Formulator  ·  v1.0\n"
                      "Copyright © 2026 Dr Thanos Goulas\n"
                      "thanosgoulas@outlook.com",
                 bg=ACCENT_SOFT, fg=TEXT_DIM,
                 font=("Segoe UI", 8), justify="left",
                 anchor="w", padx=12, pady=8).pack(fill="x")

        # ── BUTTONS ─────────────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", side="bottom")
        bf = tk.Frame(self, bg=BG_HDR, pady=8); bf.pack(fill="x", side="bottom")
        _btn(bf, _T("✔  OK"),      self._ok,     "normal" ).pack(side="right", padx=(6,14))
        _btn(bf, _T("Apply"),      self._apply,  "neutral").pack(side="right", padx=6)
        _btn(bf, _T("✕  Cancel"),  self.destroy, "neutral").pack(side="right", padx=6)
        _btn(bf, _T("Restore Defaults"), self._restore, "neutral").pack(side="left", padx=14)

    def _collect(self):
        lang_display = self._var_lang.get()
        self._s["language"] = next(
            (code for code, name in LANGUAGES.items() if name == lang_display), "en")
        self._s["font_scale"]          = self._var_font.get()
        self._s["high_contrast"]       = self._var_hc.get()
        self._s["colorblind_mode"]     = self._var_cb.get()
        self._s["confirm_destructive"] = self._var_confirm.get()
        self._s["large_targets"]       = self._var_lt.get()

    def _apply(self):
        self._collect()
        self.app.settings = dict(self._s)
        save_settings(self._s)
        # Close the dialog first — it will be destroyed when we rebuild the UI
        self.destroy()
        self.app.live_apply_settings()

    def _ok(self):
        self._apply()   # _apply already destroys self

    def _restore(self):
        if messagebox.askyesno(_T("Restore Defaults"),
                               "Reset all settings to their defaults?", parent=self):
            self._s = dict(SETTINGS_DEFAULTS)
            # Push defaults into all widgets
            self._var_lang.set(LANGUAGES.get(self._s.get("language","en"), "English"))
            self._var_font.set(self._s["font_scale"])
            self._var_hc.set(self._s["high_contrast"])
            self._var_cb.set(self._s["colorblind_mode"])
            self._var_confirm.set(self._s["confirm_destructive"])
            self._var_lt.set(self._s.get("large_targets", False))
            # Apply immediately so the user sees the effect
            self._apply()


# ─────────────────────────────────────────────
#  REGISTRATION DIALOG
# ─────────────────────────────────────────────
class RegisterDialog(tk.Toplevel):
    """Registration dialog for update notifications."""
    _REG_KEY = "registered"

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Register for Updates")
        _set_icon(self)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self._already = app.settings.get(self._REG_KEY, False)
        self._build()
        self.update_idletasks()
        w = max(520, self.winfo_reqwidth())
        h = max(460, self.winfo_reqheight())
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        tk.Frame(self, bg=ACCENT, height=3).pack(fill="x")
        hdr = tk.Frame(self, bg=BG_WHITE)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=BORDER, height=1).pack(fill="x", side="bottom")
        tk.Label(hdr, text="\U0001f4e7  Register for Updates",
                 bg=BG_WHITE, fg=TEXT, font=("Segoe UI", 13, "bold"),
                 anchor="w", padx=20, pady=12).pack(fill="x")
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=14)
        if self._already:
            note = tk.Frame(body, bg="#D1FAE5")
            note.pack(fill="x", pady=(0, 12))
            tk.Label(note,
                     text="  \u2713  You are already registered. Thank you!",
                     bg="#D1FAE5", fg="#065F46",
                     font=("Segoe UI", 9), anchor="w",
                     padx=10, pady=6).pack(fill="x")
        intro = ("Register to receive notifications about new releases and "
                 "materials database updates. You can unsubscribe at any "
                 "time by emailing " + REGISTRATION_EMAIL + ".")
        tk.Label(body, text=intro, bg=BG, fg=TEXT_DIM,
                 font=("Segoe UI", 9), justify="left",
                 wraplength=440, anchor="w").pack(fill="x", pady=(0, 12))
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(0, 12))

        def _row(lbl, var, ph="", req=False):
            r = tk.Frame(body, bg=BG); r.pack(fill="x", pady=4)
            tag = lbl + ("  *" if req else "  (optional)")
            tk.Label(r, text=tag, bg=BG, fg=TEXT,
                     font=("Segoe UI", 9), width=20,
                     anchor="w").pack(side="left")
            e = tk.Entry(r, textvariable=var, width=28,
                         bg=BG_WHITE, fg=TEXT,
                         insertbackground=ACCENT, relief="flat", bd=1,
                         highlightthickness=1,
                         highlightbackground=BORDER_MED,
                         highlightcolor=ACCENT,
                         font=("Segoe UI", 9))
            e.pack(side="left", fill="x", expand=True)
            if ph:
                e.insert(0, ph); e.config(fg=TEXT_MUTED)
                def _fi(ev, en=e, p=ph):
                    if en.get()==p: en.delete(0,'end'); en.config(fg=TEXT)
                def _fo(ev, en=e, p=ph):
                    if not en.get(): en.insert(0,p); en.config(fg=TEXT_MUTED)
                e.bind('<FocusIn>', _fi); e.bind('<FocusOut>', _fo)
            return e

        self._var_name  = tk.StringVar()
        self._var_affil = tk.StringVar()
        self._var_email = tk.StringVar()
        _row("Full Name",     self._var_name,  "e.g. Dr Jane Smith")
        _row("Affiliation",   self._var_affil, "e.g. University of Bath")
        self._email_e = _row("Email Address", self._var_email,
                             "your@email.com", req=True)
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(12, 8))
        n_mats = len(self.app.materials_db)
        info = tk.Frame(body, bg=ACCENT_SOFT)
        info.pack(fill="x")
        tk.Label(info,
                 text=(f"  Software version:    v{APP_VERSION}\n"
                       f"  Materials database:  {n_mats} entries"),
                 bg=ACCENT_SOFT, fg=TEXT_DIM,
                 font=("Segoe UI", 8), justify="left",
                 anchor="w", padx=12, pady=6).pack(fill="x")
        self._var_consent = tk.BooleanVar(value=False)
        tk.Frame(body, bg=BG, height=6).pack()
        tk.Checkbutton(body,
                       text=("I agree to receive occasional update "
                             "notifications from Dr Thanos Goulas. "
                             "I can unsubscribe at any time."),
                       variable=self._var_consent,
                       bg=BG, fg=TEXT_DIM, activebackground=BG,
                       selectcolor=BG_WHITE,
                       font=("Segoe UI", 8),
                       justify="left", anchor="w",
                       wraplength=440).pack(anchor="w", pady=(4, 0))
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(12, 8))
        contrib = ("\U0001f4a1  Want to contribute materials data? "
                   "Send your entries to " + REGISTRATION_EMAIL + " and "
                   "they will be reviewed for inclusion in future database releases.")
        tk.Label(body, text=contrib, bg=BG, fg=TEXT_DIM,
                 font=("Segoe UI", 8, "italic"),
                 justify="left", wraplength=440, anchor="w").pack(fill="x")
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", side="bottom")
        bf = tk.Frame(self, bg=BG_HDR, pady=8)
        bf.pack(fill="x", side="bottom")
        _btn(bf, "\U0001f4e7  Send Registration",
             self._submit, "normal").pack(side="right", padx=(6, 14))
        _btn(bf, "\u2715  Cancel",
             self.destroy, "neutral").pack(side="right", padx=6)

    def _submit(self):
        email = self._var_email.get().strip()
        bad = {"your@email.com", ""}
        if email in bad or "@" not in email or "." not in email:
            messagebox.showwarning("Email Required",
                                   "Please enter a valid email address.",
                                   parent=self)
            self._email_e.focus_set(); return
        if not self._var_consent.get():
            messagebox.showwarning("Consent Required",
                                   "Please tick the consent checkbox to proceed.",
                                   parent=self)
            return
        name   = self._var_name.get().strip()
        affil  = self._var_affil.get().strip()
        n_mats = len(self.app.materials_db)
        from datetime import date as _reg_date
        reg_date = _reg_date.today().strftime("%Y-%m-%d")
        affil_short = affil or "Not provided"
        name_short  = name  or "Not provided"
        body = (
            f"3DP FORMULATOR — NEW USER REGISTRATION\n"
            f"{'='*50}\n\n"
            f"  Name:          {name_short}\n"
            f"  Affiliation:   {affil_short}\n"
            f"  Email:         {email}\n"
            f"  Date:          {reg_date}\n\n"
            f"{'─'*50}\n"
            f"  Software:      The 3D Printing Formulator  v{APP_VERSION}\n"
            f"  DB entries:    {n_mats} materials\n\n"
            f"{'─'*50}\n"
            f"  Consent:       YES — agreed to receive update notifications\n"
            f"  Unsubscribe:   user may email thanosgoulas@outlook.com\n\n"
            f"{'='*50}\n"
            f"Sent automatically from the registration form."
        )
        subject = (
            f"[3DPF] New Registration | "
            f"{name_short} | "
            f"{affil_short} | "
            f"v{APP_VERSION} | "
            f"{reg_date}"
        )
        import urllib.parse, subprocess, sys
        try:
            mailto = (
                f"mailto:{REGISTRATION_EMAIL}"
                f"?subject={urllib.parse.quote(subject)}"
                f"&body={urllib.parse.quote(body)}"
            )
            if sys.platform == 'win32':
                import os; os.startfile(mailto)
            else:
                subprocess.Popen(['xdg-open', mailto])
            self.app.settings[self._REG_KEY] = True
            save_settings(self.app.settings)
            messagebox.showinfo(
                "Registration",
                "Your email client has opened with the registration form.\n\n"
                "Please click Send to complete your registration.\n\n"
                "Thank you!",
                parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not open email client:\n{e}\n\n"
                f"Please email {REGISTRATION_EMAIL} manually.",
                parent=self)


class HelpDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(_T("Help & User Guide — The 3D Printing Formulator"))
        _set_icon(self)
        self.configure(bg=SIDEBAR)
        self.geometry(f"{_s(980)}x{_s(640)}")
        self.minsize(_s(760), _s(500))
        self.resizable(True, True)
        self._nav_items = []   # (frame, label, index)
        self._build()

    def _build(self):
        # ── Accent bar ───────────────────────────────────────────────
        tk.Frame(self, bg=ACCENT, height=3).pack(fill="x")

        # ── Main area: sidebar nav | content ─────────────────────────
        body = tk.Frame(self, bg=SIDEBAR)
        body.pack(fill="both", expand=True)

        # ── Left sidebar ─────────────────────────────────────────────
        sb = tk.Frame(body, bg=SIDEBAR, width=_s(210))
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        # Sidebar header
        tk.Label(sb, text=_T("Help & User Guide"), bg=SIDEBAR, fg="#FFFFFF",
                 font=("Segoe UI", 11, "bold"), anchor="w",
                 padx=18, pady=14).pack(fill="x")
        tk.Frame(sb, bg=SIDEBAR_HOV, height=1).pack(fill="x")

        # Nav items
        def _make_nav(title, idx):
            f = tk.Frame(sb, bg=SIDEBAR, cursor="hand2")
            f.pack(fill="x", padx=8, pady=1)
            lb = tk.Label(f, text=f"  {title}", bg=SIDEBAR, fg=SIDEBAR_FG,
                          font=("Segoe UI", 9), anchor="w", padx=8, pady=6,
                          wraplength=_s(190), justify="left")
            lb.pack(fill="x")
            def _click(e=None):
                self._show_section(idx)
                for fi, li, ii in self._nav_items:
                    c = SIDEBAR_SEL if ii == idx else SIDEBAR
                    fi.config(bg=c); li.config(bg=c)
            def _ent(e):
                if f.cget("bg") != SIDEBAR_SEL:
                    f.config(bg=SIDEBAR_HOV); lb.config(bg=SIDEBAR_HOV)
            def _lea(e):
                if f.cget("bg") != SIDEBAR_SEL:
                    f.config(bg=SIDEBAR); lb.config(bg=SIDEBAR)
            for w in (f, lb):
                w.bind("<Button-1>", _click)
                w.bind("<Enter>", _ent)
                w.bind("<Leave>", _lea)
            self._nav_items.append((f, lb, idx))

        for i, (title, _) in enumerate(_get_help_sections(_LANG)):
            _make_nav(title, i)

        # Close button at bottom of sidebar
        tk.Frame(sb, bg=SIDEBAR_HOV, height=1).pack(fill="x", side="bottom")
        close_f = tk.Frame(sb, bg=SIDEBAR, cursor="hand2")
        close_f.pack(side="bottom", fill="x", padx=8, pady=4)
        close_lb = tk.Label(close_f, text="  ✕  Close", bg=SIDEBAR,
                            fg=SIDEBAR_FG2, font=("Segoe UI", 9),
                            anchor="w", padx=8, pady=8)
        close_lb.pack(fill="x")
        for w in (close_f, close_lb):
            w.bind("<Button-1>", lambda e: self.destroy())
            w.bind("<Enter>",    lambda e: (close_f.config(bg=SIDEBAR_HOV),
                                            close_lb.config(bg=SIDEBAR_HOV)))
            w.bind("<Leave>",    lambda e: (close_f.config(bg=SIDEBAR),
                                            close_lb.config(bg=SIDEBAR)))

        # ── Right content panel ───────────────────────────────────────
        content_area = tk.Frame(body, bg=BG)
        content_area.pack(side="left", fill="both", expand=True)

        # Content topbar — shows current section title
        self._topbar = tk.Frame(content_area, bg=BG_WHITE)
        self._topbar.pack(fill="x")
        tk.Frame(self._topbar, bg=BORDER, height=1).pack(fill="x", side="bottom")
        self._title_lbl = tk.Label(self._topbar, text="", bg=BG_WHITE, fg=TEXT,
                                   font=("Segoe UI", 12, "bold"),
                                   anchor="w", padx=20, pady=10)
        self._title_lbl.pack(fill="x")

        # Scrollable text area
        rf = tk.Frame(content_area, bg=BG_WHITE)
        rf.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(rf, orient="vertical")
        vsb.pack(side="right", fill="y")
        self._text = tk.Text(rf,
            font=("Segoe UI", 10), bg=BG_WHITE, fg=TEXT,
            relief="flat", bd=0, wrap="word",
            padx=24, pady=14,
            yscrollcommand=vsb.set, state="disabled",
            spacing1=1, spacing3=3,
            cursor="arrow")
        self._text.pack(fill="both", expand=True)
        vsb.config(command=self._text.yview)

        # ── Text tags ────────────────────────────────────────────────
        # Section heading (ALL CAPS in content → rendered as styled subhead)
        self._text.tag_configure("section",
            font=("Segoe UI", 9, "bold"), foreground=BG_WHITE,
            background=ACCENT,
            lmargin1=0, lmargin2=0,
            spacing1=14, spacing3=4)
        # Sub-mode heading (──── MODE N: ... ────)
        self._text.tag_configure("mode",
            font=("Segoe UI", 9, "bold"), foreground=ACCENT,
            background=ACCENT_SOFT,
            lmargin1=0, lmargin2=0,
            spacing1=10, spacing3=2)
        # Normal body text
        self._text.tag_configure("body",
            font=("Segoe UI", 10), foreground=TEXT,
            lmargin1=0, lmargin2=0, spacing1=1, spacing3=2)
        # Indented body (examples, explanations under a bullet)
        self._text.tag_configure("indent",
            font=("Segoe UI", 10), foreground=TEXT_DIM,
            lmargin1=24, lmargin2=24, spacing1=1, spacing3=1)
        # ✓ tip lines
        self._text.tag_configure("tip",
            font=("Segoe UI", 10), foreground="#166534",
            background="#F0FDF4",
            lmargin1=0, lmargin2=24, spacing1=2, spacing3=2)
        # ✗ / ⚠ warning lines
        self._text.tag_configure("warn",
            font=("Segoe UI", 10), foreground=BTN_RED,
            background="#FFF5F5",
            lmargin1=0, lmargin2=24, spacing1=2, spacing3=2)
        # Step lines (STEP N / Step N)
        self._text.tag_configure("step",
            font=("Segoe UI", 10, "bold"), foreground=ACCENT,
            spacing1=10, spacing3=2)
        # Divider line (─────)
        self._text.tag_configure("divider",
            font=("Segoe UI", 7), foreground=BORDER,
            spacing1=8, spacing3=4)
        # Formula / code block
        self._text.tag_configure("formula",
            font=("Consolas", 9), foreground=TEXT,
            background="#F1F5FB",
            lmargin1=24, lmargin2=24,
            spacing1=1, spacing3=1)
        # Notation (variable = definition)
        self._text.tag_configure("notation",
            font=("Consolas", 9), foreground=TEXT_DIM,
            lmargin1=24, lmargin2=24,
            spacing1=1, spacing3=0)
        # Bullet point lines (  •  ...)
        self._text.tag_configure("bullet",
            font=("Segoe UI", 10), foreground=TEXT,
            lmargin1=12, lmargin2=28, spacing1=2, spacing3=1)
        # PROBLEM: label
        self._text.tag_configure("problem",
            font=("Segoe UI", 10, "bold"), foreground=BTN_RED,
            spacing1=12, spacing3=2)
        # Empty spacer line
        self._text.tag_configure("space",
            font=("Segoe UI", 4), spacing1=0, spacing3=0)

        # Select first section
        self._show_section(0)
        f0, lb0, _ = self._nav_items[0]
        f0.config(bg=SIDEBAR_SEL); lb0.config(bg=SIDEBAR_SEL)

    def _on_select(self, _=None):
        pass  # handled by nav item click bindings

    def _show_section(self, idx):
        title, raw = _get_help_sections(_LANG)[idx]
        self._title_lbl.config(text=title)

        t = self._text
        t.config(state="normal")
        t.delete("1.0", "end")

        is_formulae = ("Formulae" in title)

        import re as _re
        _in_warn = False   # track multi-line warn paragraphs
        _in_tip  = False   # track multi-line tip paragraphs

        for line in raw.strip().split("\n"):
            s = line.strip()

            # ── Empty line → end any running paragraph, insert spacer ─
            if not s:
                _in_warn = False
                _in_tip  = False
                t.insert("end", "\n", "space")
                continue

            # ── Continuation of a warn paragraph ─────────────────
            if _in_warn and not s.startswith("✓") and not s.startswith("──"):
                # still part of the warning block — keep warn style
                t.insert("end", "   " + s + "\n", "warn")
                continue

            # ── Continuation of a tip paragraph ──────────────────
            if _in_tip and not s.startswith("⚠") and not s.startswith("──"):
                t.insert("end", "   " + s + "\n", "tip")
                continue

            # Reset paragraph trackers on structural lines
            if s.startswith("──") or (len(s) > 4 and s.upper() == s
                    and any(c.isalpha() for c in s)):
                _in_warn = False
                _in_tip  = False

            # ── Horizontal rule ───────────────────────────────────
            if s.startswith("──") or s.startswith("─" * 5):
                t.insert("end", s + "\n", "divider")
                continue

            # ── ALL-CAPS section heading (e.g. "THE TARGET BAR") ──
            if (len(s) > 4 and s.upper() == s
                    and any(c.isalpha() for c in s)
                    and not s.startswith("•")):
                t.insert("end", "  " + s + "  \n", "section")
                continue

            # ── Mode/relationship sub-heading (────── MODE N: ──) ──
            if (s.startswith("MODE") or s.startswith("RELATIONSHIP")
                    or s.startswith("STEP") or s.startswith("PROBLEM:")):
                if s.startswith("PROBLEM:"):
                    t.insert("end", s + "\n", "problem")
                else:
                    t.insert("end", s + "\n", "mode")
                continue

            # ── Step lines (Step N —) ─────────────────────────────
            if _re.match(r"^Step\s+\d+", s):
                t.insert("end", s + "\n", "step")
                continue

            # ── ✓ tip ─────────────────────────────────────────────
            if s.startswith("✓"):
                _in_tip = True; _in_warn = False
                t.insert("end", s + "\n", "tip")
                continue

            # ── ✗ / ⚠ warning ────────────────────────────────────
            if s.startswith("✗") or s.startswith("⚠"):
                _in_warn = True; _in_tip = False
                t.insert("end", s + "\n", "warn")
                continue

            # ── Bullet points (•  or  -  or  →) ──────────────────
            if s.startswith("•") or (s.startswith("-") and len(s) > 2):
                t.insert("end", "  " + s + "\n", "bullet")
                continue

            # ── Formula / notation (Consolas, indented) ──────────
            if is_formulae:
                if (line.startswith("    ") and s and
                        any(c in s for c in "=·/−[]ΣVmρMTF_")):
                    t.insert("end", line + "\n", "formula")
                    continue
                if (s and len(s) > 2 and s[0].islower() and "=" in s):
                    t.insert("end", line + "\n", "notation")
                    continue

            # ── Indented lines (examples, sub-explanations) ───────
            if line.startswith("    ") or line.startswith("         "):
                t.insert("end", line + "\n", "indent")
                continue

            # ── Default: normal body ──────────────────────────────
            t.insert("end", line + "\n", "body")

        t.config(state="disabled")
        t.yview_moveto(0)


if __name__=="__main__":
    app=FormulatorApp(); app.mainloop()