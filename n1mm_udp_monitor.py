# -*- coding: utf-8 -*-
"""
n1mm_udp_monitor.py - Display various attributes from the broadcast of an N1MM+ Ham Radio Logger.

@author: Ric Sanders
         KN4FTT
         ricsanders69@gmail.com

@author: John Huggins (Amendments)
         KX4O
         john@johnhuggins.com
"""

from threading import Thread
import socket
import select
import xml.etree.ElementTree as ET
import tkinter as tk
import tkinter.font as tkFont
import tkinter.ttk as ttk


UDP_IP = "127.0.0.1"
UDP_PORT = 12060 # default for N1MM
UDP_BUF_SIZE = 8192 # in bytes
SN_FONT_SIZE = 140
SN_FONT_SIZE = 140
RADIO_FONT_SIZE = 50
LABEL_FONT_SIZE = 30
QSO_FONT_SIZE = 40
SPOT_FONT_SIZE = 20
BACKGROUND_COLOR = "purple"
TEXT_COLOR_HEADING = "yellow"
TEXT_COLOR_SERIAL = "orange"
TEXT_COLOR_RADIO = "orange"


class UDP_Listener(Thread):
    """
        UDP_Listener - Thread that listens for UDP Datagrams and grabs
                        values.
    """
    def __init__(self, sock, app):
        super().__init__()
        self.sock = sock
        self.app = app
        self.keeping_running = True
        print(f"Listening on {UDP_IP}:{UDP_PORT}")
        # Keep track of the values that we receive via udp
        self.snt = 0
        self.sntnr = 0
        self.radio = 0
        self.freq = 0
        
    def stop(self):
        self.keeping_running = False
        
    def run(self):
        #print('Kick off UDP Listener')
        #print(type(self.app))
        #print(type(self.app.radioValue))
        while self.keeping_running:
            rfds, _wfds, _xfds = select.select([self.sock], [], [], 0.5)
            if self.sock in rfds:
                try:
                    datagram, addr = self.sock.recvfrom(UDP_BUF_SIZE)
                except self.sock.error as err:
                    print(f"Error from receiving socket {err}")
                    
                #print(f"received message from ({addr}): {datagram}")
                #print(f"Data received from: {addr[0]}")
                 
                #print(datagram)
                 
                n1mm_xml = ET.fromstring(datagram)
                # Need to check if we have a <contactinfo> frame and ignore the rest
                print(n1mm_xml.tag)
                info = ''
                match n1mm_xml.tag:
                    case 'contactinfo':
                        self.sntnr = n1mm_xml.find('sntnr').text    #This represents the last number sent
                        self.call = n1mm_xml.find('call').text
                        self.band = n1mm_xml.find('band').text
                        self.mode = n1mm_xml.find('mode').text
                        self.rcvnr = n1mm_xml.find('rcvnr').text
                        self.qth = n1mm_xml.find('exchange1').text
                        #info = f'call:{self.call}'
                        #print(f"Mode: {self.mode}")
                        next_number = int(self.sntnr) + 1
                        self.app.master.serial_numberValue.set(f'{next_number:04}')
                        self.app.master.callValue.set(f'{self.call}')
                        temp = f'{self.rcvnr} {self.qth}'
                        #print (temp)
                        self.app.master.rcvnrqthValue.set(temp)
                        #self.app.master.bandValue.set(f'{self.band}')
                        temp2 = f'{self.band} {self.mode}'
                        self.app.master.modeValue.set(temp2)

                        info = "QSO datagram received."
                    case 'RadioInfo':
                        self.radio = n1mm_xml.find('RadioNr').text
                        self.freq = n1mm_xml.find('Freq').text
                        self.mode = n1mm_xml.find('Mode').text
                        freq_hundred = self.freq[-2:]
                        freq_kilo = self.freq[:len(self.freq)-2]
                        freq_mode = self.mode
                        # Combine freq and mode into one variable
                        freq_text = " " f'{freq_kilo} {freq_mode}'
                        if (len(freq_text)==8):
                            freq_text = "   " f'{freq_text}'
                        # Store single variable to radio 1 or 2
                        if(self.radio=='1'):
                            self.app.master.radio1Value.set(freq_text)
                        elif(self.radio=='2'):
                            self.app.master.radio2Value.set(freq_text)
                        
                        info = f'RadioNr:{self.radio} Freq:{self.freq}'
                    case 'spot':
                        self.dxcall = n1mm_xml.find('dxcall').text
                        self.frequency = n1mm_xml.find('frequency').text
                        self.spottercall = n1mm_xml.find('spottercall').text
                        self.mode = n1mm_xml.find('mode').text
                        spotstring = f'Spot:{self.dxcall} at {self.frequency}'
                        self.app.master.spotValue.set(spotstring)
                        #info = f'Spot:{self.dxcall} at {self.frequency}'
                        #info = spotstring
                    case _:
                        info = f'We just received an unexpected {n1mm_xml.tag} frame.'
                print(info)



