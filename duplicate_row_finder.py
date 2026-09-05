"""
Duplicate Row Finder
=====================
A desktop GUI (tkinter) for finding duplicate rows in a CSV or Excel file.

Run with:
    python app.py

Requires: pandas, openpyxl (for .xlsx), xlrd (only if you need old .xls files)
"""

import os
import queue
import threading
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd

APP_TITLE = "Duplicate Row Finder"
MAX_ROWS_DISPLAYED = 2000          # cap on rows shown in the results table
LARGE_FILE_WARN_BYTES = 200 * 1024 * 1024   # 200 MB
LARGE_ROW_WARN_COUNT = 500_000
CSV_ENCODINGS_TO_TRY = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]


# --------------------------------------------------------------------------- #
# Data loading helpers (run on a background thread, must not touch Tk widgets)
# --------------------------------------------------------------------------- #

class LoadError(Exception):
    """Raised for any problem we want shown to the user as a clean message."""


def get_excel_sheet_names(path):
    try:
        xls = pd.ExcelFile(path)
        return xls.sheet_names
    except ImportError as e:
        raise LoadError(
            "Missing a required library to read this Excel file.\n"
            "Try: pip install openpyxl xlrd"
        ) from e
    except Exception as e:
        raise LoadError(f"Could not open the Excel file:\n{e}") from e


def read_csv_robust(path):
    """Try a handful of encodings and let pandas sniff the delimiter."""
    last_error = None
    for encoding in CSV_ENCODINGS_TO_TRY:
        try:
            df = pd.read_csv(
                path,
                sep=None,           # auto-detect delimiter (comma, tab, semicolon, ...)
                engine="python",
                encoding=encoding,
                dtype=str,          # keep raw text; safest for exact duplicate matching
                keep_default_na=False,
                na_values=[""],
            )
            return df
        except (UnicodeDecodeError, UnicodeError) as e:
            last_error = e
            continue
        except pd.errors.EmptyDataError as e:
            raise LoadError("The file appears to be empty (no data found).") from e
        except pd.errors.ParserError as e:
            # Delimiter sniffing failed on this encoding; try a plain comma fallback
            try:
                df = pd.read_csv(
                    path,
                    encoding=encoding,
                    dtype=str,
                    keep_default_na=False,
                    na_values=[""],
                )
                return df
            except Exception as e2:
                last_error = e2
                continue
        except Exception as e:
            last_error = e
            continue

    raise LoadError(
        "Could not parse this CSV file. It may be corrupted, use an unusual "
        f"encoding, or have inconsistent columns.\n\nLast error: {last_error}"
    )


def read_excel_robust(path, sheet_name):
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, dtype=str)
        return df
    except ImportError as e:
        raise LoadError(
            "Missing a required library to read this Excel file.\n"
            "Try: pip install openpyxl xlrd"
        ) from e
    except ValueError as e:
        raise LoadError(f"Could not read sheet '{sheet_name}':\n{e}") from e
    except Exception as e:
        raise LoadError(f"Could not read the Excel file:\n{e}") from e


def load_dataframe(path, sheet_name=None):
    """Loads a CSV or Excel file into a DataFrame of strings (NaN preserved)."""
    if not os.path.exists(path):
        raise LoadError(f"File not found:\n{path}")
    if not os.access(path, os.R_OK):
        raise LoadError(f"Permission denied reading file:\n{path}")

    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        df = read_csv_robust(path)
    elif ext in (".xlsx", ".xlsm", ".xls"):
        if sheet_name is None:
            raise LoadError("No sheet was specified for this Excel file.")
        df = read_excel_robust(path, sheet_name)
    else:
        raise LoadError(
            f"Unsupported file type '{ext}'. Please choose a .csv, .xlsx, .xlsm, or .xls file."
        )

    if df is None or df.shape[1] == 0:
        raise LoadError("No columns were found in this file.")
    if df.shape[0] == 0:
        raise LoadError("The file has headers but no data rows.")

    # Clean up header row: strip stray whitespace, fix blank/duplicate names
    df.columns = _clean_column_names(df.columns)

    return df


