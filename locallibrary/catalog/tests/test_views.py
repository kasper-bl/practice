from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.auth.mixins import LoginRequiredMixin
from catalog.models import Author, Book, BookInstance, Genre, Language
import datetime
from django.utils import timezone
from django.views import generic

class AuthorListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        number_of_authors = 13
        for author_id in range(number_of_authors):
            Author.objects.create(
                first_name=f'Christian {author_id}',
                last_name=f'Surname {author_id}',
            )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/catalog/authors/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('authors'))
        self.assertTemplateUsed(response, 'catalog/author_list.html')

    def test_pagination_is_ten(self):
        response = self.client.get(reverse('authors'))
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['author_list']), 10)

    def test_lists_all_authors(self):

        response = self.client.get(reverse('authors') + '?page=2')
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['author_list']), 3)


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class LoanedBookInstancesByUserListViewTest(TestCase):
    def setUp(self):

        test_user1 = User.objects.create_user(username='testuser1', password='QWEasd123!')
        test_user2 = User.objects.create_user(username='testuser2', password='QWEasd123!')
        test_user1.save()
        test_user2.save()

        test_author = Author.objects.create(first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(
            title='Book Title',
            summary='My book summary',
            isbn='ABCDEFG',
            author=test_author,
            language=test_language,
        )
        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        number_of_book_copies = 30
        for book_copy in range(number_of_book_copies):
            return_date = timezone.now() + datetime.timedelta(days=book_copy % 5)
            the_borrower = test_user1 if book_copy % 2 else test_user2
            status = 'm'  
            BookInstance.objects.create(
                book=test_book,
                imprint='Unlikely Imprint, 2016',
                due_back=return_date,
                borrower=the_borrower,
                status=status,
            )

    def test_redirect_if_not_logged_in(self):

        resp = self.client.get(reverse('my-borrowed'))
        self.assertRedirects(resp, '/accounts/login/?next=/catalog/mybooks/')

    def test_logged_in_uses_correct_template(self):

        login = self.client.login(username='testuser1', password='QWEasd123!')
        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(str(resp.context['user']), 'testuser1')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'catalog/bookinstance_list_borrowed_user.html')

    def test_only_borrowed_books_in_list(self):

        login = self.client.login(username='testuser1', password='QWEasd123!')
        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(str(resp.context['user']), 'testuser1')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('bookinstance_list' in resp.context)
        self.assertEqual(len(resp.context['bookinstance_list']), 0)

        get_ten_books = BookInstance.objects.all()[:10]
        for copy in get_ten_books:
            copy.status = 'o'
            copy.save()

        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(str(resp.context['user']), 'testuser1')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('bookinstance_list' in resp.context)


        for bookitem in resp.context['bookinstance_list']:
            self.assertEqual(resp.context['user'], bookitem.borrower)
            self.assertEqual('o', bookitem.status)

    def test_pages_ordered_by_due_date(self):

        for copy in BookInstance.objects.all():
            copy.status = 'o'
            copy.save()

        login = self.client.login(username='testuser1', password='QWEasd123!')
        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(str(resp.context['user']), 'testuser1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['bookinstance_list']), 10)

        last_date = None
        for copy in resp.context['bookinstance_list']:
            if last_date is None:
                last_date = copy.due_back
            else:
                self.assertTrue(last_date <= copy.due_back)


class RenewBookInstancesViewTest(TestCase):
    def setUp(self):
        test_user1 = User.objects.create_user(username='testuser1', password='QWEasd123!')
        test_user2 = User.objects.create_user(username='testuser2', password='QWEasd123!')
        test_user1.save()
        test_user2.save()


        permission = Permission.objects.get(name='Set book as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()


        test_author = Author.objects.create(first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(
            title='Book Title',
            summary='My book summary',
            isbn='ABCDEFG',
            author=test_author,
            language=test_language,
        )
        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance1 = BookInstance.objects.create(
            book=test_book,
            imprint='Unlikely Imprint, 2016',
            due_back=return_date,
            borrower=test_user1,
            status='o', 
        )

        self.test_bookinstance2 = BookInstance.objects.create(
            book=test_book,
            imprint='Unlikely Imprint, 2016',
            due_back=return_date,
            borrower=test_user2,
            status='o',
        )

    def test_redirect_if_not_logged_in(self):

        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_redirect_if_logged_in_but_not_correct_permission(self):

        login = self.client.login(username='testuser1', password='QWEasd123!')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_logged_in_with_permission_borrowed_book(self):

        login = self.client.login(username='testuser2', password='QWEasd123!')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance2.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_logged_in_with_permission_another_users_borrowed_book(self):
        login = self.client.login(username='testuser2', password='QWEasd123!')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_HTTP404_for_invalid_book_if_logged_in(self):

        import uuid
        test_uid = uuid.uuid4()
        login = self.client.login(username='testuser2', password='QWEasd123!')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': test_uid}))
        self.assertEqual(resp.status_code, 404)

    def test_uses_correct_template(self):
       
        login = self.client.login(username='testuser2', password='QWEasd123!')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'catalog/book_renew_librarian.html')

    def test_form_renewal_date_initially_has_date_three_weeks_in_future(self):
       
        login = self.client.login(username='testuser2', password='QWEasd123!')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 200)
        date_3_weeks_in_future = datetime.date.today() + datetime.timedelta(weeks=3)
        self.assertEqual(resp.context['form'].initial['renewal_date'], date_3_weeks_in_future)

    def test_redirects_to_all_borrowed_book_list_on_success(self):

        login = self.client.login(username='testuser2', password='QWEasd123!')
        valid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=2)
        resp = self.client.post(
            reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}),
            {'renewal_date': valid_date_in_future}
        )
        self.assertRedirects(resp, reverse('all-borrowed'))

    def test_form_invalid_renewal_date_past(self):

        login = self.client.login(username='testuser2', password='QWEasd123!')
        date_in_past = datetime.date.today() - datetime.timedelta(weeks=1)
        resp = self.client.post(
            reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}),
            {'renewal_date': date_in_past}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp.context['form'], 'renewal_date', 'Invalid date - renewal in past')

    def test_form_invalid_renewal_date_future(self):

        login = self.client.login(username='testuser2', password='QWEasd123!')
        invalid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=5)
        resp = self.client.post(
            reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}),
            {'renewal_date': invalid_date_in_future}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp.context['form'], 'renewal_date', 'Invalid date - renewal more than 4 weeks ahead')



