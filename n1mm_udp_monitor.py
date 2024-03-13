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
import configparser
import argparse
import os.path


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
        print(f"Listening on {config.udp_ip}:{config.udp_port}")
        
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
                    datagram, addr = self.sock.recvfrom(config.udp_buf_size)
                except self.sock.error as err:
                    print(f"Error from receiving socket {err}")
                    
                #print(f"received message from ({addr}): {datagram}")
                #print(f"Data received from: {addr[0]}")
                 
                #print(datagram)
                 
                n1mm_xml = ET.fromstring(datagram)
                # Need to check if we have a <contactinfo> frame and ignore the rest
                #print(n1mm_xml.tag)
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
                        #freq_hundred = self.freq[-2:]
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
                        #self.spottercall = n1mm_xml.find('spottercall').text
                        self.mode = n1mm_xml.find('mode').text
                        spotstring = f'{self.dxcall} at {self.frequency} {self.mode}'
                        #self.app.master.spot_var.set(spotstring)
                        self.app.master.spotBox.insert(0, spotstring)
                        #info = f'Spot:{self.dxcall} at {self.frequency}'
                        info = spotstring
                    
                    case _:
                        info = f'We just received an unexpected {n1mm_xml.tag} frame.'
                print(info)

class App(tk.Frame):
    """
        App - App class that instantiates all other classes and manages
                the GUI
    """
    def __init__(self, sock, master=None):
        super().__init__(master)
        self.master = master # The GUI tk.Frame
        self.sock = sock
        self.spot_items = ['Ric Sanders - KN4FTT - Author', 'John Huggins - KX4O - Author']
        # Fonts to use
        self.master.spot_font = tkFont.Font(family=config.spot_font
                                            , size=config.spot, weight='bold')
        self.master.label_font = tkFont.Font(family=config.label_font
                                             , size=config.label, weight='bold')
        self.master.radio_font = tkFont.Font(family=config.radio_font
                                             , size=config.radio, weight='bold')
        self.master.serial_num_font = tkFont.Font(family=config.serial_num_font
                                                  , size=config.serial_num, weight='bold')
        self.master.qso_font = tkFont.Font(family=config.qso_font
                                           , size=config.qso, weight='bold')
        
        self.create_radio_widgets()
        self.create_qso_widgets()
        self.create_spot_widgets()
        #self.resize_grid()
        self.udp_listener = None
        self.start_udp_listener()

    def create_spot_widgets(self):
        # Labels
        self.master.spotLabel = tk.Label(self.master)
        self.master.spotLabel['text'] = 'Spots'
        self.master.spotLabel['bg'] = config.background
        self.master.spotLabel['fg'] = config.text_heading
        self.master.spotLabel['font'] = self.master.label_font
        self.master.spotLabel.grid(row=7, column=0, padx=0, pady=0, sticky=tk.W)

        # Changed the Spot's widget into a ListBox that will scroll away as more spots come in.
        self.master.spot_var = tk.StringVar()
        self.master.spot_var.set(self.spot_items)
        self.master.spotBox = tk.Listbox(self.master, listvariable=self.master.spot_var, height=5, width=30)
        self.master.spotBox['bg'] = config.background
        self.master.spotBox['fg'] = config.text_heading
        self.master.spotBox['font'] = self.master.spot_font
        self.master.spotBox.grid(row=7, column=0, columnspan=2, padx=0, pady=0)

    def create_radio_widgets(self):
        # Labels
        self.master.radio1Label = tk.Label(self.master)
        self.master.radio1Label['text'] = 'Radio #1'
        self.master.radio1Label['bg'] = config.background
        self.master.radio1Label['fg'] = config.text_heading
        self.master.radio1Label['font'] = self.master.label_font
        self.master.radio1Label.grid(row=0,column=0,padx=0,pady=0)

        self.master.radio2Label = tk.Label(self.master)
        self.master.radio2Label['text'] = 'Radio #2'
        self.master.radio2Label['bg'] = config.background
        self.master.radio2Label['fg'] = config.text_heading
        self.master.radio2Label['font'] = self.master.label_font
        self.master.radio2Label.grid(row=0,column=1,padx=0,pady=0)

        # Values
        self.master.radio1Value = tk.StringVar()
        self.master.radio1 = tk.Entry(self.master, width=11)
        self.master.radio1['text'] = self.master.radio1Value
        self.master.radio1['font'] = self.master.radio_font
        self.master.radio1['bg'] = config.background
        self.master.radio1['fg'] = config.text_radio
        self.master.radio1.grid(row=1,column=0, rowspan=2)

        self.master.radio2Value = tk.StringVar()
        self.master.radio2 = tk.Entry(self.master, width=11)
        self.master.radio2['text'] = self.master.radio2Value
        self.master.radio2['font'] = self.master.radio_font
        self.master.radio2['bg'] = config.background
        self.master.radio2['fg'] = config.text_radio
        self.master.radio2.grid(row=1,column=1, rowspan=2)

    def create_qso_widgets(self):
        self.master.serial_qsoLabel = tk.Label(self.master)
        self.master.serial_qsoLabel['text'] = 'Previous QSO'
        self.master.serial_qsoLabel['bg'] = config.background
        self.master.serial_qsoLabel['fg'] = config.text_heading
        self.master.serial_qsoLabel['font'] = self.master.label_font
        self.master.serial_qsoLabel.grid(row=3, column=0, columnspan=1)

        self.master.callValue = tk.StringVar()
        self.master.call = tk.Entry(self.master, width=10)
        self.master.call['textvariable'] = self.master.callValue
        self.master.call['font'] = self.master.qso_font
        self.master.call['bg'] = config.background
        self.master.call['fg'] = config.text_serial_num
        self.master.call.grid(row=4,column=0,rowspan=1,columnspan=1)

        self.master.rcvnrqthValue = tk.StringVar()
        self.master.rcvnrqth = tk.Entry(self.master, width=10)
        self.master.rcvnrqth['textvariable'] = self.master.rcvnrqthValue
        self.master.rcvnrqth['font'] = self.master.qso_font
        self.master.rcvnrqth['bg'] = config.background
        self.master.rcvnrqth['fg'] = config.text_serial_num
        self.master.rcvnrqth.grid(row=5, column=0, rowspan=1, columnspan=1)

        self.master.modeValue = tk.StringVar()
        self.master.mode = tk.Entry(self.master, width=10)
        self.master.mode['textvariable'] = self.master.modeValue
        self.master.mode['font'] = self.master.qso_font
        self.master.mode['bg'] = config.background
        self.master.mode['fg'] = config.text_serial_num
        self.master.mode.grid(row=6, column=0, rowspan=1, columnspan=1)

        self.master.serial_numberLabel = tk.Label(self.master)
        self.master.serial_numberLabel['text'] = 'Next Serial Number'
        self.master.serial_numberLabel['bg'] = config.background
        self.master.serial_numberLabel['fg'] = config.text_heading
        self.master.serial_numberLabel['font'] = self.master.label_font
        self.master.serial_numberLabel.grid(row=3,column=1,columnspan=1)

        self.master.serial_numberValue = tk.StringVar()
        self.master.serial_number = tk.Entry(self.master, width=4)
        self.master.serial_number['textvariable'] = self.master.serial_numberValue
        self.master.serial_number['font'] = self.master.serial_num_font
        self.master.serial_number['bg'] = config.background
        self.master.serial_number['fg'] = config.text_serial_num
        self.master.serial_number.grid(row=4,column=1,rowspan=3, columnspan=1)

        
        
    def mainloop(self, *args):
        super().mainloop(*args)
        # If the mainloop ends we need to close up our other thread
        if self.udp_listener:
            self.udp_listener.stop()
       
        
    def start_udp_listener(self):
        self.udp_listener = UDP_Listener(self.sock, self)
        self.udp_listener.start()

