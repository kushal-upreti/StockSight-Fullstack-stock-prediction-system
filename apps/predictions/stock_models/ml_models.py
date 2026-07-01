import os
from django.conf import settings
from tensorflow.keras.models import load_model

MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "apps",
    "predictions",
    "stock_models",
    "tesla_model.keras"
)

model = load_model(MODEL_PATH)

def get_model():
    return model