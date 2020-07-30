from PIL import Image
import progressbar
import math

# Constans
THRESHOLD = 10**10
ITERATIONS = 500

SIZEX_FINAL = 100
SIZEY_FINAL = 100

SIZEX = round(SIZEX_FINAL * 1.2)
SIZEY = round(SIZEY_FINAL * 1.2)

CENTERX = -0.77568377
CENTERY = 0.13646737

ZOOM = 50

OFFSETX = CENTERX * ZOOM
OFFSETY = CENTERY * ZOOM


# Check for divergence
def diverge(c, z=complex(0, 0), count=0):
    # If length over threshhold diverges
    if abs(z) > THRESHOLD:
        return (True, count)
    # If max iters is reached, does not diverge
    elif count > ITERATIONS:
        return (False, count)
    # Recurse
    else:
        return diverge(c, z=(z**2 + c), count=count + 1)


# Image init
img = Image.new("HSV", (SIZEX, SIZEY), (0, 0, 0))
pixels = img.load()

# Progress bar init
count = 0
total = img.size[0] * img.size[1]

bar = progressbar.ProgressBar(maxval=total)

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
img.save("test.png")
