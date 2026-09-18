#Date last changed: Sep 17, 2026
#Description: GUI and functionality to merge 2 files on key columns with any join type, or concatenate 2 files or a folder of csv files. Extensive error checking

import tkinter as tk
import pandas as pd
from tkinter import filedialog
from tkinter import ttk
from pathlib import Path
import os


#------- Main function -------
def merge(path1, path2, pathfolder, option, key1=None, key2=None, join_type=None, ignore_inner=None):
    """
    Primary merge function. takes button inputs and routes to correct workhorse functions after some error checking
    """

    #Checks if input is insufficient size
    if not ((path1 and path2) or pathfolder):
        if selected_option.get() == "merge":
            path_message3.config(text="Please select 2 files")
            return
        else:
            path_message3.config(text="Please select 2 files or a folder")
            return

    #Checks if files are unique on merge mode specifically, as it only matters for merge
    if path1 == path2:
        if path1 is not None:
            if option == "merge":
                path_message3.config(text="Please select 2 unique files")
                return

    #Sends to merge function
    if option == "merge":
        merge_files(path1, path2, key1, key2, join_type, ignore_inner)

    #Sends to folder or 2-file concat function 
    else:
        if pathfolder:
            concat_folder(pathfolder, False)
        else:
            concat_2files(path1, path2, False)




#------- Primary program functions -------

def merge_files(path1, path2, key1, key2, join_type, ignore_inner):
    """
    Merges 2 files (path1, path2) on a shared key (key1, key2) using a selected join type (join_type) with support for excluding inner rows (ignore_inner)
    """

    #Resets error message 4 for clarity
    path_message4.config(text="")

    #Load files into dataframes
    try:
        df1 = pd.read_csv(path1)
        df2 = pd.read_csv(path2)
    except:
        path_message3.config(text="Issue with at least 1 file")
        return

    #Creates a pathlib object for names and folder path
    pathlibpath1 = Path(path1)
    pathlibpath2 = Path(path2)
    folder = pathlibpath1.parent
    name1 = pathlibpath1.name
    name2 = pathlibpath2.name

    #Checks if both keys are not unique
    if not df1[key1].is_unique and not df2[key2].is_unique:
        path_message4.config(text="Key columns are not unique identifiers - duplicate values will multiply rows\nChange key values or clean data")
        return

    #Merge dataframes together entierly to begin with
    try:
        merged = df1.merge(df2, left_on=key1, right_on=key2, how="outer", indicator=True)
    except:
        path_message4.config(text="- Merge error -\nCheck if selected keys are compatible types or file includes suffixes '_x' or '_y'")
        return

    #Set up filtering based on join type
    keep_list = []
    if join_type == "inner":
        keep_list.append("both")
    elif join_type == "left":
        keep_list.append("left_only")
    elif join_type == "right":
        keep_list.append("right_only")
    else:
        keep_list.append("left_only")
        keep_list.append("right_only")

    #Change filtering based on whether user wants to ignore inner rows
    if not ignore_inner:
        keep_list.append("both")

    #Creates list of Trues and Falses for rows to keep and not keep
    boolean_list = merged["_merge"].isin(keep_list)

    #Drops rows that are not kept (Falses from previous command) - Applies join type and ignore_inner options
    result = merged[boolean_list].drop(columns="_merge")

    #Checks if resulting file would be empty
    if result.empty:
        path_message4.config(text="Result file would be empty given selected options - No file created")
        return

    #Creates csv with merged file - Primary goal of function
    try:
        result.to_csv(f"{folder}/_merged.csv", index=False, encoding="utf-8")
    except:
        path_message4.config(text="Issue creating csv - Close _merged.csv if it is open")
        return

    #Gets values for join categories for reporting
    matched = (merged["_merge"] == "both").sum()
    left = (merged["_merge"] == "left_only").sum()
    right = (merged["_merge"] == "right_only").sum()
    total = len(merged)
    output = len(result)

    #Opens confirmation window with relevant information and allows user to open file location
    confirmation_window(name1, name2, folder, "merged", 0, matched, left, right, total, output)


