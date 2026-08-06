import ipaddress
from celery import shared_task
from django.core.cache import cache
from icmplib import ping

from subnet_app.models.SubnetQueryLog import SubnetQueryLog
from subnet_app.models.PingResultLog import PingResultLog


@shared_task
def process_subnet_ping(query_id, subnet_value):

    clean_subnet = subnet_value.strip()
    cache_key = f"subnet_scan:{clean_subnet}"

    try:
        query_log = SubnetQueryLog.objects.get(id=query_id)
    except SubnetQueryLog.DoesNotExist:
        return {"error": f"SubnetQueryLog with id {query_id} not found."}


    cached_results = cache.get(cache_key)
    if cached_results is not None:
        _save_ping_results(query_log, cached_results)
        query_log.status = "COMPLETED"
        query_log.save()
        return {
            "query_id": query_id,
            "subnet": clean_subnet,
            "source": "cache",
            "results_count": len(cached_results)
        }

    query_log.status = "PROCESSING"
    query_log.save()

    scan_results = []
    network = ipaddress.ip_network(clean_subnet, strict=False)

    for host in network.hosts():
        host_ip = str(host)

        try:
            host_result = ping(host_ip, count=1, timeout=1, privileged=False)
            is_active = host_result.is_alive
            rtt = host_result.avg_rtt if is_active else None
        except Exception:
            is_active = False
            rtt = None

        scan_results.append({
            "ip_address": host_ip,
            "is_active": is_active,
            "rtt": rtt
        })


    cache.set(cache_key, scan_results, timeout=3600)
    _save_ping_results(query_log, scan_results)
    query_log.status = "COMPLETED"
    query_log.save()

    return {
        "query_id": query_id,
        "subnet": clean_subnet,
        "source": "scanned",
        "results_count": len(scan_results)
    }

def _save_ping_results(query_log, results):
    ping_log_objects = [
        PingResultLog(
            query_log=query_log,
            ip_address=item["ip_address"],
            is_active=item.get("is_active", False),
            rtt=item.get("rtt")
        )
        for item in results
    ]
    PingResultLog.objects.bulk_create(ping_log_objects)