class Config():
    def __init__(self, filename): # Default settings
        self.filename = filename
        # app
        self.title = 'N1MM UDP Monitor'
        self.callsign = 'KN4FTT'
        # Network
        self.udp_ip = '127.0.0.1'
        self.udp_port = 12060
        self.udp_buf_size = 8192
        
    def read_config(self):
        config_parser = configparser.ConfigParser()
        config_parser.read(self.filename)
        
        # app
        if 'title' in config_parser['app'].keys():
            self.title = config_parser['app']['title']
        if 'callsign' in config_parser['app'].keys():
            self.callsign = config_parser['app']['callsign']
        # net
        if 'udp_ip' in config_parser['net'].keys():
            self.udp_ip = config_parser['net']['udp_ip']
        if 'udp_port' in config_parser['net'].keys():
            self.udp_port = int(config_parser['net']['udp_port'])
        if 'udp_buf_size' in config_parser['net'].keys():
            self.udp_buf_size = int(config_parser['net']['udp_buf_size'])
        # size
        if 'serial_num' in config_parser['size'].keys():
            self.serial_num = config_parser['size']['serial_num']
        if 'radio' in config_parser['size'].keys():
            self.radio = config_parser['size']['radio']
        if 'label' in config_parser['size'].keys():
            self.label = config_parser['size']['label']
        if 'qso' in config_parser['size'].keys():
            self.qso = config_parser['size']['qso']
        if 'spot' in config_parser['size'].keys():
            self.spot = config_parser['size']['spot']
        # font
        if 'spot_font' in config_parser['font'].keys():
            self.spot_font = config_parser['font']['spot_font']
        if 'label_font' in config_parser['font'].keys():
            self.label_font = config_parser['font']['label_font']
        if 'serial_num_font' in config_parser['font'].keys():
            self.serial_num_font = config_parser['font']['serial_num_font']
        if 'radio_font' in config_parser['font'].keys():
            self.radio_font = config_parser['font']['radio_font']
        if 'qso_font' in config_parser['font'].keys():
            self.qso_font = config_parser['font']['qso_font']
        # color
        if 'background' in config_parser['color'].keys():
            self.background = config_parser['color']['background']
        if 'text_heading' in config_parser['color'].keys():
            self.text_heading = config_parser['color']['text_heading']
        if 'text_serial_num' in config_parser['color'].keys():
            self.text_serial_num = config_parser['color']['text_serial_num']
        if 'text_radio' in config_parser['color'].keys():
            self.text_radio = config_parser['color']['text_radio']
        # screen
        if 'width' in config_parser['screen'].keys():
            self.width = config_parser['screen']['width']
        if 'height' in config_parser['screen'].keys():
            self.height = config_parser['screen']['height']
        if 'full' in config_parser['screen'].keys():
            self.full = config_parser['screen']['full'] == 'True'
            
