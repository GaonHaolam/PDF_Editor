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
            new_order[i] = reader.pages[i+1]   # Right -> First
            new_order[i+1] = reader.pages[i]   # Left -> Second

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

    print(f"Success. Reordered PDF saved as: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python reorder.py <input_pdf> <mode> [output_pdf]")
        print("Modes:")
        print("1. Booklet Right to Left")
        print("2. Booklet Left to Right")
        print("3. Spreads Right to Left")
        print("4. Spreads Left to Right")
    else:
        try:
            mode_arg = int(sys.argv[2])
            inp = sys.argv[1]
            if len(sys.argv) >= 4:
                out = sys.argv[3]
            else:
                out = f"reordered_{os.path.basename(inp)}"
            reorder_pdf(inp, out, mode_arg)
        except ValueError as e:
            print(f"Error: {e}")
