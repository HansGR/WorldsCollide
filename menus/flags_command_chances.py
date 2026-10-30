import menus.pregame_track_scroll_area as scroll_area
import instruction.f0 as f0

class FlagsCommandChances(scroll_area.ScrollArea):
    # shares 18 with FlagsCommandWeights: a seed uses legacy Chances or new Weights, never both
    MENU_NUMBER = 18

    def __init__(self, chances):
        # chances: [(command name, percent)] in -compr/-compru order
        self.number_items = len(chances)
        self.lines = []

        self.lines.append(scroll_area.Line(f"Command Chances ({self.number_items})", f0.set_blue_text_color))
        self.lines.append(scroll_area.Line("Chance each command rolls:", f0.set_gray_text_color))

        for list_value in FlagsCommandChances._format_menu(chances):
            padding = scroll_area.WIDTH - (len(list_value))
            self.lines.append(scroll_area.Line(f"{' ' * padding}{list_value}", f0.set_user_text_color))

        super().__init__()

    def _format_menu(chances):
        COLUMN_WIDTHS = [13, 13]
        labels = [f"{name:<7}{percent:>4}%" for name, percent in chances]
        lines = []

        # Step through the commands by the number of columns
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
