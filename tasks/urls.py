from django.urls import path
from tasks.views import manager_deshboard, employee_deshboard, test, create_task,view_task,update_task, task_details, dashboard, CreateTask, ViewProject, TaskDetail,DeleteTask, UpdateTask
urlpatterns =[
    path('manager_dashboard/', manager_deshboard, name="manager-dashboard"),
    path('user_dashboard/', employee_deshboard, name='user-dashboard'),
    path('test/', test),
    path('create-task/', CreateTask.as_view(), name='create-task'),
    path('view_task/', ViewProject.as_view(), name='view-task'),
    path('task/<int:task_id>/details', TaskDetail.as_view(),  name='task-details'),
    path('update-task/<int:id>/', UpdateTask.as_view(), name='update-task'),
    path('delete-task/<int:id>/', DeleteTask.as_view(), name='delete-task'),
    path('dashboard/', dashboard, name='dashboard')
]