from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models


class BaseModel(models.Model):
    create_timestamp = models.DateTimeField(auto_now_add=True)
    update_timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Exam(BaseModel):
    QUESTION_MIN_LIMIT = 3
    QUESTION_MAX_LIMIT = 100

    class LEVEL(models.IntegerChoices):
        BASIC = 0, 'Basic',
        MIDDLE = 1, 'Middle',
        ADVANCED = 2, 'Advanced',

    uuid = models.UUIDField(default=uuid4, db_index=True, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    level = models.PositiveSmallIntegerField(choices=LEVEL.choices, default=LEVEL.BASIC)

    def __str__(self):
        return self.title

    # def questions_count(self):
    #     return self.questions.count()

    class Meta:
        db_table = 'exam'
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'


class Question(BaseModel):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    order_num = models.PositiveSmallIntegerField()
    text = models.CharField(max_length=1024)
    image = models.ImageField(upload_to='questions/', null=True, blank=True)

    def __str__(self):
        return self.text

    class Meta:
        db_table = 'question'
        verbose_name = 'question'
        verbose_name_plural = 'questions'


class Choice(BaseModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=1024)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

    class Meta:
        db_table = 'choice'
        verbose_name = 'Choice'
        verbose_name_plural = 'Choices'


class Result(BaseModel):
    class STATE(models.IntegerChoices):
        NEW = 0, 'New',
        FINISHED = 1, 'Finished',

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='results')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    state = models.PositiveSmallIntegerField(choices=STATE.choices, default=STATE.NEW)
    uuid = models.UUIDField(default=uuid4, db_index=True, unique=True)
    current_order_number = models.PositiveSmallIntegerField(default=0)
    num_correct_answers = models.PositiveSmallIntegerField(default=0)
    num_incorrect_answers = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'result'
        verbose_name = 'Result'
        verbose_name_plural = 'Results'

    def update_result(self, order_number, question, select_choices):
        correct_choice = [choice.is_correct for choice in question.choices.all()]
        correct_answer = True
        for zip_group in zip(select_choices, correct_choice):
            correct_answer = correct_answer and (zip_group[0] == zip_group[1])

        self.num_correct_answers += int(correct_answer)
        self.num_incorrect_answers += 1 - int(correct_answer)
        self.current_order_number = order_number

        if order_number == question.exam.questions.count():
            self.state = self.STATE.FINISHED

        self.save()
