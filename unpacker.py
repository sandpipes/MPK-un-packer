import os, sys, struct, argparse, pathlib, csv
from os.path import join

def readString(f):
    chars = []
    while True:
        c = f.read(1)
        if c == b'\0':
            return "".join(chars)
        chars.append(c.decode("ascii"))

def unpack(mpkpath, outpath, verbose):
    print("---MPK Unpacker---")
    print("")
    if outpath is None:
        print("No extract path specified, printing file information in MPK only.")
        print()

    mpkfile = pathlib.Path(mpkpath)

    toc = []

    with mpkfile.open("rb") as f:
        if f.read(4) != b"MPK\0":
            print("This is not a MPK file!")
            print("Aborting!")
            return

        version = f.read(4)
        count = struct.unpack("<Q", f.read(8))[0]

        print("Found %i file(s) in MPK file!" % count)

        for i in range(count):
            f.seek(0x40 + (i * 0x100), os.SEEK_SET)
            
            isCompressed = False if f.read(4) == b'' else True
            id = struct.unpack("<L", f.read(4))[0]
            offset = struct.unpack("<Q", f.read(8))[0]
            compressedSize = struct.unpack("<Q", f.read(8))[0]
            uncompressedSize = struct.unpack("<Q", f.read(8))[0]
            readFilepath = readString(f)

            if verbose:
                print("ID: {0}\tCSize: {1} B\tASize: {2} B\t{3}".format(id, compressedSize, uncompressedSize, readFilepath))

            if outpath:
                intFilePath = readFilepath.split('\\')
                if len(intFilePath) > 1:
                    filename = intFilePath.pop()
                else:
                    filename = intFilePath[0]
                    intFilePath = ['.']

                itemDirPath = pathlib.Path(join(outpath, mpkfile.name[:-4], *intFilePath))
                itemDirPath.mkdir(parents=True, exist_ok=True)

                f.seek(offset, os.SEEK_SET)

                binData = f.read(compressedSize)

                itemPath = pathlib.Path(join(outpath, mpkfile.name[:-4], *intFilePath, filename))

                with itemPath.open("wb") as itemF:
                    itemF.write(binData)

                toc.append((id, itemPath.absolute(), readFilepath))
        
        if outpath:
            with open(join(outpath, mpkfile.name[:-4] + "_toc.csv"), "w") as csvfile:
                fwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csvfile.write("#id,filepath on system,filepath in MPK\n")

                for n in toc:
                    fwriter.writerow(n)

            print("Extracted %i file(s) from MPK and wrote TOC." % count)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to unpack MPK files from the Steins;Gate visual novel.")
    parser.add_argument("file")
    parser.add_argument("--out", "-o", metavar="<path>", type=str, help="set output path for files")
    parser.add_argument("-v", "--verbose", help="enable output verbosity", action="store_true")

    args = parser.parse_args()

    mpkfile = args.file
    outpath = args.out

    verbose = False
    if args.verbose or outpath is None:
        verbose = True

    if not os.path.isfile(mpkfile):
        print("The MPK file does not exist.")
        sys.exit()

    if outpath and not os.path.isdir(outpath):
        print("The output path specified does not exist.")
        sys.exit()

    unpack(mpkfile, outpath, verbose)