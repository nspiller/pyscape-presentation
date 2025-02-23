# pyscape-presentation
A script and a template file file for preparing presentations via Inkscape and Python.

This Python script (``presentscape.py``) and the associated SVG file represent my workflow for preparing slideshow presentations, mainly for academic purposes. The idea is as follows:

1. Create the presentation using Inkscape based on the template in presentation_template.svg.
2. Convert the slides in the SVG file to PDF files and add the slide numbers using the Python script.
3. Combine the slides (the multiple PDF files) into a presentation (a single PDF file).

How I have structured the presentation according to the template presentation_template.svg:

1. With some exceptions, each layer represents a slide.
2. MASTER layer represents the template for the basic slides.
3. TITLE layer represents the title slide.
4. END layer represents the ending of the main presentation (e.g. the "Thank You & Acknowledgements" slide).
5. STOP indicates the end real ending of the presenation. The contents of the STOP layered are not converted to pdf in the Python script.
6. NUMBER layer defines the placing and the style of the slide numbering that is used by the Python script.
7. The regular slides of the presentation are included as layers between MASTER and END. Feel free to use any labels besides TITLE, MASTER, END, STOP or NUMBER for these layers. The same applies to backup/bonus slides after the official END slide.
8. NEW FEATURE: whenever the string "copy" appears in the slide name, the slide number is not increased.
This is useful when popping in parts of a slide without increasing the page number.
Note that this will not work with the NS/NT at the moment. Furthermore, it limits the naming of the layers somewhat.
Control this by changing `number_skip_string`.

to create the presentation from the presentation_template.svg run the following::

    python presentscape.py presentation_template.svg

On Linux, pyscape can also be run like a normal command, so the follwoing works::

    presentscape.py presentation_template.svg

More instructions for creating the slides can be found in the pyscape.py file.

The Python script has been tested using
- Python 3.11
- Ghostscript 9.55.0
- Inkscape 1.4
