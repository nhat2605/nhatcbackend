from django.shortcuts import render
import requests
from io import BytesIO
from PIL import Image
import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image as keras_image
from tensorflow import keras
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ImageURLSerializer
import json

model_path = '/home/lamduynhatle/nhatcbackend/image_classifier_api/scenary_classification_model'
img_height = 150  # Replace with the height used during training
img_width = 150   # Replace with the width used during training
class_names = ['buildings', 'forest', 'glacier', 'mountain', 'sea', 'street']

def download_image(image_url):
    response = requests.get(image_url)
    response.raise_for_status()  # Check if the download was successful
    return Image.open(BytesIO(response.content))

def classify_image(image_url, model_dir, img_height, img_width, class_names):
    # Assume download_image is a function that downloads and returns an image given a URL
    img = download_image(image_url)  # You need to define this function or import it if not already done
    img = img.resize((img_width, img_height))
    img_array = keras_image.img_to_array(img)
    img_array = np.expand_dims(img_array, 0)  # Create a batch

    # Adjustments for TFSMLayer
    model_layer = keras.layers.TFSMLayer(model_dir, call_endpoint='serving_default')
    inputs = keras.Input(shape=(img_height, img_width, 3))  # Adjust the input shape as necessary
    outputs = model_layer(inputs)
    model = keras.Model(inputs=inputs, outputs=outputs)

    # Make predictions
    predictions = model.predict(img_array)
    # Access the 'outputs' key in the predictions dictionary
    predictions_array = predictions['outputs']
    score = tf.nn.softmax(predictions_array[0])  # Now applying softmax correctly
    predicted_class = class_names[np.argmax(score)]
    confidence = 100 * np.max(score)
    return predicted_class, confidence

class ImageClassifierView(APIView):
    def post(self, request):
        # Attempt to extract and parse the '_content' key if present
        raw_content = request.data.get('_content')
        if raw_content:
            try:
                # Parse the JSON-formatted string from '_content'
                parsed_content = json.loads(raw_content)
                image_url = parsed_content.get('image_url')
            except json.JSONDecodeError:
                # If parsing fails, return a 400 Bad Request response
                return Response({'error': "Invalid JSON format in request."},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            # Fallback to directly accessing 'image_url' in case '_content' is not used
            image_url = request.data.get('image_url')

        if image_url:  # Check if image_url is not None or empty
            # Assuming classify_image is defined elsewhere and properly imported
            predicted_class, confidence = classify_image(image_url, model_path, img_height, img_width, class_names)
            result = f"This image most likely belongs to {predicted_class} with a {confidence:.2f} percent confidence."
            return Response({'result': result}, status=status.HTTP_200_OK)
        else:
            # If image_url is missing or empty, return a 400 Bad Request response
            return Response({'error': "The 'image_url' field is required."}, status=status.HTTP_400_BAD_REQUEST)

class TestView(APIView):
    def get(self,request):
        return Response({'result': "hello"}, status=status.HTTP_200_OK)

