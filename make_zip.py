# make_zip.py - Package all ResearchMate AI code into ResearchMate_AI.zip
import os
import zipfile

def create_zip():
    zip_filename = "ResearchMate_AI.zip"
    exclude_dirs = {"__pycache__", ".git", ".pytest_cache", "uploads", "exports", ".system_generated"}
    exclude_files = {zip_filename, "researchmate.db"}
    
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file in exclude_files or file.endswith(".pyc"):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, ".")
                zipf.write(file_path, arcname)
                print(f"Added to zip: {arcname}")
                
    print(f"\nSuccessfully created {zip_filename} ({os.path.getsize(zip_filename)} bytes)!")

if __name__ == "__main__":
    create_zip()
