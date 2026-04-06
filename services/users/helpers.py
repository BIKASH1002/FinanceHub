import random
import uuid
import secrets
import logging
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from rest_framework_simplejwt.tokens import RefreshToken

from utilities.utils import get_response_format
from utilities.constants import ROLE_CLIENT, ROLE_ADMIN, ROLE_ANALYST, SIGNUP_TYPE_ADMIN, SIGNUP_TYPE_SELF
from .models import Role, UserProfile, UserAuthToken, UserSession, EmailOTP

logger = logging.getLogger(__name__)


def register_user(user_info):
    response = get_response_format()

    user_obj = None
    role_obj = None
    profile_obj = None
    email_otp_obj = None

    username_user_obj = None
    email_user_obj = None

    if user_info["username"]:
        try:
            username_user_obj = User.objects.get(username=user_info["username"])
        except Exception as e:
            logger.info("User not found with same username.", str(e))

    if user_info["email"]:
        try:
            email_user_obj = User.objects.get(email=user_info["email"])
        except Exception as e:
            logger.info("User not found with same email.", str(e))

    try:
        role_obj = Role.objects.get(role_code=user_info["role_code"], is_active=True)
    except Exception as e:
        logger.error("Role not found.", str(e))

    if user_info["username"] and user_info["email"] and user_info["password"] and \
       user_info["first_name"] and user_info["last_name"] and user_info["role_code"]:

        if not role_obj:
            response["success"] = False
            response["errors"].append("Role not found.")
            response["error_code"] = 100404

        elif username_user_obj and email_user_obj and username_user_obj.id != email_user_obj.id:
            response["success"] = False
            response["errors"].append("Username and email belong to different users.")
            response["error_code"] = 100402

        else:
            if username_user_obj:
                user_obj = username_user_obj
            elif email_user_obj:
                user_obj = email_user_obj

            if user_obj:
                try:
                    profile_obj = UserProfile.objects.get(user=user_obj)
                except Exception as e:
                    logger.error("User profile not found.", str(e))

                if user_obj.is_active and profile_obj and profile_obj.email_verified:
                    response["success"] = False
                    response["errors"].append("Username or email already exists.")
                    response["error_code"] = 100402

                else:
                    try:
                        user_obj.username = user_info["username"]
                        user_obj.email = user_info["email"]
                        user_obj.set_password(user_info["password"])
                        user_obj.is_active = False
                        user_obj.save()
                    except Exception as e:
                        logger.error("User update failed.", str(e), user_info)
                        response["success"] = False
                        response["errors"].append("User update failed.")
                        response["error_code"] = 100405

                    if user_obj:
                        if profile_obj:
                            try:
                                profile_obj.role = role_obj
                                profile_obj.first_name = user_info["first_name"]
                                profile_obj.middle_name = user_info["middle_name"]
                                profile_obj.last_name = user_info["last_name"]
                                profile_obj.phone_number = user_info["phone_number"]
                                profile_obj.signup_type = user_info["signup_type"]
                                profile_obj.email_verified = False
                                profile_obj.phone_verified = False
                                profile_obj.is_active = True
                                profile_obj.save()
                            except Exception as e:
                                logger.error("User profile update failed.", str(e), user_info)
                                response["success"] = False
                                response["errors"].append("User profile update failed.")
                                response["error_code"] = 100406
                        else:
                            try:
                                profile_obj = UserProfile(
                                    user=user_obj,
                                    role=role_obj,
                                    first_name=user_info["first_name"],
                                    middle_name=user_info["middle_name"],
                                    last_name=user_info["last_name"],
                                    phone_number=user_info["phone_number"],
                                    signup_type=user_info["signup_type"],
                                    email_verified=False,
                                    phone_verified=False,
                                    is_active=True
                                )
                                profile_obj.save()
                            except Exception as e:
                                logger.error("User profile save failed.", str(e), user_info)
                                response["success"] = False
                                response["errors"].append("User profile not created.")
                                response["error_code"] = 100406

                    if user_obj and len(response["errors"]) == 0:
                        try:
                            EmailOTP.objects.filter(
                                user=user_obj,
                                email=user_info["email"],
                                is_verified=False
                            ).update(expires_at=timezone.now())
                        except Exception as e:
                            logger.error("Previous OTP expiry update failed.", str(e))

                        otp = str(random.randint(100000, 999999))
                        expires_at = timezone.now() + timedelta(minutes=10)

                        try:
                            email_otp_obj = EmailOTP(
                                user=user_obj,
                                email=user_info["email"],
                                otp=otp,
                                expires_at=expires_at
                            )
                            email_otp_obj.save()
                        except Exception as e:
                            logger.error("OTP save failed.", str(e), user_info)
                            response["success"] = False
                            response["errors"].append("OTP not generated.")
                            response["error_code"] = 100407

                        if email_otp_obj:
                            try:
                                send_mail(
                                    subject="Email Verification OTP",
                                    message=f"Your OTP is {otp}. It is valid for 10 minutes.",
                                    from_email=settings.DEFAULT_FROM_EMAIL,
                                    recipient_list=[user_info["email"]],
                                    fail_silently=False,
                                )
                            except Exception as e:
                                logger.error("OTP mail send failed.", str(e), user_info)
                                response["success"] = False
                                response["errors"].append("OTP email not sent.")
                                response["error_code"] = 100408

                        if email_otp_obj and len(response["errors"]) == 0:
                            response["success"] = True
                            response["data"]["user_info"] = {
                                "username": user_obj.username,
                                "email": user_obj.email,
                                "otp_sent": True,
                                "is_new_user": False
                            }

            else:
                try:
                    user_obj = User.objects.create_user(
                        username=user_info["username"],
                        email=user_info["email"],
                        password=user_info["password"]
                    )
                    user_obj.is_active = False
                    user_obj.save()
                except Exception as e:
                    logger.error("User save failed.", str(e), user_info)
                    response["success"] = False
                    response["errors"].append("User not created.")
                    response["error_code"] = 100405

                if user_obj:
                    try:
                        profile_obj = UserProfile(
                            user=user_obj,
                            role=role_obj,
                            first_name=user_info["first_name"],
                            middle_name=user_info["middle_name"],
                            last_name=user_info["last_name"],
                            phone_number=user_info["phone_number"],
                            signup_type=user_info["signup_type"],
                            is_active=True
                        )
                        profile_obj.save()
                    except Exception as e:
                        logger.error("User profile save failed.", str(e), user_info)
                        response["success"] = False
                        response["errors"].append("User profile not created.")
                        response["error_code"] = 100406

                if user_obj and profile_obj:
                    otp = str(random.randint(100000, 999999))
                    expires_at = timezone.now() + timedelta(minutes=10)

                    try:
                        email_otp_obj = EmailOTP(
                            user=user_obj,
                            email=user_info["email"],
                            otp=otp,
                            expires_at=expires_at
                        )
                        email_otp_obj.save()
                    except Exception as e:
                        logger.error("OTP save failed.", str(e), user_info)
                        response["success"] = False
                        response["errors"].append("OTP not generated.")
                        response["error_code"] = 100407

                    if email_otp_obj:
                        try:
                            send_mail(
                                subject="Email Verification OTP",
                                message=f"Your OTP is {otp}. It is valid for 10 minutes.",
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[user_info["email"]],
                                fail_silently=False,
                            )
                        except Exception as e:
                            logger.error("OTP mail send failed.", str(e), user_info)
                            response["success"] = False
                            response["errors"].append("OTP email not sent.")
                            response["error_code"] = 100408

                    if email_otp_obj and len(response["errors"]) == 0:
                        response["success"] = True
                        response["data"]["user_info"] = {
                            "username": user_obj.username,
                            "email": user_obj.email,
                            "otp_sent": True,
                            "is_new_user": True
                        }
    else:
        response["success"] = False
        response["errors"].append("Invalid input, required fields not provided.")
        response["error_code"] = 100401

    return response


