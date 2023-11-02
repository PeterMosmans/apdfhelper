# apdfhelper: Annotated PDF Helper

This tool is originally meant to customize a PDF planner, and enhance its usage.
It can:

- remove pages

  If you don't use certain pages (anymore), you can remove them.

- rewrite (broken) internal links

  Rewire named links in a document to specific pages.

- extract annotations

  Extract text annotations in text format.

- fix link types

  Ensure that internal links show the correct page, fitted in a PDF viewer.

Currently only a command-line version of this tool is supplied.

## Installation

Python 3 is required.

```bash
pip install -r requirements.txt
```

## Usage

### Remove one or more pages

```bash
remove [OPTIONS] INFILE OUTFILE RANGES

Remove ranges of pages from a PDF file and save to outfile. Specify a range
using a '-', and multiple ranges or numbers using a ','.

Arguments:
INFILE [required]
OUTFILE [required]
RANGES [required]
```

Example to remove page 1, and page 189 up to and including 212:

```
python apdfhelper.py calendar.pdf output.pdf 1,189-212
```

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

### Extract annotations from a PDF file

Extract all text annotations from a PDF file, and optionally show the page
number of the annotation.

Example:

```
python apdfhelper.py notes --location calendar.pdf
```

This will return a list of all text annotations in a document, grouped per page.

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

Alternatively, you can supply dictionary, in order to map page numbers to a
better human-readable format. This can be easier when for instance a lot of
links point to the same page number. The dictionary consists of a unique name,
and a page number. Then, in the link file, use that unique name instead of the
page number.

Example contents of a dictionary file:

```
JANUARY 14
OCTOBER 23
WEEK_40 24
```

Then, in the link file, you can supply WEEK_40 as page number, instead of a
number:

```
mossery-dpln-2023_third-edition.indd:2023-04-WG-Week39:131 OCTOBER
mossery-dpln-2023_third-edition.indd:2023-04-WG-Week3:15 JANUARY
mossery-dpln-2023_third-edition.indd:2023-04-WG-Week40:135 WEEK_40
```

This might be easier when converting lots of similar links, or when often
changing page numbers.

#### Usage

```
apdfhelper.py rewrite [OPTIONS] INFILE OUTFILE LINKS

  Rewrite links in a PDF file based on a configuration file.

  If fit is given, rewrite type of link to 'Fit to page'.

Arguments:
  INFILE   [required]
  OUTFILE  [required]
  LINKS    [required]

Options:
  --fit / --no-fit  [default: no-fit]
```

#### Example

```
python apdfhelper.py rewrite calendar.pdf output.pdf filecontaininglinks.txt --fit
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

Output format is: pagenumber left top right bottom [INTERNAL | EXTERNAL] link.

When resolve is given, specify the page number of the link instead of the
named link.

Arguments:
INFILE [required]

Options:
--page INTEGER [default: 0]
--resolve / --no-resolve [default: no-resolve]
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
