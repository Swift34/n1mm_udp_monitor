# -*- coding: utf-8 -*-
"""
Created on Sat Feb 24 20:25:05 2024

@author: Ric Sanders
         KN4FTT
         ricsanders69@gmail.com
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
UDP_BUF_SIZE = 4096 # in bytes
SN_FONT_SIZE = 48
RADIO_FONT_SIZE = 40
LABEL_FONT_SIZE = 20


class UDP_Listener(Thread):
    """
        UDP_Listener - Thread that listens for UDP Datagrams and grabs
                        the snt and sntnr values.
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
                print(f"Data received from: {addr[0]}")
                 
                #print(datagram)
                 
                n1mm_xml = ET.fromstring(datagram)
                # Need to check if we have a <contactinfo> frame and ignore the rest
                #print(n1mm_xml.tag)
                info = ''
                match n1mm_xml.tag:
                    case 'contactinfo':
                        self.sntnr = n1mm_xml.find('sntnr').text    #This represents the last number sent
                        info = f'snrnr:{self.sntnr}'
                        next_number = int(self.sntnr) + 1
                        #next_number_text = str(next_number)
                        self.app.master.serial_numberValue.set(f'{next_number:04}')
                    case 'RadioInfo':
                        self.radio = n1mm_xml.find('RadioNr').text
                        self.freq = n1mm_xml.find('Freq').text
                        freq_hundred = self.freq[-2:]
                        freq_kilo = self.freq[:len(self.freq)-2]
                        freq_text = f'{freq_kilo}.{freq_hundred}'
                        if(self.radio=='1'):
                            self.app.master.radio1Value.set(freq_text)
                        elif(self.radio=='2'):
                            self.app.master.radio2Value.set(freq_text)
                        
                        info = f'RadioNr:{self.radio} Freq:{self.freq}'
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
        self.create_sn_widgets()
        self.resize_grid()
        self.udp_listener = None
        self.start_udp_listener()
        
    def create_radio_widgets(self):
        # Fonts to use
        # self.master.label_font = tkFont.Font(family="Helvetiva", size=LABEL_FONT_SZIE, weight='bold')
        # self.master.radio_font = tkFont.Font(family="Helvetiva", size=RADIO_FONT_SIZE, weight='bold')
        self.master.label_font = tkFont.Font(family="Arial", size=LABEL_FONT_SIZE, weight='bold')
        self.master.radio_font = tkFont.Font(family="Arial", size=RADIO_FONT_SIZE, weight='bold')

        self.master.radio1Label = tk.Label(self.master)
        self.master.radio1Label['text'] = 'Radio #1'
        self.master.radio1Label['font'] = self.master.label_font
        self.master.radio1Label.grid(row=0,column=0,padx=0,pady=0)
        self.master.radio2Label = tk.Label(self.master)
        self.master.radio2Label['text'] = 'Radio #2'
        self.master.radio2Label['font'] = self.master.label_font
        self.master.radio2Label.grid(row=0,column=1,padx=0,pady=0)
        self.master.radio1Value = tk.StringVar()
        self.master.radio1 = tk.Entry(self.master, width=9)
        self.master.radio1['textvariable'] = self.master.radio1Value
        self.master.radio1['font'] = self.master.radio_font
        self.master.radio1.grid(row=1,column=0, rowspan=2)
        self.master.radio2Value = tk.StringVar()
        self.master.radio2 = tk.Entry(self.master, width=9)
        self.master.radio2['textvariable'] = self.master.radio2Value
        self.master.radio2['font'] = self.master.radio_font
        self.master.radio2.grid(row=1,column=1, rowspan=2)



    def create_sn_widgets(self):
        # Fonts to use
        self.master.label_font = tkFont.Font(family="Helvetiva", size=LABEL_FONT_SIZE, weight='bold')
        self.master.serial_number_font = tkFont.Font(family="Helvetiva", size=SN_FONT_SIZE, weight='bold')

        self.master.serial_numberLabel = tk.Label(self.master)
        self.master.serial_numberLabel['text'] = 'Next Serial Number'
        self.master.serial_numberLabel['font'] = self.master.label_font
        self.master.serial_numberLabel.grid(row=3,column=0,columnspan=2)
        self.master.serial_numberValue = tk.StringVar()
        self.master.serial_number = tk.Entry(self.master, width=4)
        self.master.serial_number['textvariable'] = self.master.serial_numberValue
        self.master.serial_number['font'] = self.master.serial_number_font
        self.master.serial_number.grid(row=4,column=0,rowspan=2, columnspan=2)

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
    root.geometry('725x250')
    root.wm_title('UDP Listener')

    app = App(sock,master=root)
    app.mainloop()
    
if __name__ == '__main__':
    main()