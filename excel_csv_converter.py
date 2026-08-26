"""
Excel to CSV Batch Converter
----------------------------
Converts every Excel file in a folder into CSV.

Multi-sheet workbooks become one CSV per sheet, named <workbook>__<sheet>.csv,
so nothing gets silently dropped. Single-sheet workbooks just become <workbook>.csv.
A recursive run mirrors the input folder structure on the output side, so two files
with the same name in different folders don't overwrite each other.

Run it two ways:

    python excel_csv_converter.py                      # no arguments -> opens the GUI
    python excel_csv_converter.py data/                # any argument -> command line
    python excel_csv_converter.py data/ -o converted/
    python excel_csv_converter.py data/ --recursive --overwrite

Requires: pandas, openpyxl (for .xlsx/.xlsm), xlrd (only if you need legacy .xls)
The GUI additionally needs tkinter, which ships with most Python installs.
"""

import argparse
import queue
import sys
import threading
from pathlib import Path

import pandas


# Extensions worth trying. .xls needs xlrd installed, which most people don't
# have anymore, so it's included but failures on it are reported not fatal.
EXCEL_EXTENSIONS = {".xlsx", ".xlsm", ".xls"}


# ----------------------------------------------------------------------
# Core conversion - no printing in here, callers pass in a log function.
# That's what lets the same code drive both the terminal and the GUI.
# ----------------------------------------------------------------------

def find_excel_files(folder, recursive=False):
    """Return every Excel file in folder, sorted for predictable output order."""
    pattern = "**/*" if recursive else "*"
    files = [
        path for path in folder.glob(pattern)
        if path.is_file()
        and path.suffix.lower() in EXCEL_EXTENSIONS
        and not path.name.startswith("~$")   # Excel's temp lock files
    ]
    return sorted(files)


def safe_name(text):
    """Strip characters that aren't safe in a filename (sheet names allow a lot)."""
    bad = '<>:"/\\|?*'
    for character in bad:
        text = text.replace(character, "_")
    return text.strip()


def label(path, root):
    """Path shown in the log, relative to root, so nested files are distinguishable."""
    return path.relative_to(root).as_posix()


def output_path_for(workbook, sheet_name, sheet_count, out_folder, source_root):
    """
    One sheet   -> book.csv
    Many sheets -> book__Sheet1.csv, book__Sheet2.csv ...

    The result is placed under the same subfolder the workbook came from, so a
    recursive run mirrors the input tree instead of flattening it. Without this,
    2025/sales.xlsx and 2026/sales.xlsx both want to be out/sales.csv and one of
    them loses.
    """
    if sheet_count == 1:
        filename = f"{workbook.stem}.csv"
    else:
        filename = f"{workbook.stem}__{safe_name(sheet_name)}.csv"

    # e.g. workbook = root/2026/sales.xlsx  ->  relative_folder = 2026
    # For a non-recursive run this is just '.', which Path harmlessly collapses.
    relative_folder = workbook.parent.relative_to(source_root)
    return out_folder / relative_folder / filename


def convert_workbook(workbook, out_folder, source_root, overwrite, log):
    """
    Convert one workbook. Returns (written, skipped) counts so the caller
    can build a summary. Raises on unreadable files - handled one level up.
    """
    # sheet_name=None gives back a dict of {sheet name: DataFrame} for every sheet.
    sheets = pandas.read_excel(workbook, sheet_name=None)

    written = 0
    skipped = 0

    for sheet_name, frame in sheets.items():
        # Completely empty sheets aren't worth a file.
        if frame.empty:
            log(f"   - skipped empty sheet '{sheet_name}'")
            skipped += 1
            continue

        destination = output_path_for(workbook, sheet_name, len(sheets), out_folder, source_root)

        if destination.exists() and not overwrite:
            log(f"   - skipped {label(destination, out_folder)} (already exists, turn on Overwrite)")
            skipped += 1
            continue

        # The subfolder may not exist yet on the output side - make it on demand.
        destination.parent.mkdir(parents=True, exist_ok=True)

        # index=False keeps pandas from adding a nameless 0,1,2 column.
        frame.to_csv(destination, index=False)
        log(f"   - wrote {label(destination, out_folder)}  ({len(frame)} rows, {len(frame.columns)} cols)")
        written += 1

    return written, skipped


