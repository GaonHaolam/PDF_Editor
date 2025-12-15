import sys
import os
import copy
from pypdf import PdfReader, PdfWriter

def slice_pdf(input_path, output_path):
    """
    Slices a PDF file by splitting each page into two.
    Always outputs [Visual Left, Visual Right] sequence.
    
    Args:
        input_path (str): Path to source PDF.
        output_path (str): Path to save processed PDF.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File '{input_path}' not found.")

    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    num_pages = len(reader.pages)

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

        # Output Order: Always Left then Right
        # Reordering is handled by reorder.py
        writer.add_page(p_left)
        writer.add_page(p_right)

    with open(output_path, "wb") as f_out:
        writer.write(f_out)
        
    print(f"Success. Sliced PDF saved as: {output_path}")
