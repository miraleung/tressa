import os
import csv
import sys


SUFFIX = "_linearity-monotonicity.float"


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: " + sys.argv[0] + " <outfile>")
        sys.exit(-1)

    outfile = sys.argv[1]
    with open(outfile, 'w', newline='') as out:
        out.write('"Repository Name",Linearity,Monotonicity\n')

        linfiles = (d for d in os.listdir("results") if d.endswith(SUFFIX))

        for linfile in linfiles:
            with open('results/' + linfile, 'r') as f:
                line = f.readline()
                linearity = float(line)
                monotonicity = f.readline()

                projname = linfile[:-len(SUFFIX)]
                out.write("{pn},{lin},{mon}\n"
                        .format(pn=projname, lin=linearity, mon=monotonicity))






