# main.py
# Python 3.4.3 (v3.4.3:9b73f1c3e601, Feb 24 2015, 22:43:06) [MSC v.1600 32 bit (Intel)] on win32
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import serial
import sys
import glob
from time import sleep
import os
# import binascii
from threading import Thread
from queue import Queue
import urllib.request
import json


# Define Tk objects
root = Tk()
mainframe = ttk.Frame(root, padding="13 13 24 24")
Frame_Dummy = ttk.Frame(mainframe)
s1 = ttk.Separator(mainframe)
Label_Com = ttk.Label(mainframe)
Button_Refresh = ttk.Button(mainframe)
Pgm_Com_Label = ttk.Label(mainframe)
Pgm_Label = ttk.Label(mainframe)
Cart_Label = ttk.Label(mainframe)
Status_Pgm = ttk.Label(mainframe)
Status_Crt = ttk.Label(mainframe)
WebRadio = ttk.Radiobutton(mainframe)
LocalRadio = ttk.Radiobutton(mainframe)
Button_File = ttk.Button(mainframe)
File_Label = ttk.Label(mainframe)
Button_PGM = ttk.Button(mainframe)
s2 = ttk.Separator(mainframe)
Message_Label = ttk.Label(mainframe)
P_Bar = ttk.Progressbar(mainframe)
Button_Web = ttk.Button(mainframe)
ComboWeb = ttk.Combobox(mainframe)

# Define image objects
imgobj_gb = PhotoImage(file='GB.gif')
imgobj_rb = PhotoImage(file='RB.gif')

Enter = 0
# port = []
file_path = ""
But_Ref_Txt = StringVar()
FilePath_Var = StringVar()
Message_Var = StringVar()
P_Bar_Var = StringVar()
ComboVar = StringVar()
RadioVar = IntVar()
PGM_Var = StringVar()

#Define globals
local_filename = ()
headers = ()
ComboValues = []
parsedROM = {}