class App(ttk.Frame):
    """
        App - App class that instantiates all other classes and manages
                the GUI
    """
    def __init__(self, sock, master=None):
        super().__init__(master)
        self.master = master # The GUI tk.Frame
        self.sock = sock
        #self.pack()
        self.create_radio_widgets()
        self.create_qso_widgets()
        self.create_spot_widgets()
        self.resize_grid()
        self.udp_listener = None
        self.start_udp_listener()

    def create_spot_widgets(self):
        # Font to use
        self.master.spot_font = tkFont.Font(family="Courier New", size=SPOT_FONT_SIZE, weight='bold')
        self.master.label_font = tkFont.Font(family="Courier New", size=LABEL_FONT_SIZE, weight='bold')

        # Labels
        self.master.spotLabel = tk.Label(self.master)
        self.master.spotLabel['text'] = 'Spots'
        self.master.spotLabel['bg'] = BACKGROUND_COLOR
        self.master.spotLabel['fg'] = TEXT_COLOR_HEADING
        self.master.spotLabel['font'] = self.master.label_font
        self.master.spotLabel.grid(row=7, column=0, padx=0, pady=0)
        # Values
        self.master.spotValue = tk.StringVar()
        self.master.spot = tk.Entry(self.master, width=50)
        self.master.spot['font'] = self.master.spot_font
        self.master.spot['bg'] = BACKGROUND_COLOR
        self.master.spot['fg'] = TEXT_COLOR_RADIO
        self.master.spot.grid(row=8, column=0, columnspan=2)

    def create_radio_widgets(self):
        # Fonts to use
        self.master.label_font = tkFont.Font(family="Courier New", size=LABEL_FONT_SIZE, weight='bold')
        self.master.radio_font = tkFont.Font(family="Courier New", size=RADIO_FONT_SIZE, weight='bold')

        # Labels
        self.master.radio1Label = tk.Label(self.master)
        self.master.radio1Label['text'] = 'Radio #1'
        self.master.radio1Label['bg'] = BACKGROUND_COLOR
        self.master.radio1Label['fg'] = TEXT_COLOR_HEADING
        self.master.radio1Label['font'] = self.master.label_font
        self.master.radio1Label.grid(row=0,column=0,padx=0,pady=0)

        self.master.radio2Label = tk.Label(self.master)
        self.master.radio2Label['text'] = 'Radio #2'
        self.master.radio2Label['bg'] = BACKGROUND_COLOR
        self.master.radio2Label['fg'] = TEXT_COLOR_HEADING
        self.master.radio2Label['font'] = self.master.label_font
        self.master.radio2Label.grid(row=0,column=1,padx=0,pady=0)

        # Values
        self.master.radio1Value = tk.StringVar()
        self.master.radio1 = tk.Entry(self.master, width=11)
        self.master.radio1['text'] = self.master.radio1Value
        self.master.radio1['font'] = self.master.radio_font
        self.master.radio1['bg'] = BACKGROUND_COLOR
        self.master.radio1['fg'] = TEXT_COLOR_RADIO
        self.master.radio1.grid(row=1,column=0, rowspan=2)

        self.master.radio2Value = tk.StringVar()
        self.master.radio2 = tk.Entry(self.master, width=11)
        self.master.radio2['text'] = self.master.radio2Value
        self.master.radio2['font'] = self.master.radio_font
        self.master.radio2['bg'] = BACKGROUND_COLOR
        self.master.radio2['fg'] = TEXT_COLOR_RADIO
        self.master.radio2.grid(row=1,column=1, rowspan=2)



    def create_qso_widgets(self):
        # Fonts to use
        self.master.label_font = tkFont.Font(family="Courier New", size=LABEL_FONT_SIZE, weight='bold')
        self.master.serial_number_font = tkFont.Font(family="Courier New", size=SN_FONT_SIZE, weight='bold')
        self.master.qso_font = tkFont.Font(family="Courier New", size=QSO_FONT_SIZE, weight='bold')

        self.master.serial_qsoLabel = tk.Label(self.master)
        self.master.serial_qsoLabel['text'] = 'Previous QSO'
        self.master.serial_qsoLabel['bg'] = BACKGROUND_COLOR
        self.master.serial_qsoLabel['fg'] = TEXT_COLOR_HEADING
        self.master.serial_qsoLabel['font'] = self.master.label_font
        self.master.serial_qsoLabel.grid(row=3, column=0, columnspan=1)

        self.master.callValue = tk.StringVar()
        self.master.call = tk.Entry(self.master, width=10)
        self.master.call['textvariable'] = self.master.callValue
        self.master.call['font'] = self.master.qso_font
        self.master.call['bg'] = BACKGROUND_COLOR
        self.master.call['fg'] = TEXT_COLOR_SERIAL
        self.master.call.grid(row=4,column=0,rowspan=1,columnspan=1)

        self.master.rcvnrqthValue = tk.StringVar()
        self.master.rcvnrqth = tk.Entry(self.master, width=10)
        self.master.rcvnrqth['textvariable'] = self.master.rcvnrqthValue
        self.master.rcvnrqth['font'] = self.master.qso_font
        self.master.rcvnrqth['bg'] = BACKGROUND_COLOR
        self.master.rcvnrqth['fg'] = TEXT_COLOR_SERIAL
        self.master.rcvnrqth.grid(row=5, column=0, rowspan=1, columnspan=1)

        #self.master.rcvnrValue = tk.StringVar()
        #self.master.rcvnr = tk.Entry(self.master, width=10)
        #self.master.rcvnr['textvariable'] = self.master.rcvnrValue
        #self.master.rcvnr['font'] = self.master.qso_font
        #self.master.rcvnr['bg'] = BACKGROUND_COLOR
        #self.master.rcvnr['fg'] = TEXT_COLOR_SERIAL
        #self.master.rcvnr.grid(row=5, column=0, rowspan=1, columnspan=1)

        #self.master.qthValue = tk.StringVar()
        #self.master.qth = tk.Entry(self.master, width=3)
        #self.master.qth['textvariable'] = self.master.qthValue
        #self.master.qth['font'] = self.master.qso_font
        #self.master.qth['bg'] = BACKGROUND_COLOR
        #self.master.qth['fg'] = TEXT_COLOR_SERIAL
        #self.master.qth.grid(row=6, column=0, rowspan=1, columnspan=1)

        #self.master.bandValue = tk.StringVar()
        #self.master.band = tk.Entry(self.master, width=10)
        #self.master.band['textvariable'] = self.master.bandValue
        #self.master.band['font'] = self.master.qso_font
        #self.master.band['bg'] = BACKGROUND_COLOR
        #self.master.band['fg'] = TEXT_COLOR_SERIAL
        #self.master.band.grid(row=6, column=0, rowspan=1, columnspan=1)

        self.master.modeValue = tk.StringVar()
        self.master.mode = tk.Entry(self.master, width=10)
        self.master.mode['textvariable'] = self.master.modeValue
        self.master.mode['font'] = self.master.qso_font
        self.master.mode['bg'] = BACKGROUND_COLOR
        self.master.mode['fg'] = TEXT_COLOR_SERIAL
        self.master.mode.grid(row=6, column=0, rowspan=1, columnspan=1)

        self.master.serial_numberLabel = tk.Label(self.master)
        self.master.serial_numberLabel['text'] = 'Next Serial Number'
        self.master.serial_numberLabel['bg'] = BACKGROUND_COLOR
        self.master.serial_numberLabel['fg'] = TEXT_COLOR_HEADING
        self.master.serial_numberLabel['font'] = self.master.label_font
        self.master.serial_numberLabel.grid(row=3,column=1,columnspan=1)

        self.master.serial_numberValue = tk.StringVar()
        self.master.serial_number = tk.Entry(self.master, width=4)
        self.master.serial_number['textvariable'] = self.master.serial_numberValue
        self.master.serial_number['font'] = self.master.serial_number_font
        self.master.serial_number['bg'] = BACKGROUND_COLOR
        self.master.serial_number['fg'] = TEXT_COLOR_SERIAL
        self.master.serial_number.grid(row=4,column=1,rowspan=3, columnspan=1)

    def resize_grid(self):
        # # self.master is root or master
        # col_count, row_count = self.master.grid_size()

        # for col in range(col_count):
        #     self.master.grid_columnconfigure(col, minsize = 10)

        # for row in range(row_count):
        #     self.master.grid_rowconfigure(row, minsize = 10)
        pass
        
        
    def mainloop(self, *args):
        super().mainloop(*args)
        # If the mainloop ends we need to close up our other thread
        if self.udp_listener:
            self.udp_listener.stop()
       
        
    def start_udp_listener(self):
        self.udp_listener = UDP_Listener(self.sock, self)
        self.udp_listener.start()
        
 
def main():
    sock = socket.socket(socket.AF_INET, # Internet
                          socket.SOCK_DGRAM) # UDP
    sock.bind((UDP_IP, UDP_PORT))
    root = tk.Tk()
    root.geometry('1024x600')
    root.configure(background=BACKGROUND_COLOR)
    root.wm_title('N1MM UDP Mobile Multi-Op Monitor')

    app = App(sock,master=root)
    app.mainloop()
    
if __name__ == '__main__':
    main()
