import os
import shutil
import tkinter as tk
import threading
import requests
from flask import Flask, jsonify

app = Flask(__name__)

def define_files():
    """
    Function that returns an array of tuples, with a filepath and respective file type for every file in current directory
    """
    files = []
    for i in (os.listdir()):
        if i == "361MainProgram.py":
            continue

        filepath = i
        filename, filepath = os.path.splitext(filepath)
        
        if (filepath == ".jpg") or (filepath == ".jpeg") or (filepath == ".webp") or (filepath == ".png") or (filepath == ".avif"):
            files.append((os.getcwd()+"/"+i,"image"))
        
        elif (filepath == ".ogg") or (filepath ==".mov") or (filepath ==".mp4"):
            files.append((os.getcwd()+"/"+i,"video"))

        elif filepath == ".gif":
            files.append((os.getcwd()+"/"+i,"gif"))

        elif (filepath == ".mp3") or (filepath == ".wav"):
            files.append((os.getcwd()+"/"+i,"audio"))

        elif (filepath == ".pdf") or (filepath == ".docx") or (filepath == ".pptx"):
            files.append((os.getcwd()+"/"+i,"document"))

        elif (filepath == ".txt") or (filepath == ".rtf"):
            files.append((os.getcwd()+"/"+i,"text"))

        elif (filepath == ".py") or (filepath == ".sql") or (filepath == ".asm") or (filepath == ".http") or (filepath == ".har") or (filepath == ".json") or (filepath == ".mjs"):
            files.append((os.getcwd()+"/"+i,"program"))

        elif (filepath == ".app") or (filepath == ".exe") or (filepath == ".msi") or (filepath == ".apk"):
            files.append((os.getcwd()+"/"+i,"application"))

        elif filepath == "":
            if (filename == "Images") or (filename == "Videos") or (filename == "Gifs") or (filename == "Audio") or (filename == "Documents") or (filename == "TextFiles") or (filename == "PlainFolders") or (filename == "Program") or (filename == "Docs") or (filename == "Apps") or (filename == "Other") or (filename == "Folders") or (filename == "Media") or (filename == "ZipFolders")or (filename == "ProgramFiles"):
                continue
            files.append((os.getcwd()+"/"+i,"folder"))

        elif (filepath == ".zip") or (filepath == ".rar"):
            files.append((os.getcwd()+"/"+i,"zip"))
        
        else:
            files.append((os.getcwd()+"/"+i,"other"))
    return files
    

def create_folders(template):
    if template == "Standard":
        os.mkdir("Images")
        os.mkdir("Videos")
        os.mkdir("Gifs")
        os.mkdir("Audio")
        os.mkdir("Documents")
        os.mkdir("TextFiles")
        os.mkdir("Program")
        os.mkdir("Apps")
        os.mkdir("Folders")
        os.mkdir("Other")

    
    elif template == "Broad":

        os.mkdir("Media")
        os.mkdir("Documents")
        os.mkdir("ProgramFiles")
        os.mkdir("Folders")
        os.mkdir("Other")


    elif template == "2Layer":
        os.mkdir("Media")
        os.chdir("Media")
        os.mkdir("Images")
        os.mkdir("Videos")
        os.mkdir("Gifs")
        os.mkdir("Audio")
        os.chdir("..")

        os.mkdir("Documents")
        os.chdir("Documents")
        os.mkdir("Docs")
        os.mkdir("TextFiles")
        os.chdir("..")

        os.mkdir("ProgramFiles")
        os.chdir("ProgramFiles")
        os.mkdir("Program")
        os.mkdir("Apps")
        os.chdir("..")

        os.mkdir("Folders")
        os.chdir("Folders")
        os.mkdir("PlainFolders")
        os.mkdir("ZipFolders")
        os.chdir("..")

        os.mkdir("Other")
    else:
        print("Template does not exist in internal system")

