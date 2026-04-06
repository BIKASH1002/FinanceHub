import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response

from utilities.utils import convert_data, get_response_format

from .helpers import create_transaction_category, update_transaction_category, get_transaction_categories, \
    create_transaction_record, update_transaction_record, get_transaction_records, get_transaction_record_detail, \
    delete_transaction_record

logger = logging.getLogger(__name__)


@api_view(['POST'])
def createtransactioncategory(request):
    response = get_response_format()

    if request.method == "POST":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)
            name = post_data.get("name", None)
            description = post_data.get("description", None)
            transaction_type = post_data.get("transaction_type", None)

            response = create_transaction_category({
                "loggedin_username": loggedin_username.strip().lower() if loggedin_username else None,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
                "name": name,
                "description": description,
                "transaction_type": transaction_type,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['POST'])
def updatetransactioncategory(request):
    response = get_response_format()

    if request.method == "POST":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)
            category_id = post_data.get("category_id", None)
            name = post_data.get("name", None)
            description = post_data.get("description", None)
            transaction_type = post_data.get("transaction_type", None)
            is_active = post_data.get("is_active", None)

            response = update_transaction_category({
                "loggedin_username": loggedin_username.strip().lower() if loggedin_username else None,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
                "category_id": category_id,
                "name": name,
                "description": description,
                "transaction_type": transaction_type,
                "is_active": is_active,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['GET'])
def gettransactioncategories(request):
    response = get_response_format()

    if request.method == "GET":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)
            transaction_type = post_data.get("transaction_type", None)

            response = get_transaction_categories({
                "loggedin_username": loggedin_username.strip().lower() if loggedin_username else None,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
                "transaction_type": transaction_type,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['POST'])
def createtransactionrecord(request):
    response = get_response_format()

    if request.method == "POST":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)
            title = post_data.get("title", None)
            amount = post_data.get("amount", None)
            transaction_type = post_data.get("transaction_type", None)
            category_id = post_data.get("category_id", None)
            transaction_date = post_data.get("transaction_date", None)
            description = post_data.get("description", None)

            response = create_transaction_record({
                "loggedin_username": loggedin_username.strip().lower() if loggedin_username else None,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
                "title": title,
                "amount": amount,
                "transaction_type": transaction_type,
                "category_id": category_id,
                "transaction_date": transaction_date,
                "description": description,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['POST'])
def updatetransactionrecord(request):
    response = get_response_format()

    if request.method == "POST":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)
            transaction_id = post_data.get("transaction_id", None)
            title = post_data.get("title", None)
            amount = post_data.get("amount", None)
            transaction_type = post_data.get("transaction_type", None)
            category_id = post_data.get("category_id", None)
            transaction_date = post_data.get("transaction_date", None)
            description = post_data.get("description", None)

            response = update_transaction_record({
                "loggedin_username": loggedin_username.strip().lower() if loggedin_username else None,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
                "transaction_id": transaction_id,
                "title": title,
                "amount": amount,
                "transaction_type": transaction_type,
                "category_id": category_id,
                "transaction_date": transaction_date,
                "description": description,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['GET'])
def gettransactionrecords(request):
    response = get_response_format()

    if request.method == "GET":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)
            page = post_data.get("page", 1)
            page_size = post_data.get("page_size", 10)
            transaction_type = post_data.get("transaction_type", None)
            category_id = post_data.get("category_id", None)
            start_date = post_data.get("start_date", None)
            end_date = post_data.get("end_date", None)
            search = post_data.get("search", None)

            response = get_transaction_records({
                "loggedin_username": loggedin_username.strip().lower() if loggedin_username else None,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
                "page": page,
                "page_size": page_size,
                "transaction_type": transaction_type,
                "category_id": category_id,
                "start_date": start_date,
                "end_date": end_date,
                "search": search,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['GET'])
def gettransactionrecorddetail(request):
    response = get_response_format()

    if request.method == "GET":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)
            transaction_id = post_data.get("transaction_id", None)

            response = get_transaction_record_detail({
                "loggedin_username": loggedin_username.strip().lower() if loggedin_username else None,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
                "transaction_id": transaction_id,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['POST'])
def deletetransactionrecord(request):
    response = get_response_format()

    if request.method == "POST":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)
            transaction_id = post_data.get("transaction_id", None)

            response = delete_transaction_record({
                "loggedin_username": loggedin_username.strip().lower() if loggedin_username else None,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
                "transaction_id": transaction_id,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)