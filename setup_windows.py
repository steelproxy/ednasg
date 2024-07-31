import curses
import message_win
import bottom_win

def setup_windows(stdscr):
    """Initialize the curses windows."""
    term_height, term_width = stdscr.getmaxyx()
    message_win.win = curses.newwin(term_height - 1, term_width, 0, 0)
    bottom_win.win = curses.newwin(1, term_width, term_height - 1, 0)
    bottom_win.win.keypad(1)
    message_win.win.keypad(1)