---
name: Systematic Precision
colors:
  surface: '#f8f9ff'
  surface-dim: '#d7dae0'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f3fa'
  surface-container: '#ebeef4'
  surface-container-high: '#e6e8ef'
  surface-container-highest: '#e0e2e9'
  on-surface: '#181c20'
  on-surface-variant: '#404752'
  inverse-surface: '#2d3136'
  inverse-on-surface: '#eef1f7'
  outline: '#707784'
  outline-variant: '#c0c7d4'
  surface-tint: '#0060a9'
  primary: '#0060a9'
  on-primary: '#ffffff'
  primary-container: '#409eff'
  on-primary-container: '#003460'
  inverse-primary: '#a2c9ff'
  secondary: '#5c5e62'
  on-secondary: '#ffffff'
  secondary-container: '#e1e2e7'
  on-secondary-container: '#626468'
  tertiary: '#8b5000'
  on-tertiary: '#ffffff'
  tertiary-container: '#e18500'
  on-tertiary-container: '#4e2a00'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d3e4ff'
  primary-fixed-dim: '#a2c9ff'
  on-primary-fixed: '#001c38'
  on-primary-fixed-variant: '#004881'
  secondary-fixed: '#e1e2e7'
  secondary-fixed-dim: '#c5c6cb'
  on-secondary-fixed: '#191c1f'
  on-secondary-fixed-variant: '#45474b'
  tertiary-fixed: '#ffdcbe'
  tertiary-fixed-dim: '#ffb871'
  on-tertiary-fixed: '#2d1600'
  on-tertiary-fixed-variant: '#6a3c00'
  background: '#f8f9ff'
  on-background: '#181c20'
  surface-variant: '#e0e2e9'
  success: '#67C23A'
  warning: '#E6A23C'
  danger: '#F56C6C'
  surface-bg: '#F0F2F5'
  text-primary: '#303133'
  text-regular: '#606266'
  text-secondary: '#909399'
  border-base: '#DCDFE6'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 18px
  code:
    fontFamily: courierPrime
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  container-padding: 20px
  gutter: 16px
  margin-sm: 12px
  sidebar-width: 240px
  sidebar-collapsed: 64px
---

## Brand & Style
This design system is engineered for high-density administrative interfaces, prioritizing clarity, efficiency, and professional rigor. The brand personality is grounded and utilitarian, designed to fade into the background so that user data and workflows remain the primary focus.

The aesthetic follows a **Corporate / Modern** approach. It leverages a structured grid, ample whitespace for legibility, and a restrained color application. The visual language is inspired by the Element Plus ecosystem: logical, predictable, and highly functional. It avoids unnecessary decoration in favor of clear state indicators and consistent interactive patterns.

## Colors
The palette is built on a foundation of "Administrative Blue" (#409EFF) to denote action and primary focus. Backgrounds utilize a subtle off-white (#F0F2F5) to create a soft contrast against pure white (#FFFFFF) content containers, reducing eye strain during long-duration usage.

Semantic colors (Success, Warning, Danger) are strictly reserved for feedback and status indicators. Neutral tones are tiered to establish a clear information hierarchy:
- **Text Primary:** Deep grey for headlines and high-importance data.
- **Text Regular:** Standard body text and labels.
- **Text Secondary:** Metadata, placeholders, and disabled states.
- **Border Base:** Used for inputs, dividers, and structural outlines to maintain a clean grid without visual clutter.

## Typography
The system uses **Inter** as the primary typeface for its exceptional legibility and neutral character. A systematic scale ensures that information density is managed effectively across complex dashboards.

- **Headlines:** Use Semi-bold weights (600) to anchor sections and page titles.
- **Body:** The standard size is 14px (body-md), which offers the best balance for data-heavy tables and forms.
- **Labels:** Medium weights (500) are used for form labels and table headers to distinguish them from data values.
- **Mono:** For technical data or IDs, Courier Prime is used sparingly to provide visual differentiation.

## Layout & Spacing
The layout follows a **Fixed Grid** approach for the sidebar and a **Fluid Grid** for the main content area. The main workspace is wrapped in a 20px padding to ensure content never touches the edges of the viewport.

- **Sidebar:** A rigid 240px width that can collapse to 64px. It uses a vertical navigation pattern with 1px borders to separate it from the main stage.
- **Grid:** A 12-column system is used for dashboard widgets, allowing for flexible arrangements of cards (e.g., 3-column, 4-column, or 2-column spans).
- **Rhythm:** An 8px base unit drives all internal component spacing, ensuring consistent alignment between buttons, inputs, and text blocks.

## Elevation & Depth
This design system uses a "Flat-Plus" approach. Depth is conveyed primarily through **Tonal Layers** and extremely **Subtle Shadows**. 

- **Surface:** The page background is #F0F2F5.
- **Container:** All primary content sits on white (#FFFFFF) cards.
- **Shadows:** A single, soft elevation is used for cards: `0 2px 12px 0 rgba(0, 0, 0, 0.1)`. This provides a gentle lift without creating distracting dark spots.
- **Interactions:** Hover states on interactive elements like buttons or menu items should utilize a slight darkening of the background color or a primary-tinted ghost fill rather than increasing shadow depth.

## Shapes
The shape language is "Soft" and professional. A standard 4px radius is applied to small components like buttons and input fields to maintain a crisp, precise feel. Larger containers like cards and modal dialogs may use an 8px (rounded-lg) radius to soften the overall appearance of the dashboard. Tags and chips follow the same 4px rule to remain consistent with action elements.

## Components
- **Buttons:** Solid fills for primary actions, outlined for secondary. Use a 4px border radius. Padding should be 8px 15px for standard size.
- **Input Fields:** Use #DCDFE6 for borders. On focus, transition the border color to primary blue (#409EFF). Use 14px text for input values.
- **Cards:** White background, 8px border radius, and the standard subtle shadow. Include a header section with a 1px bottom border for titled cards.
- **Tags (Chips):** Use a light tint of the semantic colors (e.g., light green background with dark green text) for status indicators.
- **Sidebar:** Light theme uses a white background with a right-hand border. Active states are indicated by primary blue text and a subtle 2px vertical bar on the leading edge.
- **Breadcrumbs:** Use Text Secondary (#909399) for inactive links and Text Primary (#303133) for the current page, separated by a slash (/) or chevron.
- **Tables:** Essential for this system. Use a clean header with a light grey background (#FAFAFA) and thin 1px horizontal borders between rows. No vertical borders except for the outermost container.