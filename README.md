# ocatfs

filesystem in userspace to browse overclockers.at

Currently supports reading subforums and threads, but only the first page.

Tested with python3 on ArchLinux

Depends on:
* fusepy >= 2.0.4
* requests >= 2.13.0
* beautifulsoup4 >= 4.5.3

Usage:

`./run.py [-h] [--background] [--debug] mountpoint` 
