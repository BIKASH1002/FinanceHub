def authenticate_user(func):
    def wrapper(request, *args, **kwargs):


        return func(request, *args, **kwargs)

    return wrapper