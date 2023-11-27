import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Question


class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)


    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=2)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)


    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is between now and 1 day in the past.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)


def create_question(question_text, days, choices=(())):
    """
    Create a question with the given `question_text` having the pub_date set according to number of `days` from now
    (negative for questions published in the past, positive for questions that have yet to be published). Add choices
    to the question if any.
    """
    time = timezone.now() + datetime.timedelta(days=days)
    question = Question.objects.create(question_text=question_text, pub_date=time)
    for choice_text in choices:
        question.choice_set.create(choice_text=choice_text, votes=0)
    return question


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_past_question_without_choice(self):
        """
        Questions with a pub_date in the past and having no choice are not displayed on the
        index page.
        """
        create_question(question_text="Past question.", days=0)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_past_question_with_one_choice(self):
        """
        Questions with a pub_date in the past and having one choice are not displayed on the
        index page.
        """
        create_question(question_text="Past question.", days=-30, choices=("Childhood",))
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"],[])

    def test_past_question_with_choices(self):
        """
        Questions with a pub_date in the past and having at least two choices are displayed on the
        index page.
        """
        question = create_question(question_text="Past question.", days=0, choices=("Childhood", "Young age"))
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question],
        )

    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't displayed on
        the index page.
        """
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        with at least two choices are displayed.
        """
        question = create_question(question_text="Past question.", days=0, choices=("Childhood", "Young age", "Old age"))
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question],
        )

    def test_two_past_questions_with_choices(self):
        """
        The questions index page may display multiple questions.
        """
        question1 = create_question(question_text="Past question 1.", days=-30, choices=("Childhood", "Young age", "Old age"))
        question2 = create_question(question_text="Past question 2.", days=-5, choices=("Old age", "D","E","F","G"))
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question2, question1],
        )

    def test_past_questions_with_and_without_choices(self):
        """
        Even if both choice and no choice questions exist, only the question with at least two choices is
        displayed.
        """
        question = create_question(question_text="What's new?", days=0, choices=("My car", "My house", "My bike"))
        create_question(question_text="What's my name?", days=0)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question],
        )


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text="Future question.", days=1, choices=("My car",))
        url = reverse("polls:detail", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question_without_choice(self):
        """
        The detail view of a question with a pub_date in the past and having no choice
        returns a 404 not found.
        """
        past_question = create_question(question_text="Past question.", days=1)
        url = reverse("polls:detail", args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question_with_one_choice(self):
        """
        The detail view of a question with a pub_date in the past and having one choice
        returns a 404 not found.
        """
        past_question = create_question(question_text="Past question.", days=1, choices=("My car",))
        url = reverse("polls:detail", args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question_with_choices(self):
        """
        The detail view of a question with a pub_date in the past and having at least two choices displays the question's text.
        """
        past_question = create_question(question_text="Past Question.", days=-5, choices=("Childhood", "Young age","Old age"))
        url = reverse("polls:detail", args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)



class QuestionResultsViewTests(TestCase):
    def test_future_question(self):
        """
        The results view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text="Future question.", days=5, choices=("Childhood", "Young age"))
        url = reverse("polls:results", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question_without_choice(self):
        """
        The results view of a question with a pub_date in the past and having no choice
        returns a 404 not found.
        """
        past_question = create_question(question_text="Past question.", days=1)
        url = reverse("polls:results", args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question_with_one_choice(self):
        """
        The results view of a question with a pub_date in the past and having one choice
        returns a 404 not found.
        """
        past_question = create_question(question_text="Past question.", days=1, choices=("My car",))
        url = reverse("polls:results", args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question_with_choices(self):
        """
        The results view of a question with a pub_date in the past and having at least two choices displays the question's text.
        """
        past_question = create_question(question_text="Past Question.", days=-5, choices=("Childhood", "Young age","Old age"))
        url = reverse("polls:results", args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)
