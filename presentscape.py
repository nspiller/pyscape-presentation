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

import logging
import subprocess
import sys
import xml.etree.ElementTree as xmltree
from copy import deepcopy
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory

from pypdf import PdfWriter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Starting ...")

NUMBER_SKIP_STRING = "copy"
SLIDE_NUMBER = "slidenumber"  # just the name of the slidenumber quantity


class Namespace(Enum):
    SVG = "http://www.w3.org/2000/svg"
    INKSCAPE = "http://www.inkscape.org/namespaces/inkscape"


def xml_tag(namespace: Namespace, tag: str):
    return f"{{{namespace.value}}}{tag}"


def is_svg(filename):
    with open(filename) as f:
        try:
            _, first_element = next(xmltree.iterparse(f, ("start",)))
            return first_element.tag == xml_tag(Namespace.SVG, "svg")
        except xmltree.ParseError:
            logger.error(f"Error parsing {first_element}")
            return False


def remove_hidden(tree):
    """removes hidden slides because they are not needed

    takes argument: xml tree
    returns modified xml tree
    """
    root = tree.getroot()
    for child in root.findall(xml_tag(Namespace.INKSCAPE, "g")):
        if "display:none" in child.get("style"):
            root.remove(child)


def check_label(child, tag):
    return child.get(xml_tag(Namespace.INKSCAPE, "label")) == tag


input_file = Path(sys.argv[1])
if not input_file.exists():
    logger.error(f"File {input_file} not found")
    sys.exit()

if not is_svg(input_file):
    logger.error(f"File {input_file} is not an SVG file")
    sys.exit()

output_file = input_file.with_suffix(".pdf")
if output_file.exists():
    logger.error(f"File {output_file} already exists.")
    sys.exit()


tree = xmltree.parse(input_file)
root = tree.getroot()

# loop through layers looking for NUMBER slide layer
foundNumberElement = False

for child in root:
    child.set("style", "display:none")

    if check_label(child, "NUMBER"):
        logger.debug(f"Found NUMBER slide, now looking for label containing {SLIDE_NUMBER}")

        numberlayer = child

        for subchild in child.iter():
            if subchild.tag == xml_tag(Namespace.SVG, "text"):
                logger.debug("found text tag")

                labelFound = True
                try:
                    labelcontents = subchild.attrib[xml_tag(Namespace.SVG, "label")]

                except KeyError:
                    labelFound = False

                if labelFound and (labelcontents == SLIDE_NUMBER):
                    logger.debug(f"found label with contents {SLIDE_NUMBER}")

                    tspans = subchild.findall(xml_tag(Namespace.SVG, "tspan"))

                    number = tspans[0]
                    slide_num_text = tspans[0].text

                    logger.debug(f"Template slide_num_text is: {slide_num_text}")
                    foundNumberElement = True
                    break

            if foundNumberElement:
                break

        if not foundNumberElement:
            logger.debug("Number text element not found!")

        break

# count the slides
num_slides = 0
for child in root.findall(xml_tag(Namespace.SVG, "g")):
    if check_label(child, "STOP"):
        break

    if check_label(child, "TITLE"):
        num_slides = 1
        continue

    if check_label(child, "MASTER"):
        continue

    if check_label(child, "END"):
        num_slides += 1
        continue

    elif num_slides > 0:
        num_slides += 1

slide_counter = -1
slide_counter_ = -1
logger.debug("Beginning pdf creation ...")

# ensure number layer is not displayed until we decide to
if numberlayer is not None:
    numberlayer.set("style", "display:none")

slides_svg = []
with TemporaryDirectory(prefix=f"{input_file.name}") as tmpdir:
    tmpdir_path = Path(tmpdir)

    for child in root:
        if check_label(child, "STOP"):
            logger.debug("Found STOP, ending processing")
            break

        if check_label(child, "TITLE"):
            logger.debug("Processing TITLE")

            child.set("style", "display:inline")

            cropped_tree = deepcopy(tree)
            remove_hidden(cropped_tree)

            tmp_file = tmpdir_path / "title_slide.svg"
            cropped_tree.write(tmp_file)
            slides_svg.append(tmp_file)

            child.set("style", "display:none")
            slide_counter = 1
            slide_counter_ = 1
            continue

        if check_label(child, "MASTER"):
            logger.debug("Found MASTER")
            child.set("style", "display:inline")

            if foundNumberElement:
                numberlayer.set("style", "display:inline")

        elif check_label(child, "END"):
            logger.debug(f"slide {slide_counter:d}")

            if foundNumberElement:
                temp_text = slide_num_text

                temp_text = temp_text.replace("NS", f"{slide_counter_:02d}")
                temp_text = temp_text.replace("NT", f"{num_slides:d}")

                number.text = temp_text

                numberlayer.set("style", "display:none")

            child.set("style", "display:inline")

            cropped_tree = deepcopy(tree)
            remove_hidden(cropped_tree)
            tmp_file = tmpdir_path / f"slide{slide_counter:02d}.svg"
            cropped_tree.write(tmp_file)
            slides_svg.append(tmp_file)

            child.set("style", "display:none")
            slide_counter = slide_counter + 1
            slide_counter_ = slide_counter_ + 1

        elif slide_counter > 0:
            logger.debug(f"Processing slide {slide_counter:02d}")
            slide_name = child.get(xml_tag(Namespace.INKSCAPE, "label"))
            if slide_name and NUMBER_SKIP_STRING in slide_name:
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
            tmp_file = tmpdir_path / f"slide{slide_counter:02d}.svg"
            cropped_tree.write(tmp_file)
            slides_svg.append(tmp_file)

            child.set("style", "display:none")
            slide_counter = slide_counter + 1
            slide_counter_ = slide_counter_ + 1

    subprocess.call(["inkscape", "--export-type=pdf", "--export-dpi=500"] + slides_svg)

    merger = PdfWriter()

    for svg in slides_svg:
        pdf = svg.with_suffix(".pdf")
        merger.append(pdf)

    merger.write(output_file)
    merger.close()

logger.info("Finished!")
