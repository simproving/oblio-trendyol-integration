import os
from pathlib import Path
from PyPDF2 import PdfMerger

def combine_pdfs_in_folder(folder_path):
    """Combine all PDF files in a folder into one PDF."""
    folder = Path(folder_path)
    
    if not folder.exists() or not folder.is_dir():
        print(f"Folder {folder_path} does not exist or is not a directory")
        return
    
    # Get all PDF files in the folder, sorted by name
    pdf_files = sorted(folder.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return
    
    print(f"Found {len(pdf_files)} PDF files in {folder_path}")
    
    # Create a PdfMerger object
    merger = PdfMerger()
    
    # Add each PDF to the merger
    for pdf_file in pdf_files:
        print(f"  Adding: {pdf_file.name}")
        merger.append(str(pdf_file))
    
    # Extract invoice numbers from first and last PDF filenames
    first_invoice = pdf_files[0].stem  # filename without extension
    last_invoice = pdf_files[-1].stem
    
    # Create output filename with invoice range
    output_filename = folder / f"{first_invoice}-{last_invoice}.pdf"
    
    # Write the combined PDF
    with open(output_filename, 'wb') as output_file:
        merger.write(output_file)
    
    merger.close()
    print(f"✓ Combined PDF saved as: {output_filename}\n")

def main():
    """Find the most recent downloaded_invoices folder and combine PDFs."""
    current_dir = Path(".")
    
    # Find all folders that start with "downloaded_invoices"
    invoice_folders = [f for f in current_dir.iterdir() 
                      if f.is_dir() and f.name.startswith("downloaded_invoices")]
    
    if not invoice_folders:
        print("No downloaded_invoices folders found")
        return
    
    # Get the most recent folder (sorted by name, which includes date)
    most_recent_folder = sorted(invoice_folders)[-1]
    
    print(f"Processing most recent folder: {most_recent_folder.name}\n")
    combine_pdfs_in_folder(most_recent_folder)
    
    print("Done!")

if __name__ == "__main__":
    main()