def concat_2files(path1, path2, bypass):
    """
    Concatenates 2 csv files (path1, path2)
    """

    #Loads files into dataframes
    try:
        df1 = pd.read_csv(path1)
        df2 = pd.read_csv(path2)
    except:
        path_message3.config(text="Issue with at least 1 file")
        return

    #Checks to see if any columns are mismatched
    #bypass allows users to proceed even if columns are mismatched
    if not bypass:
        set1 = set(df1.columns)
        set2 = set(df2.columns)
        if set1 != set2:
            matching = 0
            mismatching = 0
            for i in set1:
                if i in set2:
                    matching += 1
                else:
                    mismatching += 1
            for i in set2:
                if i not in set1:
                    mismatching += 1

            #Opens imperfect_columns_window to allow user to proceed with bypass or back out
            imperfect_columns_window(2, matching, mismatching, path1, path2)
            return

    #Create concatenated dataframe
    finaldf = pd.concat([df1, df2], ignore_index=True)

    #Create pathlib objects for reporting and folder path
    pathlibpath1 = Path(path1)
    pathlibpath2 = Path(path2)

    #Creates new concatenated csv file
    finaldf.to_csv(f"{pathlibpath1.parent}/_merged.csv", index=False, encoding="utf-8")

    #Opens confirmation window with relevant information and allows user to open file location
    confirmation_window(pathlibpath1.name, pathlibpath2.name, pathlibpath1.parent, "concatenated", 0)


def concat_folder(path, bypass):
    """
    Concatenates all csv files in a selected folder
    """

    #Tracks good csv file paths, and number of unusable csv files
    csv_files = []
    bad_csvs = 0

    #Loops through selected folder
    for file in os.listdir(path):
        pathlib_temp = Path(file)
        if pathlib_temp.suffix == ".csv":
            #Ignores output file from previous run - file will still be overwritten, just not used in concatenation
            if pathlib_temp.name == "_merged.csv":
                continue

            #Adds usable csv files to list, tracks unusbale csv files (empty or corrupted)
            try:
                df = pd.read_csv(f"{path}/{file}")
                csv_files.append(df)
            except:
                bad_csvs += 1

    #Guards against not having enough usuable csv files in selected folder
    if len(csv_files) < 2:
        path_message2.config(text="Less than 2 usable csvs in folder")
        return

    #Checks to see if any columns are mismatched, and reports how many files are affected
    #bypass allows users to proceed even if columns are mismatched
    if not bypass:
        if csv_files:
            columns_set = set(csv_files[0].columns)
        else:
            path_message2.config(text="No files in folder")
            return
        matching = 0
        mismatching = 0
        files = 0
        for df in csv_files[1:]:
            tempset = set(df.columns)
            badfile = False
            for item in tempset:
                if item not in columns_set:
                    mismatching += 1
                    badfile = True
                else:
                    matching += 1
            for item in columns_set:
                if item not in tempset:
                    mismatching += 1
                    badfile = True
            if badfile:
                files += 1

        if files != 0:
            #Opens imperfect_columns_window to allow user to proceed with bypass or back out
            imperfect_columns_window(files, matching, mismatching, path, None)
            return

    #Final concatenation and creation of csv file
    finaldf = pd.concat(csv_files, ignore_index=True)
    finaldf.to_csv(f"{path}/_merged.csv", index=False, encoding="utf-8")

    #Opens confirmation window with relevant information and allows user to open file location
    confirmation_window(len(csv_files), None , path, "concatenated", bad_csvs)


#------- File selection functions -------

def browse_file1():
    """
    Allows user to select file number 1 and updates everything accordingly
    """

    #Browse and select file 1
    global filepath1
    filepath1 = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
    pathlibpath = Path(filepath1)
    path_message1.config(text=f"File 1: {pathlibpath.name}")

    #Clears folder selection
    global folderpath
    folderpath = None
    path_message3.config(text=f"")

    #Resets 4th error message for clarity
    path_message4.config(text="")

    #Resets key for this file and populates new dropdown
    key1_var.set("")
    populate_dropdown1(filepath1)


