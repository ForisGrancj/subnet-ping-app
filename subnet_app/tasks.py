import ipaddress
from celery import shared_task
from django.core.cache import cache
from icmplib import ping
from subnet_app.models.PingResultLog import PingResultLog

@shared_task
def process_subnet_ping_task(query_log_id,subnet_str):

    network = ipaddress.ip_network(subnet_str)

    cache_result=[]
    ping_objects =[]

    for ip in network:
        ip_str = str(ip)

        try:
            host_result = ping(ip_str, count=1, timeout=1, privileged=False)
            is_active = host_result.is_alive
        except Exception as e:
            print(f"Ping error for {ip_str}: {e}")
            is_active=False

        ping_objects.append(
            PingResultLog(
                query_log_id=query_log_id,
                ip_address=ip_str,
                is_active=is_active
            )
        )

        cache_result.append({
            "ip":ip_str,
            "is_active":is_active,
        })

    PingResultLog.objects.bulk_create(ping_objects)
    cache_key= f"subnet_logs_{query_log_id}"
    cache.set(cache_key,cache_result,timeout=3600)
    return f"For {subnet_str} ping scanning completed"
