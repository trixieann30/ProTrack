from rest_framework import serializers
from .models import TrainingModule

class TrainingModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingModule
        fields = '__all__'
