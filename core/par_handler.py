import os
import subprocess
import math
import shutil
from typing import List, Dict

def determine_par_strategy(total_chunks: int) -> Dict:
    """
    Determine the optimal PAR2 creation strategy based on the number of chunks.
    
    :param total_chunks: Total number of chunks in the archive
    :return: Dictionary containing PAR2 strategy parameters
    """
    if total_chunks <= 10:
        return {
            'subdirs': 1,
            'chunks_per_subdir': total_chunks,
            'par2_params': '-n8 -r20 -u -m4096',  # Small archives (≤10 chunks): High redundancy (20%) because the total size is small, so we can afford more protection without significant space impact.
            'use_sliding_window': False,
            'create_overall_par': False
        }
    elif total_chunks <= 30:
        return {
            'subdirs': math.ceil(total_chunks / 10),
            'chunks_per_subdir': 10,
            'par2_params': '-n16 -r15 -u -m8192',  # 15% for subdirectories to provide strong local protection
            'use_sliding_window': False,
            'create_overall_par': True,
            'overall_par2_params': '-n24 -r10 -u -m12288'  # Increased to 10% redundancy for overall to provide an additional layer of protection without too much overhead
        }
    elif total_chunks <= 50:
        return {
            'subdirs': math.ceil(total_chunks / 10),
            'chunks_per_subdir': 10,
            'par2_params': '-n24 -r15 -u -m8192',  # 15% for subdirectories to provide strong local protection
            'use_sliding_window': False,
            'create_overall_par': True,
            'overall_par2_params': '-n32 -r8 -u -m12288'  # 8% redundancy for overall to provide an additional layer of protection without too much overhead
        }
    else:
        return {
            'subdirs': math.ceil(total_chunks / 40),
            'chunks_per_subdir': 40,
            'par2_params': '-n32 -r15 -u -m10240',  # 15% for subdirectories to provide strong local protection
            'use_sliding_window': True,
            'window_size': 40,
            'window_slide': 10,
            'create_overall_par': True,
            'overall_par2_params': '-n40 -r5 -u -m12288'  # Keeping 5% for very large archives for overall to provide an additional layer of protection without too much overhead
        }

def create_par2_files(month_dir: str, archive_name: str, incr: str, total_chunks: int, logger) -> None:
    """
    Create PAR2 files for the given archive using an optimized strategy.
    
    :param month_dir: Directory containing the chunks for the month
    :param archive_name: Name of the archive
    :param incr: Increment value (usually date in YYMMDD format)
    :param total_chunks: Total number of chunks in the archive
    :param logger: Logger object for logging messages
    """
    original_dir = os.getcwd()
    os.chdir(month_dir)
    logger.debug(f"Processing {month_dir}")
    
    strategy = determine_par_strategy(total_chunks)
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
    Create PAR2 files using subdirectories and symlinks.
    """
    for subdir_index in range(1, strategy['subdirs'] + 1):
        subdir = f"{incr} FULL {archive_name} {subdir_index:02d}"
        subdir_path = os.path.join(base_dir, subdir)
        os.makedirs(subdir_path, exist_ok=True)
        
        start_index = (subdir_index - 1) * strategy['chunks_per_subdir']
        end_index = min(subdir_index * strategy['chunks_per_subdir'], len(all_files))
        group_files = all_files[start_index:end_index]
        
        for file in group_files:
            try:
                source_path = os.path.join(base_dir, file)
                link_path = os.path.join(subdir_path, file)
                os.symlink(source_path, link_path)
                logger.debug(f"Created symlink for {file} in {subdir_path}")
            except Exception as e:
                logger.error(f"Error creating symlink for {file}: {str(e)}")
        
        create_par2_for_subdir(base_dir, subdir, archive_name, incr, strategy['par2_params'], logger)

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
    """
    Create an overall protection layer PAR2 file for the entire archive.
    """
    logger.info("Creating overall protection layer")
    os.chdir(base_dir)
    logger.debug(f"Current working directory: {os.getcwd()}")
    
    par2_base_name = f"{incr} FULL {archive_name} OVERALL"
    par2_create = f"par2 create {strategy['overall_par2_params']} \"{par2_base_name}\" {incr}\\ FULL\\ {archive_name}.7z.*"
    logger.debug(f"Executing overall PAR2 command: {par2_create}")
    
    result = subprocess.run(par2_create, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("Overall PAR2 creation failed")
        logger.debug(f"Error output: {result.stderr}")
    else:
        logger.info("Overall PAR2 creation successful")
    
    par2_files = [f for f in os.listdir() if f.endswith('.par2') and 'OVERALL' in f]
    if par2_files:
        logger.info(f"Created {len(par2_files)} overall PAR2 files")
    else:
        logger.warning("No overall PAR2 files were created")

def get_relevant_chunks(base_dir: str, archive_name: str, target_date: str, logger) -> List[str]:
    """
    Get all relevant chunks for the given archive and date.
    
    :param base_dir: Base directory of the archive
    :param archive_name: Name of the archive
    :param target_date: Target date in YYMMDD format
    :param logger: Logger object for logging messages
    :return: List of relevant chunk filenames
    """
    all_files = os.listdir(base_dir)
    logger.debug(f"All files in {base_dir}: {all_files}")
    
    relevant_files = [f for f in all_files if f.startswith(f"{target_date} FULL {archive_name}.7z.")]
    logger.debug(f"Relevant files found: {relevant_files}")
    return sorted(relevant_files)

def process_archive(base_dir: str, archive_name: str, incr: str, logger) -> None:
    """
    Process an entire archive, determining chunk count and creating PAR2 files.
    
    :param base_dir: Base directory of the archive
    :param archive_name: Name of the archive
    :param incr: Increment value (date in YYMMDD format)
    :param logger: Logger object for logging messages
    """
    os.chdir(base_dir)
    logger.info(f"Processing archive: {archive_name}")
    logger.debug(f"Base directory: {base_dir}")
    
    relevant_chunks = get_relevant_chunks(base_dir, archive_name, incr, logger)
    total_chunks = len(relevant_chunks)
    
    logger.info(f"Total relevant chunks: {total_chunks}")
    logger.debug(f"Chunks included: {', '.join(relevant_chunks)}")
    
    month_dir = os.path.join(base_dir, "_ Month")
    os.makedirs(month_dir, exist_ok=True)
    
    for chunk in relevant_chunks:
        source_path = os.path.join(base_dir, chunk)
        dest_path = os.path.join(month_dir, chunk)
        if os.path.exists(source_path):
            if not os.path.exists(dest_path):
                try:
                    shutil.move(source_path, dest_path)
                    logger.debug(f"Moved {chunk} to {month_dir}")
                except Exception as e:
                    logger.error(f"Error moving {chunk}: {str(e)}")
            else:
                logger.debug(f"{chunk} already exists in {month_dir}")
        else:
            logger.warning(f"Chunk file not found: {source_path}")
    
    if not os.listdir(month_dir):
        logger.error(f"No chunks were moved to {month_dir}. Aborting PAR2 creation.")
        return
    
    create_par2_files(month_dir, archive_name, incr, total_chunks, logger)