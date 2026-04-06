from django.db import models
from django.contrib.auth.models import User
from utilities.constants import SIGNUP_TYPE_CHOICES, SIGNUP_TYPE_SELF
import uuid


class Role(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    role_code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='role_created_by')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='role_updated_by')

    def __str__(self):
        return f"{self.name} - {self.role_code}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_profile")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_profiles")
    first_name = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    signup_type = models.CharField(max_length=20, choices=SIGNUP_TYPE_CHOICES, default=SIGNUP_TYPE_SELF)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="userprofile_created_by")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="userprofile_updated_by")

    def __str__(self):
        return self.user.username


class UserAuthToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_auth_tokens")
    token = models.TextField(unique=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="userauthtoken_created_by")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="userauthtoken_updated_by")

    def __str__(self):
        return self.user.username


class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_sessions")
    auth_token = models.ForeignKey(UserAuthToken, on_delete=models.CASCADE, related_name="user_sessions")
    session_id = models.CharField(max_length=100, unique=True)
    device_token = models.CharField(max_length=255, unique=True)
    device_ip = models.CharField(max_length=100, null=True, blank=True)
    device_info = models.TextField(null=True, blank=True)
    logged_in = models.BooleanField(default=True)
    logged_in_at = models.DateTimeField()
    expiry_at = models.DateTimeField()
    refresh_at = models.DateTimeField(null=True, blank=True)
    logout_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="usersession_created_by")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="usersession_updated_by")

    def __str__(self):
        return self.session_id


class EmailOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_otps")
    email = models.EmailField()
    otp = models.CharField(max_length=10)
    is_verified = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="emailotp_created_by")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="emailotp_updated_by")

    def __str__(self):
        return f"{self.user.username} - {self.email}"
