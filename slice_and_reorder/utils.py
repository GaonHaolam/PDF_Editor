import os
import fitz

def delete_page_from_pdf(file_path, page_number_1_based):
    """
    Deletes a page from a PDF file.
    
    Args:
        file_path (str): Path to the PDF file.
        page_number_1_based (int): The page number to delete (1-indexed).
        
    Returns:
        bool: True if successful, False if page number was invalid.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    try:
        doc = fitz.open(file_path)
        # fitz uses 0-based indexing
        page_idx = int(page_number_1_based) - 1
        
        if 0 <= page_idx < len(doc):
            doc.delete_page(page_idx)
            doc.saveIncr() # Incremental save to apply changes
            doc.close()
            return True
        else:
            doc.close()
            return False
            
    except Exception as e:
        raise e
