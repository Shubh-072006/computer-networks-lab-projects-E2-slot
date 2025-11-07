import sys, os
outname = sys.argv[1]
i = 1
with open(outname, 'wb') as w:
    while True:
        fname = f"chunk{i}"
        if not os.path.exists(fname):
            break
        with open(fname,'rb') as r:
            w.write(r.read())
        i += 1
print("merged into", outname)
