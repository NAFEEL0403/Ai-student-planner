from rest_framework import serializers

class StudyPlanRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    subjects = serializers.ListField(
        child=serializers.CharField(max_length=100),
        allow_empty=False
    )
    topics = serializers.ListField(
        child=serializers.CharField(max_length=255),
        allow_empty=False
    )
    exam_date = serializers.DateField()
    daily_hours = serializers.IntegerField(min_value=1, max_value=24)
    knowledge_level = serializers.ChoiceField(choices=['Beginner', 'Intermediate', 'Advanced'])
    preferred_session = serializers.ChoiceField(choices=['Morning', 'Afternoon', 'Evening', 'Flexible'])
    duration_days = serializers.IntegerField(min_value=1, max_value=365)
