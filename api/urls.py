# api/urls.py
from django.urls import path
from .views import PromptAPIViewAsync, FileDownloadView, FileSystemView, FileContentView,AvailableModelsView,StopAgentView

urlpatterns = [
    path('prompt/', PromptAPIViewAsync.as_view(), name='prompt_async'),
    path('files/list/', FileSystemView.as_view(), name='list_files'),
    path('files/download/', FileDownloadView.as_view(), name='download_file'),
    path('files/view/', FileContentView.as_view(), name='see_file'),
    path('models/', AvailableModelsView.as_view(), name='available-models'),  # ADD THIS LINE
    path('agent/stop/', StopAgentView.as_view(), name='stop-agent'),

]