def move_files(template):
    print("Files Moved:")
    if template == "Standard":
        for i in (define_files()):
            print(i)
            if (i[1] == "image"):
                shutil.move(i[0], os.getcwd() + "/Images")
        
            elif (i[1] == "gif"):
                shutil.move(i[0], os.getcwd() + "/Gifs")
        

            elif (i[1] == "program"):
                shutil.move(i[0], os.getcwd() + "/Program")

        
            elif (i[1] == "document"):
                shutil.move(i[0], os.getcwd() + "/Documents")

        
            elif (i[1] == "text"):
                shutil.move(i[0], os.getcwd() + "/TextFiles")

        
            elif (i[1] == "folder") or (i[1] == "zip"):
                shutil.move(i[0], os.getcwd() + "/Folders")

        
            elif (i[1] == "audio"):
                shutil.move(i[0], os.getcwd() + "/Audio")

        
            elif (i[1] == "application"):
                shutil.move(i[0], os.getcwd() + "/Apps")
        
        
            elif (i[1] == "video"):
                shutil.move(i[0], os.getcwd() + "/Videos")

            else:
                shutil.move(i[0], os.getcwd() + "/Other")
        

    elif template == "Broad":
        for i in (define_files()):
            print(i)
            if (i[1] == "image"):
                shutil.move(i[0], os.getcwd() + "/Media")
        
            elif (i[1] == "gif"):
                shutil.move(i[0], os.getcwd() + "/Media")
        

            elif (i[1] == "program"):
                shutil.move(i[0], os.getcwd() + "/ProgramFiles")

        
            elif (i[1] == "document"):
                shutil.move(i[0], os.getcwd() + "/Documents")

        
            elif (i[1] == "text"):
                shutil.move(i[0], os.getcwd() + "/Documents")

        
            elif (i[1] == "folder") or (i[1] == "zip"):
                shutil.move(i[0], os.getcwd() + "/Folders")

        
            elif (i[1] == "audio"):
                shutil.move(i[0], os.getcwd() + "/Media")

        
            elif (i[1] == "application"):
                shutil.move(i[0], os.getcwd() + "/ProgramFiles")
        
        
            elif (i[1] == "video"):
                shutil.move(i[0], os.getcwd() + "/Media")

            else:
                shutil.move(i[0], os.getcwd() + "/Other")

    elif template == "2Layer":
        for i in (define_files()):
            print(i)
            if (i[1] == "image"):
                shutil.move(i[0], os.getcwd() + "/Media/Images")
        
            elif (i[1] == "gif"):
                shutil.move(i[0], os.getcwd() + "/Media/Gifs")
        

            elif (i[1] == "program"):
                shutil.move(i[0], os.getcwd() + "/ProgramFiles/Program")

        
            elif (i[1] == "document"):
                shutil.move(i[0], os.getcwd() + "/Documents/Docs")

        
            elif (i[1] == "text"):
                shutil.move(i[0], os.getcwd() + "/Documents/TextFiles")

        
            elif (i[1] == "folder"):
                shutil.move(i[0], os.getcwd() + "/Folders/PlainFolders")
            
            elif (i[1] == "zip"):
                shutil.move(i[0], os.getcwd() + "/Folders/ZipFolders")
        
            elif (i[1] == "audio"):
                shutil.move(i[0], os.getcwd() + "/Media/Audio")

        
            elif (i[1] == "application"):
                shutil.move(i[0], os.getcwd() + "/ProgramFiles/Apps")
        
        
            elif (i[1] == "video"):
                shutil.move(i[0], os.getcwd() + "/Media/Videos")

            else:
                shutil.move(i[0], os.getcwd() + "/Other")


def undo_sorting():
    print(os.listdir())
    for i in os.listdir():
        if i in ["Images", "Videos", "Gifs", "Audio", "Documents", "Docs", "TextFiles", "Program", "Apps", "Folders", "PlainFolders", "Other", "Media", "ProgramFiles", "ZipFolders"]:
            for j in os.listdir(os.getcwd() + "/" + i):
                shutil.move(os.getcwd() + "/" + i + "/" + j, os.getcwd())
            os.rmdir(os.getcwd() + "/" + i)


def sort_files(template):
    print(template)
    create_folders(template)
    move_files(template)


#GUI helper functions:
def select_button(button, template):
    global selected_button
    global selected_template
    if selected_button is not None:
        selected_button.config(relief=tk.RAISED, text="Select")
    
    button.config(relief=tk.SUNKEN, text="Selected")
    selected_button = button
    selected_template = template
    print(selected_template + " Template Selected")

def run_program(window, template):
    try:
        sort_files(template)
        window.destroy()
        confirmationWindow()
    except:
        window.destroy()
        errorWindow()






#GUI Windows:

def infoWindow():
        infowindow = tk.Toplevel(window)
        infowindow.title("Information")
        infowindow.geometry("400x150")

        infolabel = tk.Label(infowindow, text="This program moves all files \nin the current directory that the program is located, \nand sorts them into appropriate folders \nset by the template you select", font=18)
        infolabel.pack()

        infobackbutton = tk.Button(infowindow, text="Close", command=infowindow.destroy, font=24)
        infobackbutton.pack(pady=20)

def areYouSureWindow():
        global selected_template
        surewindow = tk.Toplevel(window)
        surewindow.title("Are you Sure?")
        surewindow.geometry("400x200")

        surelabel = tk.Label(surewindow, text= "Are you sure?", font=("Arial", 26, "bold"))
        surelabel.pack(padx=10, pady=10)

        explainationLabel = tk.Label(surewindow, text="This will move files on your computer into new directories", font=14)
        explainationLabel.pack()

        yesButton = tk.Button(surewindow, text="Yes", font=20, command=lambda: run_program(surewindow, selected_template))
        yesButton.place(x=75, y=100, width=100)

        noButton = tk.Button(surewindow, text="No", font=20, command=surewindow.destroy)
        noButton.place(x=225, y=100, width=100)


        

