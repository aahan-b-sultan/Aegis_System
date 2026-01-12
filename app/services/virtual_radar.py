import pandas as pd
import numpy as np
import random
import os
import io

class VirtualRadar:
    def __init__(self, data_lake_path: str):
        self.data_path = data_lake_path
        self.full_stream = None # Stores the massive full CSV
        self.stream_index = 0   # Current position in the file
        self.window_size = 128  # Width of the view (Time steps)
        self.step_size = 4      # Speed of scroll (Higher = Faster)
        
        # THIS IS THE NEW VARIABLE WE NEED
        self.current_filename = "System_Idle" 

    def get_current_filename(self):
        """Returns the name of the file currently being streamed."""
        return self.current_filename

    def load_scenario(self, category: str):
        return self._load_file_generic(category)

    def load_random_scenario(self):
        return self._load_file_generic(None)

    def _load_file_generic(self, category=None):
        """Helper to find and load a file."""
        if category:
            search_dir = os.path.join(self.data_path, category)
        else:
            search_dir = self.data_path # Search everywhere

        if not os.path.exists(search_dir):
            return False, f"Directory not found.", None

        # Recursive search
        all_csvs = []
        for root, _, files in os.walk(search_dir):
            for file in files:
                if file.lower().endswith('.csv'):
                    # Save path and the parent folder name as the label
                    label = os.path.basename(os.path.dirname(root))
                    if category: label = category # Force label if specific category requested
                    all_csvs.append((os.path.join(root, file), label))

        if not all_csvs:
            return False, "No data streams found.", None

        selected_file, true_label = random.choice(all_csvs)

        try:
            # Load the FULL recording
            df = pd.read_csv(selected_file, header=None)
            self.full_stream = df.select_dtypes(include=[np.number]).values
            
            # Reset pointer
            self.stream_index = 0
            
            # Validation: Repeat if too short
            if self.full_stream.shape[1] < self.window_size:
                repeats = (self.window_size // self.full_stream.shape[1]) + 2
                self.full_stream = np.tile(self.full_stream, (1, repeats))

            # --- UPDATE THE FILENAME HERE ---
            self.current_filename = os.path.basename(selected_file)
            
            return True, f"Stream Active: {self.current_filename}", true_label

        except Exception as e:
            return False, str(e), None

    def inject_external_data(self, file_bytes, filename):
        import io
        try:
            decoded_file = io.StringIO(file_bytes.decode("utf-8"))
            
            # 1. Try reading with no header first
            df = pd.read_csv(decoded_file, header=None)
            
            # 2. Check if first row is text (Header detection)
            if df.iloc[0].apply(lambda x: isinstance(x, str)).any():
                # Reload with header
                decoded_file.seek(0)
                df = pd.read_csv(decoded_file)
            
            # 3. Extract ONLY numbers
            self.full_stream = df.select_dtypes(include=[np.number]).values
            
            # 4. Check shape (Crucial for ResNet)
            # If data is transposed (Time x Freq instead of Freq x Time), flip it
            if self.full_stream.shape[0] > self.full_stream.shape[1]:
                # Assume Time is the long axis, so we want (Freq, Time)
                self.full_stream = self.full_stream.T

            # Reset
            self.stream_index = 0
            
            # Validation
            if self.full_stream.shape[1] < self.window_size:
                repeats = (self.window_size // self.full_stream.shape[1]) + 2
                self.full_stream = np.tile(self.full_stream, (1, repeats))
                
            self.current_filename = f"External_{filename}"
            return True, f"External Feed Active: {filename}", "UNKNOWN"
            
        except Exception as e:
            return False, f"Upload Failed: {str(e)}", None

    def get_next_frame(self):
        """
        Returns a SLICE of the data (The Sliding Window).
        """
        if self.full_stream is None:
            return None

        # Calculate Window Coordinates
        start = self.stream_index
        end = start + self.window_size
        
        # Check if we reached the end of the recording
        total_time_steps = self.full_stream.shape[1]
        
        if end >= total_time_steps:
            # LOOP BACK to the start (Infinite Playback)
            self.stream_index = 0
            start = 0
            end = self.window_size

        # SLICE THE DATA
        frame = self.full_stream[:, start:end]

        # Move the pointer forward
        self.stream_index += self.step_size

        # Normalize Frame
        min_val = np.min(frame)
        max_val = np.max(frame)
        if max_val - min_val == 0:
            frame_norm = np.zeros_like(frame)
        else:
            frame_norm = (frame - min_val) / (max_val - min_val)

        return frame_norm

# Init
BASE_DIR = os.getcwd()
DATA_LAKE_PATH = os.path.join(BASE_DIR, "data_lake")
virtual_radar = VirtualRadar(DATA_LAKE_PATH)