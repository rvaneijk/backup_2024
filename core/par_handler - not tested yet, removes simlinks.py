import os
import subprocess
import math
import shutil
import glob
from typing import List, Dict

def determine_par_strategy(total_chunks: int) -> Dict:
    """
    Determine the optimal PAR2 creation strategy based on the number of chunks.
    
    :param total_chunks: Total number of chunks in the archive
    :return: Dictionary containing PAR2 strategy parameters
    """
    if total_chunks <= 2:
        return {
            'subdirs': 1,
            'chunks_per_subdir': total_chunks,
            'par2_params': '-n4 -r30 -u -m2048',  # Very small archives (≤2 chunks): Highest redundancy (30%)
            'use_sliding_window': False,
            'create_overall_par': False
        }
    elif total_chunks <= 10:
        return {
            'subdirs': 1,
            'chunks_per_subdir': total_chunks,
            'par2_params': '-n8 -r25 -u -m4096',  # Small archives (3-10 chunks): High redundancy (25%)
            'use_sliding_window': False,
            'create_overall_par': False
        }
    elif total_chunks <= 20:
        return {
            'subdirs': math.ceil(total_chunks / 5),
            'chunks_per_subdir': 5,
            'par2_params': '-n12 -r20 -u -m6144',  # Medium-small archives (11-20 chunks): 20% redundancy
            'use_sliding_window': False,
            'create_overall_par': True,
            'overall_par2_params': '-n16 -r15 -u -m6144'  # 15% redundancy for overall
        }
    elif total_chunks <= 40:
        return {
            'subdirs': math.ceil(total_chunks / 10),
            'chunks_per_subdir': 10,
            'par2_params': '-n16 -r18 -u -m8192',  # Medium archives (21-40 chunks): 18% redundancy
            'use_sliding_window': False,
            'create_overall_par': True,
            'overall_par2_params': '-n24 -r12 -u -m8192'  # 12% redundancy for overall
        }
    elif total_chunks <= 70:
        return {
            'subdirs': math.ceil(total_chunks / 20),
            'chunks_per_subdir': 20,
            'par2_params': '-n24 -r15 -u -m10240',  # Large archives (41-70 chunks): 15% redundancy
            'use_sliding_window': True,
            'window_size': 20,
            'window_slide': 5,
            'create_overall_par': True,
            'overall_par2_params': '-n32 -r10 -u -m10240'  # 10% redundancy for overall
        }
    else:
        return {
            'subdirs': math.ceil(total_chunks / 40),
            'chunks_per_subdir': 40,
            'par2_params': '-n32 -r15 -u -m12288',  # Very large archives (>70 chunks): 15% redundancy
            'use_sliding_window': True,
            'window_size': 40,
            'window_slide': 10,
            'create_overall_par': True,
            'overall_par2_params': '-n40 -r8 -u -m12288'  # 8% redundancy for overall
        }

def create_subdir_and_symlinks(base_dir: str, subdir: str, files: List[str], logger):
    subdir_path = os.path.join(base_dir, subdir)
    os.makedirs(subdir_path, exist_ok=True)
    
    for file in files:
        try:
            source_path = os.path.join(base_dir, file)
            link_path = os.path.join(subdir_path, file)
            os.symlink(source_path, link_path)
            logger.debug(f"Created symlink for {file} in {subdir_path}")
        except Exception as e:
            logger.error(f"Error creating symlink for {file}: {str(e)}")

def cleanup_symlinks(base_dir: str, logger):
    """
    Clean up symlinks in all subdirectories of the given base directory using the 'find' command.
    
    :param base_dir: Base directory containing subdirectories with symlinks
    :param logger: Logger object for logging messages
    """
    logger.info(f"Cleaning up symlinks in {base_dir}")
    try:
        # Use find command to locate and remove symlinks
        cmd = f"find {base_dir} -type l -delete"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        logger.info("Symlink cleanup completed successfully")
        logger.debug(f"Cleanup command output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clean up symlinks: {e}")
        logger.debug(f"Error output: {e.stderr}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during symlink cleanup: {str(e)}")

