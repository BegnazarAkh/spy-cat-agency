import requests
from rest_framework import serializers
from .models import SpyCat, Mission, Target


class SpyCatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpyCat
        fields = ['id', 'name', 'years_of_experience', 'breed', 'salary', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_breed(self, value):
        """Validate breed using TheCatAPI"""
        try:
            response = requests.get('https://api.thecatapi.com/v1/breeds', timeout=500)
            if response.status_code == 200:
                breeds = response.json()
                valid_breeds = [breed['name'].lower() for breed in breeds]
                if value.lower() not in valid_breeds:
                    raise serializers.ValidationError(
                        "Invalid breed. Must be a valid cat breed from TheCatAPI."
                    )
            else:
                raise serializers.ValidationError("Unable to validate breed at this time.")
        except requests.RequestException as exc:
            raise serializers.ValidationError("Unable to validate breed at this time.") from exc

        return value


class TargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = ['id', 'name', 'country', 'notes', 'complete', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        # Check if trying to update notes on completed target or mission
        if self.instance:
            if self.instance.complete and 'notes' in data and data['notes'] != self.instance.notes:
                raise serializers.ValidationError({
                    'notes': 'Cannot update notes on a completed target.'
                })
            if self.instance.mission.complete and 'notes' in data and data['notes'] != self.instance.notes:
                raise serializers.ValidationError({
                    'notes': 'Cannot update notes on a target belonging to a completed mission.'
                })
        return data


class TargetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = ['name', 'country', 'notes']


class MissionSerializer(serializers.ModelSerializer):
    targets = TargetSerializer(many=True, read_only=True)
    cat_details = SpyCatSerializer(source='cat', read_only=True)

    class Meta:
        model = Mission
        fields = ['id', 'cat', 'cat_details', 'targets', 'complete', 'created_at', 'updated_at']
        read_only_fields = ['id', 'complete', 'created_at', 'updated_at']


class MissionCreateSerializer(serializers.ModelSerializer):
    targets = TargetCreateSerializer(many=True)

    class Meta:
        model = Mission
        fields = ['cat', 'targets']

    def validate_targets(self, value):
        if len(value) < 1 or len(value) > 3:
            raise serializers.ValidationError("Mission must have between 1 and 3 targets.")
        return value

    def validate_cat(self, value):
        # Check if cat is already assigned to an incomplete mission
        if value:
            existing_mission = Mission.objects.filter(cat=value, complete=False).first()
            if existing_mission:
                raise serializers.ValidationError(
                    f"Cat is already assigned to mission {existing_mission.id}."
                )
        return value

    def create(self, validated_data):
        targets_data = validated_data.pop('targets')
        mission = Mission.objects.create(**validated_data)

        for target_data in targets_data:
            Target.objects.create(mission=mission, **target_data)

        return mission


class MissionAssignCatSerializer(serializers.Serializer):
    cat_id = serializers.IntegerField()

    def create(self, validated_data):
        raise NotImplementedError("Create method not implemented")

    def update(self, instance, validated_data):
        raise NotImplementedError("Update method not implemented")

    def validate_cat_id(self, value):
        try:
            cat = SpyCat.objects.get(id=value)
        except SpyCat.DoesNotExist as exc:
            raise serializers.ValidationError("Cat does not exist.") from exc

        # Check if cat is already assigned to an incomplete mission
        existing_mission = Mission.objects.filter(cat=cat, complete=False).first()
        if existing_mission:
            raise serializers.ValidationError(
                f"Cat is already assigned to mission {existing_mission.id}."
            )

        return value


class TargetUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = ['notes', 'complete']

    def validate(self, data):
        # Check if trying to update notes on completed target or mission
        if self.instance:
            if self.instance.complete and 'notes' in data and data['notes'] != self.instance.notes:
                raise serializers.ValidationError({
                    'notes': 'Cannot update notes on a completed target.'
                })
            if self.instance.mission.complete and 'notes' in data and data['notes'] != self.instance.notes:
                raise serializers.ValidationError({
                    'notes': 'Cannot update notes on a target belonging to a completed mission.'
                })
        return data
