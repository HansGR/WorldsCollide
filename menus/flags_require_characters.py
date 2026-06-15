import menus.pregame_track_scroll_area as scroll_area
import instruction.f0 as f0

class FlagsRequireCharacters(scroll_area.ScrollArea):
    MENU_NUMBER = 17

    def __init__(self, character_names):
        self.number_items = len(character_names)
        self.lines = []

        self.lines.append(scroll_area.Line(f"Require Characters ({self.number_items})", f0.set_blue_text_color))
        self.lines.append(scroll_area.Line("Always in the party:", f0.set_gray_text_color))

        for list_value in FlagsRequireCharacters._format_menu(character_names):
            padding = scroll_area.WIDTH - (len(list_value))
            self.lines.append(scroll_area.Line(f"{' ' * padding}{list_value}", f0.set_user_text_color))

        super().__init__()

    def _format_menu(character_names):
        COLUMN_WIDTHS = [13, 13]
        labels = [FlagsRequireCharacters._label(name) for name in character_names]
        lines = []

        # Step through the characters by the number of columns
        for idx in range(0, len(labels), len(COLUMN_WIDTHS)):
            current_line = ''
            for col in range(0, len(COLUMN_WIDTHS)):
                if idx + col < len(labels):
                    label = labels[idx + col]
                    padding = COLUMN_WIDTHS[col] - len(label)
                    current_line += f"{label}{' ' * padding}"
                else:
                    current_line += f"{' ' * COLUMN_WIDTHS[col]}"
            lines.append(current_line)
        return lines

    def _label(name):
        if name == "random":
            return "Random"
        if name == "randomngu":
            return "Random NGU"
        return name.capitalize()
