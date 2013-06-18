#!/usr/bin/env python

# Your chess.com username (or, in other words, the user you want to download the 
# games for).
#
# Example:
#     USERNAME = "myusername"
USERNAME = "derekmaciel"

# Optional: Your chess.com password. You only need to supply this if you are a
# premium user and you wish to download games older than 6 weeks.
#
# Leave blank if you do not wish to take advantage of that
#
# Example with password:
#     PASSWORD = "mypassword"
# Example without password:
#     PASSWORD = ""
PASSWORD = ""

# The path you wish to save your PGNs to. If on Windows and using forward
# slashes, you must escape them. Do not add a trailing slash afterward
#
# Example on Windows:
#     USERNAME = "C:\\Users\\Me\\pgns"
# Example on Mac/Linux/Unix
#     USERNAME = "/home/me/pgns"
# Bad example with trailing slash
#    USERNAME = "/home/me/pgns/"
PGNDIR  = "~/pgns"

import urllib2
from bs4 import BeautifulSoup
import re
from os.path import exists, expanduser
from os import makedirs

def main():
    # If credentials supplied:
        # Sign in

    # Files Saved counter
    saved = 0
    
    # For each game type
    types = ['echess', 'live_bullet', 'live_blitz', 'live_standard']
    for gametype in types:
        
        url = "http://www.chess.com/home/game_archive?show={0}&member={1}".format(gametype, USERNAME)
        try:
            html = get_file(url)
        except URLError:
            print "I could not access the page at {0}".format(url)
            print "The server may be down. In that case, I'm sure it'll work again later."
        else:
            soup = BeautifulSoup(html)
        
            # If no games are found of this type, go to the next type
            if soup.find("table", id="c14") == None: 
                print "No games found of type {0}".format(gametype)
                continue
            
            else:
                print "Checking {0} games".format(gametype)
                row = 0
            
                # For every game listed:
                while True:
                    game = {}
            
                    # If the row 's first column does not exist, the row must not exist
                    # Go to the next game type
                    if get_table_cell(soup, row, 1) == None:
                        break
                    
                    # Technically, get_path_from_info() and get_game_info() could be
                    # merged into a simple get_path().
                    # An info variable is used however because if the script is expanded to 
                    # work on domains other than chess.com, there will need to be 
                    # get_game_info() functions for those domains. And I did not want
                    # to rewrite get_path_from_info() every time.
                    info = get_game_info(soup, row, gametype)
                    path = expanduser(PGNDIR + "/" + get_path_from_info(info, gametype))
                
                    # If the directory structure does not exist, create it
                    if not exists(path):
                        makedirs(path)
                    
                    # If the pgn does not exist, download it
                    date = "{0}_{1}_{2}".format(info['year'], info['month'], info['day'])
                    filename = "{0}_vs_{1}_{2}.pgn".format(info['white'], info['black'], date)
                    destination = path + "/" + filename
                
                    if not exists(destination):
                        print "Downloading {0}".format(filename)
                        if gametype == 'echess':
                            url = "http://www.chess.com/echess/download_pgn?id={0}".format(info['id'])
                        else:
                            url = "http://www.chess.com/echess/download_pgn?lid={0}".format(info['id'])
                        save_file(url, destination)
                        saved += 1
                
                    row += 1
                    
        print "Finished checking {0} games\n".format(gametype)
            
    print "Done."    
    print "Saved {0} files".format(saved)
                    
        
def get_file(url):
    """ Downloads and returns the data at the given url """
    response = urllib2.urlopen(url)
    return response.read()
    
def save_file(url, path):
    """ 
    Downloads the data at the given url and saves it to the given path.
    This function uses get_file() to download the file. If get_file()
    throws a URLError, the file to be saved will not be created.
    """
    try:
        data = get_file(url)
    except URLError:
        print "I could not download the file at {0}".format(url)
        print "The server may be down. In that case, I'm sure it'll work again later."
    else:
        try:
            output = open(path, "wb")
        except IOError:
            print "I could not write to the file {0}".format(path)
            print "Make sure I have permission to write to that directory and try again"
        else:
            output.write(data)
            output.close

def get_table_cell(soup, row, col):
    """
    Returns the HTML table cell tag at the given row and col
    from the Game History table.
    """
    # All cells in the table have an id of "c14_row{row number}_{col number}"
    expr = "c14_row{0}_{1}".format(row, col)
    tag = soup.find("td", id=re.compile(expr))
    return tag
    
def get_game_info(soup, row, gametype):
    """
    Scrapes the game information from the given row and returns
    it as a dictionary. More speciically, it searches for the
    white and black players, the game ID, the year, month, 
    and day the game was completed, as well as if the game is a
    960 game and if the game has been analyzed or not.
    """
    # Cells are in the format "c14_row{ROW}_{COL}"
    
    info = {}
    
    # Check the images in the 0th column.
    cell = get_table_cell(soup, row, 0)
    for tags in cell.find_all("span"):
        info["is960"] = "c960" in tags["class"] # One of the span's classes would be "c960"
        info["analyzed"] = "computer" in tags["class"] # Would only show if signed in
                
    # White player
    cell = get_table_cell(soup, row, 1)
    info['white'] = cell.find_all("a")[1].get_text() #Player's name is the second link in the cell
        
    # Black player
    cell = get_table_cell(soup, row, 2)
    info['black'] = cell.find_all("a")[1].get_text() #Player's name is the second link in the cell
        
    # Game ID
    cell = get_table_cell(soup, row, 7)
    link = cell.find("a")['href'] # the ID is part of the URL of the link in the cell
    # /echess/ for corresp., /livechess/ otherwise
    if gametype == 'echess':
        info['id'] = link.replace("/echess/game?id=", "")
    else:
        info['id'] = link.replace("/livechess/game?id=", "")
                
    # Date
    cell = get_table_cell(soup, row, 6)
    date_str = cell.get_text() # the date is in mm/dd/yy and must be converted to yyyy, mm, and dd
    info['year'] = "20" + date_str.split("/")[2]
    info['month'] = "%02d" % int(date_str.split("/")[0]) # Add leading zero if needed
    info['day'] = "%02d" % int(date_str.split("/")[1]) # Add leading zero if needed
    
    return info
    
def get_path_from_info(info, gametype):
    """
    Determines, from the given game information, where
    its PGN file would be saved and returns its
    expected location.
    
    The path returned would be
    `type/subtype/year/month`, where "type" is either
    "live" or "correspondence", and the subtype is either
    "chess960" or "standard" for correspondence games
    or "bullet", "blitz", or "standard" for live games.
    """

    path = ""

    if gametype == 'echess':
        if info["is960"] == True: # if this is a 960 game
            path = "/correspondence/chess960"
        else:
            path = "/correspondence/standard"
                        
    elif gametype == 'live_bullet':
        path = "/live/bullet"
                    
    elif gametype == 'live_blitz':
        path = "/live/blitz"
                    
    elif gametype == 'live_standard':
        path = "/live/standard"
        
    # Add the year and month to the end of the path
    path = "{0}/{1}/{2}".format(path, info['year'], info['month']) 
        
    return path
    

if __name__ == '__main__':
    main()

