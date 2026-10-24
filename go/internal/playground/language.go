package playground

import "fmt"

func normalizeOptions(options Options) (Options, error) {
	if options.Theme == "" {
		options.Theme = "dark"
	}
	if options.Colors == "" {
		options.Colors = "auto"
	}
	if options.Lang == "" {
		options.Lang = "ko"
	}
	if options.Lang != "ko" && options.Lang != "en" {
		return options, fmt.Errorf("invalid language %q: use ko or en", options.Lang)
	}
	if !contains(themeNames, options.Theme) || !contains(profileNames, options.Colors) {
		return options, fmt.Errorf("invalid theme or color profile")
	}
	return options, nil
}

// Keep translations beside their Korean source so changes stay in sync.
func (u *UI) text(ko, en string) string {
	if u.options.Lang == "en" {
		return en
	}
	return ko
}

const guideTextEN = `TUIVORY · What can you explore?

1. Components
Enter a name and try password masking, choices, and checkboxes.
Use Apply/Popup/Reset to explore states and modal behavior.
Press Enter in the grid's Name column, edit, and save to see an * marker.
This example does not save to a database or file.

2. Themes and colors
F2 cycles Dark/Light/Monochrome; F3 cycles Auto/8/16/256/True Color.
Input values, checkboxes, selections, and edited cells are preserved.
Color selection previews tokens; it does not change terminal capabilities.
Your terminal may approximate colors using a smaller palette.

3. Color tokens
Use F6 or the left menu. Compare foreground/background pairs for 16 roles.
The samples use the Go style palette; shared tokens provide role ordering.

4. Controls
Tab/Shift+Tab: move focus
Arrow keys: navigate lists/grids or move between buttons
Enter: activate buttons, open choices, or edit a name cell
F1: help / F4: popup / F5: input errors / F6: switch view
Esc: close the open choice or popup
Ctrl+Q: quit

Mouse interaction is available for choices, buttons, and popups.
Below 80×24, a message asks you to resize the terminal.
Actual ANSI palettes, fonts, and mouse support vary by terminal.`
