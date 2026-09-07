from .models import Profile


def user_profile(request):
    profile = None
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
    return {'user_profile': profile}