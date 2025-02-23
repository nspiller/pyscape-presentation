#!/usr/bin/python3
#
# This script converts a presentation made in inkscape and saved
# as SVG to a PDF presentation.
#
# Invoke the script on the command line with:
#
#  presentscape.py <yoursvgname.svg>
#
# This is done by converting layers in the SVG to individual pdf files
# and merging them. Merging will only be done if the 'pdftk' program is
# available. This would be done manually with the command:
#
#  pdftk slide*.pdf output presentation.pdf
#
# The script has a few assumptions:
#
# 1. Slide labeled "TITLE" is the first slide of the presentation (the title
#    slide, obviously)
#
# 2. The master slide (the template for the presentation) is after the title
#    slide
#
# 3. The final "thank you" slide is labelled "END"
#
# 4. Additional layer/slide labelled "STOP" is put after "END" and possible
#    backup slides, so the script knows when to stop.
#
# 5. A layer labelled "NUMBER" may also be placed somewhere after "STOP".
#    It should contain only a text element positioned appropriately as a
#    placeholder for the slide number text. The Label property of this
#    text object should be changed to "slidenumber" (this will already be
#    set in the template svg). If you need to change it, click on the text
#    object and go to Object->Object Properties. The text can be anything
#    you like, pyscape will search for "NS" in the text and replace it
#    with the slide number if it is found. pyscape will also search for
#    "NT" and replace this with the total number of slides in the
#    presentation. e.g. the text "Slide NS of NT" would become
#    "Slide 02 of 10" for slide 2 of a 10 slide presentation.
#    The number text will not appear on the title slide.
#

import glob
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as xmltree
from copy import deepcopy

number_skip_string = "copy"

nargs = len(sys.argv)

# the svg file to work on
input_fname = str(sys.argv[1])
output_fname = input_fname.rstrip("svg") + "pdf"

# temp files directory
tempdir = os.path.join(tempfile.gettempdir(), "slides")

# make sure temp slide directory is cleared of old files by deleting it
# and all contents
if os.path.exists(tempdir):
    shutil.rmtree(tempdir)

# create the empty directory again
os.makedirs(tempdir)

# define some parameters
label = "{http://www.inkscape.org/namespaces/inkscape}label"  # namespace for inkscape label
name = "slidenumber"  # just the name of the slidenumber quantity


def is_svg(filename):
    tag = None
    with open(filename) as f:
        try:
            for _, el in xmltree.iterparse(f, ("start",)):
                tag = el.tag
                break
        except xmltree.ParseError:
            pass

    return tag == "{http://www.w3.org/2000/svg}svg"


def remove_hidden(tree):
    """removes hidden slides because they are not needed

    takes argument: xml tree
    returns modified xml tree
    """
    root = tree.getroot()
    for child in root.findall("{http://www.w3.org/2000/svg}g"):
        if "display:none" in child.get("style"):
            root.remove(child)


if os.path.exists(input_fname):
    if not is_svg(input_fname):
        # it's not svg
        print(f"The input file:\n{input_fname}\ndoes not appear to be a valid svg file.")
        sys.exit()

    else:
        # read the svg file as XML tree
        tree = xmltree.parse(input_fname)
        root = tree.getroot()

else:
    print(f"The input file:\n{input_fname}\ncould not be found")
    sys.exit()

# loop through layers looking for NUMBER slide layer
foundNumberElement = False

for child in root:
    child.set("style", "display:none")

    if child.get(label) == "NUMBER":
        print(f"Found NUMBER slide, now looking for label containing {name}")

        numberlayer = child

        for subchild in child.iter():
            if subchild.tag == "{http://www.w3.org/2000/svg}text":
                print("found text tag")

                print(subchild.attrib)

                labelFound = True
                try:
                    # idcontents = subchild.attrib['id']
                    labelcontents = subchild.attrib[label]

                except KeyError:
                    labelFound = False

                # if subchild.get('name')==name:
                if labelFound and (labelcontents == name):
                    print(f"found label with contents {name}")

                    tspans = subchild.findall("{http://www.w3.org/2000/svg}tspan")

                    number = tspans[0]
                    slide_num_text = tspans[0].text

                    print(f"Template slide_num_text is: {slide_num_text}")

                    # print(number)

                    foundNumberElement = True

                    break

            if foundNumberElement:
                break

        if not foundNumberElement:
            print("Number text element not found!")

        break

