from PIL import Image
import progressbar
import math
import os
import multiprocessing as mp
import shutil
import datetime

# Constans
THRESHOLD = 10**20
ITERATIONS = 255

SIZEX_FINAL = 1280
SIZEY_FINAL = 720

SIZEX = round(SIZEX_FINAL * 1.2)
SIZEY = round(SIZEY_FINAL * 1.2)

M232 = complex(-0.77568377, 0.13646737)

CENTERX = 0
CENTERY = 0

CONSTANT = complex(0.7885, 0)

ZOOM = 300
ZOOMFACTOR = 0

OFFSETX = CENTERX * ZOOM
OFFSETY = CENTERY * ZOOM

FNAME = datetime.datetime.utcnow().strftime("%Y.%d.%m-%H.%M.%S")

FRAMECOUNT = 600

# COLOURMAP
HUEMAP = []
VALMAP = []

for a in range(0, ITERATIONS):
    HUEMAP.append((160 + round(360 * (((ITERATIONS - a) / ITERATIONS)))) % 361)
    VALMAP.append(round(255 * math.sqrt(a / ITERATIONS)))

MAP = HUEMAP


def animation(frame):
    a = frame * (2 * math.pi) / FRAMECOUNT

    return CONSTANT * math.e ** (a * complex(0, 1))


# Check for divergence
def diverge(c, z=complex(0, 0), count=0):
    while count < ITERATIONS:
        # If length over threshhold diverges
        if abs(z) > THRESHOLD:
            return (True, count)
        z = (z**2 + c)
        count += 1
    # If max iters is reached, does not diverge
    return (False, count)


def make_image(name, CONSTANTT):
    # Image init
    img = Image.new("HSV", (SIZEX, SIZEY), (0, 0, 0))
    pixels = img.load()

    # Iterate over pixels, real values on X and imaginary on Y
    for R in range(img.size[0]):
        xval = (R - SIZEX / 2) / ZOOM
        for I in range(img.size[1]):
            # Update progress bar

            # Calculating actual coordinates
            zoom_offset_x = OFFSETX / ZOOM
            zoom_offset_y = OFFSETY / ZOOM

            yval = (I - SIZEY / 2) / ZOOM

            z = complex(xval + zoom_offset_x, yval + zoom_offset_y)

            # Get divergence
            out = diverge(CONSTANTT, z=z)
            if out[0]:
                # Map degree of divergence to HSV value
                val = MAP[out[1]]

                # Edit pixel
                if MAP == HUEMAP:
                    pixels[R, I] = (val, 255, 255)
                elif MAP == VALMAP:
                    pixels[R, I] = (180, 100, val)

    # Save image
    img = img.resize((SIZEX_FINAL, SIZEY_FINAL), Image.ANTIALIAS)
    img = img.convert("RGB")
    img.save(f"jout/julia{name}.png")


if __name__ == "__main__":
    imagec = 0

    if not os.path.isdir("jout"):
        os.mkdir("jout")

    # Progress bar init
    count = mp.Value("i", 0)
    total = SIZEX * SIZEY * FRAMECOUNT

    threads = []

    bar = progressbar.ProgressBar(maxval=FRAMECOUNT)

    print("Starting threads...")

    while imagec <= FRAMECOUNT:
        bar.update(imagec)
        ZOOM += ZOOMFACTOR
        OFFSETX = CENTERX * ZOOM
        OFFSETY = CENTERY * ZOOM

        # Calculate constant
        CONSTANTT = animation(imagec)

        # Start threads
        threads.append(mp.Process(target=make_image, args=(imagec, CONSTANTT)))
        threads[-1].start()

        imagec += 1

        # Join threads when they are 8
        if not (imagec) % 16:
            for thread in threads:
                threads.pop().join()

    for thread in threads:
        thread.join()
    if FRAMECOUNT != 1:
        os.system(f"ffmpeg -r 30 -i jout/julia%01d.png -vcodec libx264 -crf 15 -pix_fmt yuv420p -y {FNAME}.mp4")
        os.system(f"ffmpeg -i {FNAME}.mp4 -filter_complex \"[0:v] split [a][b];[a] palettegen [p];[b][p] paletteuse\" {FNAME}.gif")

        if input("Delete jout? [y/N]").lower() == "y":
            shutil.rmtree("jout")
