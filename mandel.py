from PIL import Image
import progressbar
import math

# Constans
THRESHOLD = 2
ITERATIONS = 255

SIZEX_FINAL = 500
SIZEY_FINAL = 350

SIZEX = round(SIZEX_FINAL * 1.2)
SIZEY = round(SIZEY_FINAL * 1.2)

M232 = (-0.77568377, 0.13646737)

CENTERX = M232[0]
CENTERY = M232[1]

ZOOM = 100

OFFSETX = CENTERX * ZOOM
OFFSETY = CENTERY * ZOOM

FRAMECOUNT = 1


# Check for divergence
def diverge(c, z=complex(0, 0), count=0):
    # If length over threshhold diverges
    if abs(z) > THRESHOLD:
        return (True, count)
    # If max iters is reached, does not diverge
    elif count > ITERATIONS or abs(c) <= 0.6:
        return (False, count)
    # Recurse
    else:
        return diverge(c, z=(z**2 + c), count=count + 1)


imagec = 1

# Progress bar init
count = 0
total = SIZEX * SIZEY * FRAMECOUNT

bar = progressbar.ProgressBar(maxval=total)

frames = []

while imagec <= FRAMECOUNT:
    try:
        ZOOM += 0
        OFFSETX = CENTERX * ZOOM
        OFFSETY = CENTERY * ZOOM

        # Image init
        img = Image.new("HSV", (SIZEX, SIZEY), (0, 0, 0))
        pixels = img.load()

        # Iterate over pixels, real values on X and imaginary on Y
        for R in range(img.size[0]):
            for I in range(img.size[1]):
                # Update progress bar
                bar.update(count)

                # Calculating actual coordinates
                zoom_offset_x = OFFSETX / ZOOM
                zoom_offset_y = OFFSETY / ZOOM

                xval = (R - SIZEX / 2) / ZOOM
                yval = (I - SIZEY / 2) / ZOOM

                c = complex(xval + zoom_offset_x, yval + zoom_offset_y)

                # Get divergence
                out = diverge(c)
                if out[0]:
                    # Map degree of divergence to HSV value
                    aux = math.sqrt(out[1] / ITERATIONS)
                    val = round(aux * 255)

                    # Edit pixel
                    pixels[R, I] = (180, 100, val)

                count += 1

        # pixels[round(img.size[0]/2), round(img.size[1]/2)] = (0,255,255)

        # Save image
        img = img.resize((SIZEX_FINAL, SIZEY_FINAL), Image.ANTIALIAS)
        img = img.convert("RGB")
        frames.append(img)
        imagec += 1
    except:
        print("broke")
        break

frames[0].save("anim.gif", format="GIF", append_images=frames[1:], optimize=False, save_all=True, duration=30, loop=0)
