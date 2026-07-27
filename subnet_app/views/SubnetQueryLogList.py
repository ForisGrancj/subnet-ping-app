from rest_framework import generics, status
from rest_framework.response import Response
from django.core.cache import cache

from subnet_app.models.SubnetQueryLog import SubnetQueryLog
from subnet_app.serializers.serializer import SubnetQueryLogSerializer

class SubnetQueryLogListView(generics.ListAPIView):
    queryset = SubnetQueryLog.objects.all().order_by('-created_at')
    serializer_class = SubnetQueryLogSerializer

    def list(self, request, *args, **kwargs):
        query_id = request.query_params.get('query_id')

        if query_id:
            cache_key = f"subnet_logs_{query_id}"
            cached_data = cache.get(cache_key)

            if cached_data:
                return Response({
                    "source": "Redis Cache",
                    "query_id": query_id,
                    "results": cached_data
                }, status=status.HTTP_200_OK)

        response = super().list(request, *args, **kwargs)

        return Response({
            "source": "Database",
            "data": response.data
        }, status=status.HTTP_200_OK)