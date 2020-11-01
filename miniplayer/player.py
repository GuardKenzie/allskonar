#!/bin/python
import curses
import os
from mpd import MPDClient
import ffmpeg
from pixcat import Image
import time

# Terminal ratio
TERMINAL_RATIO = 24/11

# Music directory
MUSICDIR = "~/Music"
MUSICDIR = os.path.expanduser(MUSICDIR)

# Curses
stdscr = curses.initscr()
curses.noecho()
curses.curs_set(0)

curses.start_color()
curses.use_default_colors()
curses.init_pair(1, curses.COLOR_GREEN, -1)
curses.init_pair(2, curses.COLOR_YELLOW, -1)

# MPD
client = MPDClient()
client.connect("localhost", 6600)

# Curses window

lines = stdscr.getmaxyx()

window_width = lines[1]
window_height = lines[0]

text_start = int(window_height - 5)
album_space = text_start - 1

center = ((lines[0] - window_height) // 2, (lines[1] - window_width) // 2)

IMAGERATIO = (11, 24)

if window_width * IMAGERATIO[0] > album_space * IMAGERATIO[1]:
    IMAGEWIDTHPX = album_space * IMAGERATIO[1]
else:
    IMAGEWIDTHPX = window_width * IMAGERATIO[0]

IMAGEWIDTH = int(IMAGEWIDTHPX // IMAGERATIO[0])
IMAGEHEIGHT = int(IMAGEWIDTHPX // IMAGERATIO[1])

# # Calculate image
# IMAGERATIO = (11, 16)

# if window_width < text_start * TERMINAL_RATIO:
#     IMAGEWIDTHPX = window_width * IMAGERATIO[0]
# else:
#     IMAGEWIDTHPX = text_start * IMAGERATIO[1]

# IMAGEWIDTH = int(IMAGEWIDTHPX/IMAGERATIO[0])
# IMAGEHEIGHT = int(IMAGEWIDTHPX/IMAGERATIO[1])

image_y_pos = (album_space - IMAGEHEIGHT) // 2

def main():
    global lines
    global center
    global text_start
    global window_height
    global window_width
    global image_y_pos
    global IMAGEWIDTHPX
    global IMAGEWIDTH
    global IMAGEHEIGHT
    global album_space

    # Init window
    win = curses.newwin(window_height, window_width, center[0], center[1])
    last_song = None

    # Main loop
    while True:
        # Update lines if window changes
        if stdscr.getmaxyx() != lines:
            stdscr.clear()
            lines = stdscr.getmaxyx()

            window_width = lines[1]
            window_height = lines[0]

            center = ((lines[0] - window_height) // 2, (lines[1] - window_width) // 2)

            text_start = int(window_height - 5)
            album_space = text_start - 1

            if window_width * IMAGERATIO[0] > album_space * IMAGERATIO[1]:
                IMAGEWIDTHPX = album_space * IMAGERATIO[1]
            else:
                IMAGEWIDTHPX = window_width * IMAGERATIO[0]

            IMAGEWIDTH = int(IMAGEWIDTHPX // IMAGERATIO[0])
            IMAGEHEIGHT = int(IMAGEWIDTHPX // IMAGERATIO[1])

            image_y_pos = (album_space - IMAGEHEIGHT) // 2

            win.resize(window_height, window_width)
            win.move(center[0], center[1])
            last_song = None

        # Get song info
        status = client.status()
        if status["state"] == "stop":
            win.clear()
            infomsg = "Put some beats on!"
            win.addstr(lines[0] // 2,(lines[1] - len(infomsg)) // 2, infomsg)
            win.refresh()
            time.sleep(1)
            continue

        song = client.currentsong()

        elapsed = float(status["elapsed"])
        duration = float(status["duration"])
        progress = elapsed/duration

        # Update song info if different
        if last_song != song:
            win.clear()
            album = song["album"]
            artist = song["artist"]
            title = song["title"]

            win.addstr(text_start, 0, f"{title}")
            win.addstr(text_start + 1, 0, f"{artist} - {album}")

            # Get album art
            song_file = song["file"]
            song_file_abs = os.path.join(MUSICDIR, song_file)
            process = (
                    ffmpeg
                    .input(song_file_abs)
                    .output("/tmp/cover-miniplayer.jpg")
            )
            process.run(quiet=True, overwrite_output=True)

        # Progress bar
        song_duration = (int(duration / 60), round(duration % 60))
        song_elapsed = (int(elapsed / 60), round(elapsed % 60))

        win.addstr(text_start + 2, 0, "-"*(int((window_width - 1) * progress)) + ">", curses.color_pair(1))

        # Duration string
        time_string = f"{song_elapsed[0]}:{song_elapsed[1]:02d}/{song_duration[0]}:{song_duration[1]:02d}"
        win.addstr(text_start + 3, 0, f"{time_string:>{window_width}}", curses.color_pair(2))

        win.refresh()

        # Draw album art
        Image("/tmp/cover-miniplayer.jpg").thumbnail(IMAGEWIDTHPX).show(x=(lines[1] - IMAGEWIDTH)//2,y=image_y_pos)

        # Record current song
        last_song = song

        time.sleep(1)


try:
    main()
except KeyboardInterrupt:
    pass
finally:
    curses.endwin()
    client.close()
    client.disconnect()


