import tkinter as tk
import os
import pandas as pd
from tkinter import filedialog
from pathlib import Path
from docx import Document
import pdfplumber #pip install pdfplumber in powershell if not active


def extract(path, tables, filetype):

    #File selection error handling
    if not path:
        path_message.config(text="Please select a file or folder")
        return

    #Convert path to pathlib path for handling
    pathlib_path = Path(path)

    #Check if input is one file or batch of files (folder)
    batch=True
    if pathlib_path.suffix == ".pdf":
        batch=False

    #If just one file
    if batch == False:
        text, page_total, file_tables = extract_file(path, tables)
        create_new_file(text, file_tables, filetype, pathlib_path.stem, pathlib_path.parent)
        extracted = 1
        total_tables = len(file_tables)

    #If folder
    else:
        extracted = 0
        page_total = 0
        total_tables = 0
        for file in os.listdir(filepath):
            pathlib_temp = Path(file)
            if pathlib_temp.suffix == ".pdf":
                    text, pages, file_tables = extract_file(f"{path}/{file}", tables)
                    create_new_file(text, file_tables, filetype, pathlib_temp.stem, path)
                    extracted += 1
                    page_total += pages
                    total_tables += len(file_tables)

    #Confirmation
    if batch:
        folder = f"{pathlib_path.name}/"
        folder_path = pathlib_path
    else:
        folder = f"{pathlib_path.parent.name}/"
        folder_path = pathlib_path.parent
    confirm_window(page_total, folder, extracted, total_tables, folder_path)


def confirm_window(pages, folder, extracted, total_tables, folder_path):
    confirmwndow = tk.Toplevel(window)
    confirmwndow.title("Success")
    confirmwndow.geometry("450x100")

    confirmlabel = tk.Label(confirmwndow, text=f"Extracted {pages} pages and {total_tables} tables from {extracted} files\nOutput files in {folder}", font=18)
    confirmlabel.pack(pady=10)

    openbutton = tk.Button(confirmwndow, text="Open file location 📂", command=lambda: open_filepath(folder_path, confirmwndow))
    openbutton.pack()

def open_filepath(path, close_window):
    os.startfile(path)
    close_window.destroy()

def browse_file():
    global filepath
    filepath = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")])
    pathlibpath = Path(filepath)
    path_message.config(text=f"File: {pathlibpath.name}")

def browse_folder():
    global filepath
    filepath = filedialog.askdirectory()
    pathlibpath = Path(filepath)
    path_message.config(text=f"Folder: {pathlibpath.name}/")

def extract_file(path, include_tables):
    with pdfplumber.open(path) as pdf:
        pages = 0
        text = ""
        all_tables = []
        for page in pdf.pages:
            pages += 1
            text += f"\n----Page {page}----\n"
            text += page.extract_text() or ""
            if include_tables:
                tables = page.extract_tables()
                for table in tables:
                    all_tables.append(table)
    return (text, pages, all_tables)

def create_new_file(text, file_tables, filetype, name, path):
    if filetype == "txt":
        with open(f"{path}/{name}.txt", "w", encoding="utf-8") as file:
            file.write(text)

    else:
        doc = Document()
        style = doc.styles['Normal']
        style.font.name = 'Calibri'
        doc.add_paragraph(text)
        doc.save(f"{path}/{name}.docx")

    global tables_made
    tables_made = 0
    if file_tables:
        dataframes = []
        for table in file_tables:
            dataframe = pd.DataFrame(table[1:], columns=table[0])
            dataframes.append(dataframe)
            tables_made += 1

        df = pd.concat(dataframes, axis=1).fillna("")
        df.to_csv(f"{path}/{name}.csv", index=False, encoding='utf-8')


    
window = tk.Tk()
window.geometry("420x250")
window.title("PDF Text extractor")

title = tk.Label(window, text="PDF Text extractor", font=("Arial", 18))
title.pack(pady=(20, 10))

frame = tk.LabelFrame(window, padx=15, pady=10)
frame.pack(fill="x", padx=20, pady=10)
frame.columnconfigure(1, minsize=140)

#File or Folder
filepath = None

select_button = tk.Button(frame, text="Choose File", width=20, command=browse_file)
select_button.grid(row=0, column=0, sticky="w", pady=5)

select_button = tk.Button(frame, text="Choose Folder", width=20, command=browse_folder)
select_button.grid(row=1, column=0, sticky="w", pady=5)

path_message = tk.Label(frame, text="")
path_message.grid(row=0, column=1, sticky="w", padx=(10, 0))

#Filetype options
selected_option = tk.StringVar(value="txt")

subframe = tk.Frame(frame)
subframe.grid(row=1, column=1, sticky="w", padx=(10, 0))
tk.Label(subframe, text="Select file type:").grid(row=0,column=0, padx=1)
rb1 = tk.Radiobutton(subframe, text="txt", variable=selected_option, value="txt").grid(row=0,column=1, padx=1)
rb2 = tk.Radiobutton(subframe, text="docx", variable=selected_option, value="doc").grid(row=0,column=2, padx=1)

#Tables option
include_tables = tk.BooleanVar(value=True)

table_check = tk.Checkbutton(frame, text="Include Tables", variable=include_tables)
table_check.grid(row=2, column=1, sticky="w", padx=(10, 0))

#Button
button1 = tk.Button(frame, text="Extract", font=("Arial", 12), width=10, command=lambda: extract(filepath, include_tables.get(), selected_option.get()))
button1.grid(row=2, column=0, sticky="w", padx=(5, 0))

if __name__ == "__main__":
    window.mainloop()