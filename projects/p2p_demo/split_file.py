import sys, os
fpath = sys.argv[1]
chunk_size = int(sys.argv[2]) if len(sys.argv) > 2 else 51200
base = os.path.splitext(os.path.basename(fpath))[0]
with open(fpath,'rb') as f:
    i = 0
    while True:
        b = f.read(chunk_size)
        if not b:
            break
        with open(f"chunk{i+1}",'wb') as out:
            out.write(b)
        i += 1
print("created", i, "chunks named chunk1, chunk2, ...")
