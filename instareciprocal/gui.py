"""Dark desktop interface for InstaReciprocal (Phase 3).

The UI reads local Instagram export snapshots and comparison reports only.
It does not log in to Instagram or perform follow/unfollow actions.
"""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import webbrowser

try:
    import customtkinter as ctk
except ImportError as exc:  # pragma: no cover - exercised by real desktop install
    raise SystemExit(
        "CustomTkinter is not installed. Run: pip install -r requirements.txt"
    ) from exc

from .comparator import (
    compare_accounts,
    load_import,
    load_whitelist,
    save_reports,
    save_whitelist,
)
from .importer import import_instagram_export, import_from_json_files, save_import
from .parser import InstagramExportError
from .review_store import ReviewStore
from .app_paths import app_path, ensure_app_directories
from .history_store import HistoryStore


APP_TITLE = "InstaReciprocal"
ensure_app_directories()
DEFAULT_IMPORT = app_path("exports", "phase1-import.json")
DEFAULT_WHITELIST = app_path("data", "whitelist.json")
DEFAULT_REPORTS = app_path("exports")
DEFAULT_DATABASE = app_path("data", "instareciprocal.db")


class InstaReciprocalApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_TITLE} — Instagram Relationship Manager")
        self.geometry("1120x720")
        self.minsize(900, 600)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.import_path: Path | None = None
        self.result = None
        self.whitelist = load_whitelist(DEFAULT_WHITELIST)
        self.review_store = ReviewStore(DEFAULT_DATABASE)
        self.history_store = HistoryStore(DEFAULT_DATABASE)
        self.current_filter = "Not following back"
        self.search_var = tk.StringVar()
        self.selected: set[str] = set()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()
        self._load_existing_import()

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(7, weight=1)
        ctk.CTkLabel(sidebar, text="InstaReciprocal", font=ctk.CTkFont(size=23, weight="bold")).grid(
            row=0, column=0, padx=20, pady=(28, 4), sticky="w"
        )
        ctk.CTkLabel(sidebar, text="RELATIONSHIP MANAGER", text_color="gray").grid(
            row=1, column=0, padx=20, pady=(0, 28), sticky="w"
        )
        for row, (label, callback) in enumerate([
            ("Dashboard", self.show_dashboard),
            ("Not following back", lambda: self.set_filter("Not following back")),
            ("Mutual follows", lambda: self.set_filter("Mutual follows")),
            ("You don't follow back", lambda: self.set_filter("You don't follow back")),
            ("Whitelist", self.manage_whitelist),
        ], start=2):
            ctk.CTkButton(
                sidebar, text=label, anchor="w", height=42,
                fg_color="transparent", hover_color=("gray75", "gray25"),
                command=callback,
            ).grid(row=row, column=0, padx=14, pady=4, sticky="ew")
        ctk.CTkLabel(
            sidebar, text="LOCAL DATA ONLY\nNo Instagram login or auto-unfollow",
            text_color="gray", justify="left",
        ).grid(row=8, column=0, padx=20, pady=22, sticky="sw")

    def _build_main(self) -> None:
        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=26, pady=24)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(4, weight=1)

        header = ctk.CTkFrame(self.main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        header.grid_columnconfigure(0, weight=1)
        self.heading = ctk.CTkLabel(header, text="Dashboard", font=ctk.CTkFont(size=28, weight="bold"))
        self.heading.grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="Import Instagram export", command=self.import_export).grid(
            row=0, column=1, padx=(8, 0)
        )
        ctk.CTkButton(header, text="Refresh comparison", command=self.refresh_comparison).grid(
            row=0, column=2, padx=(8, 0)
        )

        self.cards = ctk.CTkFrame(self.main, fg_color="transparent")
        self.cards.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        for col in range(4):
            self.cards.grid_columnconfigure(col, weight=1)
        self.card_values: dict[str, ctk.CTkLabel] = {}
        for col, (key, title) in enumerate([
            ("followers", "Followers"), ("following", "Following"),
            ("mutual", "Mutual"), ("not_back", "Not following back"),
        ]):
            card = ctk.CTkFrame(self.cards, corner_radius=12)
            card.grid(row=0, column=col, padx=(0 if col == 0 else 10, 0), sticky="ew")
            ctk.CTkLabel(card, text=title, text_color="gray").pack(anchor="w", padx=16, pady=(14, 2))
            value = ctk.CTkLabel(card, text="—", font=ctk.CTkFont(size=30, weight="bold"))
            value.pack(anchor="w", padx=16, pady=(0, 14))
            self.card_values[key] = value

        toolbar = ctk.CTkFrame(self.main, fg_color="transparent")
        toolbar.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        toolbar.grid_columnconfigure(0, weight=1)
        self.search_entry = ctk.CTkEntry(
            toolbar, textvariable=self.search_var, placeholder_text="Search usernames..."
        )
        self.search_entry.grid(row=0, column=0, sticky="ew")
        self.search_var.trace_add("write", lambda *_: self.render_accounts())
        ctk.CTkButton(toolbar, text="Select visible", width=110, command=self.select_visible).grid(
            row=0, column=1, padx=8
        )
        ctk.CTkButton(toolbar, text="Clear selection", width=120, command=self.clear_selection).grid(
            row=0, column=2
        )
        ctk.CTkButton(toolbar, text="Bulk review", width=105, command=self.bulk_review).grid(
            row=0, column=3, padx=(8, 0)
        )
        ctk.CTkButton(toolbar, text="History", width=85, command=self.show_history).grid(
            row=0, column=4, padx=(8, 0)
        )

        self.list_title = ctk.CTkLabel(
            self.main, text="Not following back · review list",
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        self.list_title.grid(row=3, column=0, sticky="w", pady=(0, 8))

        self.list_frame = ctk.CTkScrollableFrame(self.main, corner_radius=12)
        self.list_frame.grid(row=4, column=0, sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)

        footer = ctk.CTkFrame(self.main, fg_color="transparent")
        footer.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        self.status = ctk.CTkLabel(footer, text="Import an Instagram data export to begin.", text_color="gray")
        self.status.pack(side="left")
        ctk.CTkButton(footer, text="Open selected profiles", command=self.open_selected).pack(side="right")

    def _load_existing_import(self) -> None:
        if DEFAULT_IMPORT.exists():
            self.import_path = DEFAULT_IMPORT
            self.refresh_comparison()

    def import_export(self) -> None:
        """Import a ZIP, one or more JSON export files, or an extracted export folder."""
        selected = filedialog.askopenfilenames(
            title="Select Instagram export ZIP or JSON files",
            filetypes=[
                ("Instagram export files", "*.zip *.json"),
                ("ZIP archive", "*.zip"),
                ("JSON files", "*.json"),
                ("All files", "*.*"),
            ],
        )

        try:
            if selected:
                paths = [Path(item) for item in selected]
                zip_files = [item for item in paths if item.suffix.lower() == ".zip"]
                json_files = [item for item in paths if item.suffix.lower() == ".json"]

                if zip_files and json_files:
                    messagebox.showerror(
                        "Choose one import type",
                        "Please select either one ZIP archive or JSON files, not both.",
                    )
                    return
                if len(zip_files) > 1:
                    messagebox.showerror("Choose one ZIP", "Select one Instagram ZIP archive at a time.")
                    return
                if zip_files:
                    result = import_instagram_export(zip_files[0])
                elif json_files:
                    result = import_from_json_files(json_files)
                else:
                    messagebox.showerror("Unsupported selection", "Select a ZIP archive or JSON export files.")
                    return
            else:
                folder = filedialog.askdirectory(
                    title="Select the extracted Instagram export folder"
                )
                if not folder:
                    return
                result = import_instagram_export(folder)

            save_import(result, DEFAULT_IMPORT)
            self.import_path = DEFAULT_IMPORT
            self.selected.clear()
            self.status.configure(
                text=f"Imported {result.follower_count} followers and {result.following_count} following."
            )
            self.refresh_comparison()
        except (InstagramExportError, OSError, ValueError) as exc:
            messagebox.showerror("Import failed", str(exc))

    def refresh_comparison(self) -> None:
        if not self.import_path or not self.import_path.exists():
            candidate = DEFAULT_IMPORT
            if candidate.exists():
                self.import_path = candidate
            else:
                messagebox.showinfo("No import found", "Import your Instagram JSON export first.")
                return
        try:
            data = load_import(self.import_path)
            self.whitelist = load_whitelist(DEFAULT_WHITELIST)
            self.result = compare_accounts(data, self.whitelist)
            self.history_store.save_snapshot(
                self.result.imported_at,
                data.get("followers", []),
                data.get("following", []),
                self.result.not_following_back,
            )
            save_reports(self.result, DEFAULT_REPORTS)
            self.card_values["followers"].configure(text=str(self.result.followers_count))
            self.card_values["following"].configure(text=str(self.result.following_count))
            self.card_values["mutual"].configure(text=str(len(self.result.mutual)))
            self.card_values["not_back"].configure(text=str(len(self.result.not_following_back)))
            self.status.configure(
                text=f"Snapshot: {self.result.imported_at} · {len(self.result.review_queue)} accounts need review"
            )
            self.render_accounts()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Comparison failed", str(exc))

    def show_dashboard(self) -> None:
        """Return to the dashboard's default review-list view."""
        self.current_filter = "Dashboard"
        self.heading.configure(text="Dashboard")
        self.list_title.configure(text="Not following back · review list")
        self.render_accounts()

    def set_filter(self, name: str) -> None:
        self.current_filter = name
        self.heading.configure(text=name)
        self.list_title.configure(text=name)
        self.render_accounts()

    def _visible_usernames(self) -> list[str]:
        if not self.result:
            return []
        mapping = {
            "Not following back": self.result.review_queue,
            "Mutual follows": self.result.mutual,
            "You don't follow back": self.result.you_dont_follow_back,
            "Dashboard": self.result.review_queue,
        }
        usernames = mapping.get(self.current_filter, self.result.review_queue)
        query = self.search_var.get().strip().lower()
        return [name for name in usernames if query in name.lower()]

    def render_accounts(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()
        usernames = self._visible_usernames()
        if not usernames:
            ctk.CTkLabel(self.list_frame, text="No accounts to display.", text_color="gray").grid(
                row=0, column=0, padx=20, pady=28
            )
            return
        for row, username in enumerate(usernames):
            item = ctk.CTkFrame(self.list_frame, corner_radius=8)
            item.grid(row=row, column=0, sticky="ew", padx=4, pady=4)
            item.grid_columnconfigure(1, weight=1)
            checked = tk.BooleanVar(value=username in self.selected)
            ctk.CTkCheckBox(
                item, text="", variable=checked, width=24,
                command=lambda u=username, v=checked: self._toggle_selected(u, v.get()),
            ).grid(row=0, column=0, padx=(12, 6), pady=10)
            ctk.CTkLabel(item, text=f"@{username}", font=ctk.CTkFont(size=14)).grid(
                row=0, column=1, sticky="w", pady=10
            )
            status = self.review_store.get_status(username)
            status_labels = {
                "pending": "PENDING",
                "reviewed": "REVIEWED",
                "skipped": "SKIPPED",
                "unfollowed_manually": "UNFOLLOWED MANUALLY",
            }
            status_color = "#d6aa52" if status == "pending" else "#70b77e"
            ctk.CTkLabel(item, text=status_labels.get(status, status.upper()),
                         text_color=status_color).grid(row=0, column=2, padx=8)
            if username in self.whitelist:
                ctk.CTkLabel(item, text="PROTECTED", text_color="#70b77e").grid(
                    row=0, column=3, padx=6
                )
            ctk.CTkButton(
                item, text="Open profile", width=100,
                command=lambda u=username: webbrowser.open(f"https://www.instagram.com/{u}/"),
            ).grid(row=0, column=4, padx=5, pady=6)
            ctk.CTkButton(
                item, text="Reviewed", width=82,
                command=lambda u=username: self.update_review_status(u, "reviewed"),
            ).grid(row=0, column=5, padx=3, pady=6)
            ctk.CTkButton(
                item, text="Skip", width=55,
                command=lambda u=username: self.update_review_status(u, "skipped"),
            ).grid(row=0, column=6, padx=3, pady=6)
            ctk.CTkButton(
                item, text="Unfollowed", width=92,
                fg_color="#8b3a3a", hover_color="#6f2d2d",
                command=lambda u=username: self.confirm_manual_unfollow(u),
            ).grid(row=0, column=7, padx=(3, 10), pady=6)

    def update_review_status(self, username: str, status: str) -> None:
        try:
            self.review_store.set_status(username, status)
            self.status.configure(text=f"@{username} marked as {status.replace('_', ' ')}")
            self.render_accounts()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not save review", str(exc))

    def confirm_manual_unfollow(self, username: str) -> None:
        confirmed = messagebox.askyesno(
            "Confirm manual unfollow",
            f"Have you already unfollowed @{username} manually on Instagram?\n\n"
            "This only records your confirmation. InstaReciprocal will not unfollow anyone.",
        )
        if confirmed:
            self.update_review_status(
                username, "unfollowed_manually"
            )

    def _toggle_selected(self, username: str, checked: bool) -> None:
        if checked:
            self.selected.add(username)
        else:
            self.selected.discard(username)

    def select_visible(self) -> None:
        self.selected.update(self._visible_usernames())
        self.render_accounts()

    def clear_selection(self) -> None:
        self.selected.clear()
        self.render_accounts()

    def open_selected(self) -> None:
        if not self.selected:
            messagebox.showinfo("Nothing selected", "Select one or more accounts first.")
            return
        if not messagebox.askyesno(
            "Open Instagram profiles",
            f"Open {len(self.selected)} selected profiles in your browser?\n\n"
            "This will not unfollow anyone. Review and take any action manually on Instagram.",
        ):
            return
        names = sorted(self.selected)
        if len(names) > 10 and not messagebox.askyesno(
            "Open many profiles",
            f"This will open {len(names)} browser tabs. Continue? "
            "Opening in smaller groups of 10 is easier to manage."
        ):
            return
        for start in range(0, len(names), 10):
            batch = names[start:start + 10]
            if start and not messagebox.askyesno(
                "Next batch",
                f"Opened {start} of {len(names)} profiles. Open the next {len(batch)}?"
            ):
                break
            for username in batch:
                webbrowser.open_new_tab(f"https://www.instagram.com/{username}/")

    def bulk_review(self) -> None:
        """Apply safe review statuses to selected accounts in one operation."""
        if not self.selected:
            messagebox.showinfo("Nothing selected", "Select accounts first.")
            return
        window = ctk.CTkToplevel(self)
        window.title("Bulk review")
        window.geometry("430x300")
        window.transient(self)
        ctk.CTkLabel(
            window, text=f"{len(self.selected)} selected accounts",
            font=ctk.CTkFont(size=21, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(22, 8))
        ctk.CTkLabel(
            window,
            text="Choose a review status. Bulk review cannot mark accounts as unfollowed; "
                 "that status requires an individual confirmation after you unfollow manually.",
            wraplength=380, justify="left", text_color="gray",
        ).pack(anchor="w", padx=20, pady=(0, 18))

        def apply(status: str) -> None:
            names = sorted(self.selected)
            if not messagebox.askyesno(
                "Confirm bulk review",
                f"Mark {len(names)} selected accounts as {status.replace('_', ' ')}?"
            ):
                return
            for name in names:
                self.review_store.set_status(name, status, "Bulk review action")
            self.selected.clear()
            window.destroy()
            self.render_accounts()
            self.status.configure(text=f"Bulk updated {len(names)} accounts: {status}")

        buttons = ctk.CTkFrame(window, fg_color="transparent")
        buttons.pack(fill="x", padx=20, pady=8)
        ctk.CTkButton(buttons, text="Mark reviewed", command=lambda: apply("reviewed")).pack(
            fill="x", pady=5
        )
        ctk.CTkButton(buttons, text="Skip", command=lambda: apply("skipped")).pack(
            fill="x", pady=5
        )
        ctk.CTkButton(buttons, text="Reset to pending", fg_color="#555555",
                      command=lambda: apply("pending")).pack(fill="x", pady=5)

    def show_history(self) -> None:
        snapshots = self.history_store.list_snapshots()
        delta = self.history_store.compare_latest()
        window = ctk.CTkToplevel(self)
        window.title("Scan history")
        window.geometry("680x560")
        window.transient(self)
        ctk.CTkLabel(
            window, text="Scan history & changes",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 10))
        if not snapshots:
            ctk.CTkLabel(window, text="No scan history yet. Import an Instagram export first.",
                         text_color="gray").pack(anchor="w", padx=20, pady=20)
            return

        if delta is None:
            summary = "Import another export to compare changes with this scan."
        else:
            summary = (
                f"Since previous scan: +{len(delta['new_followers'])} followers, "
                f"-{len(delta['lost_followers'])} followers, "
                f"+{len(delta['new_following'])} following, "
                f"{len(delta['new_non_followers'])} newly not following back."
            )
        ctk.CTkLabel(window, text=summary, wraplength=630, justify="left",
                     text_color="#70b77e").pack(anchor="w", padx=20, pady=(0, 12))

        listing = ctk.CTkScrollableFrame(window)
        listing.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        for snap in snapshots:
            row = ctk.CTkFrame(listing)
            row.pack(fill="x", pady=4)
            label = (
                f"Imported: {snap['imported_at']}\\n"
                f"Followers {snap['followers_count']} · Following {snap['following_count']} · "
                f"Mutual {snap['mutual_count']} · Not back {snap['not_following_back_count']}"
            )
            ctk.CTkLabel(row, text=label, justify="left").pack(
                side="left", padx=12, pady=10
            )

    def manage_whitelist(self) -> None:
        window = ctk.CTkToplevel(self)
        window.title("Manage whitelist")
        window.geometry("480x440")
        window.transient(self)
        ctk.CTkLabel(
            window, text="Protected accounts",
            font=ctk.CTkFont(size=21, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 8))
        ctk.CTkLabel(
            window, text="One username per line. Protected accounts stay out of the review queue.",
            text_color="gray", wraplength=430, justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))
        textbox = ctk.CTkTextbox(window, height=260)
        textbox.pack(fill="both", expand=True, padx=20, pady=4)
        textbox.insert("1.0", "\n".join(sorted(self.whitelist)))

        def save() -> None:
            names = {
                line.strip().lstrip("@").lower()
                for line in textbox.get("1.0", "end").splitlines()
                if line.strip()
            }
            save_whitelist(names, DEFAULT_WHITELIST)
            self.whitelist = names
            window.destroy()
            self.refresh_comparison()
            self.status.configure(text=f"Whitelist saved · {len(names)} protected accounts")

        ctk.CTkButton(window, text="Save whitelist", command=save).pack(
            anchor="e", padx=20, pady=16
        )


def main() -> None:
    app = InstaReciprocalApp()
    app.mainloop()


if __name__ == "__main__":
    main()
