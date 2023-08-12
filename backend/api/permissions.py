from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    def object_permission(self, request, view, object):
        if request.method in permissions.SAFE_METHODS:
            return True
        return object.author == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    def permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_superuser