class AuthorCreateViewTest(TestCase):
    def setUp(self):

        self.test_user = User.objects.create_user(
            username='testuser', password='QWEasd123!'
        )
        permission = Permission.objects.get(name='Set book as returned')
        self.test_user.user_permissions.add(permission)
        self.test_user.save()

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('author-create'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_logged_in_without_permission(self):
        User.objects.create_user(username='noperm', password='QWEasd123!')
        self.client.login(username='noperm', password='QWEasd123!')
        response = self.client.get(reverse('author-create'))
        self.assertEqual(response.status_code, 403)  

    def test_logged_in_with_permission_uses_correct_template(self):
        self.client.login(username='testuser', password='QWEasd123!')
        response = self.client.get(reverse('author-create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/author_form.html')

    def test_initial_date_of_death_value(self):
        self.client.login(username='testuser', password='QWEasd123!')
        response = self.client.get(reverse('author-create'))
        self.assertEqual(
            response.context['form'].initial['date_of_death'],
            '12/10/2016'  
        )

    def test_redirects_to_author_detail_on_success(self):
        self.client.login(username='testuser', password='QWEasd123!')
        response = self.client.post(
            reverse('author-create'),
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'date_of_birth': '1980-01-01',
                'date_of_death': '2020-01-01',
            }
        )
        self.assertEqual(Author.objects.count(), 1)
        new_author = Author.objects.first()
        self.assertRedirects(response, reverse('author-detail', kwargs={'pk': new_author.pk}))