def run_batch(folder, out_folder, recursive, overwrite, log,
              on_file_done=None, should_stop=None):
    """
    Convert a whole folder. Shared by the CLI and the GUI.

    log            - called with each line of output
    on_file_done   - called after each workbook, for the GUI's progress bar
    should_stop    - called between workbooks; if it returns True, stop early

    Returns a summary dict. Raises ValueError if the source folder is bad.
    """
    folder = Path(folder).expanduser().resolve()
    if not folder.is_dir():
        raise ValueError(f"'{folder}' is not a folder.")

    out_folder = Path(out_folder).expanduser().resolve() if out_folder else folder
    out_folder.mkdir(parents=True, exist_ok=True)

    files = find_excel_files(folder, recursive)
    summary = {"files": len(files), "written": 0, "skipped": 0, "failed": [], "cancelled": False}

    if not files:
        log(f"No Excel files found in {folder}")
        return summary

    log(f"Found {len(files)} Excel file(s) in {folder}\n")

    for index, workbook in enumerate(files, start=1):
        if should_stop is not None and should_stop():
            summary["cancelled"] = True
            log("\nCancelled.")
            break

        log(label(workbook, folder))
        try:
            written, skipped = convert_workbook(workbook, out_folder, folder, overwrite, log)
            summary["written"] += written
            summary["skipped"] += skipped
        except Exception as error:
            # One bad file shouldn't kill the whole batch.
            log(f"   ! failed: {error}")
            summary["failed"].append(label(workbook, folder))

        if on_file_done is not None:
            on_file_done(index, len(files))

    return summary


def summary_line(summary):
    """One-line result, used by both front ends."""
    opener = "Cancelled." if summary["cancelled"] else "Done."
    text = f"{opener} {summary['written']} CSV(s) written, {summary['skipped']} skipped."
    if summary["failed"]:
        text += f" Failed on {len(summary['failed'])}: {', '.join(summary['failed'])}"
    return text


# ----------------------------------------------------------------------
# Command line front end
# ----------------------------------------------------------------------

def run_cli(argv):
    parser = argparse.ArgumentParser(description="Batch convert Excel files to CSV.")
    parser.add_argument("folder", nargs="?", default=".", help="folder to scan (default: current)")
    parser.add_argument("-o", "--output", help="where to put the CSVs (default: alongside the sources)")
    parser.add_argument("-r", "--recursive", action="store_true", help="also scan subfolders")
    parser.add_argument("--overwrite", action="store_true", help="replace CSVs that already exist")
    args = parser.parse_args(argv)

    try:
        summary = run_batch(
            args.folder, args.output, args.recursive, args.overwrite, log=print
        )
    except ValueError as error:
        print(error)
        return 1

    print(f"\n{summary_line(summary)}")
    return 0


# ----------------------------------------------------------------------
# GUI front end
#
# The conversion runs on a background thread, otherwise the window would
# freeze solid for the length of the batch. Background threads must never
# touch tkinter widgets, so the worker pushes messages onto a Queue and the
# main thread drains that queue on a timer (see poll_queue).
# ----------------------------------------------------------------------

