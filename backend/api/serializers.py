from rest_framework import serializers
from users.models import User_list, Register_user


class UserlistSerializer(serializers.Serializer):
    class Meta:
        model = User_list
        fields = ['count', 'next', 'previous', 'reults']

class RegisteruserSerializer(serializers.Serializer):
    class Meta:
        model = Register_user
        fields = ['email', 'id', 'username', 'first_name', 'last_name']
    