def find_programmer():
    """
    Cycles through the serial ports until it finds the programmer
    :return:
    Programmer not found = 0
    """
    PGM_Var.set("SEEKING")
    root.update_idletasks()
    if sys.platform.startswith('win'):
        ports = ['COM' + str(i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this is to exclude your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    if(len(result)==0):
        # print("NO PORTS!")
        Status_Pgm['image'] = imgobj_rb
        Status_Crt['image'] = imgobj_rb
        PGM_Var.set("NO PORTS")
        Button_PGM['state'] = "disable"
        return 0
    for i in result:
        # print(i)
        n = test_com_port(i)
        #n = get_programmer([i])
        if(n == 0):
            # print("Not",i)
            pass
        if(n == 1):
            # print("Programmer Only", i)
            Status_Pgm['image'] = imgobj_gb
            Status_Crt['image'] = imgobj_rb
            PGM_Var.set(i)
            Button_PGM['state'] = "disable"
            return 0
        if(n == 2):
            #print("Programmer + Cart", i)
            Status_Pgm['image'] = imgobj_gb
            Status_Crt['image'] = imgobj_gb
            PGM_Var.set(i)
            if(FilePath_Var.get() != ""):
                Button_PGM['state'] = "enable"
            return 0
    PGM_Var.set("NOT FOUND")
    Status_Pgm['image'] = imgobj_rb
    Status_Crt['image'] = imgobj_rb
    Button_PGM['state'] = "disable"


def test_com_port(port=[]):
    """
    Pings the COM port to find the Programmer
    Send Code 1 to programmer
    Programmer return 186 if no Cart
    Programmer returns 174 if Cart is present
    :param port:
    COM port to be tested
    :return:
    No Programmer found = 0
    Programmer but no Cart = 1
    Programmer + Cart = 2
    """
    # print("Testing", port)
    s = serial.Serial(port, 115200, timeout=2)
    s.write(bytes([1]))
    s.write(bytes([13]))
    #n = 0
    #while n == 0:
        #n = s.inWaiting()
    try:
        m = ord(s.read())
        if m == 186:
            s.close()
            return 1
        if m == 174:
            s.close()
            return 2
        s.close()
        return 0
    except:
        return 0

def get_file_path():
    Button_PGM['state'] = "disable"
    # Open file dialogue window
    file_path = filedialog.askopenfilename()
    if file_path == "":
        return None
    # get file size
    filesize = os.stat(file_path).st_size
    # check if it's a .bin file
    if file_path.lower()[-3:] != 'bin':
        FilePath_Var.set("Not a .BIN file!")
        return None
    # check if file too large
    if filesize > 32768:
        FilePath_Var.set("File size too large!")
        return None
    # set file path in Label window
    FilePath_Var.set(file_path)
    f = PGM_Var.get()
    if "NOT FOUND" in f:
        return None
    if "SEEKING" not in f:
        if f != "":
            Button_PGM['state'] = "enable"


def program_nvram_thread(fileName,serPort,fileSize):
    """
    This function runs as a daemon thread
    It waits for the file name and serial port
    to be passed in as Queue variables and then
    programs the NVRAM cart
    It also passes back the progress bar status
    via the "busy" Queue variable
    :param fileName:
    :param serPort:
    :return:
    """
    while TRUE:
        # get file size
        # print("run thread")
        name_file = fileName.get()
        fileName.task_done()
        filesize = fileSize.get()
        fileSize.task_done()
        #filesize = os.stat(name_file).st_size
        # print(filesize)
        # open file
        romfile = open(name_file,"rb")
        # Converts 'bytes' to 'hex'
        # print(binascii.hexlify(test))
        # print(serPort.get())
        # Open serial port
        s = serial.Serial(serPort.get(), 115200)
        serPort.task_done()
        # send program NVRAM command to programmer
        s.write(bytes([2]))
        s.write(bytes([13]))
        # wait for response
        n = 0
        while n == 0:
            n = s.inWaiting()
        m = ord(s.read())
        # print(hex(m))
        # prep file size, MSB first
        x = filesize >> 8
        # print(binascii.hexlify(bytes([x])))
        # Then LSB
        y = filesize & 0xff
        # print(binascii.hexlify(bytes([y])))
        # send filesize to programmer
        s.write(bytes([x]))
        s.write(bytes([y]))
        # prep progress bar elements
        bar = []
        a = filesize // 50
        b = a
        for i in range(50):
            bar.append(a)
            a = a + b
        # send ROM file to programmer
        for i in range(0, filesize):
            z = romfile.read(1)
            s.write(z)
            for j in bar:
                if j == i:
                    busy.put(j)
                    break
        # done, wait for response from programmer
        n = 0
        while n == 0:
            n = s.inWaiting()
        m = ord(s.read())
        # print(hex(m))
        s.close()
        romfile.close()
        busy.put(0)
        busy.put(-1)


def refresh_timer():
    """
    Runs ever millisecond to update the progress bar
    Looks for a value in Queue variable "busy" to pass into the progress bar
    :return:
    """
    try:
        p = busy.get_nowait()
        busy.task_done()
        if p == -1:
            Button_Refresh['state'] = "enable"
            Button_File['state'] = "disable"
            Button_PGM['state'] = "disable"
            Button_Web['state'] = 'disable'
            ComboWeb['state'] = "disable"
            RadioVar.set(0)
        else:
            Message_Var.set("Writing Byte: "+str(p))
            P_Bar_Var.set(p)
            root.update_idletasks()
    except:
        pass
    root.after(1, refresh_timer)


def send_serial():
    """
    Passes the file name, serial port and file size to the
    program NVRAM thread via Queue variables
    This kicks off ROM programming of the NVRAM cart
    It also sets the max value of the progress bar
    :return:
    """
    global ComboValues
    global local_filename
    global headers
    global parsedROM
    Button_Refresh['state'] = "disabled"
    Button_File['state'] = "disabled"
    Button_PGM['state'] = "disabled"
    #Check if local file
    if RadioVar.get() == 2:
        P_Bar['maximum'] = os.stat(FilePath_Var.get()).st_size
        fileName.put(FilePath_Var.get())
        fileSize.put(os.stat(FilePath_Var.get()).st_size)
        serPort.put(PGM_Var.get())
    #Check if Web file
    if RadioVar.get() == 1:
        FilePath_Var.set("Fetching File from Web")
        a = parsedROM['VECTREX ROMS']['TITLES'][ComboVar.get()]['FILE NAME']
        local_filename, headers = urllib.request.urlretrieve('http://www.myexjwlife.com/vectrex/'+a)
        P_Bar['maximum'] = int(headers['Content-Length'])
        FilePath_Var.set("")
        fileName.put(local_filename)
        fileSize.put(int(headers['Content-Length']))
        serPort.put(PGM_Var.get())

def fetch_index_json():
    """
    This function fetches a json file from a web server
    The json file hold all the data used to describe the game and find the ROM
    """
    global ComboValues
    global local_filename
    global headers
    global parsedROM
    del ComboValues[:]
    parsedROM.clear()
    #Pull in json file from web site
    a = "TEST.json"
    try:
        local_filename, headers = urllib.request.urlretrieve('http://www.myexjwlife.com/vectrex/'+a)
    except urllib.error.HTTPError:
        FilePath_Var.set("Missing Index File")
    except urllib.error.URLError:
        FilePath_Var.set("Can't Reach Web Page")
    except:
        FilePath_Var.set("Unknown Error: \n" + str(sys.exc_info()[0]))
    else:
        #open json file
        openfile = open(local_filename, 'r')
        #parse the json file
        parsedROM = json.loads(openfile.read())
        #Get the titles for the Combobox
        for a in parsedROM['VECTREX ROMS']['TITLES']:
            ComboValues.append(a)
        openfile.close()
        #Sort the titles and update the GUI
        ComboValues.sort()
        ComboWeb['values'] = ComboValues
        ComboVar.set(ComboValues[0])
        #Here we fill in the ROM and game info
        a = ""
        a = "Year: " + parsedROM['VECTREX ROMS']['TITLES'][ComboVar.get()]["YEAR"] + "\n"
        a = a + "Dev: "
        x = 0
        for b in parsedROM['VECTREX ROMS']['TITLES'][ComboVar.get()]["DEVELOPERS"]:
            if b != "":
                if x == 0:
                    a = a + b
                    x += 1
                else:
                    a = a + ", " + b
        FilePath_Var.set(a)
        f = PGM_Var.get()
        if "NOT FOUND" in f:
            root.update_idletasks()
            return None
        if "SEEKING" not in f:
            if f != "":
                Button_PGM['state'] = "enable"
        if f == "":
            root.update_idletasks()
            return None
    return None


def update_ROM_info(object):
    """
    We come here whenever the user makes a Combobox selection
    """
    global ComboValues
    global local_filename
    global headers
    global parsedROM
    #Here we fill in the ROM and game info
    a = ""
    a = "Year: " + parsedROM['VECTREX ROMS']['TITLES'][ComboVar.get()]["YEAR"] + "\n"
    a = a + "Dev: "
    x = 0
    for b in parsedROM['VECTREX ROMS']['TITLES'][ComboVar.get()]["DEVELOPERS"]:
        if b != "":
            if x == 0:
                a = a + b
                x += 1
            else:
                a = a + ", " + b
    FilePath_Var.set(a)
    root.update_idletasks()


def handle_radio_buttons():
    global ComboValues
    global parsedROM
    FilePath_Var.set("")
    del ComboValues[:]
    parsedROM.clear()
    ComboWeb['state'] = "readonly"
    ComboWeb['values'] = ComboValues
    ComboVar.set("")
    a = RadioVar.get()
    if a == 1:
        Button_Web['state'] = 'enable'
        ComboWeb['state'] = "readonly"
        Button_File['state'] = 'disable'
        Button_PGM['state'] = 'disable'
    if a == 2:
        Button_Web['state'] = 'disable'
        ComboWeb['state'] = 'disable'
        Button_File['state'] = 'enable'
        Button_PGM['state'] = 'disable'

if __name__ == '__main__':
    # define Queue variables
    fileName = Queue(maxsize=0)
    serPort = Queue(maxsize=0)
    fileSize = Queue(maxsize=0)
    busy = Queue(maxsize=0)
    myState = Queue(maxsize = 0)
    prime = Queue(maxsize= 0)

    # spin up the NVRAM program thread
    worker = Thread(target=program_nvram_thread, args=(fileName,serPort,fileSize))
    worker.setDaemon(TRUE)
    worker.start()
    # spin up the refresh timer
    refresh_timer()
    
    # Main window
    root.title("Vectrex NVRAM")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    mainframe.columnconfigure(0, weight=1)
    mainframe.rowconfigure(0, weight=1)

    # Show image of programmer
    Frame_Dummy['width'] = 300
    Frame_Dummy['height'] = 180
    # Frame_Dummy['relief'] = 'sunken'
    Frame_Dummy.grid(columnspan=3,column=0, row=0)
    label_img = ttk.Label(Frame_Dummy)
    label_img.grid(column=0,row=0)
    imgobj = PhotoImage(file='NVRAM.gif')
    label_img['image'] = imgobj

    # Seperator line
    s1['orient'] = 'horizontal'
    s1.grid(columnspan=3, row=1, sticky = "ew")
    #s1.grid(column=1, row=2)

    # Show 'COM port label
    Label_Com.grid(sticky = "e")
    Label_Com['text'] = "COM PORT:"
    Label_Com.grid(column=0, row=2,sticky="e")

    PGM_Var.set("")
    # Show Programmer COM port
    Pgm_Com_Label['width'] = 12
    Pgm_Com_Label['textvariable'] = PGM_Var
    Pgm_Com_Label['borderwidth'] = 5
    Pgm_Com_Label['relief']= "sunken"
    Pgm_Com_Label.grid(column=1, row=2, sticky="w")

    # COM port refresh button
    But_Ref_Txt.set("  REFRESH   ")
    Button_Refresh['textvariable'] = But_Ref_Txt
    Button_Refresh['command'] = find_programmer
    Button_Refresh.grid(column=2,row=2, sticky="w")

    # Programmer Status Label and Graphic
    Pgm_Label.grid(column=0, row=3, sticky = "e")
    Pgm_Label['text'] = "PROGRAMMER:"
    Status_Pgm.grid(column=1, row=3, sticky = "W")
    Status_Pgm['image'] = imgobj_rb

    # Cart Status Label and Graphic
    Cart_Label.grid(column=0, row=4, sticky = "E")
    Cart_Label['text'] = "CART:"
    Status_Crt.grid(column=1, row=4, sticky = "W")
    Status_Crt['image'] = imgobj_rb

    #From Web Radio Button
    RadioVar.set(0)
    WebRadio['text'] = "FROM WEB"
    WebRadio['value'] = 1
    WebRadio['variable'] = RadioVar
    WebRadio['command'] = handle_radio_buttons
    WebRadio.grid(column=0, row=5, sticky = "W")

    #From Web Radio Button
    RadioVar.set(0)
    LocalRadio['text'] = "FROM LOCAL"
    LocalRadio['value'] = 2
    LocalRadio['variable'] = RadioVar
    LocalRadio['command'] = handle_radio_buttons
    LocalRadio.grid(column=1, row=5, sticky = "E")

    #Get the ROM fle index from the web site
    #this retrieve a json file from the web site
    Button_Web['text'] = "REFRESH WEB ROMS"
    Button_Web['command'] = fetch_index_json
    Button_Web['state'] = 'disabled'
    Button_Web.grid(column=0,row=6)

    ComboVar.set("")
    # Combobox
    ComboWeb['width'] = 30
    ComboWeb['values'] = ComboValues
    ComboWeb['textvariable'] = ComboVar
    ComboWeb.bind('<<ComboboxSelected>>', update_ROM_info)
    ComboWeb['state'] = 'disabled'
    ComboWeb.grid(columnspan=2, column=1, row=6, sticky="w")

    # Open File button
    Button_File['text'] = "OPEN LOCAL FILE"
    Button_File['command'] = get_file_path
    Button_File['state'] = 'disabled'
    Button_File.grid(column=0,row=7)

    FilePath_Var.set("")
    # File Path Label
    File_Label['textvariable'] = FilePath_Var
    File_Label['width'] = 32
    File_Label['wraplength'] = "180"
    File_Label['relief'] = "sunken"
    File_Label.grid(columnspan=2, column=1, row=7, sticky="w")

    # Program NVRAM button
    Button_PGM['text'] = "PROGRAM NVRAM"
   # Button_PGM['command'] = program_nvram
    Button_PGM['command'] = send_serial
    Button_PGM['state'] = "disabled"
    Button_PGM.grid(column=0,row=8, sticky = "w")

    # Seperator line
    s2['orient'] = 'horizontal'
    s2.grid(columnspan=3, column = 0, row = 9, sticky = "ew")

    # Message Label
    Message_Var.set(" ")
    Message_Label['textvariable'] = Message_Var
    Message_Label['width'] = 30
    Message_Label['relief'] = "sunken"
    Message_Label.grid(columnspan = 2, column=0, row=10, sticky="w")

    # Progress Bar
    P_Bar['orient'] = "horizontal"
    P_Bar['length'] = 300
    P_Bar['mode'] = "determinate"
    P_Bar['variable'] = P_Bar_Var
    P_Bar.grid(columnspan = 3, column = 0, row = 11, sticky = "w")

    for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

    root.mainloop()
