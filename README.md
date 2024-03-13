# n1mm_udp_monitor
Provides a remote window to display some broadcast data from an N1MM+ Ham Radio Logger. This can be displayed on another machine, monitor, or even a phone/tablet if the fonts are adjusted.

![N1MM UDP Monitor Screenshot](https://raw.githubusercontent.com/Swift34/n1mm_udp_monitor/main/n1mm_udp_monitor.JPG "N1MM_UDP_Monitor Screenshot")

N1MM+ can send out UDP packets to provide information to remote systems like a Contest Dashboard for a Multi-Station. The details about the xml that are sent can be found here: https://n1mmwp.hamdocs.com/mmfiles/udp_external_udp_broadcasts-xml/

To run you need a properly installed python3 instance then you run with:

python n1mm_udp_monitor.py --config=n1mm_udp_monitor.ini

Of course you can edit the ini file to suite your needs and even have a different config for different purposes.

73<br>
Ric<br>
KN4FTT
