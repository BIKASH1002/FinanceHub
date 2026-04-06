import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response

from utilities.utils import convert_data, get_response_format
from .helpers import get_dashboard_summary, get_category_wise_summary, get_monthly_transaction_trend, \
    get_recent_transaction_activity, get_transaction_audit_logs

logger = logging.getLogger(__name__)


@api_view(['GET'])
def getdashboardsummary(request):
    response = get_response_format()

    if request.method == "GET":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)
            start_date = post_data.get("start_date", None)
            end_date = post_data.get("end_date", None)

            response = get_dashboard_summary({
                "loggedin_username": loggedin_username.strip().lower() if loggedin_username else None,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
                "start_date": start_date,
                "end_date": end_date,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['GET'])
def getcategorywisesummary(request):
    response = get_response_format()

    if request.method == "GET":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)
            start_date = post_data.get("start_date", None)
            end_date = post_data.get("end_date", None)
            transaction_type = post_data.get("transaction_type", None)

            response = get_category_wise_summary({
                "loggedin_username": loggedin_username.strip().lower() if loggedin_username else None,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
                "start_date": start_date,
                "end_date": end_date,
                "transaction_type": transaction_type,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['GET'])
def getmonthlytransactiontrend(request):
    response = get_response_format()

    if request.method == "GET":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)
            year = post_data.get("year", None)
            transaction_type = post_data.get("transaction_type", None)

            response = get_monthly_transaction_trend({
                "loggedin_username": loggedin_username.strip().lower() if loggedin_username else None,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
                "year": year,
                "transaction_type": transaction_type,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['GET'])
def getrecenttransactionactivity(request):
    response = get_response_format()

    if request.method == "GET":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)
            limit = post_data.get("limit", 5)

            response = get_recent_transaction_activity({
                "loggedin_username": loggedin_username.strip().lower() if loggedin_username else None,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
                "limit": limit,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['GET'])
def gettransactionauditlogs(request):
    response = get_response_format()

    if request.method == "GET":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)
            transaction_id = post_data.get("transaction_id", None)
            page = post_data.get("page", 1)
            page_size = post_data.get("page_size", 10)

            response = get_transaction_audit_logs({
                "loggedin_username": loggedin_username.strip().lower() if loggedin_username else None,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
                "transaction_id": transaction_id,
                "page": page,
                "page_size": page_size,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)