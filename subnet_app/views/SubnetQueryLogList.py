from rest_framework import generics, status
from rest_framework.response import Response
from django.core.cache import cache

from subnet_app.models.SubnetQueryLog import SubnetQueryLog
from subnet_app.serializers.serializer import SubnetQueryLogSerializer


class SubnetQueryLogListView(generics.ListAPIView):
    queryset = SubnetQueryLog.objects.all().order_by('-created_at')
    serializer_class = SubnetQueryLogSerializer

    def list(self, request, *args, **kwargs):
        subnet_param = request.query_params.get('subnet') or request.query_params.get('subnet_value')
        query_id = request.query_params.get('query_id') or request.query_params.get('query_value')

        if query_id:
            try:
                log_obj = (
                    SubnetQueryLog.objects
                    .prefetch_related('results')
                    .get(id=query_id)
                )
                serializer = self.get_serializer(log_obj)
                return Response({
                    "source": "Database",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            except SubnetQueryLog.DoesNotExist:
                return Response(
                    {"error": f"{query_id} There no such an ID"},
                    status=status.HTTP_404_NOT_FOUND
                )
        if subnet_param:
            clean_subnet = subnet_param.strip()
            cache_key = f"subnet_scan:{clean_subnet}"
            cached_data = cache.get(cache_key)

            if cached_data:
                return Response({
                    "source": "Redis Cache",
                    "subnet": clean_subnet,
                    "results": cached_data
                }, status=status.HTTP_200_OK)

        response = super().list(request, *args, **kwargs)

        return Response({
            "source": "Database",
            "data": response.data
        }, status=status.HTTP_200_OK)