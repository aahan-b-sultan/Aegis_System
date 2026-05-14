import sys
import os
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
import pickle
import random

# Fix Path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.core.config import settings

# Setup
MODEL_PATH = settings.MODEL_PATH
DATA_LAKE = os.path.join(BASE_DIR, "data_lake")
IMG_SIZE = (224, 224)

def process_file(filepath):
    try:
        df = pd.read_csv(filepath, header=None)
        matrix = df.select_dtypes(include=[np.number]).values
        # Normalize
        matrix_norm = (matrix - np.min(matrix)) / (np.max(matrix) - np.min(matrix) + 1e-6)
        # Resize
        tensor = tf.image.resize(matrix_norm[..., np.newaxis], IMG_SIZE)
        tensor_rgb = tf.image.grayscale_to_rgb(tensor)
        return tensor_rgb, matrix_norm # Return both tensor and raw matrix
    except:
        return None, None

def generate_visuals():
    print("📊 Loading Resources...")
    
    # 1. Load Model & Encoder
    model = tf.keras.models.load_model(MODEL_PATH)
    with open(settings.LABEL_ENCODER_PATH, "rb") as f:
        le = pickle.load(f)
    
    classes = le.classes_
    print(f"✅ Classes Found: {classes}")

    # 2. Gather Test Data (Random 100 files per class)
    X_test = []
    y_true = []
    
    print("📂 Gathering Test Data from Data Lake...")
    for label in classes:
        folder = os.path.join(DATA_LAKE, label.lower()) # Assuming folder names match labels
        if not os.path.exists(folder):
            # Try mapping caps if needed, or just skip
            continue
            
        files = []
        for root, _, filenames in os.walk(folder):
            for f in filenames:
                if f.endswith('.csv'):
                    files.append(os.path.join(root, f))
        
        # Pick random sample
        sample_files = random.sample(files, min(len(files), 50))
        
        for f in sample_files:
            tensor, _ = process_file(f)
            if tensor is not None:
                X_test.append(tensor)
                y_true.append(label)

    X_test = np.array(X_test)
    print(f"✅ Processing {len(X_test)} samples for Confusion Matrix...")

    # 3. Predict
    preds = model.predict(X_test)
    y_pred_indices = np.argmax(preds, axis=1)
    y_pred_labels = [classes[i] for i in y_pred_indices]

    # --- GENERATE GRAPH 1: CONFUSION MATRIX ---
    print("🎨 Drawing Confusion Matrix...")
    cm = confusion_matrix(y_true, y_pred_labels, labels=classes)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
    plt.title('AEGIS AI Classification Performance')
    plt.ylabel('Actual Ground Truth')
    plt.xlabel('AI Prediction')
    plt.savefig('Confusion_Matrix.png', dpi=300)
    print("📸 Saved: Confusion_Matrix.png")

    # --- GENERATE GRAPH 2: SAMPLE SPECTROGRAM ---
    print("🎨 Drawing Sample Spectrogram...")
    # Just grab the last processed file
    sample_file = sample_files[0]
    _, raw_matrix = process_file(sample_file)
    
    plt.figure(figsize=(10, 4))
    plt.imshow(raw_matrix.T, aspect='auto', cmap='inferno', origin='lower')
    plt.colorbar(label='Signal Amplitude (dB)')
    plt.title(f'Micro-Doppler Spectrogram Input ({classes[0]})')
    plt.xlabel('Time Frames')
    plt.ylabel('Frequency Bins')
    plt.savefig('Sample_Spectrogram.png', dpi=300)
    print("📸 Saved: Sample_Spectrogram.png")

if __name__ == "__main__":
    generate_visuals()