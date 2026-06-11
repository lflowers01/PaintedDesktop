"""Info popup and history window for PaintedDesktop."""

import tkinter as tk
from tkinter import ttk
import threading
from typing import Optional, Dict, List
import webbrowser


class InfoPopup:
    """Popup window showing current wallpaper info."""
    
    def __init__(self, entry: Dict, on_close_callback=None):
        """
        Initialize info popup.
        
        Args:
            entry: History entry dict
            on_close_callback: Function to call when closed
        """
        self.entry = entry
        self.on_close_callback = on_close_callback
        self.window = None
    
    def show(self):
        """Show the info popup."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Tk()
        self.window.title("What's on my desktop?")
        self.window.geometry("500x300")
        self.window.resizable(False, False)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text=self.entry.get('title', 'Unknown'),
            font=('Arial', 14, 'bold'),
            wraplength=450
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Artist
        artist_label = ttk.Label(
            main_frame,
            text=f"Artist: {self.entry.get('artist', 'Unknown')}",
            font=('Arial', 11)
        )
        artist_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Year
        year = self.entry.get('year')
        if year:
            year_label = ttk.Label(
                main_frame,
                text=f"Year: {year}",
                font=('Arial', 11)
            )
            year_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Institution
        institution_label = ttk.Label(
            main_frame,
            text=f"Source: {self.entry.get('source_institution', 'Unknown')}",
            font=('Arial', 11)
        )
        institution_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Date set
        date_set = self.entry.get('date_set', 'Unknown')
        if 'T' in date_set:
            date_set = date_set.split('T')[0]  # Extract just the date
        date_label = ttk.Label(
            main_frame,
            text=f"Set on: {date_set}",
            font=('Arial', 10),
            foreground='gray'
        )
        date_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Link button
        def open_link():
            url = self.entry.get('source_url', '')
            if url:
                webbrowser.open(url)
        
        link_button = ttk.Button(
            main_frame,
            text="View on source website",
            command=open_link
        )
        link_button.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)
        
        # Close button
        close_button = ttk.Button(
            main_frame,
            text="Close",
            command=self.window.destroy
        )
        close_button.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        def on_closing():
            if self.on_close_callback:
                self.on_close_callback()
            self.window.destroy()
        
        self.window.protocol("WM_DELETE_WINDOW", on_closing)
        self.window.mainloop()
    
    def show_threaded(self):
        """Show popup in a separate thread."""
        thread = threading.Thread(target=self.show, daemon=True)
        thread.start()


class HistoryWindow:
    """Window showing wallpaper history."""
    
    def __init__(self, history_entries: List[Dict], on_close_callback=None):
        """
        Initialize history window.
        
        Args:
            history_entries: List of history entry dicts
            on_close_callback: Function to call when closed
        """
        self.history_entries = history_entries
        self.on_close_callback = on_close_callback
        self.window = None
        self.info_popup = None
    
    def show(self):
        """Show the history window."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Tk()
        self.window.title("Wallpaper History")
        self.window.geometry("700x500")
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Wallpaper History",
            font=('Arial', 14, 'bold')
        )
        title_label.grid(row=0, column=0, sticky=tk.W, pady=10)
        
        # Create treeview for history
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
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Populate tree
        for entry in self.history_entries:
            date_set = entry.get('date_set', 'Unknown')
            if 'T' in date_set:
                date_set = date_set.split('T')[0]
            
            tree.insert('', 'end', values=(
                date_set,
                entry.get('title', 'Unknown'),
                entry.get('artist', 'Unknown')
            ), tags=(entry.get('painting_id', ''),))
        
        # Double-click to show details
        def on_double_click(event):
            selection = tree.selection()
            if selection:
                item = selection[0]
                tags = tree.item(item)['tags']
                if tags:
                    painting_id = tags[0]
                    # Find entry with this ID
                    for entry in self.history_entries:
                        if entry.get('painting_id') == painting_id:
                            self.info_popup = InfoPopup(entry)
                            self.info_popup.show_threaded()
                            break
        
        tree.bind('<Double-1>', on_double_click)
        
        # Close button
        close_button = ttk.Button(
            main_frame,
            text="Close",
            command=self.window.destroy
        )
        close_button.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        def on_closing():
            if self.on_close_callback:
                self.on_close_callback()
            self.window.destroy()
        
        self.window.protocol("WM_DELETE_WINDOW", on_closing)
        self.window.mainloop()
    
    def show_threaded(self):
        """Show window in a separate thread."""
        thread = threading.Thread(target=self.show, daemon=True)
        thread.start()
