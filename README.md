# apdfhelper: Annotated PDF Helper

This tool is originally meant to customize a PDF planner, and enhance its usage.
It can:

- remove pages

  If you don't use certain pages (anymore), you can remove them.

- display or add bookmarks

  Would you like to have some bookmarks (an outline, or table of contents in
  PDF-parlance)? With this tool you can view and edit them.

- extract notes

  Extract notes (text annotations) in text format, ordered per page. If there is
  a bookmark defined for that page, it will show the title on which page the
  note(s) appear(s).

- rewrite (broken) internal links

  Rewire named links in a document to specific pages.

- fix link types

  Ensure that internal links show the correct page, fitted in a PDF viewer.

- swap pages

  Not happy with the current page ordering? Swap them around.

- split PDF into multiple single pages

  Extract all pages from a PDF file as single PDF files.

Sorry, currently only a command-line version of this tool is supplied, no
graphical interface exists (yet...).

## Installation

Python 3 is required.

```bash
pip install -r requirements.txt
```

## Usage

When wanting to 're-organize' a PDF file, say `calendar.pdf`, first ensure that
the pages themselves are in order. Then, create a text file with bookmarks,
`toc.txt`, the table of contents. The format of the file is PAGENUMBER TITLE,
for example:

```
3 Overview 2024-2025
14 January
29 Week 44
```

This table of contents creates 3 bookmarks, for 'Overview 2024-2025' pointing to
page 3, to 'January' on page 14, and 'Week 44' on page 29.

Then, if there are any named links in the document defined, extract them using
`python apdfhelper.py links calendar.pdf > links.txt`. This outputs all named
links to `links.txt` with the page numbers it's referring to.

Next, edit `links.txt` and use the correct page numbers or use any of the titles
that are defined in the table of contents file `toc.txt`. When using titles,
don't forget to use quotes around them, for example:

```
mossery-dpln-2023_third-edition.indd:2023-03-2023&2024YC:244 "Overview 2024-2025"
mossery-dpln-2023_third-edition.indd:2023-04-M-Jan:5 "January"
mossery-dpln-2023_third-edition.indd:2023-04-WG-Week44:148 "Week 44"
mossery-dpln-2023_third-edition.indd:2023-04-Note-02:183 6
```

Next, embed the table of contents in `calendar.pdf` and create or update the
links using the `rewrite` command:

```bash
python apdfhelper.py rewrite calendar.pdf --toc toc.txt output.pdf links.txt
```

And voila, the file `output.pdf` will now contain the defined bookmarks, as well
as links to the correct pages.

### Remove one or more pages

Specify one page number, multiple page numbers (separated by a ','), or ranges
of pages (separated by a '-') to be deleted.

```bash
python apdfhelper.py remove INFILE OUTFILE RANGES
```

Example to remove page 1, and page 189 up to and including 212:

```
python apdfhelper.py calendar.pdf output.pdf 1,189-212
```

### View bookmarks

```bash
python apdfhelper.py bookmarks INFILE
```

### Add bookmarks

```bash
python apdfhelper.py bookmarks --add --title "Title of my bookmark" --page PAGENUMBER
```

### Extract notes (annotations) from a PDF file

Extract all notes (text annotations) from a PDF file, and optionally show the
bookmark title or page number of the annotation.

Example:

```
python apdfhelper.py notes --headers calendar.pdf
```

This will return a list of all text annotations in `calendar.pdf`, grouped per
page. If there is a bookmark defined for that page, it will show the title of
the bookmark instead.

### Extract all named links from a PDF file

Instead of directly linking to page numbers, PDF links can be named. `links`
extracts all named links that are defined in a PDF file, with the page number
it's pointing to. This can be useful as input when rewriting links. If the link
says `broken`, it's pointing to a non-existing page. Note that this can be fixed
using `rewrite`.

Example:

```
python apdfhelper.py links calendar.pdf
```

### Rewrite links in a PDF file

Sometimes named links are broken: They point to non-existing pages. Or, you'd
like to rewire the location of a named link. Use as input a text file,
containing the named link, followed by a space and a page number.

