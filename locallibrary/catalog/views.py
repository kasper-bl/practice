from django.shortcuts import render
from .models import Book, Author, BookInstance, Genre, Language

def index(request):

    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_instances_available = BookInstance.objects.filter(
        status__exact='a').count()
    num_authors = Author.objects.count()  
    num_genres = Genre.objects.count()
    search_word = 'окак'

    num_books_with_word = Book.objects.filter(title__icontains=search_word).count()

    num_visits = request.session.get('num_visits', 0)
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