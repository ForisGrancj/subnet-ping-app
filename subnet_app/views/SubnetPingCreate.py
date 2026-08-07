# subnet_app/views/SubnetPingCreate.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.cache import cache
from subnet_app.serializers.serializer import SubnetPingSerializer
from subnet_app.models.SubnetQueryLog import SubnetQueryLog
from subnet_app.tasks import process_subnet_ping


class SubnetPingCreateView(APIView):
    def post(self, request):
        serializer = SubnetPingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        raw_subnet = serializer.validated_data.get('subnet_value') or serializer.validated_data.get('subnet_input')

        if not raw_subnet:
            return Response(
                {"error": "Subnet parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        clean_subnet = raw_subnet.strip()
        cache_key = f"subnet_scan:{clean_subnet}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            existing_log = SubnetQueryLog.objects.filter(subnet_input=clean_subnet).last()
            log_id = existing_log.id if existing_log else "cache"
            return Response(
                {
                    "message": f"the subnet value is already exist with {log_id} id",
                    "source": "Redis Cache",
                    "data": cached_data
                },
                status=status.HTTP_200_OK
            )

        existing_log = SubnetQueryLog.objects.filter(subnet_input=clean_subnet).last()
        if existing_log:
            results = list(existing_log.results.values('ip_address', 'is_active', 'rtt'))
            if results:
                cache.set(cache_key, results, timeout=3600)

            return Response(
                {
                    "message": f"the subnet value is already exist with {existing_log.id}",
                    "source": "Database Fallback"
                },
                status=status.HTTP_200_OK
            )

        # 3. Step 3: Neither Cache nor DB contains it -> Create record using 'subnet_input'
        new_log = SubnetQueryLog.objects.create(
            subnet_input=clean_subnet,  # Match model field name
            status="PENDING"
        )
        process_subnet_ping.delay(new_log.id, clean_subnet)

        return Response(
            {
                "message": "Subnet ping task created successfully.",
                "id": new_log.id
            },
            status=status.HTTP_201_CREATED
        )