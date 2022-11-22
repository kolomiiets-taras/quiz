from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic.list import MultipleObjectMixin

from .forms import ChoicesFormSet
from .models import Exam
from .models import Question
from .models import Result


class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = 'exam/list.html'
    context_object_name = 'exams'       # object_list


class ExamDetailView(LoginRequiredMixin, DetailView, MultipleObjectMixin):
    model = Exam
    template_name = 'exam/details.html'
    context_object_name = 'exam'
    pk_url_kwarg = 'uuid'
    paginate_by = 3

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return self.model.objects.get(uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(object_list=self.get_queryset(), **kwargs)

        return context

    def get_queryset(self):
        return Result.objects.filter(
            exam=self.get_object(),
            user=self.request.user
        ).order_by('state', '-create_timestamp')    # ORDER BY state ASC, create_timestamp DESC


class ExamResultCreateView(LoginRequiredMixin, CreateView):
    def post(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        result = Result.objects.create(
            user=request.user,
            exam=Exam.objects.get(uuid=uuid),
            state=Result.STATE.NEW
        )

        result.save()

        return HttpResponseRedirect(
            reverse(
                'quiz:question',
                kwargs={
                    'uuid': uuid,
                    'res_uuid': result.uuid,
                    # 'order_num': 1
                }
            )
        )


class ExamResultQuestionView(LoginRequiredMixin, UpdateView):
    def get_params(self, **kwargs):
        uuid = kwargs.get('uuid')
        res_uuid = kwargs.get('res_uuid')
        # order_num = kwargs.get('order_num')
        order_num = Result.objects.filter(
            uuid=res_uuid, user=self.request.user
        ).values('current_order_number').first()['current_order_number'] + 1

        return uuid, res_uuid, order_num

    def get_question(self, uuid, order_num):
        return Question.objects.get(
            exam__uuid=uuid,
            order_num=order_num,
        )

    def get(self, request, *args, **kwargs):
        uuid, res_uuid, order_num = self.get_params(**kwargs)
        question = self.get_question(uuid, order_num)

        choices = ChoicesFormSet(queryset=question.choices.all())

        return render(request, 'exam/question.html', context={'question': question, 'choices': choices})

    def post(self, request, *args, **kwargs):
        uuid, res_uuid, order_num = self.get_params(**kwargs)
        question = self.get_question(uuid, order_num)

        choices = ChoicesFormSet(data=request.POST)
        selected_choices = ['is_selected' in form.changed_data for form in choices.forms]

        if sum(selected_choices) == len(choices):
            messages.error(request, f'You can`t select all answers')
            return HttpResponseRedirect(reverse('quiz:question', kwargs={'uuid': uuid, 'res_uuid': res_uuid}))

        elif sum(selected_choices) == 0:
            messages.error(request, f'Select at least one answer')
            return HttpResponseRedirect(reverse('quiz:question', kwargs={'uuid': uuid, 'res_uuid': res_uuid}))

        else:
            result = Result.objects.get(uuid=res_uuid)
            result.update_result(order_num, question, selected_choices)

            if result.state == Result.STATE.FINISHED:
                return HttpResponseRedirect(
                    reverse(
                        'quiz:result_details',
                        kwargs={
                            'uuid': uuid,
                            'res_uuid': result.uuid
                        }
                    )
                )

            return HttpResponseRedirect(
                reverse(
                    'quiz:question',
                    kwargs={
                        'uuid': uuid,
                        'res_uuid': res_uuid,
                        # 'order_num': order_num + 1
                    }
                )
            )


class ExamResultDetailView(LoginRequiredMixin, DetailView):
    model = Result
    template_name = 'result/details.html'
    context_object_name = 'result'
    pk_url_kwarg = 'uuid'

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('res_uuid')

        return self.get_queryset().get(uuid=uuid)


class ExamResultUpdateView(LoginRequiredMixin, UpdateView):
    def get(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        res_uuid = kwargs.get('res_uuid')
        user = request.user

        result = Result.objects.get(
            user=user,
            uuid=res_uuid,
            # exam__uuid=uuid,
        )

        return HttpResponseRedirect(
            reverse(
                'quiz:question',
                kwargs={
                    'uuid': uuid,
                    'res_uuid': res_uuid,
                    # 'order_num': result.current_order_number + 1
                }
            )
        )


class ExamResultDeleteView(LoginRequiredMixin, DeleteView):
    model = Result
    template_name = 'result/delete.html'
    success_url = reverse_lazy('quiz:list')
    pk_url_kwarg = 'uuid'

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('res_uuid')

        return self.get_queryset().get(uuid=uuid)
