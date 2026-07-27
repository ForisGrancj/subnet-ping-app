import ipaddress
from rest_framework import serializers
from subnet_app.models.SubnetQueryLog import SubnetQueryLog
from subnet_app.models.PingResultLog import PingResultLog

class SubnetPingSerializer(serializers.Serializer):
    subnet = serializers.CharField(max_length=50)

    def validate_subnet(self, value):
        try:
            network = ipaddress.ip_network(value, strict=False)
        except ValueError:
            raise serializers.ValidationError("Invalid IPv4 and IPv6 address!")
        if network.version == 4 and network.prefixlen <24:
            raise serializers.ValidationError("For entered Ipv4 the max subnet mask value should be less than 24")
        if network.version == 6 and network.prefixlen <64:
            raise serializers.ValidationError("For entered Ipv6 the max subnet mask value should be less than 64")
        return str(network)

class PingResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PingResultLog
        fields = ['ip_address', 'is_active', 'checked_at']

class SubnetQueryLogSerializer(serializers.ModelSerializer):
    results = PingResultSerializer(many=True, read_only=True)
    class Meta:
        model= SubnetQueryLog
        fields = ['id', 'subnet_input', 'created_at', 'results']