def verify_email_otp(otp_info):
    response = get_response_format()

    user_obj = None
    otp_obj = None
    profile_obj = None

    if otp_info["username"] and otp_info["otp"]:
        try:
            user_obj = User.objects.get(username=otp_info["username"])
        except Exception as e:
            logger.error("User not found.", str(e))

        if user_obj:
            try:
                otp_obj = EmailOTP.objects.filter(
                    user=user_obj,
                    otp=otp_info["otp"],
                    is_verified=False
                ).latest("created_at")
            except Exception as e:
                logger.error("OTP not found.", str(e))

            if otp_obj:
                if timezone.now() > otp_obj.expires_at:
                    response["success"] = False
                    response["errors"].append("OTP expired.")
                    response["error_code"] = 100410
                else:
                    try:
                        otp_obj.is_verified = True
                        otp_obj.save()
                    except Exception as e:
                        logger.error("OTP verification save failed.", str(e))

                    try:
                        user_obj.is_active = True
                        user_obj.save()
                    except Exception as e:
                        logger.error("User activation failed.", str(e))

                    try:
                        profile_obj = UserProfile.objects.get(user=user_obj)
                    except Exception as e:
                        logger.error("User profile not found.", str(e))

                    if profile_obj:
                        try:
                            profile_obj.email_verified = True
                            profile_obj.save()
                        except Exception as e:
                            logger.error("Profile email verification update failed.", str(e))

                    response["success"] = True
                    response["data"]["user_info"] = {
                        "username": user_obj.username,
                        "email_verified": True,
                        "account_active": True
                    }
            else:
                response["success"] = False
                response["errors"].append("Invalid OTP.")
                response["error_code"] = 100409
        else:
            response["success"] = False
            response["errors"].append("User not found.")
            response["error_code"] = 100404
    else:
        response["success"] = False
        response["errors"].append("Invalid input, required fields not provided.")
        response["error_code"] = 100401

    return response