def create_par2_files(month_dir: str, archive_name: str, incr: str, total_chunks: int, logger, strategy: Dict) -> None:
    """
    Create PAR2 files for the given archive using an optimized strategy.
    
    :param month_dir: Directory containing the chunks for the month
    :param archive_name: Name of the archive
    :param incr: Increment value (usually date in YYMMDD format)
    :param total_chunks: Total number of chunks in the archive
    :param logger: Logger object for logging messages
    :param strategy: Strategy dictionary for PAR2 creation
    """
    original_dir = os.getcwd()
    os.chdir(month_dir)
    logger.debug(f"Processing {month_dir}")
    
    all_files = sorted([f for f in os.listdir() if f.startswith(f"{incr} FULL {archive_name}.7z.")])
    logger.debug(f"Relevant files for PAR2 creation: {all_files}")
    
    if strategy['subdirs'] == 1:
        create_par2_for_subdir(month_dir, "", archive_name, incr, strategy['par2_params'], logger)
    else:
        create_par2_with_subdirs(month_dir, archive_name, incr, all_files, strategy, logger)
    
    os.chdir(month_dir)
    logger.debug(f"Returned to directory: {os.getcwd()}")
    
    if strategy['create_overall_par']:
        create_overall_protection_layer(month_dir, archive_name, incr, all_files, strategy, logger)
    
    os.chdir(original_dir)
    logger.debug(f"Returned to original directory: {os.getcwd()}")

def create_par2_with_subdirs(base_dir: str, archive_name: str, incr: str, all_files: List[str], strategy: Dict, logger) -> None:
    """
    Create PAR2 files using subdirectories and symlinks, implementing an improved sliding window for large archives.
    """
    if strategy['use_sliding_window']:
        window_size = strategy['window_size']
        window_slide = strategy['window_slide']
        total_files = len(all_files)
        
        # Calculate the number of full windows
        num_full_windows = (total_files - window_size) // window_slide + 1
        
        for window_index in range(num_full_windows):
            window_start = window_index * window_slide
            window_end = window_start + window_size
            window_files = all_files[window_start:window_end]
            
            subdir = f"{incr} FULL {archive_name} {window_start:04d}-{window_end:04d}"
            create_subdir_and_symlinks(base_dir, subdir, window_files, logger)
            create_par2_for_subdir(base_dir, subdir, archive_name, incr, strategy['par2_params'], logger)
        
        # Handle the last window to ensure all remaining files are included
        if window_end < total_files:
            remaining_files = total_files - window_end
            if remaining_files <= window_slide:
                # Adjust the last full window to include the remaining files
                window_start = total_files - window_size
                window_end = total_files
            else:
                # Create a new window for the remaining files
                window_start = window_end
                window_end = total_files
            
            window_files = all_files[window_start:window_end]
            subdir = f"{incr} FULL {archive_name} {window_start:04d}-{window_end:04d}"
            create_subdir_and_symlinks(base_dir, subdir, window_files, logger)
            create_par2_for_subdir(base_dir, subdir, archive_name, incr, strategy['par2_params'], logger)
    else:
        # Original implementation for non-sliding window cases
        chunks_per_subdir = strategy['chunks_per_subdir']
        for subdir_index, chunk_start in enumerate(range(0, len(all_files), chunks_per_subdir), 1):
            chunk_end = min(chunk_start + chunks_per_subdir, len(all_files))
            subdir = f"{incr} FULL {archive_name} {chunk_start:04d}-{chunk_end:04d}"
            group_files = all_files[chunk_start:chunk_end]
            create_subdir_and_symlinks(base_dir, subdir, group_files, logger)
            create_par2_for_subdir(base_dir, subdir, archive_name, incr, strategy['par2_params'], logger)
    
    # Clean up symlinks after PAR2 creation
    cleanup_symlinks(base_dir, logger)

