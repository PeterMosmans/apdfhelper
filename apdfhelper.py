#!/usr/bin/env python3
# pylint: disable=logging-fstring-interpolation

"""apdfhelper - perform various functions on PDF files

Copyright (C) 2023 Peter Mosmans [Go Forward]
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

import logging
import sys

import typer
from pikepdf import Dictionary, OutlineItem, Page, Pdf, String
from pikepdf._core import PdfError

app = typer.Typer()


def open_pdf(infile: str) -> Pdf:
    """Open a PDF file."""
    try:
        pdf = Pdf.open(infile)
        return pdf
    except (IOError, PdfError) as e:
        print(f"Could not open {infile}: {e}", file=sys.stderr)
        sys.exit(-1)


def read_toc(filename: str) -> (dict, list):
    """Parse a file containing a table of contents.

    Return a dictionary using page numbers as the key, as a page can have only one title.
    Return a list containing the titles, the indentation, and the page number.
    """
    pages, titles = {}, []
    # Current level of entry
    level = 0
    # Remember current indentation level(s)
    parents = []
    if not filename:
        return pages, titles
    try:
        with open(filename, "r", encoding="utf-8") as filehandle:
            for line in filehandle.read().splitlines():
                try:
                    # The page number is always last
                    index = int(line.split(" ")[len(line.split(" ")) - 1 :][0])
                    indentation = len(line) - len(line.lstrip(" "))
                    title = line[indentation : len(line) - (len(str(index)) + 1)]
                    if indentation > level:
                        # a new sublevel, therefore store previous level
                        parents.append(level)
                        level = indentation
                    elif indentation < level:
                        while True:
                            level = parents.pop()
                            if level == indentation:
                                break
                    # There can be only one title per page
                    pages[index] = title
                    logging.info(f"{' '*level}{title} - page {index}")
                    titles.append((title, level, index))
                except (ValueError, IndexError) as e:
                    print(f"Could not read a valid page number for {line[0]}: {e}")
    except (IOError, UnicodeDecodeError) as e:
        logging.error(f"Could not read {filename}: {e}")
    logging.info(
        f"Read {len(pages)} different pages and {len(titles)} different titles"
    )
    return pages, titles


def read_links(filename: str, tocfile: str = None) -> dict:
    """Return a dictionary from a file containing named links,
    having named links as the key and their page number as the value.
    The format of the file is NAME [PAGENUMBER|"TOCTITLE"].
    If the value at the right contains double quotes, a bookmark title is expected.
    Note that NAME can contain spaces: The last value at the right is chosen.
    When tocfile is supplied, read titles from that file and use the correct page number.
    """
    result, toctitles = {}, {}
    if not filename:
        return result
    try:
        _, titles = read_toc(tocfile)
        # There can be similar titles, yet point to a different page number.
        # Convert the list to a dictionary, and prefer the last title
        for title, _, index in titles:
            toctitles[title] = index
        with open(filename, "r", encoding="utf-8") as filehandle:
            for line in filehandle.read().splitlines():
                try:
                    # Check whether it's a bookmark title or a page number:
                    if line[len(line) - 1] == '"':
                        link_title = line.split('"')[0].strip()
                        bookmark_title = line.split('"')[1]
                        if bookmark_title in toctitles:
                            # Convert title to page number
                            index = toctitles[bookmark_title]
                        else:
                            print(
                                f"Could not find an entry for {bookmark_title} in {tocfile}"
                            )
                            sys.exit(-1)
                    else:
                        splitted = line.split(" ")
                        link_title = " ".join(splitted[0 : len(splitted) - 1])
                        index = int(splitted[len(splitted) - 1])
                    result[link_title] = index
                except ValueError as e:
                    print(f"Could not read a valid page number for {line}: {e}")
                    sys.exit(-1)
    except IOError:
        logging.error("Could not read %s", filename)
    logging.info(f"Read {len(result)} named links from {filename}")
    return result


def save_pdf(pdf: Pdf, filename: str, fast: bool = False):
    """Save PDF to output file."""
    print(f"Saving PDF to {filename}")
    try:
        pdf.save(filename, linearize=fast)
    except (IOError, PdfError) as e:
        print(f"Could not save to {filename}: {e}", file=sys.stderr)


def convert_bookmark_item(
    bookmark: OutlineItem, results: list, dictionary: dict, level: int = 0
) -> (list, dict):
    """Convert a bookmark (OutlineItem) into a title and page number.
    Return a textual representation of the bookmarks and a dictionary per page."""
    dest_index = 0
    if bookmark.action:
        _, _, dest_index = convert_link(bookmark.action)
    else:
        try:
            dest = bookmark.to_dictionary_object(None)["/Dest"]
            dest_index = Page(dest[0]).index + 1
        except ValueError:
            logging.error(f"Title {bookmark.title} does not point to a page")
            dest_index = 0
    results.append(f"{' '*level}{bookmark.title} {dest_index}")
    dictionary[dest_index] = bookmark.title
    for child in bookmark.children:
        results, dictionary = convert_bookmark_item(
            child, results, dictionary, level=level + 1
        )
    return results, dictionary


def retrieve_titles(pdf: Pdf) -> (list, dict):
    """Read table of content entries from a PDF file and return them as textual
    list, as well as a dictionary. Note that the dictionary will only contain the last title
    specified of that page."""
    results, dictionary = [], {}
    with pdf.open_outline() as outline:
        for item in outline.root:
            results, dictionary = convert_bookmark_item(item, results, dictionary)
    return results, dictionary


def delete_bookmarks(pdf: Pdf) -> Pdf:
    """Delete all bookmarks from a PDF."""
    with pdf.open_outline() as outline:
        outline.root.clear()
    return pdf


def import_bookmarks(pdf: Pdf, infile: str) -> Pdf:
    """Import bookmarks from infile and add them to PDF."""
    _, titles = read_toc(infile)
    # Store levels with their OutlineItems
    levels = []
    with pdf.open_outline() as outline:
        for title, level, page in titles:
            item = OutlineItem(title, page - 1)
            logging.info(f"Reading entry level {level}: {title}")
            if not level:
                outline.root.append(item)
                levels = [(level, item)]
            else:
                current_level, current_item = levels.pop()
                if level == current_level:
                    current_level, current_item = levels.pop()
                if level > current_level:
                    levels.append([current_level, current_item])
                while level <= current_level:
                    current_level, current_item = levels.pop()
                current_item.children.append(item)
                levels.append([level, item])
    return pdf


def add_bookmark(pdf: Pdf, title: str, page: int) -> Pdf:
    """Add bookmark to a PDF file."""
    with pdf.open_outline() as outline:
        outline.root.append(OutlineItem(title, page - 1))
    return pdf


def swap_page(pdf: Pdf, source: int, target: int) -> Pdf:
    """Swap page SOURCE with TARGET."""
    page_temp = pdf.pages.p(target)
    pdf.pages[target - 1] = pdf.pages.p(source)
    pdf.pages[source - 1] = page_temp
    return pdf


def remove_page(pdf: Pdf, index: int) -> Pdf:
    """Remove a specific page and all of its keys in the dictionary.
    Note that the index is 1-based."""
    print(f"Removing page {index}")
    page = pdf.pages.p(index)
    for key in page.keys():
        del page[key]
    del pdf.pages[index - 1]
    return pdf


def convert_link(dictionary: Dictionary):
    """Convert an annotation / dictionary item into a link."""
    link_index = 0
    if "/S" in dictionary and dictionary["/S"] == "/URI":
        link_type = "external"
        link_target = dictionary.get("/URI")
    elif "/S" in dictionary and dictionary["/S"] == "/GoTo":
        link_type = "internal"
        link_target = dictionary.get("/D")[0]
        dest_page = Page(dictionary.get("/D")[0])
        link_index = dest_page.index + 1
    return link_type, link_target, link_index


def retrieve_links(
    pdf: Pdf, index: int = 0, detailed: bool = False, resolve: bool = False
):
    """Retrieve and print out all links of a specific page, or all pages.
    Output format is: pagenumber left top right bottom [INTERNAL|EXTERNAL] link."""
    if resolve:
        resolved = resolve_names(pdf)
    else:
        resolved = {}
    for page in pdf.pages:
        if not index or (index and (page.index == index - 1)):
            if "/Annots" in page:
                for annot in page.Annots:
                    if "/Subtype" in annot and annot.get("/Subtype") == "/Link":
                        if detailed:
                            print(annot)
                        link_type, link_target, link_name = ["", "", ""]
                        left, top, right, bottom = annot.get("/Rect")
                        if annot.get("/A").get("/S") == "/URI":
                            link_type = "external"
                            link_target = annot.get("/A").get("/URI")
                        if annot.get("/A").get("/S") == "/GoTo":
                            link_type = "internal"
                            link_target = annot.get("/A").get("/D")
                            link_name = resolved.get(link_target, "broken")
                        print(
                            f"{page.index + 1} {left} {top} {right} {bottom} {link_type} {link_target} {link_name}"
                        )


def resolve_names(pdf: Pdf):
    """Resolve named links to page numbers and return a dictionary."""
    result = {}
    for kid in pdf.Root.Names.Dests.Kids:
        names = kid.Names
        for i in range(0, len(names), 2):
            name, dest = names[i], names[i + 1]
            try:
                page = Page(dest[0])
                result[name] = int(page.index + 1)
            except ValueError:
                pass
    return result


def rewrite_named_links(
    pdf: Pdf,
    configuration: str = None,
    tocfile: str = None,
    outfile: str = None,
    detailed: bool = False,
    fit: bool = False,
    titles: dict = {},
) -> Pdf:
    """Print all named links with their corresponding page number.
    If configuration is given, rewrite the name link to another page number.
    If outfile is given, write the resulting PDF to a file.
    If fit is given, rewrite the type of link to fit.
    If titles is given, rewrite the page number to a title surrounded with quotes."""
    transformation = read_links(configuration, tocfile=tocfile)
    for kid in pdf.Root.Names.Dests.Kids:
        names = kid.Names
        for i in range(0, len(names), 2):
            name, dest = names[i], names[i + 1]
            # dest[0] = Page
            # dest[1] can be either "/XYZ" with left top zoom as [2], [3], [4]
            #                or "/Fit"
            try:
                # Sometimes this is a Dictionary instead of an Array
                if isinstance(dest, Dictionary):
                    dest = dest.get("/D")
                if detailed:
                    print(f"{dest[1]}")
                if str(dest[1]) == "/XYZ":
                    if detailed:
                        print(f"{dest[2]} {dest[3]} {dest[4]}")
                    if fit and outfile:
                        logging.info(f"Changing type of {name} link to 'Fit'")
                        dest[1] = String("/Fit")
                if name in transformation:
                    page = pdf.pages.p(transformation[name])
                    dest[0] = page.obj
                    logging.info(f"rewriting {name} to page {transformation[name]}")
                else:
                    page = Page(dest[0])
                    if page.index + 1 in titles:
                        print(f'{name} "{titles.get(page.index + 1, page.index + 1)}"')
                    else:
                        print(f"{name} {page.index + 1}")
            except ValueError:
                if name in transformation:
                    page = pdf.pages.p(transformation[name])
                    dest[0] = page.obj
                    print(f"{name} rewriting {transformation[name]}")
                else:
                    print(f"{name} broken")
    return pdf


def retrieve_notes(
    pdf: Pdf, headers: bool = False, index: int = 0, detailed: bool = False
) -> list:
    """Retrieve all text annotations of a specific page, or all pages.
    If headers is specified, show a header (or page title) for each page containing notes.
    """
    result = []
    header = ""
    if headers:
        _, titles = retrieve_titles(pdf)
    for page in pdf.pages:
        if not index or (index and (page.index == index - 1)):
            if headers:
                header = (
                    "\n" + titles.get(page.index + 1, f"Page {page.index + 1}") + "\n"
                )
            if "/Annots" in page:
                for annot in page.Annots:
                    if "/Subtype" in annot and annot.get("/Subtype") == "/FreeText":
                        if detailed:
                            left, top, right, bottom = annot.get("/Rect")
                            header += f"\n{left} {top} {right} {bottom} "
                        result.append(f"{header}{annot.Contents}")
                        header = ""
    return result


@app.command()
def cut(infile: str, outfile: str, source: int, target: int, verbose: bool = False):
    """Cut page SOURCE and insert back on location TARGET."""
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    pdf = open_pdf(infile)
    for to_swap in range(source, target, -1):
        logging.info(f"swapping {to_swap} with {to_swap-1}")
        pdf = swap_page(pdf, to_swap, to_swap - 1)
    save_pdf(pdf, outfile)


@app.command()
def toc(
    infile: str,
    outfile: str = "",
    add: str = "",
    delete: bool = False,
    tocfile: str = "",
    title: str = "",
    page: int = None,
    verbose: bool = False,
):
    """Manage table of content entries.
    --add TITLE: add a single table of content entry with TITLE for page --page
    --delete: delete all current table of content entries
    --tocfile FILENAME: delete all current entries, and import entries from FILENAME."""
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    pdf = open_pdf(infile)
    if add and page and outfile:
        pdf = add_bookmark(pdf, title, page)
    if delete and outfile:
        pdf = delete_bookmarks(pdf)
    if tocfile and outfile:
        pdf = delete_bookmarks(pdf)
        pdf = import_bookmarks(pdf, tocfile)
    if outfile:
        save_pdf(pdf, outfile)
    else:
        titles, _ = retrieve_titles(pdf)
        for title in titles:
            print(title)


@app.command()
def compare(original: str, modified: str, verbose: bool = False) -> bool:
    """Compare the number of notes and bookmarks from two PDF files."""
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    errors = False
    original_meta, modified_meta = {}, {}
    original_meta["notes"], modified_meta["notes"] = retrieve_notes(
        open_pdf(original)
    ), retrieve_notes(open_pdf(modified))
    original_meta["bookmarks"], _ = retrieve_titles(open_pdf(original))
    modified_meta["bookmarks"], _ = retrieve_titles(open_pdf(modified))
    if len(original_meta["notes"]) != len(modified_meta["notes"]):
        print(
            f"Number of notes don't match: {len(original_meta['notes'])} versus {len(modified_meta['notes'])}",
            file=sys.stderr,
        )
        errors = True
    else:
        print(f"Same number of notes: {len(original_meta['notes'])}")
    if len(original_meta["bookmarks"]) != len(modified_meta["bookmarks"]):
        print(
            f"Number of bookmarks don't match: {len(original_meta['bookmarks'])} versus {len(modified_meta['bookmarks'])}",
            file=sys.stderr,
        )
        errors = True
    else:
        print(f"Same number of bookmarks: {len(original_meta['bookmarks'])}")
    sys.exit(errors)


@app.command()
def remove(infile: str, outfile: str, ranges: str, verbose: bool = False):
    """Remove one or ranges of pages from a PDF file.
    Specify a range using a '-', and multiple ranges or page numbers using a ','."""
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    pages = []
    try:
        for segment in ranges.split(","):
            subsegment = segment.split("-")
            if len(subsegment) > 1:
                pages += range(int(subsegment[0]), int(subsegment[1]) + 1)
            else:
                pages.append(int(subsegment[0]))
    except ValueError as e:
        print(
            f"Specify ranges using integers and '-', and use a ',' to specify multiple ranges: {e}"
        )
        sys.exit(-1)
    pdf = open_pdf(infile)
    for delete in sorted(pages, reverse=True):
        pdf = remove_page(pdf, delete)
    save_pdf(pdf, outfile)


@app.command()
def notes(infile: str, page: int = 0, headers: bool = False, detailed: bool = False):
    """Extract all annotations as text on a specific page, or all pages.
    Optionally specify the location in the file."""
    pdf = open_pdf(infile)
    result = retrieve_notes(pdf, index=page, headers=headers, detailed=detailed)
    for note in result:
        print(note)


@app.command()
def page_links(
    infile: str, page: int = 0, resolve: bool = False, detailed: bool = False
):
    """Display links on a specific page, or all pages.\n
    Output format is: pagenumber left top right bottom [INTERNAL|EXTERNAL] link.\n
    When resolve is given, specify the page number of the link instead of the named link.
    """
    pdf = open_pdf(infile)
    retrieve_links(pdf, index=page, resolve=resolve, detailed=detailed)


@app.command()
def links(infile: str, detailed: bool = False, titles: bool = False):
    """Extract all named links and the page number it's pointing towards.\n
    Output format is: NAME PAGENUMBER.
    When titles is specified, resolve page numbers to table of content entries.
    """
    pdf = open_pdf(infile)
    if titles:
        _, titles = retrieve_titles(pdf)
    else:
        titles = {}
    rewrite_named_links(pdf, titles=titles, detailed=detailed)


@app.command()
def rewrite(
    infile: str,
    outfile: str,
    linkfile: str,
    tocfile: str = None,
    fit: bool = False,
    verbose: bool = False,
    fast: bool = False,
):
    """Rewrite links in a PDF file based on a configuration file.\n
    If fit is given, rewrite type of link to 'Fit to page'.
    If tocfile is given, parse page numbers from a table of contents file.
    If fast is given, optimize PDF for faster web viewing (which increases the file size).
    """
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    pdf = Pdf.open(infile)
    pdf = rewrite_named_links(
        pdf, configuration=linkfile, tocfile=tocfile, outfile=outfile, fit=fit
    )
    if tocfile:
        pdf = delete_bookmarks(pdf)
        pdf = import_bookmarks(pdf, tocfile)
    if outfile:
        save_pdf(pdf, outfile, fast=fast)


@app.command()
def split(infile: str, prefix: str, verbose: bool = False):
    """Split one PDF into multiple single pages. The name uses prefix and the
    page number."""
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    pdf = open_pdf(infile)
    for index, page in enumerate(pdf.pages, 1):
        single = Pdf.new()
        single.pages.append(page)
        save_pdf(single, f"{prefix}-{index:03d}.pdf")


@app.command()
def swap(infile: str, outfile: str, source: int, target: int, verbose: bool = False):
    """Swap the pages source and target from a PDF file."""
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    save_pdf(swap_page(open_pdf(infile), source, target), outfile)


if __name__ == "__main__":
    app()
