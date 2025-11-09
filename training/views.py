from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import TrainingModule
from .serializers import TrainingModuleSerializer

class TrainingModuleViewSet(viewsets.ModelViewSet):
    queryset = TrainingModule.objects.all().order_by('-created_at')
    serializer_class = TrainingModuleSerializer

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        module = self.get_object()
        module.status = 'archived'
        module.save()
        return Response({'message': 'Module archived successfully'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        module = self.get_object()
        module.status = 'draft'
        module.save()
        return Response({'message': 'Module restored successfully'}, status=status.HTTP_200_OK)
# Create your views here.