# count the slides
num_slides = 0
for child in root.findall("{http://www.w3.org/2000/svg}g"):
    if child.get(label) == "STOP":
        break

    if child.get(label) == "TITLE":
        num_slides = 1
        continue

    if child.get(label) == "MASTER":
        continue

    elif child.get(label) == "END":
        num_slides = num_slides + 1
        continue

    elif num_slides > 0:
        num_slides = num_slides + 1

slide_counter = -1
slide_counter_ = -1
print("Beginning pdf creation ...")
print(f"Creating individual slide pdf files in temporary directory:\n{tempdir}")

# ensure number layer is not displayed until we decide to
if numberlayer is not None:
    numberlayer.set("style", "display:none")

for child in root:
    print(child.get(label))
    #    print(child.keys())
    #    print(child.items())
    if child.get(label) == "STOP":
        print("Found STOP, ending processing")
        break

    if child.get(label) == "TITLE":
        print("Processing TITLE")

        child.set("style", "display:inline")

        cropped_tree = deepcopy(tree)
        remove_hidden(cropped_tree)
        tmp_fname = os.path.join(tempdir, "temppi.svg")
        tmp_fname = os.path.join(tempdir, "slide00.svg")
        cropped_tree.write(tmp_fname)

        child.set("style", "display:none")
        slide_counter = 1
        slide_counter_ = 1
        continue

    if child.get(label) == "MASTER":
        print("Found MASTER")
        child.set("style", "display:inline")

        if foundNumberElement:
            numberlayer.set("style", "display:inline")

    elif child.get(label) == "END":
        print(f"slide {slide_counter:d}")

        if foundNumberElement:
            temp_text = slide_num_text

            temp_text = temp_text.replace("NS", f"{slide_counter_:02d}")
            temp_text = temp_text.replace("NT", f"{num_slides:d}")

            number.text = temp_text

            numberlayer.set("style", "display:none")

        child.set("style", "display:inline")

        cropped_tree = deepcopy(tree)
        remove_hidden(cropped_tree)
        tmp_fname = os.path.join(tempdir, f"slide{slide_counter:02d}.svg")
        cropped_tree.write(tmp_fname)

        child.set("style", "display:none")
        slide_counter = slide_counter + 1
        slide_counter_ = slide_counter_ + 1

    elif slide_counter > 0:
        print(f"Processing slide {slide_counter:02d}")
        slide_name = child.get(label)
        if slide_name and number_skip_string in slide_name:
            slide_counter_ -= 1

        if foundNumberElement:
            temp_text = slide_num_text

            temp_text = temp_text.replace("NS", f"{slide_counter_:02d}")
            temp_text = temp_text.replace("NT", f"{num_slides:d}")

            number.text = temp_text

            print(number.text)

        child.set("style", "display:inline")

        cropped_tree = deepcopy(tree)
        remove_hidden(cropped_tree)
        tmp_fname = os.path.join(tempdir, f"slide{slide_counter:02d}.svg")
        cropped_tree.write(tmp_fname)

        child.set("style", "display:none")
        slide_counter = slide_counter + 1
        slide_counter_ = slide_counter_ + 1

tmplist_svg = glob.glob(os.path.join(tempdir, "slide*.svg"))
subprocess.call(["inkscape", "--export-type=pdf", "--export-dpi=500"] + tmplist_svg)

# get the list of individual slide pdf files
tmplist = glob.glob(os.path.join(tempdir, "slide*.pdf"))

# sort the file names so the slides are in the right order
tmplist.sort()


if shutil.which("gs") is not None:
    print("Combining slide pdfs into single pdf using ghostscript")

    # use gs to catenate the pdfs into one
    subprocess.call(
        [
            "gs",
            "-dBATCH",
            "-dNOPAUSE",
            "-q",
            "-sDEVICE=pdfwrite",
            f"-sOutputFile={output_fname}",
        ]
        + tmplist
    )

    print("Deleting temporary files")

    # clean up
    shutil.rmtree(tempdir)

else:
    print("Cannot join individual slide pdfs into single pdf as pdftk program is not found.")
    print(f"You will find the individual slide pdfs in the directory:\n{tempdir}.")

print("Finished!")
