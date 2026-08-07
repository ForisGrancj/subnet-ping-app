import ipaddress
from rest_framework import serializers
from subnet_app.models.SubnetQueryLog import SubnetQueryLog
from subnet_app.models.PingResultLog import PingResultLog

class SubnetPingSerializer(serializers.Serializer):
    subnet_value = serializers.CharField(max_length=50)

    def validate_subnet_value(self, value):

        try:
            network = ipaddress.ip_network(value, strict=False)
        except ValueError:
            raise serializers.ValidationError("Invalid IPv4 or IPv6 address!")

        if network.version == 4 and network.prefixlen < 24:
            raise serializers.ValidationError("For entered IPv4, the subnet mask prefix length must be 24 or greater.")

        if network.version == 6 and network.prefixlen < 64:
            raise serializers.ValidationError("For entered IPv6, the subnet mask prefix length must be 64 or greater.")

        return str(network)

class PingResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PingResultLog
        fields = ['query_log','ip_address', 'is_active', 'checked_at','rtt']

class SubnetQueryLogSerializer(serializers.ModelSerializer):
    results = PingResultSerializer(many=True, read_only=True)
    class Meta:
        model= SubnetQueryLog
        fields = ['id','subnet_input', 'created_at','status', 'results']