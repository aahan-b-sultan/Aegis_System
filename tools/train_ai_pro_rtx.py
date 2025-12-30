import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks, applications, optimizers, mixed_precision
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.utils import class_weight
import pickle
import random

# --- HARDWARE CONFIGURATION ---
# 1. Try to enable Mixed Precision (Saves VRAM on RTX cards)
try:
    mixed_precision.set_global_policy('mixed_float16')
    print("✅ Mixed Precision Enabled (16-bit float)")
except:
    print("⚠️ Mixed Precision unavailable, using standard 32-bit.")

# 2. Configure GPU Memory Growth (Prevents immediate crash on 6GB cards)
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print(f"🚀 GPU DETECTED: {len(gpus)} device(s). Ready for Training.")
    except RuntimeError as e:
        print(e)
else:
    print("⚡ GPU not detected (or CUDA missing). Switching to High-Performance CPU Mode (i7-13700HX).")

# --- PROJECT CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_LAKE = os.path.join(BASE_DIR, "data_lake")
MODEL_DIR = os.path.join(BASE_DIR, "ai_models")

# RESNET STANDARD RESOLUTION
IMG_SIZE = (224, 224) 
# 16 is safe for 6GB VRAM. If on CPU, you could go higher, but 16 is safe for both.
BATCH_SIZE = 16  
EPOCHS = 30 

os.makedirs(MODEL_DIR, exist_ok=True)

def process_csv_pro(file_path):
    """
    Reads CSV -> Normalize -> Resize (224x224) -> RGB Convert
    """
    try:
        df = pd.read_csv(file_path, header=None)
        matrix = df.select_dtypes(include=[np.number]).values
        if matrix.size == 0: return None

        # Normalize (Robust Min-Max)
        matrix_norm = (matrix - np.min(matrix)) / (np.max(matrix) - np.min(matrix) + 1e-6)
        
        # Resize to 224x224 (ResNet Requirement)
        tensor = tf.image.resize(matrix_norm[..., np.newaxis], IMG_SIZE)
        
        # Convert Grayscale (1 channel) to RGB (3 channels) by duplicating
        tensor_rgb = tf.image.grayscale_to_rgb(tensor)
        
        return tensor_rgb
    except Exception:
        return None

# --- MAIN LOGIC ---
print(f"📂 Scanning Data Lake...")

X = []
y = []

# RAM SAFETY: Limit files so your 16GB RAM doesn't overflow before training starts
# 2500 files per class * 3 classes = 7500 images (approx 4-5GB RAM)
MAX_FILES_PER_CLASS = 2500 

for label in ["car", "human", "drone"]:
    class_path = os.path.join(DATA_LAKE, label)
    if not os.path.exists(class_path): continue
    
    files = []
    for root, _, filenames in os.walk(class_path):
        for f in filenames:
            if f.lower().endswith('.csv'):
                files.append(os.path.join(root, f))
    
    # Shuffle and Limit
    random.shuffle(files)
    if len(files) > MAX_FILES_PER_CLASS:
        print(f"   ⚠️ Limiting {label} to {MAX_FILES_PER_CLASS} samples (RAM Safety).")
        files = files[:MAX_FILES_PER_CLASS]
    
    print(f"   Loading {len(files)} files for {label.upper()}...")
    
    for f in files:
        tensor = process_csv_pro(f)
        if tensor is not None:
            X.append(tensor)
            y.append(label)

X = np.array(X)
y = np.array(y)

print(f"✅ Training Data Ready. Shape: {X.shape}")

# Encode Labels
le = LabelEncoder()
y_encoded = le.fit_transform(y)
with open(os.path.join(MODEL_DIR, "label_encoder.pkl"), "wb") as f:
    pickle.dump(le, f)

# Compute Class Weights (To handle any remaining imbalance)
class_weights = class_weight.compute_class_weight(
    class_weight='balanced',
    classes=np.unique(y_encoded),
    y=y_encoded
)
class_weight_dict = dict(enumerate(class_weights))

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

# --- MODEL ARCHITECTURE (RESNET50V2) ---
print("🏗️ Building ResNet50V2 Architecture...")

base_model = applications.ResNet50V2(
    include_top=False, 
    weights='imagenet', 
    input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3)
)

# Freezing Strategy:
# Freeze the base to keep the "ImageNet" knowledge.
# Unfreezing on a laptop can be unstable if learning rate isn't perfect.
base_model.trainable = False 

model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dropout(0.4), # High dropout to prevent overfitting
    layers.Dense(256, activation='relu'),
    layers.Dropout(0.3),
    # Note: dtype='float32' is required in the final layer when using Mixed Precision
    layers.Dense(len(le.classes_), activation='softmax', dtype='float32') 
])

optimizer = optimizers.Adam(learning_rate=0.001)

model.compile(optimizer=optimizer, loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# --- TRAINING ---
print("🧠 Starting Training Sequence...")
history = model.fit(
    X_train, y_train,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    validation_data=(X_test, y_test),
    class_weight=class_weight_dict,
    callbacks=[
        # Stop if accuracy doesn't improve for 5 epochs
        callbacks.EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True, verbose=1),
        # Slow down learning rate if loss gets stuck
        callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, verbose=1)
    ]
)

# Save
model_path = os.path.join(MODEL_DIR, "radar_model.h5")
model.save(model_path)
print(f"🏆 SUCCESS: Pro Model (ResNet50) saved to {model_path}")