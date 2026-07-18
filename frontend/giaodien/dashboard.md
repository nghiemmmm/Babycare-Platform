# Technical Prompt for BabyCare AI Enhanced Dashboard (Tailwind CSS + Glassmorphism)

## Overview
Generate a high-fidelity React/HTML dashboard for a baby tracking app called **BabyCare AI**. The design uses a **Modern Glassmorphism** aesthetic with a soft, medical-serene atmosphere.

## 1. Global Styles & Config (Tailwind CSS)
- **Font**: Use 'Outfit' (Sans-serif) from Google Fonts.
- **Colors (Tailwind Config)**:
  - `primary`: `#1c648e` (Deep Navy)
  - `surface-glass`: `rgba(255, 255, 255, 0.6)`
  - `border-glass`: `rgba(255, 255, 255, 0.2)`
  - `accent-blue`: `#7cb9e8` (Feeding)
  - `accent-purple`: `#b19cd9` (Sleep)
  - `accent-gold`: `#fdfd96` (Diaper)
  - `accent-green`: `#b2e2f2` (Medication)
- **Backdrop Blur**: Global `backdrop-blur-xl` (24px) for all main panels.

## 2. Layout Structure
The page is a full-screen application layout with three main columns:

### A. Sidebar (Fixed Left, ~280px)
- **Style**: `bg-white/40 backdrop-blur-2xl border-r border-white/20`.
- **Content**:
  - Logo: "Guardian AI" with "EMPATHETIC CARE" subtext.
  - Nav Items: Dashboard (Active), Baby Profile, AI Chat Room, Activity Log, Health Records, Growth Charts, Nutrition, Reports.
  - Active State: `text-primary font-bold border-r-4 border-primary bg-primary/10`.
  - Bottom Section: User profile card (Sarah Jenkins) with "Premium Member" badge.

### B. Main Content Area (Center, Fluid)
- **Header**:
  - Baby Profile: 64px circular avatar (Bo), name, age (6 months), and weight (7.4 kg).
  - Actions: Large "+ Add Entry" button (`bg-primary text-white rounded-full px-6 py-2`), notification bell, and settings gear.
- **Quick Stats Row**:
  - 4 Square Glass Cards: Each with a centered icon (Feeding, Sleep, Diaper, Medication).
  - Hover Effect: `hover:scale-105 transition-transform duration-300`.
- **Detailed Insights Grid**:
  - 2x2 Grid of horizontal glass cards:
    - "Last Feeding": 150ml (2h 15m ago).
    - "Total Sleep": 12.5h (Target: 14h).
    - "Diaper Count": 3 today (All normal).
    - "Temperature": 36.8°C (Optimal range).
- **Interactive AI Chat Widget**:
  - A centered glass card (`bg-white/80 backdrop-blur-md rounded-[32px] p-6`).
  - Chat bubbles: Left (AI) and Right (User).
  - Input bar: pill-shaped with a microphone and send icon.
- **Growth Progress Chart**:
  - A subtle bar chart showing weight trajectory vs. WHO standard.
  - Style: Modern, flat bars with one highlighted "Now" bar.

### C. Right Panel (Daily Timeline, ~320px)
- **Style**: `bg-white/30 backdrop-blur-xl border-l border-white/20`.
- **Top Section**: "AI Insights" cards (Solids Transition, Medication Reminder) with soft colored borders.
- **Vertical Timeline**:
  - A line with nodes representing events.
  - Items: Afternoon Feed (12:45 PM), Nap Time (11:00 AM), Diaper Change (10:45 AM), Morning Feed (08:00 AM).
  - Icons: Minimalist circular icons matching the category colors.
- **Bottom Action**: "Full Log History" floating button with a plus icon.

## 3. Glassmorphism Recipe (Apply to all Cards)
```html
<div class="bg-white/60 backdrop-blur-xl border border-white/30 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[32px]">
  <!-- Card Content -->
</div>
```

## 4. Typography Hierarchy
- **Titles**: `text-primary font-bold text-2xl tracking-tight`.
- **Value Text**: `text-primary font-semibold text-xl`.
- **Label Text**: `text-slate-500 font-medium text-sm uppercase tracking-wide`.
- **Body Text**: `text-slate-600 leading-relaxed`.
