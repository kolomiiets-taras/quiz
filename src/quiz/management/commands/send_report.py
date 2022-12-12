from datetime import timedelta, time, datetime

from django.core.mail import mail_admins
from django.core.management import BaseCommand
from django.utils import timezone
from django.utils.timezone import make_aware
from prettytable import PrettyTable

from quiz.models import Result


class Command(BaseCommand):
    help = "Send Today's Report to Admins"

    def handle(self, *args, **options):
        today_start = make_aware(datetime.combine(timezone.now(), time()))
        today_end = make_aware(datetime.combine(timezone.now() + timedelta(1), time()))

        results = Result.objects.filter(update_timestamp__range=(today_start, today_end), state=1)
        # WHERE update_timestamp >= today_start AND update_timestamp < today_end
        # WHERE update_timestamp BETWEEN today_start AND today_end

        if results:
            # message = ""
            x = PrettyTable()
            x.field_names = ['User name', 'Test', 'Cor/Incor', 'Points', 'Duration']

            for result in results:
                x.add_row(
                    [
                        result.user.username,
                        result.exam.title,
                        f'{result.num_correct_answers}/{result.num_incorrect_answers}',
                        result.points(),
                        f'{round((result.update_timestamp - result.create_timestamp).total_seconds())}s.'
                    ]
                )
                # message += f"{result.user.username}  " \
                #            f"{result.exam.title}  " \
                #            f"{result.num_correct_answers}/{result.num_incorrect_answers}  " \
                #            f"{round((result.update_timestamp - result.create_timestamp).total_seconds())}\n"

            subject = f"Report from {today_start.strftime('%Y-%m-%d')} " \
                      f"to {today_end.strftime('%Y-%m-%d')}"

            mail_admins(subject=subject, message=x.get_string(), html_message=None)

            self.stdout.write("E-mail Report was sent.")
        else:
            self.stdout.write("No orders confirmed today.")