def get_display_size():
    root = tk.Tk()
    root.update_idletasks()
    root.attributes('-fullscreen', True)
    root.state('iconic')
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.destroy()
    return width, height

def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error(f"File {arg} does not exist!")
    else:
        return arg
    
def main():
    parser = argparse.ArgumentParser(prog='n1mm_udp_monitor'
                                     ,description='A remote monitoring app for use with N1MM+ Ham Radio logger.'
                                     ,formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--config'
                        ,dest="filename"
                        ,required=True
                        ,type=lambda x: is_valid_file(parser, x)
                        ,default='n1mm_udp_monitor.ini'
                        ,help='configuration_file.ini'
                        )
    args = parser.parse_args()
    #print(args)
    global config
    config = Config(args.filename)
    config.read_config()
    
    sock = socket.socket(socket.AF_INET, # Internet
                          socket.SOCK_DGRAM) # UDP
    sock.bind((config.udp_ip, config.udp_port))
    
    root = tk.Tk()
    if config.full:
        width, height = get_display_size()
    else:
        width  = config.width
        height = config.height
    #root.geometry('1024x600')
    root.geometry(f'{width}x{height}')
    
    root.configure(background=config.background)
    root.wm_title(f'{config.title} - {config.callsign}')

    app = App(sock,master=root)
    app.mainloop()
    
if __name__ == '__main__':
    main()
    
