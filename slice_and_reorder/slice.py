import sys
import os
import copy
from pypdf import PdfReader, PdfWriter

def slice_pdf(input_path, output_path, mode="spreads_ltr"):
    """
    Slices a PDF file by splitting each page into two.
    
    Args:
        input_path (str): Path to source PDF.
        output_path (str): Path to save processed PDF.
        mode (str): Processing mode. Options: 'spreads_ltr', 'spreads_rtl', 'booklet_ltr', 'booklet_rtl'.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File '{input_path}' not found.")

    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    num_pages = len(reader.pages)
    print(f"Processing '{input_path}' with {num_pages} pages in mode '{mode}'...")

    for i in range(num_pages):
        p_orig = reader.pages[i]
        
        # Determine Rotation
        rot = p_orig.rotation if p_orig.rotation is not None else 0
        rot = int(rot) % 360
        
        w = p_orig.mediabox.width
        h = p_orig.mediabox.height
        
        # Prepare two copies
        p_left = copy.deepcopy(p_orig) # Visual Left
        p_right = copy.deepcopy(p_orig) # Visual Right
        
        # Logic for Visual Left vs Visual Right based on rotation
        if rot == 0:
            # Visual Left: x=0..w/2
            p_left.cropbox.lower_left = (0, 0)
            p_left.cropbox.upper_right = (w/2, h)
            
            # Visual Right: x=w/2..w
            p_right.cropbox.lower_left = (w/2, 0)
            p_right.cropbox.upper_right = (w, h)
            
        elif rot == 90:
            # Visual Left is Bottom (y=0..h/2)
            p_left.cropbox.lower_left = (0, 0)
            p_left.cropbox.upper_right = (w, h/2)
            
            # Visual Right is Top (y=h/2..h)
            p_right.cropbox.lower_left = (0, h/2)
            p_right.cropbox.upper_right = (w, h)
            
        elif rot == 180:
            # Visual Left is Physical Right (x=w/2..w)
            p_left.cropbox.lower_left = (w/2, 0)
            p_left.cropbox.upper_right = (w, h)
            
            # Visual Right is Physical Left (0..w/2)
            p_right.cropbox.lower_left = (0, 0)
            p_right.cropbox.upper_right = (w/2, h)
            
        elif rot == 270:
            # Visual Left is Top (y=h/2..h)
            p_left.cropbox.lower_left = (0, h/2)
            p_left.cropbox.upper_right = (w, h)
            
            # Visual Right is Bottom (y=0..h/2)
            p_right.cropbox.lower_left = (0, 0)
            p_right.cropbox.upper_right = (w, h/2)
            
        else:
            # Default to 0
            p_left.cropbox.lower_left = (0, 0)
            p_left.cropbox.upper_right = (w/2, h)
            p_right.cropbox.lower_left = (w/2, 0)
            p_right.cropbox.upper_right = (w, h)

        # Output Order decision
        # If LTR: Visual Left is Page 1, Visual Right is Page 2.
        # If RTL: Visual Right is Page 1, Visual Left is Page 2.
        
        if "rtl" in mode.lower():
            writer.add_page(p_right)
            writer.add_page(p_left)
        else:
            # Default LTR
            writer.add_page(p_left)
            writer.add_page(p_right)

    with open(output_path, "wb") as f_out:
        writer.write(f_out)
        
    print(f"Success. Sliced PDF saved as: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python slice.py <input_pdf_file> [output_pdf_file]")
    else:
        inp = sys.argv[1]
        if len(sys.argv) >= 3:
            out = sys.argv[2]
        else:
            out = f"sliced_{os.path.basename(inp)}"
        slice_pdf(inp, out)
