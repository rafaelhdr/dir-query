## Purpose

The theme-toggle capability lets a visitor switch the site between light
and dark theme via a control in the site header, overriding the OS's
`prefers-color-scheme` setting, with the choice persisted across visits.

## Requirements

### Requirement: A visible header control toggles the site's light/dark theme
The system SHALL provide a toggle control in the site header, present on
every page, that switches the site between light and dark theme
regardless of the browser/OS's `prefers-color-scheme` setting.

#### Scenario: Toggling from light to dark
- **WHEN** the site is currently displaying in light theme (whether from
  OS preference or a prior explicit choice) and the user activates the
  theme toggle
- **THEN** the site immediately switches to dark theme

#### Scenario: Toggling from dark to light
- **WHEN** the site is currently displaying in dark theme and the user
  activates the theme toggle
- **THEN** the site immediately switches to light theme

### Requirement: An explicit theme choice is persisted across visits and overrides OS preference
The system SHALL store the user's explicit theme choice in the browser's
`localStorage` and SHALL apply that stored choice on every subsequent page
load, taking precedence over the OS's `prefers-color-scheme` setting. With
no stored choice, the site SHALL follow OS preference as before.

#### Scenario: Stored choice persists across a new visit
- **WHEN** a user has previously chosen dark theme via the toggle, then
  closes the browser and later revisits any page of the site
- **THEN** the page displays in dark theme, regardless of the OS's current
  `prefers-color-scheme` value

#### Scenario: No stored choice falls back to OS preference
- **WHEN** a user has never used the theme toggle (no stored preference)
- **THEN** the site's theme follows the OS's `prefers-color-scheme` setting,
  as it did before this capability existed

#### Scenario: Stored choice applies on every page, not just where it was set
- **WHEN** a user sets a theme choice on one page and then navigates to a
  different page
- **THEN** the new page loads already reflecting the stored theme choice

### Requirement: The toggle control's icon and label represent the theme it switches to
The system SHALL display an icon and accessible label on the toggle
control that represent the destination theme (the one activating the
control would switch to), not the theme currently active.

#### Scenario: Control while in light theme
- **WHEN** the site is currently displaying in light theme
- **THEN** the toggle control shows a moon icon with an accessible label
  indicating it switches to dark theme

#### Scenario: Control while in dark theme
- **WHEN** the site is currently displaying in dark theme
- **THEN** the toggle control shows a sun icon with an accessible label
  indicating it switches to light theme
