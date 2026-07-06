import tensorflow as tf
import numpy as np
import pickle
import os
from collections import deque
from app.core.config import settings

class AIEngine:
    _instance = None
    model = None
    encoder = None
    
    # NEW: A memory buffer to smooth out predictions
    # Stores the last 5 predictions to prevent "flickering"
    prediction_buffer = deque(maxlen=5)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIEngine, cls).__new__(cls)
            cls._instance.load_resources()
        return cls._instance

    def load_resources(self):
        print(f"🔧 [AI ENGINE] Loading PRO Model from: {settings.MODEL_PATH}")
        if os.path.exists(settings.MODEL_PATH) and os.path.exists(settings.LABEL_ENCODER_PATH):
            try:
                self.model = tf.keras.models.load_model(settings.MODEL_PATH)
                with open(settings.LABEL_ENCODER_PATH, "rb") as f:
                    self.encoder = pickle.load(f)
                print("✅ [AI ENGINE] Systems Online (ResNet50 Smoothed).")
            except Exception as e:
                print(f"❌ [AI ENGINE] Critical Failure: {e}")
                self.model = None
        else:
            print("⚠️ [AI ENGINE] Model files not found.")

    @tf.function(reduce_retracing=True)
    def _tf_predict(self, matrix_norm):
        # 1. Add channel dimension
        tensor = tf.expand_dims(matrix_norm, axis=-1)
        # 2. Resize to 224x224
        tensor = tf.image.resize(tensor, (224, 224))
        # 3. Convert Grayscale to RGB
        tensor_rgb = tf.image.grayscale_to_rgb(tensor)
        # 4. Add Batch Dimension
        input_tensor = tf.expand_dims(tensor_rgb, axis=0)
        # 5. Inference
        return self.model(input_tensor, training=False)

    def predict(self, matrix_norm):
        if self.model is None:
            return {"label": "SYSTEM_OFFLINE", "confidence": 0.0, "is_threat": False}

        try:
            # Execute compiled graph
            preds = self._tf_predict(matrix_norm).numpy()
            
            # --- SMOOTHING LOGIC ---
            # Add current probabilities to buffer
            self.prediction_buffer.append(preds[0])
            
            # Calculate average probability across last 5 frames
            avg_preds = np.mean(self.prediction_buffer, axis=0)
            
            # Use the AVERAGE for the final decision
            idx = np.argmax(avg_preds)
            label = self.encoder.inverse_transform([idx])[0]
            confidence = float(np.max(avg_preds) * 100)
            
            # Threat Logic
            is_threat = "drone" in label.lower()

            return {
                "label": label.upper(),
                "confidence": round(confidence, 2),
                "is_threat": is_threat,
                "raw_probs": avg_preds.tolist()
            }
        except Exception as e:
            print(f"Prediction Error: {e}")
            return {"label": "ERROR", "confidence": 0.0, "is_threat": False}

# Global instance
ai_engine = AIEngine()