def login_user(login_info):
    token = None
    user = None
    auth_token_obj = None

    if login_info["username"] and login_info["password"]:
        user = authenticate(
            username=login_info["username"],
            password=login_info["password"]
        )

        if user:
            try:
                refresh = RefreshToken.for_user(user)
                token = str(refresh.access_token)
            except Exception as e:
                logger.error("JWT token generation failed.", str(e), login_info)

            if token:
                try:
                    auth_token_obj = UserAuthToken.objects.filter(
                        user=user,
                        token=token,
                        is_active=True
                    ).first()
                except Exception as e:
                    logger.error("Existing token lookup failed.", str(e))

                if not auth_token_obj:
                    try:
                        auth_token_obj = UserAuthToken(
                            user=user,
                            token=token,
                            expires_at=timezone.now() + timedelta(hours=24),
                            is_active=True
                        )
                        auth_token_obj.save()
                    except Exception as e:
                        logger.error("Auth token save failed.", str(e), login_info)
                        token = None
        else:
            logger.error("Invalid username or password.", login_info)

    return token


def create_user_session(session_info):
    response = get_response_format()

    user_obj = None
    auth_token_obj = None
    session_obj = None

    if session_info["username"] and session_info["auth_token"]:
        try:
            user_obj = User.objects.get(username=session_info["username"], is_active=True)
        except Exception as e:
            logger.error("User not found.", str(e))

        if user_obj:
            try:
                auth_token_obj = UserAuthToken.objects.get(
                    user=user_obj,
                    token=session_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Auth token not found.", str(e))

            if auth_token_obj:
                try:
                    session_obj = UserSession(
                        user=user_obj,
                        auth_token=auth_token_obj,
                        session_id=str(uuid.uuid4()),
                        device_token=secrets.token_hex(16),
                        device_ip=session_info["device_ip"],
                        device_info=session_info["device_info"],
                        logged_in=True,
                        logged_in_at=timezone.now(),
                        expiry_at=timezone.now() + timedelta(hours=8),
                        refresh_at=timezone.now() + timedelta(hours=1)
                    )
                    session_obj.save()
                except Exception as e:
                    logger.error("User session creation failed.", str(e), session_info)

                if session_obj:
                    response["success"] = True
                    response["data"]["session_info"] = {
                        "session_id": session_obj.session_id,
                        "device_token": session_obj.device_token,
                        "expiry_at": session_obj.expiry_at,
                        "refresh_at": session_obj.refresh_at
                    }
                else:
                    response["success"] = False
                    response["errors"].append("Session not created.")
                    response["error_code"] = 100413
            else:
                response["success"] = False
                response["errors"].append("Invalid token.")
                response["error_code"] = 100412
        else:
            response["success"] = False
            response["errors"].append("User not found.")
            response["error_code"] = 100404
    else:
        response["success"] = False
        response["errors"].append("Invalid input, required fields not provided.")
        response["error_code"] = 100401

    return response


def validate_user_session(session_info):
    response = get_response_format()

    user_obj = None
    auth_token_obj = None
    session_obj = None

    if session_info["username"] and session_info["auth_token"] and \
       session_info["session_id"] and session_info["device_token"]:

        try:
            user_obj = User.objects.get(username=session_info["username"], is_active=True)
        except Exception as e:
            logger.error("User not found.", str(e))

        if user_obj:
            try:
                auth_token_obj = UserAuthToken.objects.get(
                    user=user_obj,
                    token=session_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Auth token not found.", str(e))

            if auth_token_obj:
                try:
                    session_obj = UserSession.objects.get(
                        user=user_obj,
                        auth_token=auth_token_obj,
                        session_id=session_info["session_id"],
                        device_token=session_info["device_token"],
                        logged_in=True
                    )
                except Exception as e:
                    logger.error("Session not found.", str(e))

                if session_obj:
                    if timezone.now() > session_obj.expiry_at:
                        response["success"] = False
                        response["errors"].append("Session expired.")
                        response["error_code"] = 100414
                    else:
                        response["success"] = True
                        response["data"]["session_info"] = {
                            "session_id": session_obj.session_id,
                            "device_token": session_obj.device_token,
                            "logged_in": session_obj.logged_in,
                            "expiry_at": session_obj.expiry_at,
                            "refresh_at": session_obj.refresh_at,
                        }
                else:
                    response["success"] = False
                    response["errors"].append("Invalid session.")
                    response["error_code"] = 100415
            else:
                response["success"] = False
                response["errors"].append("Invalid token.")
                response["error_code"] = 100412
        else:
            response["success"] = False
            response["errors"].append("User not found.")
            response["error_code"] = 100404
    else:
        response["success"] = False
        response["errors"].append("Invalid input, required fields not provided.")
        response["error_code"] = 100401

    return response


def logout_user(logout_info):
    response = get_response_format()

    user_obj = None
    auth_token_obj = None
    session_obj = None

    if logout_info["username"] and logout_info["auth_token"] and \
       logout_info["session_id"] and logout_info["device_token"]:

        try:
            user_obj = User.objects.get(username=logout_info["username"], is_active=True)
        except Exception as e:
            logger.error("User not found.", str(e))

        if user_obj:
            try:
                auth_token_obj = UserAuthToken.objects.get(
                    user=user_obj,
                    token=logout_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Auth token not found.", str(e))

            if auth_token_obj:
                try:
                    session_obj = UserSession.objects.get(
                        user=user_obj,
                        auth_token=auth_token_obj,
                        session_id=logout_info["session_id"],
                        device_token=logout_info["device_token"],
                        logged_in=True
                    )
                except Exception as e:
                    logger.error("Session not found.", str(e))

                if session_obj:
                    try:
                        session_obj.logged_in = False
                        session_obj.logout_at = timezone.now()
                        session_obj.expiry_at = timezone.now()
                        session_obj.save()
                    except Exception as e:
                        logger.error("Logout failed.", str(e), logout_info)

                    response["success"] = True
                    response["data"]["logout_info"] = {
                        "session_id": session_obj.session_id,
                        "logged_out": True
                    }
                else:
                    response["success"] = False
                    response["errors"].append("Invalid session.")
                    response["error_code"] = 100415
            else:
                response["success"] = False
                response["errors"].append("Invalid token.")
                response["error_code"] = 100412
        else:
            response["success"] = False
            response["errors"].append("User not found.")
            response["error_code"] = 100404
    else:
        response["success"] = False
        response["errors"].append("Invalid input, required fields not provided.")
        response["error_code"] = 100401

    return response


def create_user_by_admin(user_info):
    response = get_response_format()

    admin_user_obj = None
    admin_auth_token_obj = None
    admin_session_obj = None

    role_obj = None
    existing_username_obj = None
    existing_email_obj = None

    user_obj = None
    profile_obj = None

    if user_info["loggedin_username"] and user_info["auth_token"] and \
       user_info["session_id"] and user_info["device_token"] and \
       user_info["username"] and user_info["email"] and user_info["password"] and \
       user_info["first_name"] and user_info["last_name"] and user_info["role_code"]:

        try:
            admin_user_obj = User.objects.get(username=user_info["loggedin_username"], is_active=True)
        except Exception as e:
            logger.error("Logged in user not found.", str(e))

        if admin_user_obj:
            try:
                admin_auth_token_obj = UserAuthToken.objects.get(
                    user=admin_user_obj,
                    token=user_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Logged in user auth token not found.", str(e))

            if admin_auth_token_obj:
                try:
                    admin_session_obj = UserSession.objects.get(
                        user=admin_user_obj,
                        auth_token=admin_auth_token_obj,
                        session_id=user_info["session_id"],
                        device_token=user_info["device_token"],
                        logged_in=True
                    )
                except Exception as e:
                    logger.error("Logged in user session not found.", str(e))

                if admin_session_obj:
                    try:
                        admin_profile_obj = UserProfile.objects.get(user=admin_user_obj, is_active=True)
                    except Exception as e:
                        admin_profile_obj = None
                        logger.error("Logged in user profile not found.", str(e))

                    if admin_profile_obj and admin_profile_obj.role.role_code == ROLE_ADMIN:
                        try:
                            role_obj = Role.objects.get(role_code=user_info["role_code"], is_active=True)
                        except Exception as e:
                            logger.error("Role not found.", str(e))

                        try:
                            existing_username_obj = User.objects.get(username=user_info["username"])
                        except Exception as e:
                            logger.info("User not found with same username.", str(e))

                        try:
                            existing_email_obj = User.objects.get(email=user_info["email"])
                        except Exception as e:
                            logger.info("User not found with same email.", str(e))

                        if not role_obj:
                            response["success"] = False
                            response["errors"].append("Role not found.")
                            response["error_code"] = 100404

                        elif existing_username_obj:
                            response["success"] = False
                            response["errors"].append("Username already exists.")
                            response["error_code"] = 100402

                        elif existing_email_obj:
                            response["success"] = False
                            response["errors"].append("Email already exists.")
                            response["error_code"] = 100403

                        else:
                            try:
                                user_obj = User.objects.create_user(
                                    username=user_info["username"],
                                    email=user_info["email"],
                                    password=user_info["password"]
                                )
                                user_obj.is_active = True
                                user_obj.save()
                            except Exception as e:
                                logger.error("User save failed.", str(e), user_info)

                            if user_obj:
                                try:
                                    profile_obj = UserProfile(
                                        user=user_obj,
                                        role=role_obj,
                                        first_name=user_info["first_name"],
                                        middle_name=user_info["middle_name"],
                                        last_name=user_info["last_name"],
                                        phone_number=user_info["phone_number"],
                                        signup_type=SIGNUP_TYPE_ADMIN,
                                        email_verified=True,
                                        phone_verified=False,
                                        is_active=True,
                                        created_by=admin_user_obj,
                                        updated_by=admin_user_obj
                                    )
                                    profile_obj.save()
                                except Exception as e:
                                    logger.error("User profile save failed.", str(e), user_info)

                            if user_obj and profile_obj:
                                response["success"] = True
                                response["data"]["user_info"] = {
                                    "username": user_obj.username,
                                    "email": user_obj.email,
                                    "role_code": role_obj.role_code,
                                    "created_by_admin": True
                                }
                            else:
                                response["success"] = False
                                response["errors"].append("User not created.")
                                response["error_code"] = 100405
                    else:
                        response["success"] = False
                        response["errors"].append("User not authorized to create users.")
                        response["error_code"] = 100416
                else:
                    response["success"] = False
                    response["errors"].append("Invalid session.")
                    response["error_code"] = 100415
            else:
                response["success"] = False
                response["errors"].append("Invalid token.")
                response["error_code"] = 100412
        else:
            response["success"] = False
            response["errors"].append("User not found.")
            response["error_code"] = 100404
    else:
        response["success"] = False
        response["errors"].append("Invalid input, required fields not provided.")
        response["error_code"] = 100401

    return response


def seed_roles(seed_info):
    response = get_response_format()

    created_roles = []

    created_by_obj = None

    if seed_info["created_by_username"]:
        try:
            created_by_obj = User.objects.get(username=seed_info["created_by_username"])
        except Exception as e:
            logger.error("Created by user not found.", str(e))

    roles_data = [
        {
            "name": "Admin",
            "description": "System administrator with full access",
            "role_code": ROLE_ADMIN
        },
        {
            "name": "Analyst",
            "description": "Analyst with transaction and reporting access",
            "role_code": ROLE_ANALYST
        },
        {
            "name": "Client",
            "description": "Client with limited access",
            "role_code": ROLE_CLIENT
        },
    ]

    for role_item in roles_data:
        role_obj = None

        try:
            role_obj = Role.objects.get(role_code=role_item["role_code"])
        except Exception as e:
            logger.info("Role not found.", str(e))

        if not role_obj:
            try:
                role_obj = Role(
                    name=role_item["name"],
                    description=role_item["description"],
                    role_code=role_item["role_code"],
                    is_active=True,
                    created_by=created_by_obj,
                    updated_by=created_by_obj
                )
                role_obj.save()
                created_roles.append(role_obj.role_code)
            except Exception as e:
                logger.error("Role save failed.", str(e), role_item)

    response["success"] = True
    response["data"]["role_info"] = {
        "created_roles": created_roles
    }

    return response


def get_users_list(user_info):
    response = get_response_format()

    admin_user_obj = None
    admin_auth_token_obj = None
    admin_session_obj = None
    admin_profile_obj = None

    user_profiles = None
    paginated_users = []

    page = 1
    page_size = 10

    if user_info["loggedin_username"] and user_info["auth_token"] and \
       user_info["session_id"] and user_info["device_token"]:

        if user_info["page"]:
            page = user_info["page"]

        if user_info["page_size"]:
            page_size = user_info["page_size"]

        try:
            admin_user_obj = User.objects.get(
                username=user_info["loggedin_username"],
                is_active=True
            )
        except Exception as e:
            logger.error("Logged in user not found.", str(e))

        if admin_user_obj:
            try:
                admin_auth_token_obj = UserAuthToken.objects.get(
                    user=admin_user_obj,
                    token=user_info["auth_token"],
                    is_active=True
                )
            except Exception as e:
                logger.error("Logged in user auth token not found.", str(e))

            if admin_auth_token_obj:
                try:
                    admin_session_obj = UserSession.objects.get(
                        user=admin_user_obj,
                        auth_token=admin_auth_token_obj,
                        session_id=user_info["session_id"],
                        device_token=user_info["device_token"],
                        logged_in=True
                    )
                except Exception as e:
                    logger.error("Logged in user session not found.", str(e))

                if admin_session_obj:
                    if timezone.now() > admin_session_obj.expiry_at:
                        response["success"] = False
                        response["errors"].append("Session expired.")
                        response["error_code"] = 100414
                    else:
                        try:
                            admin_profile_obj = UserProfile.objects.get(
                                user=admin_user_obj,
                                is_active=True
                            )
                        except Exception as e:
                            logger.error("Logged in user profile not found.", str(e))

                        if admin_profile_obj and admin_profile_obj.role.role_code == ROLE_ADMIN:
                            try:
                                user_profiles = UserProfile.objects.select_related(
                                    "user", "role"
                                ).filter(
                                    is_active=True,
                                    user__is_active=True
                                ).order_by("id")
                            except Exception as e:
                                logger.error("User list fetch failed.", str(e))

                            if user_profiles is not None:
                                try:
                                    paginator = Paginator(user_profiles, page_size)
                                    users_page = paginator.page(page)
                                except PageNotAnInteger:
                                    users_page = paginator.page(1)
                                except EmptyPage:
                                    users_page = paginator.page(paginator.num_pages)
                                except Exception as e:
                                    users_page = None
                                    logger.error("Pagination failed.", str(e))

                                if users_page:
                                    try:
                                        paginated_users = [{
                                            "user_id": x.user.id,
                                            "username": x.user.username,
                                            "email": x.user.email,
                                            "first_name": x.first_name,
                                            "middle_name": x.middle_name,
                                            "last_name": x.last_name,
                                            "phone_number": x.phone_number,
                                            "role_name": x.role.name,
                                            "role_code": x.role.role_code,
                                            "email_verified": x.email_verified,
                                            "phone_verified": x.phone_verified,
                                            "signup_type": x.signup_type,
                                            "is_active": x.is_active,
                                            "created_at": x.created_at,
                                        } for x in users_page]
                                    except Exception as e:
                                        logger.error("User list formatting failed.", str(e))

                                    response["success"] = True
                                    response["data"]["users_info"] = paginated_users
                                    response["meta"]["pagination"] = {
                                        "page": users_page.number,
                                        "page_size": page_size,
                                        "total_pages": paginator.num_pages,
                                        "total_records": paginator.count,
                                        "has_next": users_page.has_next(),
                                        "has_previous": users_page.has_previous(),
                                    }
                                else:
                                    response["success"] = False
                                    response["errors"].append("Unable to paginate user data.")
                                    response["error_code"] = 100418
                            else:
                                response["success"] = False
                                response["errors"].append("Users not found.")
                                response["error_code"] = 100419
                        else:
                            response["success"] = False
                            response["errors"].append("User not authorized to access users list.")
                            response["error_code"] = 100416
                else:
                    response["success"] = False
                    response["errors"].append("Invalid session.")
                    response["error_code"] = 100415
            else:
                response["success"] = False
                response["errors"].append("Invalid token.")
                response["error_code"] = 100412
        else:
            response["success"] = False
            response["errors"].append("User not found.")
            response["error_code"] = 100404
    else:
        response["success"] = False
        response["errors"].append("Invalid input, required fields not provided.")
        response["error_code"] = 100401

    return response