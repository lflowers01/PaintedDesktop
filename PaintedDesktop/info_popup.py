"""Info popup and history window for PaintedDesktop."""

import tkinter as tk
from tkinter import ttk
import threading
from typing import Optional, Dict, List
import webbrowser


class InfoPopup:
    def __init__(self, entry: Dict, on_close_callback=None):
        self.entry = entry
        self.on_close_callback = on_close_callback

    def show(self):
        window = tk.Tk()
        window.title("What's on my desktop?")
        window.geometry("500x300")
        window.resizable(False, False)

        style = ttk.Style()
        style.theme_use('clam')

        main_frame = ttk.Frame(window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(
            main_frame,
            text=self.entry.get('title', 'Unknown'),
            font=('Arial', 14, 'bold'),
            wraplength=450
        ).grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        ttk.Label(
            main_frame,
            text=f"Artist: {self.entry.get('artist', 'Unknown')}",
            font=('Arial', 11)
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)

        year = self.entry.get('year')
        if year:
            ttk.Label(
                main_frame,
                text=f"Year: {year}",
                font=('Arial', 11)
            ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        ttk.Label(
            main_frame,
            text=f"Source: {self.entry.get('source_institution', 'Unknown')}",
            font=('Arial', 11)
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)

        date_set = self.entry.get('date_set', 'Unknown')
        if 'T' in date_set:
            date_set = date_set.split('T')[0]
        ttk.Label(
            main_frame,
            text=f"Set on: {date_set}",
            font=('Arial', 10),
            foreground='gray'
        ).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)

        def open_link():
            url = self.entry.get('source_url', '')
            if url:
                webbrowser.open(url)

        ttk.Button(
            main_frame,
            text="View on source website",
            command=open_link
        ).grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)

        ttk.Button(
            main_frame,
            text="Close",
            command=window.destroy
        ).grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E))

        def on_closing():
            if self.on_close_callback:
                self.on_close_callback()
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", on_closing)
        window.mainloop()

    def show_threaded(self):
        threading.Thread(target=self.show, daemon=True).start()


class HistoryWindow:
    def __init__(self, history_entries: List[Dict], on_close_callback=None):
        self.history_entries = history_entries
        self.on_close_callback = on_close_callback

    def show(self):
        window = tk.Tk()
        window.title("Wallpaper History")
        window.geometry("700x500")

        style = ttk.Style()
        style.theme_use('clam')

        main_frame = ttk.Frame(window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        ttk.Label(
            main_frame,
            text="Wallpaper History",
            font=('Arial', 14, 'bold')
        ).grid(row=0, column=0, sticky=tk.W, pady=10)

        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        tree = ttk.Treeview(
            tree_frame,
            columns=('Date', 'Title', 'Artist'),
            height=15,
            show='headings'
        )
        tree.heading('Date', text='Date')
        tree.heading('Title', text='Title')
        tree.heading('Artist', text='Artist')
        tree.column('Date', width=100)
        tree.column('Title', width=350)
        tree.column('Artist', width=150)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        for entry in self.history_entries:
            date_set = entry.get('date_set', 'Unknown')
            if 'T' in date_set:
                date_set = date_set.split('T')[0]
            tree.insert('', 'end', values=(
                date_set,
                entry.get('title', 'Unknown'),
                entry.get('artist', 'Unknown')
            ), tags=(entry.get('painting_id', ''),))

        def on_double_click(event):
            selection = tree.selection()
            if selection:
                item = selection[0]
                tags = tree.item(item)['tags']
                if tags:
                    painting_id = tags[0]
                    for entry in self.history_entries:
                        if entry.get('painting_id') == painting_id:
                            InfoPopup(entry).show_threaded()
                            break

        tree.bind('<Double-1>', on_double_click)

        ttk.Button(
            main_frame,
            text="Close",
            command=window.destroy
        ).grid(row=2, column=0, sticky=(tk.W, tk.E))

        def on_closing():
            if self.on_close_callback:
                self.on_close_callback()
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", on_closing)
        window.mainloop()

    def show_threaded(self):
        threading.Thread(target=self.show, daemon=True).start()