def confirmationWindow():
        conwindow = tk.Toplevel(window)
        conwindow.title("Success")
        conwindow.geometry("400x100")
        
        conlabel = tk.Label(conwindow, text=f"Successfully Sorted Files at\n{os.getcwd()}", font=24)
        conlabel.pack()

        backButton = tk.Button(conwindow, text="Close", command=conwindow.destroy)
        backButton.pack(pady=10)

def errorWindow():
        errorwindow = tk.Toplevel(window)
        errorwindow.title("Error")
        errorwindow.geometry("200x75")

        errlabel = tk.Label(errorwindow, text=f"An Error Occured", font=24)
        errlabel.pack()

        backButton = tk.Button(errorwindow, text="Close", command=errorwindow.destroy)
        backButton.pack()


#GUI:

window = tk.Tk()

window.geometry("800x800")
window.title("Organization Program")

title = tk.Label(window, text="Organization Program", font=("Arial", 24))
title.pack(padx=15, pady=15)

introduction = tk.Label(window, text="How this program works:", font=("Arial", 14))
introduction.place(x=225, y=100)
introbutton = tk.Button(window, text="ⓘ", font=20, command=infoWindow)
introbutton.place(x=440, y=100)

spacerframe = tk.Frame(window, height=100)
spacerframe.pack()

frame = tk.Frame(window, height=400)

standardlabelheader = tk.Label(frame, text="Standard Template \nConfiguration:", font=("Arial", 18, "bold"), relief="solid", padx=10, pady=10)
standardlabel = tk.Label(frame, text="/Images\n/Videos\n/Gifs\n/Audio\n/Documents\n/TextFiles\n/Program\n/Apps\n/Folders\n/Other", font=("Arial", 14), relief="sunken", justify="left")
standardlabelheader.grid(row=0, column=1, sticky="news", padx=10)
standardlabel.grid(row=1, column=1, sticky="news", padx=10)

standardlabelheader = tk.Label(frame, text="2 Layer Template \nConfiguration:", font=("Arial", 18, "bold"), relief="solid", padx=10, pady=10)
standardlabel = tk.Label(frame, text="/Media\n  ⤷/Images\n    /Videos\n    /Gifs\n    /Audio\n/Documents\n  ⤷/Docs\n    /TextFiles\n/ProgramFiles\n  ⤷/Program\n    /Apps\n/Folders\n  ⤷/PlainFolders\n    /ZipFolders\n/Other", font=("Arial", 14), relief="sunken", justify="left")
standardlabelheader.grid(row=0, column=0, sticky="news", padx=10)
standardlabel.grid(row=1, column=0, sticky="news", padx=10)

standardlabelheader = tk.Label(frame, text="Broad Template \nConfiguration:", font=("Arial", 18, "bold"), relief="solid", padx=10, pady=10)
standardlabel = tk.Label(frame, text="/Media\n/Documents\n/ProgramFiles\n/Folders\n/Other", font=("Arial", 14), relief="sunken", justify="left")
standardlabelheader.grid(row=0, column=2, sticky="news", padx=10)
standardlabel.grid(row=1, column=2, sticky="news", padx=10)

frame.pack(padx=10)






selected_button = None
button1 = tk.Button(window, text="Select", font=34, width=250, command=lambda: select_button(button1, "2Layer"))
button1.place(x=36, y=600, width=227, height=50)

button2 = tk.Button(window, text="Select", font=34, width=250, command=lambda: select_button(button2, "Standard"))
button2.place(x=283, y=600, width=247, height=50)

button3 = tk.Button(window, text="Select", font=34, width=250, command=lambda: select_button(button3, "Broad"))
button3.place(x=550, y=600, width=213, height=50)

select_button(button2, "Standard")




submitButton = tk.Button(window, text="Sort", font=("Arial", 24), command=areYouSureWindow)
submitButton.place(x=300, y=700, width=450)


dateLabel = tk.Label(window, text=f"Date: {requests.get('http://localhost:5008/date').json()['date']}", font=("Arial", 14, 'bold'))
dateLabel.place(x=20, y=20)


folderSizeLabel = tk.Label(window, text=f"Folder Size: {requests.get('http://localhost:5007/folder-size', params={'path': os.getcwd()}).json()['folder_size_mb']}mb", font=("Arial", 14, 'bold'))
folderSizeLabel.place(x=600, y=20)


undoButton = tk.Button(window, text="Undo", font=("Arial", 24), command=undo_sorting)
undoButton.place(x=50, y=700, width=200)









if __name__ == "__main__":
    flask_thread = threading.Thread(target=lambda: app.run(port=5007))
    flask_thread.daemon = True
    flask_thread.start()

    window.mainloop()





