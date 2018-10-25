from itertools import chain

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import IntegrityError
from django.http import HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import render, redirect
from django.views.generic.edit import FormMixin
from django.views.generic import (
    CreateView,
    UpdateView,
    DetailView,
    ListView,
    DeleteView,
    RedirectView,
)
from django.utils.html import mark_safe

from easydmp.utils import pprint_list, utc_epoch
from easydmp.dmpt.forms import make_form, TemplateForm, NotesForm
from easydmp.dmpt.models import Template, Question, Section
from easydmp.invitation.models import PlanInvitation
from flow.models import FSA

from .models import Plan
from .models import PlanAccess
from .models import PlanComment
from .models import QuestionValidity
from .models import SectionValidity
from .forms import DeleteForm
from .forms import NewPlanForm
from .forms import UpdatePlanForm
from .forms import SaveAsPlanForm
from .forms import PlanCommentForm
from .forms import ConfirmForm
from .forms import PlanAccessForm
from .forms import ConfirmOwnPlanAccessChangeForm


def progress(so_far, all):
    "Returns percentage done, as float"
    return so_far/float(all)*100


def has_prevquestion(question, data):
     return bool(question.get_prev_question(data))


def get_section_progress(plan, current_section=None):
    sections = plan.template.sections.filter(section_depth=1).order_by('position')
    visited_sections = plan.visited_sections.all()
    section_struct = []
    current_section = current_section.get_topmost_section()
    for section in sections:
        section_dict = {
            'label': section.label,
            'title': section.title,
            'full_title': section.full_title(),
            'pk': section.pk,
            'status': 'new',
        }
        if section in visited_sections:
            section_dict['status'] = 'visited'
        if section == current_section:
            section_dict['status'] = 'active'
        section_struct.append(section_dict)
    return section_struct


class DeleteFormMixin(FormMixin):
    # FormMixin needed in order to use a proper form in the
    # confirmation step. A DeleteView just needs a POST.
    form_class = DeleteForm


# -- sharing plans


class PlanAccessView(UserPassesTestMixin, ListView):
    "View and change who has access to what"
    template_name = 'easydmp/plan/planaccess_list.html'
    model = PlanAccess

    def dispatch(self, request, *args, **kwargs):
        self.plan = self.get_plan()
        self.invitations = self.get_invitations()
        self.queryset = self.get_queryset()
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        if self.queryset.filter(user=self.request.user):
            return True
        return False

    def get_plan(self):
        plan_id = self.kwargs['plan']
        return Plan.objects.get(pk=plan_id)

    def get_queryset(self):
        return self.model.objects.filter(plan=self.plan)

    def get_invitations(self):
        usernames = self.get_queryset().values_list('user__username', flat=True)
        return PlanInvitation.objects.filter(
            plan=self.plan,
            used__isnull=True,
        ).exclude(
            email_address__in=usernames
        ).valid_only()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invitations'] = self.invitations
        context['plan'] = self.plan
        accesses = []
        for access in self.get_queryset():
            form = PlanAccessForm(initial={'access': access.access})
            access.form = form
            accesses.append(access)
        context['accesses'] = accesses
        return context

    def get_success_url(self):
        return reverse('share_plan', kwargs={'plan': self.plan.pk})


class UpdatePlanAccessView(UserPassesTestMixin, UpdateView):
    model = PlanAccess
    form_class = PlanAccessForm
    pk_url_kwarg = 'access'
    template_name = 'easydmp/plan/planaccess_confirm_update.html'
    changing_self = None

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.request.user == self.object.user:
            self.changing_self = True
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        if self.get_object():
            return True
        return False

    def get_queryset(self):
        user_accesses = self.request.user.plan_accesses.filter(may_edit=True)
        plan_pks = user_accesses.values_list('plan__pk', flat=True)
        qs = self.model.objects.filter(plan__pk__in=plan_pks)
        return qs

    def get_form_class(self):
        if self.changing_self:
            return ConfirmOwnPlanAccessChangeForm
        return self.form_class

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if 'cancel' in self.request.POST or not form.is_valid():
            return self.form_invalid(form)
        if self.changing_self and 'submit' not in self.request.POST:
                return self.get(request, *args, **kwargs)
        return self.form_valid(form)

    def form_valid(self, form):
        access = form.cleaned_data['access']
        may_edit = False
        if access == 'view and edit':
            may_edit = True
        if may_edit != self.object.may_edit:
            self.object.may_edit = may_edit
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('share_plan', kwargs={'plan': self.object.plan.pk})


