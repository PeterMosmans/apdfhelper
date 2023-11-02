#!/usr/bin/env python3

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
from pikepdf import Page, Pdf, String

app = typer.Typer()


def read_dictionary(filename: str) -> dict:
    """Return a dictionary to translate human-readable names to page numbers.
    Format of the file is UNIQUE_NAME PAGENUMBER.
    UNIQUE_NAME cannot contain spaces."""
    result = {}
    if not filename:
        return result
    try:
        with open(filename, "r") as filehandle:
            for line in filehandle.read().splitlines():
                line = line.split(" ")
                try:
                    result[line[0]] = int(line[1])
                except (ValueError, IndexError) as e:
                    print(f"Could not read a valid page number for {line[0]}: {e}")
    except IOError:
        logging.error("Could not read %s", filename)
    print(f"Read {len(result)} dictionary entries")
    return result


def read_links(filename: str, dictionary: str = None) -> dict:
    """Return a dictionary with named links and their page numbers.
    Format of the file is NAME [PAGENUMBER|UNIQUE_NAME].
    Note that NAME can contain spaces: The last value at the right is chosen."""
    result = {}
    if not filename:
        return result
    try:
        dictionary = read_dictionary(dictionary)
        with open(filename, "r") as filehandle:
            for line in filehandle.read().splitlines():
                line = line.split(" ")
                # Take the outermost value, as sometimes names have spaces in them
                try:
                    if line[len(line) - 1] in dictionary:
                        result[line[0]] = int(dictionary[line[len(line) - 1]])
                    else:
                        result[line[0]] = int(line[len(line) - 1])
                except ValueError:
                    print(f"Could not read a valid page number for {line[0]}")
    except IOError:
        logging.error("Could not read %s", filename)
    print(f"Read {len(result)} links")
    return result


def save_pdf(pdf, filename="output.pdf"):
    """Save PDF to output file."""
    print(f"Saving PDF to {filename}")
    try:
        pdf.save(filename)
    except Exception as e:
        print(f"Could not save to {filename}: {e}")


def remove_page(pdf: Pdf, index: int) -> Pdf:
    """Remove a specific page and all of its keys in the dictionary.
    Note that the index is 1-based."""
    print(f"Removing page {index}")
    page = pdf.pages.p(index)
    for key in page.keys():
        del page[key]
    del pdf.pages[index - 1]
    return pdf


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
    dictionary: str = None,
    outfile: str = None,
    detailed: bool = False,
    fit: bool = False,
):
    """Print all named links with their corresponding page number.
    If configuration is given, rewrite the name link to another page number.
    If outfile is given, write the resulting PDF to a file.
    If fit is given, rewrite the type of link to fit"""
    transformation = read_links(configuration, dictionary=dictionary)
    for kid in pdf.Root.Names.Dests.Kids:
        names = kid.Names
        for i in range(0, len(names), 2):
            name, dest = names[i], names[i + 1]
            # dest[0] = Page
            # dest[1] can be either "/XYZ" with left top zoom as [2], [3], [4]
            #                or "/Fit"
            try:
                if detailed:
                    print(f"{dest[1]}")
                if str(dest[1]) == "/XYZ":
                    if detailed:
                        print(f"{dest[2]} {dest[3]} {dest[4]}")
                    if fit and outfile:
                        print(f"Changing type of {name} link to 'Fit'")
                        dest[1] = String("/Fit")
                if name in transformation:
                    page = pdf.pages.p(transformation[name])
                    dest[0] = page.obj
                    print(f"{name} rewriting {transformation[name]}")
                else:
                    page = Page(dest[0])
                    print(f"{name} {page.index + 1}")
            except ValueError:
                if name in transformation:
                    page = pdf.pages.p(transformation[name])
                    dest[0] = page.obj
                    print(f"{name} rewriting {transformation[name]}")
                else:
                    print(f"{name} broken")
    if outfile:
        save_pdf(pdf, outfile)


def retrieve_annotations(pdf: Pdf, location: bool = False, index: int = 0):
    """Retrieve all text annotations of a specific page, or all pages."""
    header = ""
    for page in pdf.pages:
        if not index or (index and (page.index == index - 1)):
            if location:
                header = f"\nPage {page.index + 1}\n"
            if "/Annots" in page:
                for annot in page.Annots:
                    if "/Subtype" in annot and annot.get("/Subtype") == "/FreeText":
                        #                        left, top, right, bottom = annot.get("/Rect")
                        print(f"{header}{annot.Contents}")
                        header = ""


def open_pdf(infile: str) -> Pdf:
    """Open a PDF file."""
    try:
        pdf = Pdf.open(infile)
        return pdf
    except Exception as e:
        print(f"Could not open {infile}: {e}")
        sys.exit(-1)


@app.command()
def remove(infile: str, outfile: str, ranges: str):
    """Remove ranges of pages from a PDF file and save to outfile. Specify a range using a '-', and multiple ranges or numbers using a ','."""
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
def notes(infile: str, page: int = 0, location: bool = False):
    """Extract all annotations as text on a specific page, or all pages.
    Optionally specify the location in the file."""
    pdf = open_pdf(infile)
    retrieve_annotations(pdf, index=page, location=location)


@app.command()
def page_links(infile: str, page: int = 0, resolve: bool = False):
    """Display links on a specific page, or all pages.\n
    Output format is: pagenumber left top right bottom [INTERNAL|EXTERNAL] link.\n
    When resolve is given, specify the page number of the link instead of the named link.
    """
    pdf = open_pdf(infile)
    retrieve_links(pdf, index=page, resolve=resolve)


@app.command()
def links(infile: str, detailed: bool = False):
    """Extract all named links.\n
    Output format is: NAME PAGENUMBER"""
    pdf = open_pdf(infile)
    rewrite_named_links(pdf, detailed=detailed)


@app.command()
def rewrite(
    infile: str, outfile: str, linkfile: str, dictionary: str = None, fit: bool = False
):
    """Rewrite links in a PDF file based on a configuration file.\n
    If fit is given, rewrite type of link to 'Fit to page'."""
    pdf = Pdf.open(infile)
    rewrite_named_links(
        pdf, configuration=linkfile, dictionary=dictionary, outfile=outfile, fit=fit
    )


if __name__ == "__main__":
    app()
