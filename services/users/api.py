from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from utilities.utils import convert_data, get_response_format
from utilities.utils import convert_data, get_response_format
from utilities.constants import ROLE_CLIENT, SIGNUP_TYPE_SELF
from .helpers import login_user

import logging

from .helpers import register_user, verify_email_otp, login_user, create_user_session, validate_user_session, \
    logout_user, create_user_by_admin, get_users_list

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    response = get_response_format()

    if request.method == "POST":
        post_data = convert_data(request.body)

        if post_data:
            username = post_data.get("username", None)
            email = post_data.get("email", None)
            password = post_data.get("password", None)
            first_name = post_data.get("first_name", None)
            middle_name = post_data.get("middle_name", None)
            last_name = post_data.get("last_name", None)
            phone_number = post_data.get("phone_number", None)

            response = register_user({
                "username": username.strip().lower() if username else None,
                "email": email,
                "password": password,
                "first_name": first_name,
                "middle_name": middle_name,
                "last_name": last_name,
                "phone_number": phone_number,
                "role_code": ROLE_CLIENT,
                "signup_type": SIGNUP_TYPE_SELF,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['POST'])
@permission_classes([AllowAny])
def verifyotp(request):
    response = get_response_format()

    if request.method == "POST":
        post_data = convert_data(request.body)

        if post_data:
            username = post_data.get("username", None)
            otp = post_data.get("otp", None)

            response = verify_email_otp({
                "username": username.strip().lower() if username else None,
                "otp": otp,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    response_data = {}
    token = None

    if request.method == "POST":
        post_data = convert_data(request.body)

        if post_data:
            username = post_data.get("username", None)
            password = post_data.get("password", None)

            token = login_user({
                "username": username.strip().lower() if username else None,
                "password": password
            })

            if token:
                response_data["key"] = token
            else:
                response_data["error"] = "Invalid username or password"
                return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)
        else:
            response_data["error"] = "Unable to decode data."
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    return Response(response_data)


@api_view(['POST'])
def createsession(request):
    response = get_response_format()

    if request.method == "POST":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            device_ip = post_data.get("device_ip", None)
            device_info = post_data.get("device_info", None)

            response = create_user_session({
                "username": loggedin_username,
                "auth_token": auth_token,
                "device_ip": device_ip,
                "device_info": device_info,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['POST'])
def validatesession(request):
    response = get_response_format()

    if request.method == "POST":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)

            response = validate_user_session({
                "username": loggedin_username,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['POST'])
def logout(request):
    response = get_response_format()

    if request.method == "POST":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)

            response = logout_user({
                "username": loggedin_username,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['POST'])
def createuserbyadmin(request):
    response = get_response_format()

    if request.method == "POST":
        post_data = convert_data(request.body)

        if post_data:
            loggedin_username = request.user.username
            auth_token = str(request.auth)
            session_id = post_data.get("session_id", None)
            device_token = post_data.get("device_token", None)
            username = post_data.get("username", None)
            email = post_data.get("email", None)
            password = post_data.get("password", None)
            first_name = post_data.get("first_name", None)
            middle_name = post_data.get("middle_name", None)
            last_name = post_data.get("last_name", None)
            phone_number = post_data.get("phone_number", None)
            role_code = post_data.get("role_code", None)

            response = create_user_by_admin({
                "loggedin_username": loggedin_username.strip().lower() if loggedin_username else None,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
                "username": username.strip().lower() if username else None,
                "email": email,
                "password": password,
                "first_name": first_name,
                "middle_name": middle_name,
                "last_name": last_name,
                "phone_number": phone_number,
                "role_code": role_code,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)


@api_view(['GET'])
def getusers(request):
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

            response = get_users_list({
                "loggedin_username": loggedin_username,
                "auth_token": auth_token,
                "session_id": session_id,
                "device_token": device_token,
                "page": page,
                "page_size": page_size,
            })
        else:
            response["success"] = False
            response["errors"].append("Unable to decode data.")
            response["error_code"] = 100406

    return Response(response)