def browse_file2():
    """
    Allows user to select file number 2 and updates everything accordingly
    """

    #Browse and select file 2
    global filepath2
    filepath2 = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
    pathlibpath = Path(filepath2)
    path_message2.config(text=f"File 2: {pathlibpath.name}")

    #Clears folder selection
    global folderpath
    folderpath = None
    path_message3.config(text=f"")

    #Resets 4th error message for clarity
    path_message4.config(text="")

    #Resets key for this file and populates new dropdown
    key2_var.set("")
    populate_dropdown2(filepath2)


def browse_folder():
    """
    Allows user to select folder and updates everything accordingly
    """

    #Browse and select folder
    global folderpath
    folderpath = filedialog.askdirectory()
    pathlibpath = Path(folderpath)
    path_message3.config(text=f"Folder: {pathlibpath.name}/")

    #Clears individual file selections
    global filepath1
    global filepath2
    filepath1 = None
    filepath2 = None
    path_message1.config(text=f"")
    path_message2.config(text=f"")

def populate_dropdown1(path):
    """
    Populates key selection dropdown for file 1 and handles errors and updates
    """
    #Empty path check
    if (path == None) or (path == ""):
        menu = key_dropdown1["menu"]
        menu.delete(0, "end")
        return

    #Refreshes dropdown
    menu = key_dropdown1["menu"]
    menu.delete(0, "end")

    #Populates dropdown
    try:
        columns = pd.read_csv(path, nrows=0).columns.tolist()
        for item in columns:
            menu.add_command(label=item, command=tk._setit(key1_var, item))
        key1_var.set(columns[0])
    except:
        path_message3.config(text="Issue with at least 1 file")

def populate_dropdown2(path):
    """
    Populates key selection dropdown for file 2 and handles errors and updates
    """

    #Empty path check
    if (path == None) or (path == ""):
        menu = key_dropdown2["menu"]
        menu.delete(0, "end")
        return

    #Refreshes dropdown
    menu = key_dropdown2["menu"]
    menu.delete(0, "end")

    #Populates dropdown
    try:
        columns = pd.read_csv(path, nrows=0).columns.tolist()
        for item in columns:
            menu.add_command(label=item, command=tk._setit(key2_var, item))
        key2_var.set(columns[0])
    except:
        path_message3.config(text="Issue with at least 1 file")

#------- UI option control functions -------
def change_mode(mode):
    """
    Updates UI when mode is changed
    """

    #Resets error message 4 for clarity
    path_message4.config(text="")

    #Changes to concatenate mode
    if mode == "c":
        #Enables folder selection
        select_button3.config(state=tk.NORMAL)

        #Disables key/join frame
        for child in dropdownframe.winfo_children():
            try:
                child.configure(state="disabled")
            except:
                pass
        for child in dropdown_subframe.winfo_children():
                try:
                    child.configure(state="disabled")
                except:
                    pass

    #Changes to merge mode
    else:
        #Disables folder selection and clears existing selection
        select_button3.config(state=tk.DISABLED)
        global folderpath
        folderpath = None
        path_message3.config(text=f"")

        #Enables key/join frame
        for child in dropdownframe.winfo_children():
            try:
                child.configure(state="normal")
            except:
                pass
        for child in dropdown_subframe.winfo_children():
            try:
                child.configure(state="normal")
                if join_type.get() == "inner":
                    change_join("inner")
            except:
                pass


def change_join(join_type):
    """
    Function specifically to prevent inner + ignore-inner selection contradiction
    """

    #Disables "ignore inner" option if join type is inner
    if join_type == "inner":
        ignore_inner_checkbox.config(state="disabled")
        ignore_inner.set(False)

    elif join_type == "outer":
        ignore_inner_checkbox.config(state="normal")

    elif join_type == "left":
        ignore_inner_checkbox.config(state="normal")

    elif join_type == "right":
        ignore_inner_checkbox.config(state="normal")

    
