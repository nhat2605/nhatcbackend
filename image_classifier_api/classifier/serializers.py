from rest_framework import serializers

class ImageURLSerializer(serializers.Serializer):
     image_url = serializers.URLField() 