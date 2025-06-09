# api/serializers.py
from rest_framework import serializers

class PromptRequestSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=400)
    model_id = serializers.CharField(required=True)
    session_id = serializers.CharField(required=True)

class AgentResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    active_agent = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    token_usage = serializers.IntegerField(required=False, allow_null=True)
    cost = serializers.FloatField(required=False, allow_null=True)