class ConverterApp:

    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk, scrolledtext

        self.tk = tk
        self.root = root
        root.title("Excel to CSV Batch Converter")
        root.minsize(620, 430)

        self.messages = queue.Queue()
        self.stop_flag = threading.Event()
        self.worker = None

        self.source_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=False)
        self.overwrite_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Pick a folder to get started.")

        frame = ttk.Frame(root, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Only the entry column and the log row should absorb extra space.
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(6, weight=1)

        # --- source folder ---
        ttk.Label(frame, text="Excel folder").grid(row=0, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(frame, textvariable=self.source_var).grid(row=0, column=1, sticky="ew", padx=8, pady=(0, 4))
        ttk.Button(frame, text="Browse...", command=self.pick_source).grid(row=0, column=2, pady=(0, 4))

        # --- output folder ---
        ttk.Label(frame, text="Save CSVs to").grid(row=1, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.output_var).grid(row=1, column=1, sticky="ew", padx=8)
        ttk.Button(frame, text="Browse...", command=self.pick_output).grid(row=1, column=2)

        ttk.Label(
            frame,
            text="Leave blank to save the CSVs next to the original files.",
            foreground="#6b6b6b",
        ).grid(row=2, column=1, sticky="w", padx=8, pady=(2, 10))

        # --- options ---
        options = ttk.Frame(frame)
        options.grid(row=3, column=0, columnspan=3, sticky="w", pady=(0, 10))
        ttk.Checkbutton(options, text="Include subfolders", variable=self.recursive_var).pack(side="left")
        ttk.Checkbutton(options, text="Overwrite existing CSVs", variable=self.overwrite_var).pack(side="left", padx=16)

        # --- buttons ---
        buttons = ttk.Frame(frame)
        buttons.grid(row=4, column=0, columnspan=3, sticky="w")
        self.convert_button = ttk.Button(buttons, text="Convert", command=self.start)
        self.convert_button.pack(side="left")
        self.cancel_button = ttk.Button(buttons, text="Cancel", command=self.cancel, state="disabled")
        self.cancel_button.pack(side="left", padx=8)

        # --- progress ---
        self.progress = ttk.Progressbar(frame, mode="determinate")
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", pady=10)

        # --- log ---
        self.log_box = scrolledtext.ScrolledText(frame, height=14, wrap="none", state="disabled")
        self.log_box.grid(row=6, column=0, columnspan=3, sticky="nsew")

        ttk.Label(frame, textvariable=self.status_var, foreground="#6b6b6b").grid(
            row=7, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.poll_queue()

    # -------------------- folder pickers --------------------

    def pick_source(self):
        from tkinter import filedialog
        chosen = filedialog.askdirectory(title="Choose the folder with your Excel files")
        if chosen:
            self.source_var.set(chosen)

    def pick_output(self):
        from tkinter import filedialog
        chosen = filedialog.askdirectory(title="Choose where the CSVs should go")
        if chosen:
            self.output_var.set(chosen)

    # -------------------- log helpers --------------------

    def write_log(self, text):
        """Main thread only. The widget is kept disabled so users can't type in it."""
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    # -------------------- running the batch --------------------

    def start(self):
        from tkinter import messagebox

        if self.worker is not None and self.worker.is_alive():
            return

        source = self.source_var.get().strip()
        if not source:
            messagebox.showwarning("No folder", "Pick the folder holding your Excel files first.")
            return
        if not Path(source).expanduser().is_dir():
            messagebox.showerror("Bad folder", f"Can't find a folder at:\n{source}")
            return

        self.clear_log()
        self.stop_flag.clear()
        self.progress.configure(value=0, maximum=100)
        self.convert_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.status_var.set("Converting...")

        # Read the widget values now, on the main thread, and hand plain values
        # to the worker. The worker should never reach back into tkinter.
        settings = {
            "folder": source,
            "out_folder": self.output_var.get().strip() or None,
            "recursive": self.recursive_var.get(),
            "overwrite": self.overwrite_var.get(),
        }

        self.worker = threading.Thread(target=self.work, args=(settings,), daemon=True)
        self.worker.start()

    def work(self, settings):
        """Runs on the background thread. Talks to the UI only through the queue."""
        try:
            summary = run_batch(
                settings["folder"],
                settings["out_folder"],
                settings["recursive"],
                settings["overwrite"],
                log=lambda text: self.messages.put(("log", text)),
                on_file_done=lambda done, total: self.messages.put(("progress", (done, total))),
                should_stop=self.stop_flag.is_set,
            )
            self.messages.put(("done", summary))
        except Exception as error:
            self.messages.put(("error", str(error)))

    def cancel(self):
        self.stop_flag.set()
        self.status_var.set("Finishing the current file, then stopping...")

    def poll_queue(self):
        """Drain whatever the worker has sent, then reschedule ourselves."""
        try:
            while True:
                kind, payload = self.messages.get_nowait()

                if kind == "log":
                    self.write_log(payload)
                elif kind == "progress":
                    done, total = payload
                    self.progress.configure(maximum=total, value=done)
                elif kind == "done":
                    self.finish(payload)
                elif kind == "error":
                    self.finish(None, error=payload)
        except queue.Empty:
            pass

        self.root.after(100, self.poll_queue)

    def finish(self, summary, error=None):
        from tkinter import messagebox

        self.convert_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")

        if error is not None:
            self.progress.configure(value=0)
            self.status_var.set("Something went wrong.")
            self.write_log(f"\n! {error}")
            messagebox.showerror("Conversion failed", error)
            return

        text = summary_line(summary)
        self.write_log(f"\n{text}")
        self.status_var.set(text)

    def on_close(self):
        # Ask the worker to stop, but don't block the window from closing -
        # the thread is a daemon, so it dies with the process either way.
        self.stop_flag.set()
        self.root.destroy()


def run_gui():
    try:
        import tkinter as tk
    except ImportError:
        print("tkinter isn't installed, so the GUI can't open.")
        print("Run it from the command line instead, e.g.:  python excel_csv_converter.py myfolder")
        return 1

    root = tk.Tk()
    ConverterApp(root)
    root.mainloop()
    return 0


def main():
    # No arguments at all (double-clicked, or just `python excel_csv_converter.py`)
    # means the user probably wants the window. Any argument means the terminal.
    if len(sys.argv) > 1:
        return run_cli(sys.argv[1:])
    return run_gui()


if __name__ == "__main__":
    sys.exit(main())