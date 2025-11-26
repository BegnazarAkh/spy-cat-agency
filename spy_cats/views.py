from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample
from .models import SpyCat, Mission, Target
from .serializers import (
    SpyCatSerializer,
    MissionSerializer,
    MissionCreateSerializer,
    MissionAssignCatSerializer,
    TargetUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=['Spy Cats'],
        summary='List all spy cats',
        description='Retrieve a paginated list of all spy cats in the system',
        responses={
            200: SpyCatSerializer(many=True),
        }
    ),
    retrieve=extend_schema(
        tags=['Spy Cats'],
        summary='Get a single spy cat',
        description='Retrieve detailed information about a specific spy cat',
        responses={
            200: SpyCatSerializer,
            404: OpenApiResponse(description='Spy cat not found'),
        }
    ),
    create=extend_schema(
        tags=['Spy Cats'],
        summary='Create a new spy cat',
        description='Add a new spy cat to the system. Breed will be validated against TheCatAPI.',
        request=SpyCatSerializer,
        responses={
            201: SpyCatSerializer,
            400: OpenApiResponse(description='Invalid input data or breed validation failed'),
        },
        examples=[
            OpenApiExample(
                'Create Spy Cat Example',
                value={
                    'name': 'Shadow',
                    'years_of_experience': 5,
                    'breed': 'Siamese',
                    'salary': '50000.00'
                },
                request_only=True,
            )
        ]
    ),
    update=extend_schema(
        tags=['Spy Cats'],
        summary='Update spy cat salary',
        description='Update the salary of a spy cat. Only salary field can be updated.',
        request=SpyCatSerializer,
        responses={
            200: SpyCatSerializer,
            400: OpenApiResponse(description='Invalid input data'),
            404: OpenApiResponse(description='Spy cat not found'),
        }
    ),
    partial_update=extend_schema(
        tags=['Spy Cats'],
        summary='Partially update spy cat salary',
        description='Partially update the salary of a spy cat. Only salary field can be updated.',
        request=SpyCatSerializer,
        responses={
            200: SpyCatSerializer,
            400: OpenApiResponse(description='Invalid input data'),
            404: OpenApiResponse(description='Spy cat not found'),
        }
    ),
    destroy=extend_schema(
        tags=['Spy Cats'],
        summary='Delete a spy cat',
        description='Remove a spy cat from the system',
        responses={
            204: OpenApiResponse(description='Spy cat successfully deleted'),
            404: OpenApiResponse(description='Spy cat not found'),
        }
    )
)
class SpyCatViewSet(viewsets.ModelViewSet):
    queryset = SpyCat.objects.all()
    serializer_class = SpyCatSerializer

    def update(self, request, *args, **kwargs):
        """Only allow updating salary"""
        partial = kwargs.pop('partial', False) # pylint: disable=unused-variable
        instance = self.get_object()

        # Only allow salary to be updated
        allowed_fields = {'salary'}
        data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(
        tags=['Missions'],
        summary='List all missions',
        description='Retrieve a paginated list of all missions with their targets',
        responses={
            200: MissionSerializer(many=True),
        }
    ),
    retrieve=extend_schema(
        tags=['Missions'],
        summary='Get a single mission',
        description='Retrieve detailed information about a specific mission including all targets',
        responses={
            200: MissionSerializer,
            404: OpenApiResponse(description='Mission not found'),
        }
    ),
    create=extend_schema(
        tags=['Missions'],
        summary='Create a new mission',
        description='Create a new mission with 1-3 targets in a single request. Cat assignment is optional.',
        request=MissionCreateSerializer,
        responses={
            201: MissionSerializer,
            400: OpenApiResponse(description='Invalid input data. Must have 1-3 targets.'),
        },
        examples=[
            OpenApiExample(
                'Create Mission Example',
                value={
                    'cat': 1,
                    'targets': [
                        {
                            'name': 'Target Alpha',
                            'country': 'Germany',
                            'notes': 'Initial surveillance notes'
                        },
                        {
                            'name': 'Target Beta',
                            'country': 'France',
                            'notes': 'Secondary target'
                        }
                    ]
                },
                request_only=True,
            )
        ]
    ),
    destroy=extend_schema(
        tags=['Missions'],
        summary='Delete a mission',
        description='Remove a mission from the system. Cannot delete if mission is assigned to a cat.',
        responses={
            204: OpenApiResponse(description='Mission successfully deleted'),
            400: OpenApiResponse(description='Cannot delete mission assigned to a cat'),
            404: OpenApiResponse(description='Mission not found'),
        }
    )
)
class MissionViewSet(viewsets.ModelViewSet):
    queryset = Mission.objects.all().prefetch_related('targets', 'cat')

    def get_serializer_class(self):
        if self.action == 'create':
            return MissionCreateSerializer
        return MissionSerializer

    def destroy(self, request, *args, **kwargs):
        """Prevent deletion if mission is assigned to a cat"""
        instance = self.get_object()
        if instance.cat:
            return Response(
                {'error': 'Cannot delete a mission that is assigned to a cat.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        tags=['Missions'],
        summary='Assign a cat to a mission',
        description='Assign an available spy cat to a mission. Cat cannot be assigned to multiple incomplete missions.',
        request=MissionAssignCatSerializer,
        responses={
            200: MissionSerializer,
            400: OpenApiResponse(description='Mission already has a cat or cat is busy with another mission'),
            404: OpenApiResponse(description='Mission or cat not found'),
        },
        examples=[
            OpenApiExample(
                'Assign Cat Example',
                value={'cat_id': 1},
                request_only=True,
            )
        ]
    )
    @action(detail=True, methods=['post'])
    def assign_cat(self, request, pk=None):
        """Assign a cat to a mission"""
        mission = self.get_object()

        if mission.cat:
            return Response(
                {'error': 'Mission is already assigned to a cat.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = MissionAssignCatSerializer(data=request.data)
        if serializer.is_valid():
            cat = SpyCat.objects.get(id=serializer.validated_data['cat_id'])
            mission.cat = cat
            mission.save()

            return Response(
                MissionSerializer(mission).data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Missions'],
        summary='Update a target',
        description='Update notes and/or completion status of a specific target. Notes cannot be updated if target or mission is complete.',
        request=TargetUpdateSerializer,
        parameters=[
            OpenApiParameter(
                name='target_id',
                description='ID of the target to update',
                location=OpenApiParameter.PATH,
                required=True,
                type=int,
            )
        ],
        responses={
            200: MissionSerializer,
            400: OpenApiResponse(description='Cannot update notes on completed target/mission'),
            404: OpenApiResponse(description='Mission or target not found'),
        },
        examples=[
            OpenApiExample(
                'Update Target Example',
                value={
                    'notes': 'Updated surveillance information',
                    'complete': True
                },
                request_only=True,
            )
        ]
    )
    @action(detail=True, methods=['patch'], url_path='targets/(?P<target_id>[^/.]+)')
    def update_target(self, request, pk=None, target_id=None):
        """Update a specific target's notes and/or complete status"""
        mission = self.get_object()
        target = get_object_or_404(Target, id=target_id, mission=mission)

        serializer = TargetUpdateSerializer(target, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Check if all targets are complete and update mission
            all_complete = all(t.complete for t in mission.targets.all())
            if all_complete:
                mission.complete = True
                mission.save()

            return Response(
                MissionSerializer(mission).data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
