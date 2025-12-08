from django.shortcuts import render

class CustomErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Catch 404 errors
        if response.status_code == 404:
            return render(request, "404.html", status=404)

        # Catch 500 errors (optional)
        if response.status_code == 500:
            return render(request, "500.html", status=500)

        return response