class DeletePlanAccessView(UserPassesTestMixin, DeleteFormMixin, DeleteView):
    "Delete a PlanAccess, leading to a person leaving a plan"

    model = PlanAccess
    template_name = 'easydmp/plan/planaccess_confirm_delete.html'
    success_url = reverse_lazy('plan_list')
    pk_url_kwarg = 'access'

    def test_func(self):
        if self.get_object():
            return True
        return False

    def get_queryset(self):
        return self.request.user.plan_accesses.all()

    def delete(self, request, *args, **kwargs):
        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.get_success_url())
        return super().delete(request, *args, **kwargs)


# -- plans


class PlanAccessViewMixin:

    def get_queryset(self):
        return super().get_queryset().viewable(self.request.user)


class AbstractPlanViewMixin:

    def get_success_url(self):
        kwargs = {
            'plan': self.object.pk,
            'question': self.object.get_first_question().pk,
        }
        return reverse('new_question', kwargs=kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def existing_with_same_title(self):
        return self.model.objects.filter(template=self.object.template,
                                         title=self.object.title,)

    def find_existing(self):
        user = self.request.user
        qs = self.existing_with_same_title()
        if not qs:
            return None
        qs = qs.filter(accesses__user=user)
        if not qs:
            return None
        return qs


class NewPlanView(AbstractPlanViewMixin, PlanAccessViewMixin, CreateView):
    """Create a new empty plan from the given template

    Chceks that the same adder do not have a plan of the same name already.
    """
    template_name = 'easydmp/plan/newplan_form.html'
    model = Plan
    form_class = NewPlanForm

    def get_success_url(self):
        kwargs = {
            'plan': self.object.pk,
            'question': self.object.get_first_question().pk,
        }
        return reverse('new_question', kwargs=kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.data = {}
        self.object.previous_data = {}
        self.object.added_by = self.request.user
        self.object.modified_by = self.request.user
        self.object.template = form.cleaned_data['template_type']
        existing = self.find_existing()
        if not existing:
            self.object.save()
            return HttpResponseRedirect(self.get_success_url())
        if existing.count() == 1:
            hop_to = existing[0]
            # send message
            return HttpResponseRedirect(reverse('plan_detail', kwargs={'plan': hop_to.pk}))
        # multiple plans with same editor, template and title exists
        return HttpResponseServerError()


class UpdatePlanView(PlanAccessViewMixin, AbstractPlanViewMixin, UpdateView):
    "Update metadata about a plan"

    template_name = 'easydmp/plan/updateplan_form.html'
    model = Plan
    pk_url_kwarg = 'plan'
    form_class = UpdatePlanForm

    def get_success_url(self):
        kwargs = {
            'plan': self.object.pk,
        }
        return reverse('plan_detail', kwargs=kwargs)

    def form_valid(self, form):
        existing = self.find_existing()
        if not existing:
            self.object = form.save()
            return HttpResponseRedirect(self.get_success_url())
        if existing.count() == 1:
            hop_to = existing[0]
            # send message
            return HttpResponseRedirect(reverse('plan_detail', kwargs={'plan': hop_to.pk}))
        # multiple plans with same editor, template and title exists
        return HttpResponseServerError()


class DeletePlanView(PlanAccessViewMixin, DeleteFormMixin, DeleteView):
    "Delete an unpublished Plan"

    model = Plan
    template_name = 'easydmp/plan/plan_confirm_delete.html'
    success_url = reverse_lazy('plan_list')
    pk_url_kwarg = 'plan'

    def get_queryset(self):
        qs = super().get_queryset().unpublished()
        return qs.filter(added_by=self.request.user)

    def delete(self, request, *args, **kwargs):
        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.get_success_url())
        return super().delete(request, *args, **kwargs)


class SaveAsPlanView(PlanAccessViewMixin, UpdateView):
    "Save a copy of an existing plan as a new plan"

    model = Plan
    template_name = 'easydmp/plan/plan_confirm_save_as.html'
    success_url = reverse_lazy('plan_list')
    pk_url_kwarg = 'plan'
    form_class = SaveAsPlanForm

    def get_queryset(self):
        qs = super().get_queryset()
        return qs

    def form_valid(self, form):
        title = form.cleaned_data['title']
        abbreviation = form.cleaned_data.get('abbreviation', '')
        keep_users = form.cleaned_data.get('keep_users', True)
        self.object.save_as(title, self.request.user, abbreviation, keep_users)
        return HttpResponseRedirect(self.get_success_url())


class ValidatePlanView(PlanAccessViewMixin, UpdateView):
    "Validate an entire plan"

    template_name = 'easydmp/plan/plan_confirm_validate.html'
    form_class = ConfirmForm
    model = Plan
    pk_url_kwarg = 'plan'

    def get_queryset(self):
        qs = super().get_queryset().invalid()
        return qs

    def get_success_url(self):
        return reverse('plan_detail', kwargs={'plan': self.object.pk})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.validate()
        return HttpResponseRedirect(success_url)


class LockPlanView(PlanAccessViewMixin, UpdateView):
    "Lock a plan to make it read only"

    template_name = 'easydmp/plan/plan_confirm_lock.html'
    form_class = ConfirmForm
    model = Plan
    pk_url_kwarg = 'plan'

    def get_queryset(self):
        qs = super().get_queryset().unlocked()
        return qs

    def get_success_url(self):
        return reverse('plan_detail', kwargs={'plan': self.object.pk})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.lock(request.user)
        return HttpResponseRedirect(success_url)


class PublishPlanView(PlanAccessViewMixin, UpdateView):
    """Publish a plan

    This makes it read only and undeletable.
    """

    template_name = 'easydmp/plan/plan_confirm_publish.html'
    form_class = ConfirmForm
    model = Plan
    pk_url_kwarg = 'plan'

    def get_queryset(self):
        qs = super().get_queryset().valid()
        return qs

    def get_success_url(self):
        return reverse('plan_detail', kwargs={'plan': self.object.pk})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.publish(request.user)
        return HttpResponseRedirect(success_url)


class CreateNewVersionPlanView(PlanAccessViewMixin, UpdateView):
    """Create a new version of a plan

    This reopens a read only or published plan, incrementng the version number.

    """

    template_name = 'easydmp/plan/plan_confirm_createnewversion.html'
    form_class = ConfirmForm
    model = Plan
    pk_url_kwarg = 'plan'

    def get_queryset(self):
        qs = super().get_queryset().locked()
        return qs

    def get_success_url(self):
        return reverse('plan_detail', kwargs={'plan': self.object.pk})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.create_new_version(request.user)
        return HttpResponseRedirect(success_url)


class AbstractQuestionMixin(PlanAccessViewMixin):

    def preload(self, **kwargs):
        """Store frequently used values as early as possible

        Prevents multiple database-queries to fetch known data.
        """
        self.plan_pk = self.kwargs.get('plan')
        self.plan = (Plan.objects
            .select_related('template')
            .prefetch_related('template__sections')
            .get(id=self.plan_pk)
        )
        self.template = self.plan.template
        self.queryset = self._get_queryset()

    def dispatch(self, request, *args, **kwargs):
        self.preload(**kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_question_pk(self):
        return self.question_pk

    def get_question(self):
        return self.question

    def _get_question(self):
        question_pk = self.question_pk
        # Ensure that the template does contain the question
        try:
            sections = self.template.sections.all()
            question = (Question.objects
                .select_related('section')
                .get(pk=question_pk, section__in=sections)
            )
        except Question.DoesNotExist as e:
            raise ValueError("Unknown question id: {}".format(question_pk))
        question = question.get_instance()
        return question

    def get_plan_pk(self):
        return self.plan_pk

    def _get_queryset(self):
        qs = super().get_queryset().editable(self.request.user)
        return qs.filter(pk=self.get_plan_pk())

    def get_plan(self):
        return self.plan

    def get_template(self):
        return self.template


class AbstractQuestionView(AbstractQuestionMixin, UpdateView):
    model = Plan
    template_name = 'easydmp/plan/state_form.html'
    pk_url_kwarg = 'plan'
    fields = ('plan_name', 'data')


class NewQuestionView(AbstractQuestionView):
    "Answer a Question"

    def preload(self, **kwargs):
        super().preload(**kwargs)

        self.question_pk = self.kwargs.get('question')
        self.question = self._get_question()
        self.section = self.question.section
        self.questionvalidity, _ = QuestionValidity.objects.get_or_create(
            plan=self.plan,
            question=self.question,
            defaults={'valid': False}
        )
        self.sectionvalidity, _ = SectionValidity.objects.get_or_create(
            plan=self.plan,
            section=self.section,
            defaults={'valid': False}
        )

    def set_referer(self, request):
        self.referer = request.META.get('HTTP_REFERER', None)

    def get_initial(self):
        current_data = self.object.data or {}
        previous_data = self.object.previous_data or {}
        initial = current_data.get(self.question_pk, {})
        if not initial:
            initial = previous_data.get(self.question_pk, {})
        return initial

    def get_success_url(self):
        question = self.question
        current_data = self.object.data
        kwargs = {'plan': self.object.pk}

        if 'summary' in self.request.POST:
            return reverse('plan_detail', kwargs=kwargs)
        elif 'prev' in self.request.POST:
            prev_question = question.get_prev_question(self.object.data)
            kwargs['question'] = prev_question.pk
        elif 'next' in self.request.POST:
            next_question = question.get_next_question(current_data)
            if not next_question:
                # Finished answering all questions
                return reverse('plan_detail', kwargs=kwargs)
            kwargs['question'] = next_question.pk
        else:
            kwargs['question'] = question.pk

        # Go to next on 'next', prev on 'prev', stay on same page otherwise
        return reverse('new_question', kwargs=kwargs)

    def get_context_data(self, **kwargs):
        template = self.template
        question = self.question
        section = self.section
        path = section.questions.order_by('position')
        kwargs['path'] = path
        kwargs['question'] = question
        kwargs['question_pk'] = question.pk
        kwargs['notesform'] = kwargs.get('notesform', self.get_notesform())
        kwargs['commentform'] = kwargs.get('commentform', self.get_commentform())
        kwargs['label'] = question.label
        kwargs['answers'] = question.canned_answers.values()
        kwargs['framing_text'] = question.framing_text
        kwargs['section'] = section
        neighboring_questions = Question.objects.filter(section=section)
        kwargs['questions_in_section'] = neighboring_questions
        num_questions = neighboring_questions.count()
        num_questions_so_far = len(question.get_all_preceding_questions())
        kwargs['progress'] = progress(num_questions_so_far, num_questions)
        kwargs['referrer'] = self.referer  # Not a typo! From the http header
        kwargs['section_progress'] = get_section_progress(self.object, section)
        return super().get_context_data(**kwargs)

    def get_notesform(self, **_):
        form_kwargs = self.get_form_kwargs()
        question = self.question
        form = NotesForm(**form_kwargs)
        return form

    def get_form(self, **_):
        form_kwargs = self.get_form_kwargs()
        question = self.question
        generate_kwargs = {
            'has_prevquestion': has_prevquestion(question, self.object.data),
        }
        generate_kwargs.update(form_kwargs)
        form = make_form(question, **generate_kwargs)
        return form

    def get_commentform(self, **_):
        form_kwargs = self.get_form_kwargs()
        form = PlanCommentForm(**form_kwargs)
        return form

    def delete_statedata(self, *args):
        """Delete data for the statenames in args"""
        for statename in args:
            self.object.data.pop(statename, None)
        self.object.save()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.set_referer(request)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.set_referer(request)
        form = self.get_form()
        notesform = self.get_notesform()
        if form.is_valid() and notesform.is_valid():
            self.request = request
            return self.form_valid(form, notesform)
        else:
            return self.form_invalid(form, notesform)

    def get_current_choice(self):
        return self.object.data.get(self.question_pk, {})

    def form_valid(self, form, notesform):
        notes = notesform.cleaned_data.get('notes', '')
        choice = form.serialize()
        choice['notes'] = notes
        current_choice = self.get_current_choice()
        # Only save when necessary
        if current_choice != choice:
            # save change
            self.object.data[self.question_pk] = choice
            self.object.previous_data[self.question_pk] = choice
            self.object.save(question=self.question)
            self.questionvalidity.valid = True
            self.questionvalidity.save()
            if not self.sectionvalidity.valid and self.section.validate_data(self.object.data):
                self.sectionvalidity.valid = True
                self.sectionvalidity.save()
            # remove invalidated states
    #         paths_from = self.get_template().find_paths_from(question_pk)
    #         invalidated_states = set(chain(*paths_from))
    #         invalidated_states.discard(None)
    #         invalidated_states.discard(question_pk)
    #         self.delete_statedata(*invalidated_states)
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, notesform):
        if self.questionvalidity.valid:
            self.questionvalidity.valid = False
            self.questionvalidity.save()
            self.sectionvalidity.valid = False
            self.sectionvalidity.save()
        return self.render_to_response(
            self.get_context_data(form=form, notesform=notesform))


class FirstQuestionView(PlanAccessViewMixin, RedirectView):
    "Go to the first Question of a Plan"

    def get_redirect_url(self, *args, **kwargs):
        plan_pk = self.kwargs.get('plan')
        plan = Plan.objects.get(pk=plan_pk)
        question_pk = plan.get_first_question().pk
        url = reverse(
            'new_question',
            kwargs={'plan': plan_pk, 'question': question_pk}
        )
        return url


class AddCommentView(AbstractQuestionMixin, CreateView):
    "Coment on a plan"

    model = PlanComment
    form_class = PlanCommentForm

    def get_success_url(self):
        question_pk = self.get_question_pk()
        plan_pk = self.get_plan_pk()
        kwargs = {'plan': plan_pk, 'question': question_pk}
        return reverse('new_question', kwargs=kwargs)

    def form_valid(self, form):
        comment = form.cleaned_data.get('comment', '')
        question_pk = self.get_question_pk()
        plan_pk = self.get_plan_pk()
        PlanComment.objects.create(plan_id=plan_pk, question_id=question_pk,
                                   comment=comment, added_by=self.request.user)
        return HttpResponseRedirect(self.get_success_url())


class PlanListView(PlanAccessViewMixin, ListView):
    "List all plans for a user"

    model = Plan
    template_name = 'easydmp/plan/plan_list.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.order_by('-added')


class PlanDetailView(AbstractQuestionMixin, DetailView):
    "Show an overview of a plan"
    model = Plan
    pk_url_kwarg = 'plan'
    template_name = 'easydmp/plan/plan_detail.html'

    def get_context_data(self, **kwargs):
        context = {
            'output': self.object.get_summary(),
            'plan': self.object,
            'template': self.object.template,
        }
        context.update(**kwargs)
        return super().get_context_data(**context)


class AbstractGeneratedPlanView(DetailView):
    model = Plan
    pk_url_kwarg = 'plan'
    login_required = False

    def get_queryset(self):
        "Show published plans to the public, otherwise only viewable"
        qs = self.model.objects.exclude(published=None)
        if self.request.user.is_authenticated():
            qs = qs | self.model.objects.viewable(self.request.user)
        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = self.object.get_context_for_generated_text()
        context.update(**kwargs)
        return super().get_context_data(**context)


class GeneratedPlanHTMLView(AbstractGeneratedPlanView):
    "Generate canned HTML of a plan"

    template_name = 'easydmp/plan/generated_plan.html'


# XXX: Remove
class GeneratedPlanPlainTextView(AbstractGeneratedPlanView):
    "Generate canned plaintext of a Plan"

    template_name = 'easydmp/plan/generated_plan.txt'
    content_type = 'text/plain; charset=UTF-8'


# XXX: Remove
class GeneratedPlanPDFView(AbstractGeneratedPlanView):
    "Generate canned PDF of a plan"

    template_name = 'easydmp/plan/generated_plan.pdf'
    content_type = 'text/plain'


class SectionDetailView(DetailView):
    """Show a section

    Mostly relevant for sections without questions.
    """

    model = Section
    pk_url_kwarg = 'section'
    template_name = 'easydmp/plan/section_detail.html'

    def get_plan(self, *args, **kwargs):
        plan_id = kwargs['plan']
        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            raise Http404
        return plan

    def check_plan(self, plan, section):
        if plan.template != section.template:
            return False
        return True

    def get_section(self, *args, **kwargs):
        section_id = kwargs['section']
        plan = self.get_plan(*args, **kwargs)
        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            raise Http404
        if not self.check_plan(plan, section):
            raise Http404
        return section

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        plan = self.get_plan(**self.kwargs)
        correct_plan = self.check_plan(plan, obj)
        if correct_plan:
            return obj
        raise Http404

    def dispatch(self, *args, **kwargs):
        section = self.get_section(**self.kwargs)
        plan = self.get_plan(**self.kwargs)

        # Set visited empty section
        plan.visited_sections.add(section)
        topmost = section.get_topmost_section()
        if topmost:
            plan.visited_sections.add(topmost)

        # Redirect to first question if any
        question = section.get_first_question()
        if question:
            return redirect('new_question', question=question.pk, plan=plan.pk)

        # Show page for empty section
        return super().dispatch(*args, **kwargs)

    def next(self):
        "Generate link to next page"
        plan = self.get_plan(**self.kwargs)
        next_section = self.object.get_next_section()
        if next_section is not None:
            question = next_section.get_first_question()
            if question:
                return reverse('new_question', kwargs={'question': question.pk,
                                                   'plan': plan.pk })
            return reverse('section_detail', kwargs={'plan': plan.pk,
                                                     'section':
                                                     next_section.pk})
        return reverse('plan_detail', kwargs={'plan': plan.pk})

    def prev(self):
        "Generate link to previous page"
        plan = self.get_plan(**self.kwargs)
        prev_section = self.object.get_prev_section()
        if prev_section is not None:
            question = prev_section.get_first_question()
            if question:
                return reverse('new_question', kwargs={'question': question.pk,
                                                   'plan': plan.pk })
            return reverse('section_detail', kwargs={'plan': plan.pk,
                                                     'section':
                                                     prev_section.pk})
        return reverse('plan_detail', kwargs={'plan': plan.pk})

    def get_context_data(self, **kwargs):
        plan = self.get_plan(**self.kwargs)
        next = self.object.get_next_section()
        prev = self.object.get_prev_section()
        context = {
            'plan': plan,
            'next': self.next(),
            'prev': self.prev(),
            'section_progress': get_section_progress(plan, self.object),
        }
        context.update(**kwargs)
        return super().get_context_data(**context)
