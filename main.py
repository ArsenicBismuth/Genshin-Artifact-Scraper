import translations as tr
import artifacts as art
import rate

import numpy as np
from PIL import Image

from mss import mss
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
from tesserocr import PyTessBaseAPI
import pickle
import csv

import pyautogui
import ctypes
import sys
from time import sleep

from cv2 import cv2

sct = mss()     # Screenshot
coords = []     # x1,x2, y1,y2
PARTS = 5

# Configs
LANG = tr.en()  # Language setting, placeholder
DIR = "./data/" # Output directory

MENU = [7,5,2]  # Menu dimension, x,y,page
SCROLL = 10*MENU[1]-1  # Scroll multiplier for page switch

# General utilities 
def onselect(eclick, erelease):
    # Selecting region using mouse
    if eclick.ydata > erelease.ydata:
        eclick.ydata, erelease.ydata = erelease.ydata, eclick.ydata
    if eclick.xdata > erelease.xdata:
        eclick.xdata, erelease.xdata = erelease.xdata, eclick.xdata
        
    # Zoom out if too close (just click)
    # Top-Left is (0,0)
    if erelease.xdata-eclick.xdata < 10:
        eclick.xdata = ax.get_xlim()[0] - 10
        erelease.xdata = ax.get_xlim()[1] + 10
    if erelease.ydata-eclick.ydata < 10:
        eclick.ydata = ax.get_ylim()[1] - 10
        erelease.ydata = ax.get_ylim()[0] + 10
    
    ax.set_ylim(erelease.ydata, eclick.ydata)   # Bottom, Top
    ax.set_xlim(eclick.xdata, erelease.xdata)   # Left, Right
    fig.canvas.draw()    
    
def select(img, msg):
    # Select image region using GUI
    # Returns x1,x2,y1,y2
    global fig
    global ax
    
    # Create figure & set window title
    fig = plt.figure(msg)
    ax = fig.add_subplot(111)
    plt_image=plt.imshow(img)
        
    # Select from image
    rs = widgets.RectangleSelector(
        ax, onselect, drawtype='box',
        rectprops = dict(facecolor='red', edgecolor = 'black', alpha=0.5, fill=True))

    plt.show() # Close the window after this
    return rs.extents
    
# OCR procedures
def image():
    # Screenshot then preprocess
    img = np.array(sct.grab(sct.monitors[1]))
    # img = img[::2, ::2, :] # Downscale
    img = img[:, :, :3]   # Remove alpha
    img = img[:, :, ::-1] # Reverse BGR <-> RGB
    return img

def calib(coords):
    # Redefine all regions based on 1 region
    img = image()
    old = coords[len(coords)-1] # Last line
    
    msg = "Select artifact colored area"
    new = np.array(select(img, msg), dtype=int)
    
    # Remove old offset
    coords[:, [0,1]] -= old[0] # x0 & x1 minus x1
    coords[:, [2,3]] -= old[2] # y0 & y1 minus y1
    
    # Get width
    fx = (new[1]-new[0])/(old[1] - old[0])
    fy = (new[3]-new[2])/(old[3] - old[2])
    
    # Resize
    coords[:, [0,1]] = (coords[:, [0,1]] * fx) # x0,x1 * fx
    coords[:, [2,3]] = (coords[:, [2,3]] * fy) # y0,y1 * fy
    
    # Add new offset
    coords[:, [0,1]] += new[0] # x0 & x1 plus new x0
    coords[:, [2,3]] += new[2] # y0 & y1 plus new y0
    print(new, old)
    print(coords)
    
    return coords.astype(int)
    
def init():
    # Determine the coords for each stat text
    img = image()
    coords = []
    
    msg = ["Select artifact type", 
        "Select mainstat", 
        "Select mainstat value", 
        "Select level", 
        "Select all substats & set name",
        "Select artifact colored area"]
        
    # Start selection regions for each parts
    # Plus 2 extra for future calibration
    for x in range(PARTS+1):
        coords.append(select(img, msg[x]))
    
    # Get the rs parameters
    coords = np.array(coords, dtype=int)
    
    return coords
    
def ocr(coords, lang=tr.en()):  
    img = image()
    texts = ""
    
    # Post-process (with special cases on certain regions)
    for i in range(PARTS):
        # Crop to regions
        crop = img[coords[i][2]:coords[i][3], coords[i][0]:coords[i][1], :]
        # plt_image=plt.imshow(crop) # Preview post-processing
        # plt.show() # Close the window after this
        
        # Unsharp filter
        gaussian = cv2.GaussianBlur(crop, (0, 0), 2.0)
        crop = cv2.addWeighted(crop, 1.5, gaussian, -0.5, 0)
        
        # Upscale
        crop = cv2.resize(crop, (0, 0), fx=4, fy=4)
        
        # Pre-process per case
        if i==0:
            print("Reading artifact type.")
        if i==1:
            print("Reading mainstat.")
            crop = cv2.resize(crop, (0, 0), fx=2, fy=2)
            crop = cv2.bitwise_not(crop) # Invert            
            # plt_image=plt.imshow(crop) # Preview post-processing
            # plt.show() # Close the window after this
        elif i==2:
            print("Reading mainstat value.")
            crop = cv2.bitwise_not(crop)
        elif i==3:
            print("Reading level.")
            crop = cv2.bitwise_not(crop)
        elif i==4:
            print("Reading substats & set name.")
        
        # Padding, improve accuracy significantly
        crop = cv2.copyMakeBorder(crop, 32, 32, 32, 32,
            cv2.BORDER_REPLICATE)
        
        # plt_image=plt.imshow(crop) # Preview post-processing
        # plt.show() # Close the window after this
        
        # OCR per case
        if i==2:
            # Mainstat value
            text = to_text(crop, ".,1234567890%m")
            text = text.replace("m", "11")
        elif i==3:
            # Level
            text = to_text(crop, "+1234567890")
        else:
            # Execute normal OCR
            text = to_text(crop)
        
        # Append results
        texts += text
        
        # text = tesserocr.image_to_text()

        print("########## RAW-"+str(i)+":\n", text, "\n")
    
    return texts
    
