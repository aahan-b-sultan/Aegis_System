import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers, models, applications, optimizers, callbacks
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.utils import class_weight
import pickle
import random
import multiprocessing

# --- HARDWARE OPTIMIZATION (CPU MAX) ---
# 1. Force CPU Mode (Disable GPU to avoid conflicts)
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# 2. Configure Threading for i7-13700HX
# We use the number of physical cores for operations
num_cores = multiprocessing.cpu_count()
tf.config.threading.set_inter_op_parallelism_threads(num_cores)
tf.config.threading.set_intra_op_parallelism_threads(num_cores)

print(f"🚀 CPU TURBO MODE: Active")
print(f"🧠 Detected {num_cores} Logical Cores. Optimizing for AVX2 instructions.")

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_LAKE = os.path.join(BASE_DIR, "data_lake")
MODEL_DIR = os.path.join(BASE_DIR, "ai_models")

IMG_SIZE = (224, 224) 
BATCH_SIZE = 32  # Standard batch size for CPU
EPOCHS = 25

os.makedirs(MODEL_DIR, exist_ok=True)

# --- STEP 1: GATHER FILE PATHS (Do not load data yet) ---
print("📂 Indexing Data Lake...")
file_paths = []
labels = []

for label in ["car", "human", "drone"]:
    class_path = os.path.join(DATA_LAKE, label)
    if not os.path.exists(class_path): continue
    
    for root, _, filenames in os.walk(class_path):
        for f in filenames:
            if f.lower().endswith('.csv'):
                file_paths.append(os.path.join(root, f))
                labels.append(label)

# Shuffle
temp = list(zip(file_paths, labels))
random.shuffle(temp)
file_paths, labels = zip(*temp)
file_paths = list(file_paths)
labels = list(labels)

print(f"✅ Indexed {len(file_paths)} files.")

# --- STEP 2: ENCODE LABELS ---
le = LabelEncoder()
labels_encoded = le.fit_transform(labels)

# Save Encoder
with open(os.path.join(MODEL_DIR, "label_encoder.pkl"), "wb") as f:
    pickle.dump(le, f)

# Calculate Class Weights
class_weights = class_weight.compute_class_weight(
    class_weight='balanced',
    classes=np.unique(labels_encoded),
    y=labels_encoded
)
class_weight_dict = dict(enumerate(class_weights))

# Split Paths (Not Data)
train_paths, val_paths, train_labels, val_labels = train_test_split(
    file_paths, labels_encoded, test_size=0.2, random_state=42
)

# --- STEP 3: THE HIGH-PERFORMANCE PIPELINE ---

def load_and_process_file(path_tensor, label_tensor):
    """
    This function runs in parallel on multiple CPU cores.
    """
    def _process(path):
        path = path.decode('utf-8')
        try:
            df = pd.read_csv(path, header=None)
            matrix = df.select_dtypes(include=[np.number]).values
            
            # Normalize
            matrix_norm = (matrix - np.min(matrix)) / (np.max(matrix) - np.min(matrix) + 1e-6)
            
            # Resize (Using TF for speed)
            tensor = tf.image.resize(matrix_norm[..., np.newaxis], IMG_SIZE)
            
            # RGB
            tensor_rgb = tf.image.grayscale_to_rgb(tensor)
            return tensor_rgb
        except:
            # Return a blank image on error to prevent crash
            return tf.zeros((IMG_SIZE[0], IMG_SIZE[1], 3))

    # Wrap Python code into TensorFlow graph
    image = tf.numpy_function(_process, [path_tensor], tf.float32)
    image.set_shape([IMG_SIZE[0], IMG_SIZE[1], 3])
    return image, label_tensor

def create_dataset(paths, labels, is_training=True):
    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    
    # PARALLEL LOADING: This is the magic.
    # num_parallel_calls=AUTOTUNE means TF decides how many CPU cores to use.
    ds = ds.map(load_and_process_file, num_parallel_calls=tf.data.AUTOTUNE)
    
    if is_training:
        ds = ds.shuffle(buffer_size=1000)
    
    ds = ds.batch(BATCH_SIZE)
    
    # PREFETCH: Prepare the next batch while the current one is training
    ds = ds.prefetch(buffer_size=tf.data.AUTOTUNE)
    return ds

print("⚙️ Building Data Pipelines...")
train_ds = create_dataset(train_paths, train_labels, is_training=True)
val_ds = create_dataset(val_paths, val_labels, is_training=False)

# --- STEP 4: MODEL ---
print("🏗️ Building ResNet50V2...")

base_model = applications.ResNet50V2(
    include_top=False, 
    weights='imagenet', 
    input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3)
)
base_model.trainable = False 

model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dropout(0.4),
    layers.Dense(256, activation='relu'),
    layers.Dropout(0.3),
    layers.Dense(len(le.classes_), activation='softmax')
])

optimizer = optimizers.Adam(learning_rate=0.001)
model.compile(optimizer=optimizer, loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# --- STEP 5: TRAIN ---
print(f"🧠 Training Started on i7-13700HX...")
history = model.fit(
    train_ds,
    epochs=EPOCHS,
    validation_data=val_ds,
    class_weight=class_weight_dict,
    callbacks=[
        callbacks.EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True)
    ]
)

# Save
model.save(os.path.join(MODEL_DIR, "radar_model.h5"))
print(f"🏆 SUCCESS: High-Performance CPU Model saved.")