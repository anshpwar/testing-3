"""Small helpers for JSON endpoints."""
import json

from django.http import JsonResponse


def read_json(request):
    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None
    return body if isinstance(body, dict) else None


def error(code, status=400, detail=""):
    payload = {"error": code}
    if detail:
        payload["detail"] = detail
    return JsonResponse(payload, status=status)