def _clean_column_names(columns):
    """Strip whitespace and de-duplicate blank/duplicate header names."""
    cleaned = []
    seen = {}
    for i, col in enumerate(columns):
        name = str(col).strip()
        if name == "" or name.lower().startswith("unnamed:"):
            name = f"Column_{i + 1}"
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 0
        cleaned.append(name)
    return cleaned


# --------------------------------------------------------------------------- #
# Duplicate-finding logic
# --------------------------------------------------------------------------- #

def _build_key_series(df, key_columns, ignore_case, trim_whitespace):
    """Builds one composite string key per row for the chosen columns.

    NaN is mapped to a consistent sentinel so that missing values in the
    same columns are treated as equal, matching pandas' own .duplicated().
    """
    if not key_columns:
        raise LoadError("Select at least one column to compare.")

    key_df = df[key_columns].copy()

    for col in key_columns:
        series = key_df[col]

        def normalize(v):
            if pd.isna(v):
                return v
            v = str(v)
            if trim_whitespace:
                v = v.strip()
            if ignore_case:
                v = v.lower()
            return v

        key_df[col] = series.map(normalize)

    return key_df.fillna("@@NA@@").astype(str).agg(lambda r: "|~|".join(r), axis=1)


def find_duplicates(df, key_columns, ignore_case, trim_whitespace, mode):
    """
    mode: 'all'   -> every row that belongs to a duplicate group
          'first' -> every duplicate row except the first in each group
          'last'  -> every duplicate row except the last in each group
    Returns (result_df, group_count, total_duplicate_rows) or (None, 0, 0) if none found.
    result_df has 'Duplicate Group' and 'Source Row' columns prepended.
    """
    key_series = _build_key_series(df, key_columns, ignore_case, trim_whitespace)

    mask_all = key_series.duplicated(keep=False)
    if mode == "first":
        selected_mask = key_series.duplicated(keep="first")
    elif mode == "last":
        selected_mask = key_series.duplicated(keep="last")
    else:
        selected_mask = mask_all

    n_dup_groups = key_series[mask_all].nunique()
    n_selected = int(selected_mask.sum())

    if n_selected == 0:
        return None, 0, 0

    result_df = df[selected_mask].copy()
    group_codes = pd.factorize(key_series[selected_mask])[0] + 1
    result_df.insert(0, "Duplicate Group", group_codes)
    result_df.insert(1, "Source Row", [i + 2 for i in result_df.index])  # header = row 1

    result_df = result_df.sort_values(
        by=["Duplicate Group", "Source Row"], kind="mergesort"
    ).reset_index(drop=True)

    return result_df, n_dup_groups, n_selected


def build_cleaned_dataframe(df, key_columns, ignore_case, trim_whitespace, keep="first"):
    """
    Returns (cleaned_df, n_rows_removed). cleaned_df is the ORIGINAL data
    (all original columns, original row order) with duplicate rows removed
    based on the given key columns/options. keep='first' keeps the first
    occurrence of each duplicate group and drops the rest; keep='last' keeps
    the last occurrence instead.
    """
    key_series = _build_key_series(df, key_columns, ignore_case, trim_whitespace)
    drop_mask = key_series.duplicated(keep=keep)
    cleaned_df = df[~drop_mask].copy()
    return cleaned_df, int(drop_mask.sum())


# --------------------------------------------------------------------------- #
# GUI
# --------------------------------------------------------------------------- #

class DuplicateFinderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1000x700")
        self.minsize(800, 550)

        self.file_path = None
        self.df = None
        self.result_df = None
        self.column_vars = {}
        self.msg_queue = queue.Queue()

        self._build_ui()
        self.after(100, self._poll_queue)

    # ---------------------------------------------------------------- UI --

    def _build_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass

        # --- File selection row ---
        file_frame = ttk.Frame(self, padding=(10, 10, 10, 5))
        file_frame.pack(fill="x")

        ttk.Button(file_frame, text="Open File...", command=self.browse_file).pack(side="left")
        self.file_label_var = tk.StringVar(value="No file loaded")
        ttk.Label(file_frame, textvariable=self.file_label_var).pack(side="left", padx=10)

        self.sheet_var = tk.StringVar()
        self.sheet_label = ttk.Label(file_frame, text="Sheet:")
        self.sheet_combo = ttk.Combobox(file_frame, textvariable=self.sheet_var, state="readonly", width=25)
        self.sheet_combo.bind("<<ComboboxSelected>>", self._on_sheet_change)
        # hidden until an Excel file with multiple sheets is loaded

        # --- Main paned area: options on left, results on right ---
        main_pane = ttk.PanedWindow(self, orient="horizontal")
        main_pane.pack(fill="both", expand=True, padx=10, pady=5)

        options_frame = ttk.Frame(main_pane, padding=5)
        results_frame = ttk.Frame(main_pane, padding=5)
        main_pane.add(options_frame, weight=1)
        main_pane.add(results_frame, weight=3)

        # -- Options: column picker --
        ttk.Label(options_frame, text="Columns to compare:", font=("", 9, "bold")).pack(anchor="w")

        col_btns = ttk.Frame(options_frame)
        col_btns.pack(fill="x", pady=(2, 4))
        ttk.Button(col_btns, text="Select All", command=lambda: self._set_all_columns(True)).pack(side="left")
        ttk.Button(col_btns, text="Select None", command=lambda: self._set_all_columns(False)).pack(side="left", padx=5)

        col_container = ttk.Frame(options_frame, relief="sunken", borderwidth=1)
        col_container.pack(fill="both", expand=True, pady=(0, 10))

        self.col_canvas = tk.Canvas(col_container, highlightthickness=0)
        col_scroll = ttk.Scrollbar(col_container, orient="vertical", command=self.col_canvas.yview)
        self.col_inner = ttk.Frame(self.col_canvas)
        self.col_inner.bind(
            "<Configure>",
            lambda e: self.col_canvas.configure(scrollregion=self.col_canvas.bbox("all")),
        )
        self.col_canvas.create_window((0, 0), window=self.col_inner, anchor="nw")
        self.col_canvas.configure(yscrollcommand=col_scroll.set)
        self.col_canvas.pack(side="left", fill="both", expand=True)
        col_scroll.pack(side="right", fill="y")

        # -- Options: matching behavior --
        ttk.Label(options_frame, text="Matching options:", font=("", 9, "bold")).pack(anchor="w", pady=(4, 2))
        self.ignore_case_var = tk.BooleanVar(value=True)
        self.trim_ws_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Ignore letter case", variable=self.ignore_case_var).pack(anchor="w")
        ttk.Checkbutton(options_frame, text="Ignore leading/trailing spaces", variable=self.trim_ws_var).pack(anchor="w")

        ttk.Label(options_frame, text="Rows to show:", font=("", 9, "bold")).pack(anchor="w", pady=(10, 2))
        self.mode_var = tk.StringVar(value="all")
        ttk.Radiobutton(options_frame, text="All rows in each duplicate group",
                         variable=self.mode_var, value="all").pack(anchor="w")
        ttk.Radiobutton(options_frame, text="Only extras (keep the first, flag the rest)",
                         variable=self.mode_var, value="first").pack(anchor="w")
        ttk.Radiobutton(options_frame, text="Only extras (keep the last, flag the rest)",
                         variable=self.mode_var, value="last").pack(anchor="w")

        self.find_btn = ttk.Button(options_frame, text="Find Duplicates", command=self.on_find_clicked, state="disabled")
        self.find_btn.pack(fill="x", pady=(14, 4))

        self.export_btn = ttk.Button(options_frame, text="Export Duplicate Rows...", command=self.on_export_clicked, state="disabled")
        self.export_btn.pack(fill="x")

        ttk.Separator(options_frame, orient="horizontal").pack(fill="x", pady=8)

        ttk.Label(
            options_frame,
            text="Or export your original data with duplicates removed\n"
                 "(keeps the first occurrence of each group):",
            justify="left",
        ).pack(anchor="w")
        self.export_clean_btn = ttk.Button(
            options_frame, text="Export Cleaned File...", command=self.on_export_clean_clicked, state="disabled"
        )
        self.export_clean_btn.pack(fill="x", pady=(4, 0))

        # -- Results --
        self.summary_var = tk.StringVar(value="Load a file to begin.")
        ttk.Label(results_frame, textvariable=self.summary_var, font=("", 9, "bold")).pack(anchor="w", pady=(0, 5))

        tree_container = ttk.Frame(results_frame)
        tree_container.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_container, show="headings")
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        self.tree.tag_configure("odd_group", background="#eef3fb")

        # --- Status bar / progress ---
        status_frame = ttk.Frame(self, padding=(10, 2, 10, 8))
        status_frame.pack(fill="x")
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side="left")
        self.progress = ttk.Progressbar(status_frame, mode="indeterminate", length=150)
        self.progress.pack(side="right")

    # ------------------------------------------------------------- Events --

    def browse_file(self):
        path = filedialog.askopenfilename(
            title="Select a CSV or Excel file",
            filetypes=[
                ("Data files", "*.csv *.xlsx *.xlsm *.xls"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx *.xlsm *.xls"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        self._start_file_load(path)

    def _start_file_load(self, path):
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0

        if size > LARGE_FILE_WARN_BYTES:
            proceed = messagebox.askyesno(
                APP_TITLE,
                f"This file is {size / (1024*1024):.0f} MB, which may take a while and use "
                "a lot of memory to load. Continue?",
            )
            if not proceed:
                return

        self.file_path = path
        self.file_label_var.set(os.path.basename(path))
        self._clear_results()
        self.find_btn.config(state="disabled")
        self.export_btn.config(state="disabled")
        self.export_clean_btn.config(state="disabled")

        ext = os.path.splitext(path)[1].lower()
        if ext in (".xlsx", ".xlsm", ".xls"):
            self._set_busy(True, "Reading sheet list...")
            threading.Thread(target=self._worker_list_sheets, args=(path,), daemon=True).start()
        else:
            self.sheet_label.pack_forget()
            self.sheet_combo.pack_forget()
            self._set_busy(True, "Loading file...")
            threading.Thread(target=self._worker_load_df, args=(path, None), daemon=True).start()

    def _worker_list_sheets(self, path):
        try:
            sheets = get_excel_sheet_names(path)
            self.msg_queue.put(("sheets_ready", (path, sheets)))
        except LoadError as e:
            self.msg_queue.put(("error", str(e)))
        except Exception:
            self.msg_queue.put(("error", f"Unexpected error:\n{traceback.format_exc()}"))

    def _worker_load_df(self, path, sheet_name):
        try:
            df = load_dataframe(path, sheet_name)
            self.msg_queue.put(("df_ready", df))
        except LoadError as e:
            self.msg_queue.put(("error", str(e)))
        except MemoryError:
            self.msg_queue.put(("error", "Ran out of memory loading this file. Try a smaller file."))
        except Exception:
            self.msg_queue.put(("error", f"Unexpected error while loading:\n{traceback.format_exc()}"))

    def _on_sheet_change(self, event=None):
        sheet = self.sheet_var.get()
        if not sheet or not self.file_path:
            return
        self._clear_results()
        self.find_btn.config(state="disabled")
        self.export_btn.config(state="disabled")
        self.export_clean_btn.config(state="disabled")
        self._set_busy(True, f"Loading sheet '{sheet}'...")
        threading.Thread(target=self._worker_load_df, args=(self.file_path, sheet), daemon=True).start()

    def on_find_clicked(self):
        if self.df is None:
            return
        key_columns = [c for c, v in self.column_vars.items() if v.get()]
        if not key_columns:
            messagebox.showwarning(APP_TITLE, "Select at least one column to compare.")
            return

        n_rows = len(self.df)
        if n_rows > LARGE_ROW_WARN_COUNT:
            proceed = messagebox.askyesno(
                APP_TITLE,
                f"This file has {n_rows:,} rows, which may take a while to process. Continue?",
            )
            if not proceed:
                return

        self.find_btn.config(state="disabled")
        self.export_btn.config(state="disabled")
        self.export_clean_btn.config(state="disabled")
        self._set_busy(True, "Searching for duplicates...")

        args = (
            self.df,
            key_columns,
            self.ignore_case_var.get(),
            self.trim_ws_var.get(),
            self.mode_var.get(),
        )
        threading.Thread(target=self._worker_find_duplicates, args=args, daemon=True).start()

    def _worker_find_duplicates(self, df, key_columns, ignore_case, trim_ws, mode):
        try:
            result_df, n_groups, n_rows = find_duplicates(df, key_columns, ignore_case, trim_ws, mode)
            self.msg_queue.put(("dupes_ready", (result_df, n_groups, n_rows)))
        except LoadError as e:
            self.msg_queue.put(("error", str(e)))
        except MemoryError:
            self.msg_queue.put(("error", "Ran out of memory while comparing rows. Try selecting fewer columns."))
        except Exception:
            self.msg_queue.put(("error", f"Unexpected error while searching:\n{traceback.format_exc()}"))

    def on_export_clicked(self):
        if self.result_df is None or self.result_df.empty:
            messagebox.showinfo(APP_TITLE, "There are no results to export.")
            return

        path = filedialog.asksaveasfilename(
            title="Save duplicate rows as...",
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv"), ("Excel file", "*.xlsx")],
        )
        if not path:
            return

        try:
            ext = os.path.splitext(path)[1].lower()
            if ext == ".xlsx":
                self.result_df.to_excel(path, index=False)
            else:
                self.result_df.to_csv(path, index=False)
            messagebox.showinfo(APP_TITLE, f"Saved {len(self.result_df):,} rows to:\n{path}")
        except PermissionError:
            messagebox.showerror(
                APP_TITLE, "Could not save the file — it may be open in another program."
            )
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Could not save the file:\n{e}")

    def on_export_clean_clicked(self):
        if self.df is None:
            return
        key_columns = [c for c, v in self.column_vars.items() if v.get()]
        if not key_columns:
            messagebox.showwarning(APP_TITLE, "Select at least one column to compare.")
            return

        keep = self.mode_var.get()
        if keep not in ("first", "last"):
            keep = "first"

        self.find_btn.config(state="disabled")
        self.export_btn.config(state="disabled")
        self.export_clean_btn.config(state="disabled")
        self._set_busy(True, "Building cleaned file...")

        args = (self.df, key_columns, self.ignore_case_var.get(), self.trim_ws_var.get(), keep)
        threading.Thread(target=self._worker_build_cleaned, args=args, daemon=True).start()

    def _worker_build_cleaned(self, df, key_columns, ignore_case, trim_ws, keep):
        try:
            cleaned_df, n_removed = build_cleaned_dataframe(df, key_columns, ignore_case, trim_ws, keep)
            self.msg_queue.put(("clean_ready", (cleaned_df, n_removed)))
        except LoadError as e:
            self.msg_queue.put(("error", str(e)))
        except MemoryError:
            self.msg_queue.put(("error", "Ran out of memory while comparing rows. Try selecting fewer columns."))
        except Exception:
            self.msg_queue.put(("error", f"Unexpected error while cleaning:\n{traceback.format_exc()}"))

    def _handle_clean_ready(self, cleaned_df, n_removed):
        self._set_busy(False, "Done.")
        self.find_btn.config(state="normal")
        self.export_clean_btn.config(state="normal")
        if self.result_df is not None and not self.result_df.empty:
            self.export_btn.config(state="normal")

        if n_removed == 0:
            messagebox.showinfo(
                APP_TITLE, "No duplicate rows were found — nothing to remove."
            )
            return

        path = filedialog.asksaveasfilename(
            title="Save cleaned file as...",
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv"), ("Excel file", "*.xlsx")],
        )
        if not path:
            return

        try:
            ext = os.path.splitext(path)[1].lower()
            if ext == ".xlsx":
                cleaned_df.to_excel(path, index=False)
            else:
                cleaned_df.to_csv(path, index=False)
            messagebox.showinfo(
                APP_TITLE,
                f"Removed {n_removed:,} duplicate row(s). Saved {len(cleaned_df):,} row(s) to:\n{path}",
            )
        except PermissionError:
            messagebox.showerror(
                APP_TITLE, "Could not save the file — it may be open in another program."
            )
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Could not save the file:\n{e}")

    # -------------------------------------------------------------- Queue --

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self.msg_queue.get_nowait()
                if kind == "sheets_ready":
                    self._handle_sheets_ready(*payload)
                elif kind == "df_ready":
                    self._handle_df_ready(payload)
                elif kind == "dupes_ready":
                    self._handle_dupes_ready(*payload)
                elif kind == "error":
                    self._set_busy(False, "Error.")
                    self._restore_buttons_after_error()
                    messagebox.showerror(APP_TITLE, payload)
                elif kind == "clean_ready":
                    self._handle_clean_ready(*payload)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _restore_buttons_after_error(self):
        """Re-enables buttons after a background error, based on what's loaded."""
        if self.df is not None:
            self.find_btn.config(state="normal")
            self.export_clean_btn.config(state="normal")
        if self.result_df is not None and not self.result_df.empty:
            self.export_btn.config(state="normal")

    def _handle_sheets_ready(self, path, sheets):
        self._set_busy(False, "Select a sheet.")
        self.sheet_combo["values"] = sheets
        self.sheet_label.pack(side="left", padx=(15, 2))
        self.sheet_combo.pack(side="left")
        if len(sheets) == 1:
            self.sheet_var.set(sheets[0])
            self._on_sheet_change()
        else:
            self.sheet_var.set("")

    def _handle_df_ready(self, df):
        self.df = df
        self._set_busy(False, f"Loaded {len(df):,} rows, {df.shape[1]} columns.")
        self._populate_columns(df.columns)
        self.find_btn.config(state="normal")

    def _handle_dupes_ready(self, result_df, n_groups, n_rows):
        self.result_df = result_df
        self._set_busy(False, "Done.")
        self.find_btn.config(state="normal")
        self.export_clean_btn.config(state="normal")

        if result_df is None:
            self.summary_var.set("No duplicate rows found with the selected columns and options.")
            self._clear_results(keep_summary=True)
            self.export_btn.config(state="disabled")
            return

        self.export_btn.config(state="normal")
        shown = min(len(result_df), MAX_ROWS_DISPLAYED)
        summary = f"Found {n_rows:,} duplicate row(s) in {n_groups:,} group(s)."
        if len(result_df) > MAX_ROWS_DISPLAYED:
            summary += f"  Showing first {shown:,} rows below — export to get all {len(result_df):,}."
        self.summary_var.set(summary)
        self._display_results(result_df.head(MAX_ROWS_DISPLAYED))

    # -------------------------------------------------------------- Helpers --

    def _set_busy(self, busy, status_text):
        self.status_var.set(status_text)
        if busy:
            self.progress.start(12)
        else:
            self.progress.stop()

    def _populate_columns(self, columns):
        for child in self.col_inner.winfo_children():
            child.destroy()
        self.column_vars = {}
        for col in columns:
            var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(self.col_inner, text=str(col), variable=var)
            cb.pack(anchor="w", padx=4, pady=1)
            self.column_vars[col] = var

    def _set_all_columns(self, value):
        for var in self.column_vars.values():
            var.set(value)

    def _clear_results(self, keep_summary=False):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = ()
        if not keep_summary:
            self.summary_var.set("")

    def _display_results(self, df):
        self._clear_results(keep_summary=True)
        columns = list(df.columns)
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=str(col))
            width = 140 if col not in ("Duplicate Group", "Source Row") else 90
            self.tree.column(col, width=width, anchor="w", stretch=False)

        for _, row in df.iterrows():
            values = ["" if pd.isna(v) else str(v) for v in row]
            group_no = row["Duplicate Group"]
            tag = "odd_group" if int(group_no) % 2 == 1 else ""
            self.tree.insert("", "end", values=values, tags=(tag,) if tag else ())


def main():
    app = DuplicateFinderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
