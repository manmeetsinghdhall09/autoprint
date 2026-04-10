import os
from pypdf import PdfReader, PdfWriter, PageObject

def create_blank_page(width, height):
    """Creates a blank PyPDF PageObject with the specified dimensions."""
    return PageObject.create_blank_page(width=width, height=height)

def prepare_pdf_for_custom_duplex(input_path: str, output_path: str):
    """
    Reads a PDF. If pages <= 2, saves it as-is.
    If pages > 2, inserts a blank page after the first (N-2) pages to ensure
    that when printed via a generic duplex option, the first (N-2) pages act as single-sided,
    and only the final two pages are printed on a single duplex sheet.
    """
    reader = PdfReader(input_path)
    writer = PdfWriter()
    n = len(reader.pages)
    
    if n <= 2:
        for i in range(n):
            writer.add_page(reader.pages[i])
    else:
        for i in range(n - 2):
            page = reader.pages[i]
            writer.add_page(page)
            
            # Create a blank page of the same size
            width = page.mediabox.width
            height = page.mediabox.height
            blank = create_blank_page(width=width, height=height)
            writer.add_page(blank)
            
        # Add the last two pages
        writer.add_page(reader.pages[n - 2])
        writer.add_page(reader.pages[n - 1])
        
    with open(output_path, "wb") as f:
        writer.write(f)
