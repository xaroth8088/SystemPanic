"""Performance interruption and exact-combination management in the shell."""
from .combinations import CombinationHistory, PerformanceWatch, mix_key
from .graphics import TEXT, MUTED, CYAN, EDGE, PANEL
from .paks import CHANNELS


class CombinationMenus:
    def init_combinations(self):
        self.combination_history = CombinationHistory(self.store.path.parent)
        self.performance_watch = PerformanceWatch()
        self.performance_epoch = 0
        self.performance_problem = None
        self.flagged_page = 0
        self.flagged_selected = None

    def performance_context(self):
        w = self.world
        if self.route != "game" or not self.window_focused or w is None or w.phase != "active" or w.transition > 0:
            return None
        return (id(w), mix_key(w.mix), w.wave, self.performance_epoch)

    def check_performance(self, elapsed, frame_context):
        # Attribute the completed frame only if it began and ended in this same context.
        context = self.performance_context()
        context = context if context == frame_context else None
        if self.performance_watch.observe(elapsed, context):
            watch = self.performance_watch
            self.performance_problem = (self.world.mix.copy(), watch.slow_fps, watch.seconds)
            self.combination_history.flag(*self.performance_problem)
            self.navigate("performance")

    def dismiss_performance(self, *, menu=False):
        if menu or self.world is None or not self.world.can_shuffle:
            self.home()
            return
        if not self.world.shuffle():
            self.home()
            return
        # A deliberate recovery needs no extra introduction/glitch screen.
        self.world.transition = 0.
        self.world._accumulator = 0.
        self.performance_problem = None
        self.navigate("game")
        self.audio.music(self.world.component("music").track(self.world))

    def component_rows(self, mix, x, y, width, step=46):
        for index, channel in enumerate(CHANNELS):
            pak_id = mix[channel]
            pak = self.catalog.by_id.get(pak_id)
            self.graphics.text(self.canvas, channel.upper(), (x, y + index * step), 12, CYAN, mono=True)
            self.graphics.fit_text(self.canvas, pak.name if pak else pak_id + " (unavailable)",
                                   (x + 132, y + index * step - 6), width - 132, 22, TEXT, True)

    def draw_performance(self):
        g = self.graphics
        mix, fps, seconds = self.performance_problem
        g.panel(self.canvas, (180, 100, 920, 630), PANEL, CYAN, 16)
        g.text(self.canvas, "PROBLEMATIC INTERACTION DETECTED", (640, 145), 29, CYAN, True, anchor="center")
        g.wrapped(self.canvas, "Gameplay has been paused. This exact combination is now disabled for future runs and shuffles.",
                  (230, 185), 820, 19, TEXT)
        g.text(self.canvas, f"{fps:.1f} FPS for {seconds:.2f}s / below 10 FPS for more than 1 second",
               (230, 246), 15, MUTED)
        self.component_rows(mix, 250, 275, 780, step=42)
        alternative = self.world.can_shuffle
        message = ("Continue with a different combination, keeping your run progress." if alternative else
                   "Static Remix uses fixed components. Continue to the main menu." if self.world.fixed_mix is not None else
                   "No other combination is available with this run's enabled Paks and shuffle locks.")
        g.wrapped(self.canvas, message, (230, 560), 820, 17, MUTED)
        if self.combination_history.dirty:
            g.text(self.canvas, "Disk save failed. Disabled this session; retry to keep it after exit.", (230, 529), 16, CYAN)
            self.button("performance-save", (760, 608, 290, 32), "RETRY DISK SAVE", self.combination_history.retry, size=13)
        if alternative:
            self.button("performance-continue", (230, 650, 470, 49), "RESHUFFLE & CONTINUE >", self.dismiss_performance, filled=True, size=18)
            self.button("performance-home", (720, 650, 330, 49), "MAIN MENU", lambda: self.dismiss_performance(menu=True), size=17)
        else:
            self.button("performance-home", (340, 650, 600, 49), "CONTINUE TO MAIN MENU >", self.home, filled=True, size=18)

    def selected_flagged(self):
        entries = self.combination_history.entries
        default = entries[min(self.flagged_page * 6, len(entries) - 1)] if entries else None
        return next((entry for entry in entries if mix_key(entry.mix) == self.flagged_selected), default)

    def remove_flagged(self):
        entry = self.selected_flagged()
        if entry and self.combination_history.remove(mix_key(entry.mix)):
            self.flagged_selected = None
            self.notify("Combination re-enabled. It can be selected again.")

    def review_combination(self, mix):
        self.flagged_selected = mix_key(mix)
        for index, entry in enumerate(self.combination_history.entries):
            if mix_key(entry.mix) == self.flagged_selected:
                self.flagged_page = index // 6
                break
        self.open_page("combinations")

    def draw_combinations(self):
        g, history = self.graphics, self.combination_history
        self.header("FLAGGED COMBINATIONS")
        self.button("back", (1100, 25, 140, 34), "< BACK", self.back, size=13)
        g.text(self.canvas, "Review disabled combinations.", (80, 107), 35, TEXT, True)
        g.text(self.canvas, "Exact six-component matches are skipped. Re-enable any combination to try it again.", (80, 162), 17, MUTED)
        start = self.page_controls("flagged_page", len(history.entries), 735, 80, 300)
        selected = self.selected_flagged()
        for index, entry in enumerate(history.entries[start:start + 6]):
            key = mix_key(entry.mix)
            y = 230 + index * 75
            self.button("flagged:" + str(start + index), (80, y, 370, 61),
                        f"{start + index + 1:02d} / " + entry.detected_at[:10] + f" / {entry.fps:.1f} FPS",
                        lambda k=key: setattr(self, "flagged_selected", k),
                        accent=CYAN if entry is selected else MUTED, filled=entry is selected, size=17)
        if selected:
            g.panel(self.canvas, (485, 230, 715, 460), PANEL, EDGE)
            self.component_rows(selected.mix, 510, 265, 660, step=48)
            g.text(self.canvas, "Detected (UTC): " + selected.detected_at.replace("T", " ").replace("+00:00", ""), (510, 557), 15, MUTED)
            g.text(self.canvas, f"{selected.fps:.1f} FPS over {selected.seconds:.2f} seconds", (510, 588), 17, TEXT)
            self.button("flagged-remove", (510, 632, 665, 40), "RE-ENABLE THIS COMBINATION", self.remove_flagged, size=16)
        else:
            g.text(self.canvas, "No flagged combinations.", (80, 265), 27, TEXT, True)
            g.wrapped(self.canvas, "If gameplay stays below 10 FPS for more than one second, the engine pauses and records the active components here.",
                      (80, 320), 1000, 21)
        if history.error:
            g.fit_text(self.canvas, history.error, (485, 706), 715, 15, CYAN)
        if history.dirty:
            self.button("flagged-save", (830, 741, 370, 32), "RETRY DISK SAVE", history.retry, size=13)
