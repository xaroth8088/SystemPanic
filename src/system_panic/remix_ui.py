"""Static Remix builder and local favorite menus for the desktop shell."""
from __future__ import annotations

import secrets

from .graphics import TEXT, MUTED, CYAN, EDGE, PANEL
from .paks import CHANNELS
from .combinations import mix_key
from .remixes import MAX_NAME_LENGTH, Remix, RemixStore, mix_issues, normalize_name


class RemixMenus:
    def init_remixes(self):
        self.remix_store = RemixStore(self.store.path.parent, self.catalog)
        self.remixes = self.remix_store.load()
        self.remix_mix = self.default_remix()
        self.remix_selected = None
        self.remix_picker_channel = "pilot"
        self.remix_picker_page = self.remix_saved_page = 0
        self.remix_name = ""
        self._remix_pending_mix = None
        self._remix_rename_id = None

    def default_remix(self):
        return {channel: providers[0] for channel in CHANNELS
                if (providers := self.catalog.providers(channel, self.prefs.enabled)
                    or self.catalog.providers(channel))}

    def open_remix(self):
        self.remix_mix = self.default_remix()
        self.remix_selected = None
        self.open_page("remix")

    def selected_remix(self):
        return next((item for item in self.remixes if item.id == self.remix_selected), None)

    def pick_remix_channel(self, channel):
        self.remix_picker_channel = channel
        self.remix_picker_page = 0
        self.open_page("remix-picker")

    def choose_remix_provider(self, pak_id):
        channel = self.remix_picker_channel
        if pak_id not in self.catalog.providers(channel):
            return
        if self.remix_mix.get(channel) != pak_id:
            self.remix_selected = None
        self.remix_mix[channel] = pak_id
        self.back()

    def load_remix(self, identifier):
        item = next((item for item in self.remixes if item.id == identifier), None)
        if item:
            self.remix_mix = item.mix.copy()
            self.remix_selected = item.id
            self.back()

    def play_remix(self):
        self.start(fixed_mix=self.remix_mix)

    def name_remix(self, *, from_run=False, rename=False):
        selected = self.selected_remix() if rename else None
        if rename and selected is None:
            return
        if from_run and self.world is None:
            return
        self._remix_pending_mix = (self.world.mix if from_run else
                                   selected.mix if selected else self.remix_mix).copy()
        self._remix_rename_id = selected.id if selected else None
        names = {item.name for item in self.remixes}
        index = 1
        while f"Remix {index}" in names:
            index += 1
        self.remix_name = selected.name if selected else f"Remix {index}"
        self.open_page("remix-name")

    def append_remix_name(self, text):
        text = "".join(character for character in text if character.isprintable())
        self.remix_name = (self.remix_name + text)[:MAX_NAME_LENGTH]

    def edit_remix_name(self, backspace=False):
        self.remix_name = self.remix_name[:-1] if backspace else ""

    def write_remixes(self, candidates):
        if not self.remix_store.save(candidates):
            self.notify("Could not save Remixes. Your saved favorites have not changed.")
            return False
        self.remixes = candidates
        return True

    def save_remix_name(self):
        if self._remix_pending_mix is None:
            return
        try:
            name = normalize_name(self.remix_name)
        except ValueError as exc:
            self.notify(str(exc))
            return
        identifier = self._remix_rename_id or secrets.token_hex(16)
        favorite = Remix(identifier, name, self._remix_pending_mix.copy())
        if self._remix_rename_id:
            candidates = [favorite if item.id == identifier else item for item in self.remixes]
        else:
            candidates = [*self.remixes, favorite]
        if not self.write_remixes(candidates):
            return
        return_route = self.page_history[-1] if self.page_history else "home"
        if return_route == "remix":
            self.remix_selected = identifier
        self._remix_pending_mix = None
        self.back()
        self.notify(f'Saved Remix: {name}')

    def delete_remix(self):
        selected = self.selected_remix()
        if selected and self.write_remixes([item for item in self.remixes if item.id != selected.id]):
            self.remix_selected = None
            self.back()
            self.notify(f'Deleted Remix: {selected.name}')

    def draw_remix(self):
        g = self.graphics
        self.header("REMIX / STATIC PLAY")
        self.button("back", (1100, 25, 140, 34), "< BACK", self.back, size=13)
        g.text(self.canvas, "Build your Remix.", (80, 116), 35, TEXT, True)
        selected = self.selected_remix()
        if selected:
            g.fit_text(self.canvas, selected.name, (80, 184), 700, 22, CYAN, True)
            self.button("remix-rename", (870, 178, 155, 34), "RENAME", lambda: self.name_remix(rename=True), size=13)
            self.button("remix-delete", (1040, 178, 160, 34), "DELETE", lambda: self.open_page("remix-delete"), size=13)
        else:
            g.text(self.canvas, "NEW COMBINATION", (80, 187), 13, CYAN, mono=True)
        for index, channel in enumerate(CHANNELS):
            x, y = 80 + index % 2 * 580, 228 + index // 2 * 127
            pak_id = self.remix_mix.get(channel)
            pak = self.catalog.by_id.get(pak_id)
            available = pak is not None and channel in pak.parts
            g.panel(self.canvas, (x, y, 540, 109), PANEL, EDGE)
            g.text(self.canvas, channel.upper(), (x + 18, y + 14), 12, CYAN, mono=True)
            g.fit_text(self.canvas, pak.name if available else f"Unavailable: {pak_id or 'no provider'}",
                       (x + 18, y + 42), 362, 23, pak.color if available else MUTED, True)
            if self.catalog.providers(channel):
                self.button("remix-channel:" + channel, (x + 398, y + 34, 124, 44), "CHOOSE >",
                            lambda c=channel: self.pick_remix_channel(c), size=13)
        valid = not mix_issues(self.remix_mix, self.catalog)
        blocked = valid and mix_key(self.remix_mix) in self.combination_history.keys
        if valid:
            if blocked:
                self.button("remix-blocked", (80, 630, 350, 53), "FLAGGED / REVIEW >", lambda: self.review_combination(self.remix_mix), size=18)
            else:
                self.button("remix-play", (80, 630, 350, 53), "PLAY REMIX >", self.play_remix, filled=True, size=20)
            self.button("remix-save", (450, 630, 350, 53), "SAVE AS NEW", self.name_remix, size=18)
        else:
            g.wrapped(self.canvas, "Choose an installed provider for every component to play or save this mix.", (80, 630), 700, 17, CYAN)
        self.button("remix-saved", (820, 630, 380, 53), f"SAVED REMIXES ({len(self.remixes)})",
                    lambda: self.open_page("remix-saved"), size=17)

    def draw_remix_picker(self):
        g, channel = self.graphics, self.remix_picker_channel
        self.header("REMIX / " + channel.upper())
        self.button("back", (1100, 25, 140, 34), "< BACK", self.back, size=13)
        g.text(self.canvas, f"Choose your {channel}.", (80, 118), 35, TEXT, True)
        g.text(self.canvas, "All installed providers are available for Remix.", (80, 174), 18, MUTED)
        providers = self.catalog.providers(channel)
        start = self.page_controls("remix_picker_page", len(providers), 724, 80, 1060)
        for index, pak_id in enumerate(providers[start:start + 6]):
            pak = self.catalog.by_id[pak_id]
            x, y = 80 + index % 2 * 580, 238 + index // 2 * 150
            g.panel(self.canvas, (x, y, 540, 130), PANEL, pak.color if self.remix_mix.get(channel) == pak_id else EDGE)
            self.canvas.blit(g.preview(pak_id, 74), (x + 15, y + 18))
            g.fit_text(self.canvas, pak.name, (x + 104, y + 18), 410, 25, pak.color, True)
            g.fit_text(self.canvas, pak.subtitle, (x + 104, y + 54), 410, 15, MUTED)
            self.button("provider:" + pak_id, (x + 104, y + 85, 410, 31),
                        "SELECTED / USE PAK" if self.remix_mix.get(channel) == pak_id else "USE PAK >",
                        lambda p=pak_id: self.choose_remix_provider(p), accent=pak.color, size=13)
        if not providers:
            g.text(self.canvas, "No installed Pak supplies this component.", (80, 260), 24, MUTED)

    def draw_remix_saved(self):
        g = self.graphics
        self.header("SAVED REMIXES")
        self.button("back", (1100, 25, 140, 34), "< BACK", self.back, size=13)
        g.text(self.canvas, "Your favorite combinations.", (80, 116), 35, TEXT, True)
        g.text(self.canvas, "Choose a Remix to play, edit, rename or delete.", (80, 172), 18, MUTED)
        start = self.page_controls("remix_saved_page", len(self.remixes), 735, 80, 1060, per_page=4)
        for index, item in enumerate(self.remixes[start:start + 4]):
            y = 225 + index * 119
            g.panel(self.canvas, (80, y, 1120, 112), PANEL, EDGE)
            g.fit_text(self.canvas, item.name, (100, y + 8), 700, 22, TEXT, True)
            issues = mix_issues(item.mix, self.catalog)
            blocked = mix_key(item.mix) in self.combination_history.keys
            if issues or blocked:
                g.text(self.canvas, "FLAGGED" if blocked else "UNAVAILABLE", (915, y + 15), 11, CYAN, mono=True, anchor="topright")
            for component, channel in enumerate(CHANNELS):
                pak_id = item.mix[channel]
                pak = self.catalog.by_id.get(pak_id)
                available = pak is not None and channel in pak.parts
                name = pak.name if available else pak_id + " (missing)"
                g.fit_text(self.canvas, f"{channel.title()}: {name}",
                           (100 + component % 3 * 270, y + 43 + component // 3 * 27),
                           257, 14, TEXT if available else MUTED)
            self.button("favorite:" + item.id, (950, y + 35, 230, 43), "OPEN REMIX >",
                        lambda i=item.id: self.load_remix(i), size=15)
        if not self.remixes:
            g.text(self.canvas, "No saved Remixes yet.", (80, 259), 27, TEXT, True)
            g.wrapped(self.canvas, "Build a combination here, or pause the main game and choose Save current mix.", (80, 314), 950, 21)

    def draw_remix_name(self):
        g = self.graphics
        self.header("RENAME REMIX" if self._remix_rename_id else "SAVE REMIX")
        self.button("name-cancel", (1100, 25, 140, 34), "CANCEL", self.back, size=13)
        g.text(self.canvas, "Give this mix a name.", (120, 123), 35, TEXT, True)
        g.text(self.canvas, "Type a name, or use the keys below. Enter saves.", (120, 180), 18, MUTED)
        g.panel(self.canvas, (120, 226, 1040, 76), PANEL, CYAN)
        g.fit_text(self.canvas, self.remix_name + "_", (142, 245), 990, 28, TEXT, True)
        g.text(self.canvas, f"{len(self.remix_name)} / {MAX_NAME_LENGTH}", (1158, 312), 13, MUTED, mono=True, anchor="topright")
        for index, character in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"):
            x, y = 120 + index % 12 * 88, 354 + index // 12 * 65
            self.button("name-key:" + character, (x, y, 72, 50), character,
                        lambda c=character: self.append_remix_name(c), size=21)
        self.button("name-key: ", (120, 559, 336, 48), "SPACE", lambda: self.append_remix_name(" "), size=16)
        self.button("name-key:-", (472, 559, 160, 48), "-", lambda: self.append_remix_name("-"), size=18)
        self.button("name-backspace", (648, 559, 248, 48), "BACKSPACE", lambda: self.edit_remix_name(True), size=16)
        self.button("name-clear", (912, 559, 248, 48), "CLEAR", self.edit_remix_name, size=16)
        self.button("name-save", (120, 655, 1040, 55), "SAVE REMIX >", self.save_remix_name, filled=True, size=20)
        g.text(self.canvas, "Saves the six Pak choices. Playing a saved Remix starts a fresh run.", (120, 753), 16, MUTED)

    def draw_remix_delete(self):
        g = self.graphics
        self.header("DELETE REMIX")
        selected = self.selected_remix()
        g.text(self.canvas, "Delete this saved Remix?", (120, 220), 35, TEXT, True)
        g.fit_text(self.canvas, selected.name if selected else "No Remix selected", (120, 290), 1000, 28, CYAN, True)
        self.button("delete-cancel", (120, 414, 490, 57), "KEEP REMIX", self.back, filled=True, size=18)
        self.button("delete-confirm", (650, 414, 490, 57), "DELETE REMIX", self.delete_remix, size=18)