def to_text(image, whitelist=""):
    img = Image.fromarray(np.uint8(image))
    
    with PyTessBaseAPI() as api:
        api.SetVariable('tessedit_char_whitelist', whitelist)
        api.SetImage(img)
        return api.GetUTF8Text()  # it will print only digits
    # API is automatically finalized when used in a with-statement
    
# Macro procedures
def mouse():
    img = image()
    
    msg = "Select the first 2x2 tiles"
    tiles = np.array(select(img, msg), dtype=int)
    
    # Distance to other tiles (x,y)
    delta = ((tiles[1]-tiles[0])/2, (tiles[3]-tiles[2])/2)
    # First artifact center
    start = (tiles[0]+delta[0]/2, tiles[2]+delta[1]/2)
    
    return start, delta

def admin():
    # Check admin right, if not rerun with admin right.
    # If the function succeeds, it returns a value greater than 32.
    try:
        status = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        status = False
        
    if status:
        return status
    else:
        input("Please run as administrator.\n" +
            "This is required because Genshin runs as admin.")
        # Re-run the program with admin rights
        # ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__.join(sys.argv), None, 1)

def read(coords):
    # Get data on current artifact
    # Raw OCR
    lang = LANG
    text = ocr(coords, lang)
        
    # Parsing
    print("########## PARSE:")
    type, level, set, stats = rate.parse(text, lang)
    
    # Get rating (3 tuples in (score, relative))
    score, main, sub = rate.score(level, stats, {}, lang)
    
    # Define as a piece object
    pc = art.piece(type, level, set, stats)
    pc.set_score(score, main, sub)
    
    return pc
    

def main(argv):

    print("Admin:", admin()) # Check for admin privileges
    # This is necessary as Genshin runs with admin privileges
    # No external program can work on a window without equal privileges

    # Ask to load prior settings
    if input("Load coordinates? ([y]/n): ") == 'n':
        # Start setting multiple crop regions
        coords = init()
        # Save data
        np.savetxt(DIR + 'coords.txt', coords, fmt='%d')
        
        # Mouse calibration
        start, delta = mouse()
        np.savetxt(DIR + 'mouse.txt', (start, delta), fmt='%d')
    else:
        # Load coords data
        coords = np.loadtxt(DIR + 'coords.txt', dtype=int)
        (start, delta) = np.loadtxt(DIR + 'mouse.txt', dtype=int)
        
        # Recalibrate by selecting 1 region only
        if input("Recalibrate OCR? (y/[n]): ") == 'y':
            coords = calib(coords)
            np.savetxt(DIR + 'coords.txt', coords, fmt='%d')
        
        if input("Recalibrate mouse? (y/[n]): ") == 'y':
            start, delta = mouse()
            np.savetxt(DIR + 'mouse.txt', (start, delta), fmt='%d')
    
    # Only run on current artifact
    for arg in argv:
        if arg in ("-o", "--once"):
            print("Running once.")
            pc = read(coords)
            pc.print()
            return
    
    # Go through the whole menu
    pcs = []            # Compiled pieces
    pos = list(start)   # Mouse position
    for pg in range(MENU[2]):
        print(f"Page {pg}...")
        # input("Enter to continue...")
        for y in range(MENU[1]):
            for x in range(MENU[0]):
                pyautogui.click(pos[0], pos[1])
                
                # Get data for an artifact
                pc = read(coords)
                pc.print()
                pcs.append(pc)
                
                # Next in line
                pos[0] += delta[0]
                
            # Next row
            pos[0] = start[0]
            pos[1] += delta[1]
        
        # Next page
        # Scroll (drag doesn't work)
        if pg == MENU[2]-1:
            continue
        for i in range(SCROLL):
            sleep(0.01)
            pyautogui.scroll(-1)
        
        # Set pos to start at 2nd row
        pos = list(start)

    # Store externally
    print("Saving data...")
    with open(DIR + 'arts.pkl', 'wb') as f:
        pickle.dump(pcs, f)
        
    print("Saving csv...")
    with open(DIR + 'arts.csv', 'w', newline="") as f:
        writer = csv.writer(f, delimiter=';', quotechar='"')
        for art in pcs:
            # art.print()
            writer.writerow(art.get_array())
        
    # Reload data
    print("Test loading data...")
    with open(DIR + 'arts.pkl', 'rb') as f:
        load = pickle.load(f)

    # Check
    load[0].print()
    
    
if __name__ == '__main__':
    # Pass argument except the first one (filename)
    main(sys.argv[1:])
        