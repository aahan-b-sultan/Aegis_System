import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle
import random

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Root of Aegis_System_Pro
DATA_LAKE = os.path.join(BASE_DIR, "data_lake")
MODEL_DIR = os.path.join(BASE_DIR, "ai_models")
IMG_SIZE = (128, 128)

# Ensure output directory exists
os.makedirs(MODEL_DIR, exist_ok=True)

def process_csv(file_path):
    """Reads a CSV from the nested Kaggle structure and converts to Image Tensor."""
    try:
        # Read CSV (No header, assuming Kaggle RAD-DAR format)
        df = pd.read_csv(file_path, header=None)
        
        # Select numbers only
        matrix = df.select_dtypes(include=[np.number]).values
        if matrix.shape[0] == 0 or matrix.shape[1] == 0: return None

        # Normalize (0 to 1)
        matrix_norm = (matrix - np.min(matrix)) / (np.max(matrix) - np.min(matrix) + 1e-5)
        
        # Resize to 128x128 (Standard AI Input)
        tensor = tf.image.resize(matrix_norm[..., np.newaxis], IMG_SIZE)
        return tensor
    except Exception as e:
        return None

# --- MAIN LOGIC ---
print(f"🚀 Starting Enterprise Training Sequence...")
print(f"📂 Scanning Data Lake: {DATA_LAKE}")

# 1. Recursive Data Loading
class_data = {}
all_labels = []

# Scan for folders (car, human, drone)
for label in ["car", "human", "drone"]:
    class_path = os.path.join(DATA_LAKE, label)
    if not os.path.exists(class_path):
        print(f"⚠️ Warning: Folder '{label}' not found in data_lake.")
        continue
    
    # Recursive search for CSVs
    files = []
    for root, dirs, filenames in os.walk(class_path):
        for f in filenames:
            if f.lower().endswith('.csv'):
                files.append(os.path.join(root, f))
    
    if files:
        class_data[label] = files
        print(f"   found {len(files)} raw files for class: {label.upper()}")
    else:
        print(f"   ❌ No CSV files found for {label}")

# 2. Balancing (Undersampling)
if not class_data:
    print("❌ Critical Error: No data found. Check your folder names.")
    exit()

min_samples = min([len(f) for f in class_data.values()])
# Limit to 1000 max to save time (Optional: remove this min() wrapper to use all data)
target_count = min(min_samples, 1000) 

print(f"⚖️  Balancing dataset to {target_count} samples per class...")

X = []
y = []

for label, file_list in class_data.items():
    # Shuffle and pick target_count
    selected_files = random.sample(file_list, target_count)
    
    print(f"   Processing {label}...")
    for f in selected_files:
        tensor = process_csv(f)
        if tensor is not None:
            X.append(tensor)
            y.append(label)

X = np.array(X)
y = np.array(y)

print(f"✅ Training Data Ready. Shape: {X.shape}")

# 3. Encode Labels
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Save Encoder
encoder_path = os.path.join(MODEL_DIR, "label_encoder.pkl")
with open(encoder_path, "wb") as f:
    pickle.dump(le, f)
print(f"💾 Saved Label Encoder to {encoder_path}")

# 4. Train Model
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

model = models.Sequential([
    layers.Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 1)),
    layers.Conv2D(32, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Flatten(),
    layers.Dense(128, activation='relu'),
    layers.Dense(len(le.classes_), activation='softmax')
])

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

print("🧠 Training Neural Network...")
model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_test, y_test))

# 5. Save Model
model_path = os.path.join(MODEL_DIR, "radar_model.h5")
model.save(model_path)
print(f"🎉 SUCCESS: AI Model saved to {model_path}")