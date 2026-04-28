from django.urls import path

from .views import ReadingCreateView, ReadingDeleteView, ReadingListView, ReadingUpdateView

urlpatterns = [
    path("", ReadingListView.as_view(), name="reading-list"),
    path("nueva/", ReadingCreateView.as_view(), name="reading-create"),
    path("<int:pk>/editar/", ReadingUpdateView.as_view(), name="reading-update"),
    path("<int:pk>/eliminar/", ReadingDeleteView.as_view(), name="reading-delete"),
]
