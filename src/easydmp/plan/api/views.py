from rest_framework import serializers
from rest_framework.fields import JSONField
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_filters.rest_framework.filterset import FilterSet

from easydmp.auth.api.views import UserSerializer

from easydmp.plan.models import Plan
from easydmp.plan.models import SectionValidity
from easydmp.plan.models import QuestionValidity


class LightSectionValiditySerializer(serializers.ModelSerializer):

    class Meta:
        model = SectionValidity
        fields = [
            'id',
            'section',
            'valid',
            'last_validated',
        ]


class LightQuestionValiditySerializer(serializers.ModelSerializer):

    class Meta:
        model = QuestionValidity
        fields = [
            'id',
            'question',
            'valid',
            'last_validated',
        ]


class PlanFilter(FilterSet):

    class Meta:
        model = Plan
        fields = {
            'added': ['lt', 'gt', 'lte', 'gte'],
            'modified': ['lt', 'gt', 'lte', 'gte'],
            'locked': ['lt', 'gt', 'lte', 'gte'],
            'published': ['lt', 'gt', 'lte', 'gte'],
        }


class LightPlanSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plan-detail',
        lookup_field='pk',
    )
    template = serializers.HyperlinkedRelatedField(
        view_name='template-detail',
        lookup_field='pk',
        many=False,
        read_only=True,
    )

    class Meta:
        model = Plan
        fields = [
            'id',
            'uuid',
            'url',
            'title',
            'abbreviation',
            'version',
            'template',
            'valid',
            'added',
            'modified',
            'last_validated',
            'locked',
            'published',
        ]


class HeavyPlanSerializer(LightPlanSerializer):
    data = JSONField(binary=False)
    previous_data = JSONField(binary=False)
    added_by = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        lookup_field='pk',
        many=False,
        read_only=True,
    )
    modified_by = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        lookup_field='pk',
        many=False,
        read_only=True,
    )
    locked_by = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        lookup_field='pk',
        many=False,
        read_only=True,
    )
    published_by = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        lookup_field='pk',
        many=False,
        read_only=True,
    )
    section_validity = LightSectionValiditySerializer(many=True, read_only=True)
    question_validity = LightQuestionValiditySerializer(many=True, read_only=True)

    class Meta:
        model = Plan
        fields = [
            'id',
            'uuid',
            'url',
            'title',
            'abbreviation',
            'version',
            'template',
            'section_validity',
            'question_validity',
            'data',
            'previous_data',
            'generated_html',
            'doi',
            'added',
            'added_by',
            'modified',
            'modified_by',
            'locked',
            'locked_by',
            'published',
            'published_by',
        ]


class PlanViewSet(ReadOnlyModelViewSet):
    filter_class = PlanFilter
    serializer_class = HeavyPlanSerializer

# 
#     def get_serializer_class(self):
#         if self.action == 'retrieve':
#             return HeavyPlanSerializer
#         return LightPlanSerializer

    def get_queryset(self):
        qs = Plan.objects.exclude(published=None)
        if self.request.user.is_authenticated():
            pas = self.request.user.plan_accesses.all()
            qs = qs | Plan.objects.filter(accesses__in=pas)
        return qs.distinct()
