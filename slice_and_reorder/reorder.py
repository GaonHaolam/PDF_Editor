import sys
import os
from pypdf import PdfReader, PdfWriter

def reorder_pdf(input_path, output_path, mode):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File '{input_path}' not found.")

    reader = PdfReader(input_path)
    num_pages = len(reader.pages)
    
    # Validation: Must be even number of pages
    if num_pages % 2 != 0:
        print(f"Error: The input file has {num_pages} pages.")
        print("This format requires an even number of pages.")
        raise ValueError("Input file must have an even number of pages.")

    writer = PdfWriter()
    
    # Prepare list for new page order
    new_order = [None] * num_pages
    
    # Mode Logic
    if mode == 1: # Booklet RTL
        num_spreads = num_pages // 2
        for s in range(num_spreads):
            in_left = 2 * s
            in_right = 2 * s + 1
            
            out_low = s
            out_high = num_pages - 1 - s
            
            if s % 2 == 0:
                new_order[out_low] = reader.pages[in_left]
                new_order[out_high] = reader.pages[in_right]
            else:
                new_order[out_low] = reader.pages[in_right]
                new_order[out_high] = reader.pages[in_left]

    elif mode == 2: # Booklet LTR
        num_spreads = num_pages // 2
        for s in range(num_spreads):
            in_left = 2 * s
            in_right = 2 * s + 1
            
            out_low = s
            out_high = num_pages - 1 - s
            
            if s % 2 == 0:
                new_order[out_low] = reader.pages[in_right]
                new_order[out_high] = reader.pages[in_left]
            else:
                new_order[out_low] = reader.pages[in_left]
                new_order[out_high] = reader.pages[in_right]

    elif mode == 3: # Spreads RTL
        for i in range(0, num_pages, 2):
            new_order[i] = reader.pages[i+1]
            new_order[i+1] = reader.pages[i]

    elif mode == 4: # Spreads LTR
        for i in range(num_pages):
            new_order[i] = reader.pages[i]
            
    else:
        raise ValueError("Invalid mode selected. Options 1-4.")

    # Add pages to writer
    for p in new_order:
        writer.add_page(p)

    with open(output_path, "wb") as f_out:
        writer.write(f_out)
