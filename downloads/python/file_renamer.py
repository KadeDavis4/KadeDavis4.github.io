import tkinter as tk
import os
from tkinter import filedialog
from pathlib import Path


def rename(path,name):
    name_message.config(text="")

    if not path:
        path_message.config(text="Please Select a File")
        return

    if not name:
        name_message.config(text="Please Enter a Name")
        return

    Ppath = Path(path)
    new_path = f"{Ppath.parent}/{name}{Ppath.suffix}"

    os.rename(path, new_path)

    global filepath
    filepath = None
    path_message.config(text="")

    success_window(Ppath.name, name, Ppath.suffix, Ppath.parent)

def browse_file():
    global filepath
    filepath = filedialog.askopenfilename()
    pathlibpath = Path(filepath)
    path_message.config(text=pathlibpath.name)

def open_filepath(path, close_window):
    os.startfile(path)
    close_window.destroy()

def success_window(oldname, setname, suffix, parentpath):
    confirmwndow = tk.Toplevel(window)
    confirmwndow.title("Success")
    confirmwndow.geometry("450x100")

    newname = f"{setname}{suffix}"
    confirmlabel = tk.Label(confirmwndow, text=f"{oldname} successfully renamed to {newname}", font=18)
    confirmlabel.pack(pady=10)

    openbutton = tk.Button(confirmwndow, text="Open file location 📂", command=lambda: open_filepath(parentpath, confirmwndow))
    openbutton.pack()



window = tk.Tk()
window.geometry("500x250")
window.title("File Renamer")

title = tk.Label(window, text="File Renamer", font=("Arial", 20))
title.pack(pady=(20, 10))

frame = tk.LabelFrame(window, padx=15, pady=10)
frame.pack(fill="x", padx=20, pady=10)
frame.columnconfigure(1, minsize=140)

#path
filepath = None
select_button = tk.Button(frame, text="Choose File", width=20, command=browse_file)
select_button.grid(row=0, column=0, sticky="w", pady=5)

path_message = tk.Label(frame, text="")
path_message.grid(row=0, column=1, sticky="w", padx=(10, 0))

#name
tk.Label(frame, text="New Name:").grid(row=1, column=0, sticky="w", pady=(10, 0))
title_entry = tk.Entry(frame, width=30)
title_entry.grid(row=2, column=0, sticky="w", pady=(0, 5))

name_message = tk.Label(frame, text="")
name_message.grid(row=1, column=1, sticky="w", padx=(10, 0))

#button
button1 = tk.Button(frame, text="Rename", font=("Arial", 12), width=10, command=lambda: rename(filepath, title_entry.get()))
button1.grid(row=2, column=2, sticky="e", padx=(5, 0))

if __name__ == "__main__":
    window.mainloop()