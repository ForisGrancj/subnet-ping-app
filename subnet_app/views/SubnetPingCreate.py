from rest_framework import generics, status
from rest_framework.response import Response

from subnet_app.models.SubnetQueryLog import SubnetQueryLog
from subnet_app.serializers.serializer import SubnetPingSerializer
from subnet_app.tasks import process_subnet_ping_task

class SubnetPingCreateView(generics.CreateAPIView):

    serializer_class = SubnetPingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subnet_str = serializer.validated_data['subnet']
        
        query_log = SubnetQueryLog.objects.create(subnet_input=subnet_str)

        process_subnet_ping_task.delay(query_log.id, subnet_str)

        return Response({
            "message": "The ping process has been added to the queue and initiated.",
            "query_id": query_log.id,
            "subnet": subnet_str
        }, status=status.HTTP_202_ACCEPTED)


