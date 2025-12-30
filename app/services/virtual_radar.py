import pandas as pd
import numpy as np
import random
import os

class VirtualRadar:
    def __init__(self, data_lake_path: str):
        self.data_path = data_lake_path
        self.current_stream = None
        self.stream_index = 0

    def load_scenario(self, category: str):
        """
        Simulates connecting to a specific radar feed (Car/Drone/Human).
        Now searches recursively through all subfolders.
        """
        target_dir = os.path.join(self.data_path, category)
        
        # Check if the main category folder exists
        if not os.path.exists(target_dir):
            print(f"DEBUG: Could not find directory: {os.path.abspath(target_dir)}")
            return False, f"Scenario folder '{category}' not found."

        # --- RECURSIVE SEARCH FIX ---
        all_csv_files = []
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.lower().endswith('.csv'):
                    full_path = os.path.join(root, file)
                    all_csv_files.append(full_path)

        if not all_csv_files:
            return False, "No CSV data streams available in subfolders."

        # Pick one random file to simulate a "Live Session"
        selected_file = random.choice(all_csv_files)
        
        # Load the data into memory
        try:
            # Read CSV without header
            df = pd.read_csv(selected_file, header=None)
            
            # Extract only numbers
            self.current_stream = df.select_dtypes(include=[np.number]).values
            
            # Validation: Ensure data isn't empty
            if self.current_stream.size == 0:
                return False, "Selected data stream was empty."
                
            self.stream_index = 0
            return True, f"Connected to Stream: {os.path.basename(selected_file)}"
            
        except Exception as e:
            return False, f"Corrupt Data Stream: {str(e)}"
        
    def load_random_scenario(self):
        """
        Picks a file from ANY category (Car, Drone, or Human) at random.
        Returns: (Success, Message, True_Label)
        """
        categories = ["drone", "human", "car"]
        all_files = []
        
        # Gather every single CSV file we have
        for cat in categories:
            target_dir = os.path.join(self.data_path, cat)
            if os.path.exists(target_dir):
                for root, dirs, files in os.walk(target_dir):
                    for file in files:
                        if file.lower().endswith('.csv'):
                            # Store tuple: (path, actual_category)
                            all_files.append((os.path.join(root, file), cat))
        
        if not all_files:
            return False, "No data found in Data Lake.", None

        # Pick one at random
        selected_file, actual_category = random.choice(all_files)
        
        try:
            # Load it
            df = pd.read_csv(selected_file, header=None)
            self.current_stream = df.select_dtypes(include=[np.number]).values
            
            # Validation
            if self.current_stream.size == 0:
                return False, "Stream empty.", None
                
            self.stream_index = 0
            
            # Return success, but obscure the filename in the message so the user doesn't know!
            return True, "INTERCEPTING UNKNOWN SIGNAL SOURCE...", actual_category
            
        except Exception as e:
            return False, str(e), None

    def get_next_frame(self):
        """
        Returns the processed matrix for analysis.
        """
        if self.current_stream is None:
            return None

        matrix = self.current_stream
        
        # Normalize (Signal Processing Step)
        # Avoid division by zero
        min_val = np.min(matrix)
        max_val = np.max(matrix)
        
        if max_val - min_val == 0:
            matrix_norm = np.zeros_like(matrix)
        else:
            matrix_norm = (matrix - min_val) / (max_val - min_val)
        
        return matrix_norm

# Initialize
# We use os.getcwd() to ensure we find the folder relative to where you run the command
BASE_DIR = os.getcwd()
DATA_LAKE_PATH = os.path.join(BASE_DIR, "data_lake")
virtual_radar = VirtualRadar(DATA_LAKE_PATH)