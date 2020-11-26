#!/bin/python
import curses
import os
from mpd import MPDClient
import ffmpeg
import pixcat
import time


# Image ratio
# Change this to match the (width, height) of your font.
IMAGERATIO = (11, 24)

# Music directory
MUSICDIR = "~/Music"
MUSICDIR = os.path.expanduser(MUSICDIR)


def albumArtSize(album_space, window_width):
    """
    Calculates the album art size given the window width and the height
    of the album art space
    """
    if window_width * IMAGERATIO[0] > album_space * IMAGERATIO[1]:
        image_width_px = album_space * IMAGERATIO[1]
    else:
        image_width_px = window_width * IMAGERATIO[0]

    image_width  = int(image_width_px  // IMAGERATIO[0])
    image_height = int(image_width_px  // IMAGERATIO[1])

    return image_width_px, image_width, image_height


class Player:
    def __init__(self):
        # Curses initialisation
        self.stdscr = curses.initscr()

        # Curses config
        curses.noecho()
        curses.curs_set(0)

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)

        # MPD init
        self.client = MPDClient()
        self.client.connect("localhost", 6600)

        self.last_song = None

        # Curses window
        self.window_height, self.window_width = self.stdscr.getmaxyx()
        self.win = curses.newwin(self.window_height, self.window_width, 0, 0)

        self.text_start = int(self.window_height - 5)
        self.album_space = self.text_start - 2

        # Calculate the size of the image
        self.image_width_px, self.image_width, self.image_height = albumArtSize(self.album_space, self.window_width)
        self.image_y_pos = (self.album_space - self.image_height) // 2 + 1

        # Album art location
        self.album_art_loc = "/tmp/aartminip.jpg"


    def fitText(self):
        """
        A function that fits album name, artist name and song name
        to the screen with the given width.
        """
        state = 0
        song = self.title
        album = self.album
        artist = self.artist
        width = self.window_width

        if len(song) > width:
            song = song[:-4] + "..."

        if len(album) == 0:
            sep = 0
        else:
            sep = 3

        if len(artist) + len(album) + sep > width:
            state = 1
            if len(artist) > width:
                artist = artist[:-4] + "..."
            if len(album) > width:
                album = album[:-4] + "..."

        if len(album) == 0:
            state = 2

        return (state, album, artist, song)


    def updateWindowSize(self):
        """
        A function to check if the window size changed
        """
        new_height, new_width = self.stdscr.getmaxyx()

        if (new_height, new_width) != (self.window_height, self.window_width):
            self.stdscr.clear()

            # Curses window
            self.window_height, self.window_width = self.stdscr.getmaxyx()

            self.text_start = int(self.window_height - 5)
            self.album_space = self.text_start - 2

            # Calculate the size of the image
            self.image_width_px, self.image_width, self.image_height = albumArtSize(self.album_space, self.window_width)
            self.image_y_pos = (self.album_space - self.image_height) // 2 + 1

            # Resize the window
            self.win.resize(self.window_height, self.window_width)
            self.last_song = None


    def getAlbumArt(self, song_file):
        """
        A function that extracts the album art from song_file and
        saves it to self.album_art_loc
        """
        song_file_abs = os.path.join(MUSICDIR, song_file)

        process = (
                ffmpeg
                .input(song_file_abs)
                .output(self.album_art_loc)
        )
        process.run(quiet=True, overwrite_output=True)


    def checkSongUpdate(self):
        """
        Checks if there is a new song playing

        Returns:
            1 -- if song state is "stop"
            0 -- if there is no change
            2 -- if there is a new song
        """
        status = self.client.status()

        if status["state"] == "stop":
            return 1

        song = self.client.currentsong()
        self.elapsed = float(status["elapsed"])
        self.duration = float(status["duration"])
        self.progress = self.elapsed/self.duration

        if self.last_song != song:
            self.win.clear()

            try:
                self.album = song["album"]
            except KeyError:
                self.album = ""

            self.artist = song["artist"]
            self.title = song["title"]

            self.last_song = song

            self.getAlbumArt(song["file"])
            self.last_song = song

            return 0

        else:
            return 2


    def drawInfo(self):
        """
        A function to draw the info below the album art
        """
        state, album, artist, title = self.fitText()
        if state == 0:
            # Everything fits
            self.win.addstr(self.text_start,     0, f"{title}")
            self.win.addstr(self.text_start + 1, 0, f"{artist} - {album}")

        elif state == 1:
            # Too wide
            self.win.addstr(self.text_start - 1, 0, f"{title}")
            self.win.addstr(self.text_start,     0, f"{album}")
            self.win.addstr(self.text_start + 1, 0, f"{artist}")

        else:
            # No album
            self.win.addstr(self.text_start,     0, f"{title}")
            self.win.addstr(self.text_start + 1, 0, f"{artist}")


        # Progress bar
        song_duration = (int(self.duration / 60), round(self.duration % 60))
        song_elapsed  = (int(self.elapsed / 60),  round(self.elapsed % 60))

        self.win.addstr(
            self.text_start + 2, 0,
            "-"*(int((self.window_width - 1) * self.progress)) + ">",
            curses.color_pair(1)
        )

        # Duration string
        time_string = f"{song_elapsed[0]}:{song_elapsed[1]:02d}/{song_duration[0]}:{song_duration[1]:02d}"

        self.win.addstr(
            self.text_start + 3, 0,
            f"{time_string:>{self.window_width}}",
            curses.color_pair(2)
        )

        self.win.refresh()


    def drawAlbumArt(self):
        """
        A function to draw the album art
        """
        try:
            (
                pixcat.Image(self.album_art_loc)
                .thumbnail(self.image_width_px )
                .show(x=(self.window_width - self.image_width)//2, y=self.image_y_pos)
            )
        except pixcat.terminal.KittyAnswerTimeout:
            pass


    def draw(self):
        """
        The function that draws the window
        """
        # Check for window size update
        self.updateWindowSize()

        # Force window nings
        self.win.redrawln(0, 1)
        self.win.addstr(0, 0, " ")

        # Get mpd state
        state = self.checkSongUpdate()

        # Check if state is stop
        if state == 1:
            self.win.clear()
            infomsg = "Put some beats on!"

            self.win.addstr(self.window_height // 2, (self.window_width - len(infomsg)) // 2, infomsg)
            self.win.refresh()

            return

        # Draw the window
        self.drawInfo()
        self.drawAlbumArt()


    def loop(self):
        try:
            while True:
                self.draw()
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            curses.endwin()
            self.client.close()
            self.client.disconnect()


player = Player()
player.loop()