def create_par2_for_subdir(base_dir, subdir, archive_name, incr, par2_params, logger):
    dir_path = os.path.join(base_dir, subdir)
    logger.info(f"Creating PAR2 files for: {dir_path}")
    logger.debug(f"Current working directory before chdir: {os.getcwd()}")
    os.chdir(dir_path)
    logger.debug(f"Current working directory after chdir: {os.getcwd()}")
    
    par2_base_name = f"{incr} FULL {archive_name}" if subdir == "" else f"{subdir}"
    
    # List all relevant files
    relevant_files = sorted([f for f in os.listdir() if f.startswith(f"{incr} FULL {archive_name}.7z.")])
    logger.debug(f"Relevant files: {relevant_files}")
    
    # Construct the command as a list
    cmd = ["par2", "create"] + par2_params.split() + [par2_base_name] + relevant_files
    
    logger.debug(f"Executing PAR2 command: {' '.join(cmd)}")
    logger.debug(f"Environment variables: {os.environ}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=None)
        logger.info(f"PAR2 creation successful for {dir_path}")
        logger.debug(f"PAR2 output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"PAR2 creation failed for {dir_path}")
        logger.debug(f"Error output: {e.stderr}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
    
    par2_files = [f for f in os.listdir() if f.endswith('.par2')]
    if par2_files:
        logger.info(f"Created {len(par2_files)} PAR2 files")
    else:
        logger.warning(f"No PAR2 files were created for {dir_path}")
    
    os.chdir(base_dir)

def create_overall_protection_layer(base_dir: str, archive_name: str, incr: str, all_files: List[str], strategy: Dict, logger) -> None:
    logger.info("Creating overall protection layer")
    
    # Check if we're already in a '_ Month' directory
    if os.path.basename(base_dir) == '_ Month':
        month_dir = base_dir
    else:
        month_dir = os.path.join(base_dir, '_ Month')
    
    logger.debug(f"Attempting to use directory: {month_dir}")
    
    # Fallback to base_dir if '_ Month' doesn't exist
    if not os.path.exists(month_dir):
        logger.info(f"'_ Month' directory not found. Using base directory: {base_dir}")
        month_dir = base_dir

    try:
        os.chdir(month_dir)
        logger.debug(f"Successfully changed to directory: {os.getcwd()}")
    except Exception as e:
        logger.error(f"Failed to change directory to {month_dir}: {str(e)}")
        return
    
    par2_base_name = f"{incr} {archive_name} OVERALL"
 
    logger.debug(f"Files in directory: {os.listdir()}")
    
    # Search for matching files in the current directory
    matching_files = glob.glob(f'{incr}*.7z.*')
    logger.debug(f"Matching files: {matching_files}")
    
    if not matching_files:
        logger.warning(f"No matching files found for overall PAR creation in {month_dir}")
        return
    
    # Determine the correct strategy based on the number of chunks
    total_chunks = len(matching_files)
    if total_chunks <= 2:
        overall_par2_params = '-n4 -r30 -u -m2048'
    elif total_chunks <= 10:
        overall_par2_params = '-n8 -r25 -u -m4096'
    elif total_chunks <= 20:
        overall_par2_params = '-n16 -r15 -u -m6144'
    elif total_chunks <= 40:
        overall_par2_params = '-n24 -r12 -u -m8192'
    elif total_chunks <= 70:
        overall_par2_params = '-n32 -r10 -u -m10240'
    else:
        overall_par2_params = '-n40 -r8 -u -m12288'
    
    logger.debug(f"Using overall PAR2 parameters: {overall_par2_params}")
    
    # Split the par2 parameters
    par2_params = overall_par2_params.split()
    
    # Prepare the command
    par2_command = ["par2", "create"] + par2_params + [par2_base_name] + matching_files
    logger.debug(f"Executing overall PAR2 command: {' '.join(par2_command)}")
    
    try:
        result = subprocess.run(par2_command, capture_output=True, text=True, check=True)
        logger.info("Overall PAR2 creation successful")
        logger.debug(f"PAR2 output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error("Overall PAR2 creation failed")
        logger.debug(f"Error output: {e.stderr}")
    
    par2_files = [f for f in os.listdir()