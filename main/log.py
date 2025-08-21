import logging
import shutil
import datetime
from datetime import timedelta
import os

# Create a folder for log files if it doesn't exist
log_folder = 'log'
if not os.path.exists(log_folder):
  os.makedirs(log_folder)

# Create a logger
logger = logging.getLogger('mystyle')
logger.setLevel(logging.DEBUG)

# Create a console handler and set the level to DEBUG
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

def setup_directories(directories): 
    logger.info("Managing files and folders...")
    # Create directories if they don't exist
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"Folder created: {dir_path}")
        else:
            logger.info(f"Folder already exists: {dir_path}")
    return directories
    
    
def delete_log(directory, days_to_keep):
    logger.info(f"Deleting folders from {directory} , days_to_keep is {days_to_keep}")  
    try:
        # Ensure the specified directory is inside the current working directory
        if not os.path.isabs(directory):
            directory = os.path.join(os.getcwd(), directory)

        if not directory.startswith(os.getcwd()):
            raise ValueError("The specified directory must be inside the current working directory.")

        # Calculate the date threshold for deletion
        threshold_date = datetime.datetime.now() - timedelta(days=days_to_keep)

        # List folders in the directory
        folders_to_delete = [
            folder
            for folder in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, folder))
            and parse_date_from_foldername(folder) is not None
            and parse_date_from_foldername(folder) < threshold_date.date()
        ]      

        if not folders_to_delete:
            logger.warning(f"No folders to delete older then  last {days_to_keep} days.\n {' ' * 34}")
        else:
            # Delete folders
            for folder_name in folders_to_delete:
                folder_path = os.path.join(directory, folder_name)
                shutil.rmtree(folder_path)
                logger.info(f"Deleted folder: {folder_path}")

            logger.info(f"Deletion process is finished. Folders that are older than {days_to_keep} days have been successfully removed\n {' ' * 34}")           
        
        
    except Exception as e:
        logger.error(f"Error deleting folders: {e}")

def parse_date_from_foldername(folder_name):    
  
    try:
        return datetime.datetime.strptime(folder_name, "%Y%m%d").date()
    except ValueError:
        return None

# Example usage:
# delete_old_folders("your_directory", 7)  # Delete folders older than 7 days


def initiate_log(script_name):
  # Create a file handler with a filename that includes the timestamp
  timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
  
  # Get the current date and the previous day
  current_date = datetime.datetime.now()   
  current_directory = os.getcwd()   
    
  script_folder = os.path.join(log_folder, script_name)     
  date_folder = os.path.join(script_folder, current_date.strftime("%Y%m%d"))
  
  # Create a list of directory paths
  directories = [script_folder,date_folder]
  setup_directories(directories)
  #delete_log(script_folder, 7)
   
  log_file_name = os.path.join(date_folder, f'mystyle_{script_name}_{timestamp}.log')
  
  fh = logging.FileHandler(log_file_name)
  fh.setLevel(logging.DEBUG)

  # Create a formatter and attach it to the handlers
  formatter = logging.Formatter('%(asctime)s  %(levelname)s: %(message)s')
  ch.setFormatter(formatter)
  fh.setFormatter(formatter)

  # Add a header line to the formatter
  header = '----- Log Header -----'
  formatted_header = formatter.format(logging.LogRecord(None, None, '', 0, 'header', (), None, None))
  formatter._fmt = f"{formatted_header}\n%(asctime)s  %(levelname)s: %(message)s"

  # Add the handlers to the logger
  logger.addHandler(ch)
  logger.addHandler(fh)  
  return None

class ExcludeFilter(logging.Filter):
    def filter(self, record):
        # Exclude log messages containing specific phrases
        return '*****************' not in record.getMessage()       
        
def show_logo(script_name):
    initiate_log(script_name)
    
    # Temporarily modify the formatter to exclude timestamp and log level
    original_formatter = ch.formatter
    ch.setFormatter(logging.Formatter('%(message)s'))

    # Pepoc ASCII art
    art = """
  __  ____     _______ _________     ___      ______ 
 |  \/  \ \   / / ____|__   __\ \   / / |    |  ____|
 | \  / |\ \_/ / (___    | |   \ \_/ /| |    | |__   
 | |\/| | \   / \___ \   | |    \   / | |    |  __|  
 | |  | |  | |  ____) |  | |     | |  | |____| |____ 
 |_|  |_|  |_| |_____/   |_|     |_|  |______|______|
                                                     
    """
    logger.info(art)

    # Restore the original formatter
    ch.setFormatter(original_formatter)
    
    

        
        

