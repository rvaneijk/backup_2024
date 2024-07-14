import os
import subprocess
import sys
from datetime import datetime
import yaml

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: Command failed with error: {result.stderr}")
    return result.returncode == 0

def process_directory(base_dir, archive_name, incr):
    os.chdir(base_dir)
    print(f"Processing {base_dir}")
    
    subdirs = sorted([d for d in os.listdir() if os.path.isdir(d) and d[0].isdigit()])
    
    for subdir in subdirs:
        os.chdir(subdir)
        print(f"  Processing subdirectory: {subdir}")
        
        # Move relevant files into the subdirectory
        start, end = map(int, subdir.split('-'))
        for i in range(start, end + 1):
            file_prefix = f"{incr} FULL {archive_name}.7z.{i:03d}"
            if os.path.exists(f"../{file_prefix}"):
                os.rename(f"../{file_prefix}", file_prefix)
        
        # Create par2 files
        par2_create = f"par2 create -c625 {incr} BAK {archive_name} {incr} FULL {archive_name}.7z.*"
        if not run_command(par2_create):
            print(f"  Warning: par2 create failed for {subdir}")
        
        # Verify par2 files
        par2_verify = f"par2 verify -q {incr} BAK {archive_name} {incr} BAK {archive_name}.par2"
        if not run_command(par2_verify):
            print(f"  Warning: par2 verify failed for {subdir}")
        
        os.chdir('..')
    
    # Check for any remaining files
    remaining_files = [f for f in os.listdir() if f.startswith(f"{incr} FULL {archive_name}.7z.")]
    if remaining_files:
        print(f"Warning: The following files were not processed: {', '.join(remaining_files)}")
    else:
        print("All files processed successfully.")

def get_archives_to_skip(archives):
    print("Select archives to skip (enter the number, separated by spaces):")
    for i, archive in enumerate(archives, 1):
        print(f"{i}. {archive['archive_name']}")
    skip_input = input("Enter numbers to skip (or press Enter to process all): ")
    skip_numbers = [int(num) for num in skip_input.split() if num.isdigit()]
    return set(skip_numbers)

def load_config(config_file):
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)

def main():
    if len(sys.argv) != 2:
        script_name = os.path.basename(sys.argv[0])
        print(f"Error: Missing <INCR> argument.")
        print(f"Usage: python {script_name} <INCR>")
        print(f"Example: python {script_name} 240714")
        print("Note: <INCR> should be the date of the backup in YYMMDD format.")
        sys.exit(1)
    
    incr = sys.argv[1]
    base_path = "/mnt/e/mnt/aws.local"
    
    config = load_config('configs/monthly_config.yaml')
    archives = config['backup_folders']
    
    archives_to_skip = get_archives_to_skip(archives)
    
    start_time = datetime.now()
    print(f"Starting par file creation process... ({start_time.strftime('%y%m%d %H:%M')})")
    
    for i, archive in enumerate(archives, 1):
        if i in archives_to_skip:
            print(f"Skipping {archive['archive_name']}...")
            continue
        
        full_path = os.path.join(base_path, archive['dest'])
        if os.path.exists(full_path):
            process_directory(full_path, archive['archive_name'], incr)
        else:
            print(f"Warning: Directory {full_path} does not exist. Skipping.")
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"Par file creation completed! (Duration: {duration})")

if __name__ == "__main__":
    main()