Example contents of a link file:

```
mossery-dpln-2023_third-edition.indd:2023-02-Index:241 2
mossery-dpln-2023_third-edition.indd:2023-03-YO-H1:3 29
```

This rewrites the link named
`mossery-dpln-2023_third-edition.indd:2023-02-Index:241` to page 2, and the link
named `mossery-dpln-2023_third-edition.indd:2023-03-YO-H1:3` to page 29.

Alternatively, you can supply a table of contents file, in order to map page
numbers to bookmark titles. This can be easier when for instance a lot of links
point to the same page number, or when you often change the ordering of pages.
The dictionary consists of a title, and a page number. Then, in the link file,
use that unique name instead of the page number. Don't forget to put double
quotes around the title in the link file.

#### Usage

```
apdfhelper.py rewrite [OPTIONS] INFILE OUTFILE LINKFILE

  Rewrite links in a PDF file based on a configuration file.

  If fit is given, rewrite type of link to 'Fit to page'. If toc is given,
  parse page numbers from a table of contents file.

Arguments:
  INFILE    [required]
  OUTFILE   [required]
  LINKFILE  [required]

Options:
  --toc TEXT
  --fit / --no-fit          [default: no-fit]
  --verbose / --no-verbose  [default: no-verbose]
```

#### Example

```
python apdfhelper.py rewrite calendar.pdf output.pdf --toc toc.txt links.txt
```

### Detailed link information

If you'd like to see which page contains links (clickable areas), and what the
link points to, use `page-links`. The result is the page number on which the
link occurs, with the coordinates of the link (left, top, right, bottom), the
_type_ of link (internal or external), and what the link points to.

Optionally you can see which page number a link points to, which can be useful
for troubleshooting broken links on pages.

#### Usage

```bash
apdfhelper.py page-links [OPTIONS] INFILE

Display links on a specific page, or all pages.

Output format is: pagenumber left top right bottom [internal | external] link.

When resolve is given, specify the page number of the link instead of the
named link. Otherwise links might show up as broken.

Arguments:
INFILE [required]

Options:
--page INTEGER [default: 0]
--resolve / --no-resolve [default: no-resolve]
--detailed / --no-detailed [default: no-detailed]
```

### Split PDF

Say you want to extract each page of a PDF file as single PDF file. Use the
split command to do exactly that. Naming of the extracted files can be set by
specifying a prefix, which will be followed by the page number.

```bash
apdfhelper.py split [OPTIONS] INFILE PREFIX

Split one PDF into multiple single pages. The name uses prefix and the page
number.

Arguments:
INFILE [required]
PREFIX [required]
```

## Advanced usage

As an advanced example, the PDF Mossery 2024 calendar that can be found on
https://www.mossery.co/products/2024-digital-planner contains gridded, vertical
and horizontal layouts. To remove the gridded and horizontal layouts in an
original unmodified (!) calendar file, use the following commands:

```bash
./apdfhelper.py remove calendar-2024.pdf output.pdf 38,40,41,43,44,46,47,49,51,53,54,56,57,59,60,62,63,65,67,69,70,72,73,75,76,78,80,82,83,85,86,88,89,91,93,95,96,98,99,101,102,104,105,107,109,111,112,114,115,117,118,120,122,124,125,127,128,130,131,133,135,137,138,140,141,143,144,146,147,149,151,153,154,156,157,159,160,162,164,166,167,169,170,172,173,175,176,178,180,182,183,185,186,188,189,191,193,195,196,198,199,201,202,204,205,207
```

Note that this removes the pages, which will result in broken links. Create a
file with all named links:

```
./apdfhelper.py links output.pdf > links.txt
```

Then use a text editor to fix the broken links in `links.txt` (replace them with
valid page numbers), and apply the new links to the modified file:

```bash
./apdfhelper.py rewrite output.pdf fixed.pdf links.txt --fit
```

Now the file `fixed.pdf` will contain the 2024 calendar, containing the vertical
layout, with working links.
