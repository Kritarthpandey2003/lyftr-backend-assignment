metrics_store = {
    "http_requests_total": {},
    "webhook_requests_total": {}
}

def increment_http_request(path: str, status: int):
    key = (path, str(status))
    metrics_store["http_requests_total"][key] = metrics_store["http_requests_total"].get(key, 0) + 1

def increment_webhook_result(result: str):
    metrics_store["webhook_requests_total"][result] = metrics_store["webhook_requests_total"].get(result, 0) + 1

def generate_metrics_text():
    lines = []
    for (path, status), count in metrics_store["http_requests_total"].items():
        lines.append(f'http_requests_total{{path="{path}", status="{status}"}} {count}')
    for result, count in metrics_store["webhook_requests_total"].items():
        lines.append(f'webhook_requests_total{{result="{result}"}} {count}')
    return "\n".join(lines)