from django.shortcuts import render
import requests
from io import BytesIO
from PIL import Image
import tensorflow as tf
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image as keras_image
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ImageURLSerializer

model_path = 'scenary_classification_model'
img_height = 150  # Replace with the height used during training
img_width = 150   # Replace with the width used during training
class_names = ['buildings', 'forest', 'glacier', 'mountain', 'sea', 'street']

def download_image(image_url):
    response = requests.get(image_url)
    response.raise_for_status()  # Check if the download was successful
    return Image.open(BytesIO(response.content))

def classify_image(image_url, model_path, img_height, img_width, class_names):
    model = load_model(model_path)

    # Download and preprocess the image
    img = download_image(image_url)
    img = img.resize((img_width, img_height))
    img_array = keras_image.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)  # Create a batch

    # Make predictions
    predictions = model.predict(img_array)
    score = tf.nn.softmax(predictions[0])
    predicted_class = class_names[np.argmax(score)]
    confidence = 100 * np.max(score)
    return predicted_class, confidence


class ImageClassifierView(APIView):
    def post(self, request):
        serializer = ImageURLSerializer(data=request.data)
        if serializer.is_valid():
            image_url = serializer.validated_data['image_url']
            predicted_class, confidence = classify_image(image_url, model_path, img_height, img_width, class_names)
            result = f"This image most likely belongs to {predicted_class} with a {confidence:.2f} percent confidence."
            return Response({'result': result}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)           