#------- Windows -------
def confirmation_window(name1, name2, path, mode, skipped, matched=None, left=None, right=None, total=None, output=None):
    """
    Window that displays when merge or concatenation is successful
    """

    #Change label based on folder or files
    if name2 is None:
        title = f"{name1} csv files in\n{path}\nsuccessfully {mode} to _merged.csv"
    else:
        title = f"{name1}\n{name2}\nsuccessfully {mode} to _merged.csv"

    #Report any skipped files after folder concatenating
    if skipped > 0:
        subtitle=f"{skipped} corrupted or empty csv files skipped"
    else:
        subtitle=""

    #Report matching numbers after merging
    if mode == "merged":
        subtitle=f"{matched}/{total} rows matching, {output} rows in merged file\n(Input file had: {matched} Inner rows, {left} unmatched left rows, {right} unmatched right rows)"

    #GUI
    confirmwndow = tk.Toplevel(window)
    confirmwndow.title("Success")
    confirmwndow.geometry("550x150")

    confirmlabel = tk.Label(confirmwndow, text=f"{title}", font=18)
    confirmlabel.pack(pady=5)

    skipped_label = tk.Label(confirmwndow, text=subtitle)
    skipped_label.pack(pady=5)

    openbutton = tk.Button(confirmwndow, text="Open file location 📂", command=lambda: open_filepath(path, confirmwndow))
    openbutton.pack()

def open_filepath(path, close_window):
    """Helper for confirmation window"""
    os.startfile(path)
    close_window.destroy()


def imperfect_columns_window(files, matching, nonmatching, path1, path2):
    """
    Window to warn user of imperfect column matching in concatenation and allows them to proceed or back out
    """
    errorwindow = tk.Toplevel(window)
    errorwindow.title("Column Mismatch")
    errorwindow.geometry("450x100")

    confirmlabel = tk.Label(errorwindow, text=f"{files} files do not have fully matching columns.\n{matching} columns are matching and {nonmatching} are not", font=18)
    confirmlabel.pack(pady=5)

    buttonframe = tk.Frame(errorwindow, width=450)
    buttonframe.pack(expand=True)
    buttonframe.columnconfigure(1, minsize=160)

    proceedbutton = tk.Button(buttonframe, text="Proceed", font=("Arial", 12), command=lambda: proceed(errorwindow, path1, path2))
    proceedbutton.grid(row=0, column=0, sticky="w", pady=5, padx=5)

    closebutton = tk.Button(buttonframe, text="Close", font=("Arial", 12), command=lambda: errorwindow.destroy())
    closebutton.grid(row=0, column=1, sticky="w", pady=5, padx=5)

def proceed(window, path1, path2):
    """
    Helper for imperfect columns window
    """

    #Routing for folder or 2 file input (path2 would be none if input is a folder)
    if path2 is not None:
        concat_2files(path1, path2, True)
        window.destroy()
    else:
        concat_folder(path1, True)
        window.destroy()


#---------------------------
#------- Primary GUI -------
#---------------------------

window = tk.Tk()
window.geometry("420x450")
window.title("CSV Merger")

#File and mode frame ---------------------------------------------------------------------------------------------------------------------------
frame = tk.LabelFrame(window, padx=15, pady=10)
frame.pack(fill="x", padx=20, pady=10)
frame.columnconfigure(1, minsize=140)

#Buttons for file selection
select_button1 = tk.Button(frame, text="Choose File 1", width=20, command=browse_file1)
select_button1.grid(row=0, column=0, sticky="w", pady=5)

select_button2 = tk.Button(frame, text="Choose File 2", width=20, command=browse_file2)
select_button2.grid(row=1, column=0, sticky="w", pady=5)

select_button3 = tk.Button(frame, text="Choose Folder", width=20, state=tk.DISABLED, command=browse_folder)
select_button3.grid(row=2, column=0, sticky="w", pady=5)

#Presets files to None to avoid errors on empty file submission
filepath1 = None
filepath2 = None
folderpath = None

