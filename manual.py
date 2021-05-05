import translations as tr
import artifacts as art
import rate
import main as scrape

import numpy as np

import pickle
import csv

import sys

coords = []     # x1,x2, y1,y2
PARTS = 5

# Configs
LANG = tr.en()  # Language setting, placeholder
DIR = "./data/" # Output directory
    

def main(argv):
    # Doesn't need admin elevation, since we don't use macro

    # Ask to load prior settings
    if input("Load coordinates? ([y]/n): ") == 'n':
        # Start setting multiple crop regions
        coords = scrape.init()
        # Save data
        np.savetxt(DIR + 'coords.txt', coords, fmt='%d')
        
    else:
        # Load coords data
        coords = np.loadtxt(DIR + 'coords.txt', dtype=int)
        
        # Recalibrate by selecting 1 region only
        if input("Recalibrate OCR? (y/[n]): ") == 'y':
            coords = scrape.calib(coords)
            np.savetxt(DIR + 'coords.txt', coords, fmt='%d')
    
    # Only run on current artifact
    for arg in argv:
        if arg in ("-o", "--once"):
            print("Running once.")
            pc = scrape.read(coords)
            pc.print()
            return
    
    # Go through the whole menu
    pcs = []            # Compiled pieces
    while True: # Infinite loop
        
        # Break on "n" input
        n = input("Select an artifact then press Enter (send \"n\" to stop).\n")
        if n == "n":
            break
        else:
            # Get data for an artifact
            pc = scrape.read(coords)
            pc.print()
            pcs.append(pc)

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
        