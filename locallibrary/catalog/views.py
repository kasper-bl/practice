from django.shortcuts import render
from .models import Book, Author, BookInstance, Genre, Language

from django.contrib.auth.mixins import LoginRequiredMixin

def index(request):

    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()  
    num_genres = Genre.objects.count()
    search_word = 'окак'
    num_visits=request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits+1

    num_books_with_word = Book.objects.filter(title__icontains=search_word).count()
    num_visits += 1
    request.session['num_visits'] = num_visits

    return render(
        request,
        'index.html',
        context={'num_books': num_books, 'num_instances': num_instances,
                 'num_instances_available': num_instances_available, 'num_authors': num_authors,
                 'num_genres': num_genres,
                 'num_books_with_word': num_books_with_word,
                 'num_visits': num_visits},
    )

from django.views import generic

class BookDetailView(generic.DetailView):
    model = Book

class BookListView(generic.ListView):
    model = Book
    paginate_by = 2

class AuthorListView(generic.ListView):
    model = Author

class AuthorDetailView(generic.DetailView):
    model = Author

class AuthorUpdateView(generic.UpdateView):
    model = Author



class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 2

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

