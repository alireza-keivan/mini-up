from django.shortcuts import render


def home(request):
    return render(request, 'core/home.html', {'title': 'صفحه اصلی'})


def virtual_services(request):
    return render(request, 'core/virtual_services.html', {'title': 'خدمات مجازی'})


def gaming_products(request):
    return render(request, 'core/gaming_products.html', {'title': 'محصولات گیمینگ'})


def buy_products(request):
    return render(request, 'core/buy_products.html', {'title': 'خرید محصولات'})


def mini_game(request):
    return render(request, 'core/mini_game.html', {'title': 'مینی گیم'})


def consulting(request):
    return render(request, 'core/consulting.html', {'title': 'مشاوره بازی'})


def about(request):
    return render(request, 'core/about.html', {'title': 'درباره ما'})


def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    return render(request, 'errors/500.html', status=500)