#Mode selection
selected_option = tk.StringVar(value="merge")
subframe = tk.Frame(frame)
subframe.grid(row=3, column=0, sticky="w", padx=(0, 0))
tk.Label(subframe, text="Mode:").grid(row=0,column=0, padx=1)
mrb1 = tk.Radiobutton(subframe, text="Merge", variable=selected_option, value="merge", command=lambda: change_mode("m"))
mrb2 = tk.Radiobutton(subframe, text="Concat", variable=selected_option, value="concat", command=lambda: change_mode("c"))
mrb1.grid(row=0,column=1, padx=1)
mrb2.grid(row=0,column=2, padx=1)

#Error messages and selected file information
path_message1 = tk.Label(frame, text="")
path_message1.grid(row=0, column=1, sticky="w", padx=(10, 0))

path_message2 = tk.Label(frame, text="")
path_message2.grid(row=1, column=1, sticky="w", padx=(10, 0))

path_message3 = tk.Label(frame, text="")
path_message3.grid(row=2, column=1, sticky="w", padx=(10, 0))

# End of file/mode frame ----------------------------------------------------------------------------------------------------------------------------


#Key and join type frame -------------------------------------------------------------------------------------------------------------------------
dropdownframe = tk.LabelFrame(window)
dropdownframe.pack(fill="x", padx=20, pady=10)

#Key selection dropdowns
key1_var = tk.StringVar()
tk.Label(dropdownframe, text="File 1 (Left) key column:").grid(row=0,column=0, padx=1, sticky="w")
key_dropdown1 = tk.OptionMenu(dropdownframe, key1_var, "")
key_dropdown1.grid(row=1, column=0, sticky="w", padx=(10, 5))
key_dropdown1.config(width=25)

key2_var = tk.StringVar()
tk.Label(dropdownframe, text="File 2 (Right) key column:").grid(row=2,column=0, padx=1, sticky="w")
key_dropdown2 = tk.OptionMenu(dropdownframe, key2_var, "")
key_dropdown2.grid(row=3, column=0, sticky="w", padx=(10, 5))
key_dropdown2.config(width=25)

#Divider for clarity
divider = ttk.Separator(dropdownframe, orient=tk.HORIZONTAL).grid(row=4, sticky="ew", pady=5)

#Join type selection
tk.Label(dropdownframe, text="Join type:").grid(row=5,column=0, padx=1, sticky="w")
dropdown_subframe = tk.Frame(dropdownframe)
dropdown_subframe.grid(row=6, column=0, sticky="w", padx=(0, 0))

#Selects join type
join_type = tk.StringVar(value="outer")
jrb1 = tk.Radiobutton(dropdown_subframe, text="Outer", variable=join_type, value="outer", command=lambda: change_join("outer"))
jrb2 = tk.Radiobutton(dropdown_subframe, text="Inner", variable=join_type, value="inner", command=lambda: change_join("inner"))
jrb3 = tk.Radiobutton(dropdown_subframe, text="Left", variable=join_type, value="left", command=lambda: change_join("left"))
jrb4 = tk.Radiobutton(dropdown_subframe, text="Right", variable=join_type, value="right", command=lambda: change_join("right"))
jrb1.grid(row=1,column=0, padx=1)
jrb2.grid(row=1,column=1, padx=1)
jrb3.grid(row=1,column=2, padx=1)
jrb4.grid(row=1,column=3, padx=1)

#Vertical divider for clarity
vert_divider = ttk.Separator(dropdown_subframe, orient=tk.VERTICAL).grid(row=1, column=4, sticky="ns", pady=5)

#Ignore inner selection
ignore_inner = tk.BooleanVar()
ignore_inner_checkbox = tk.Checkbutton(dropdown_subframe, variable=ignore_inner, text="ignore inner")
ignore_inner_checkbox.grid(row=1, column=5, sticky="w", padx=(10, 5))

#End of key and join type frame ---------------------------------------------------------------------------------------------------------------------


#Main function button
select_button4 = tk.Button(window, text="Merge", width=35, font=("Arial", 12), 
command=lambda: merge(filepath1, filepath2, folderpath, selected_option.get(), key1_var.get(), key2_var.get(), join_type.get(), ignore_inner.get()))
select_button4.pack()

#Error message under main button
path_message4 = tk.Label(window, text="")
path_message4.pack()

#Starts GUI when program launches
if __name__ == "__main__":
    window.mainloop()
