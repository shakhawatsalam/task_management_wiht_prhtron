from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from tasks.forms import TaskModelForm, TaskForm, TaskDetailModelForm
from  tasks.models import Task, Project
from datetime import date, timedelta
from django.db.models import Q, Count, Max, Min, Avg
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from users.views import is_admin
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.base import ContextMixin
from django.views.generic import ListView, DetailView, UpdateView, DeleteView

# Test For Tasks
def is_manager(user):
    return user.groups.filter(name='Manager').exists()
def is_employee(user):
    return user.groups.filter(name='Manager').exists()

# manager dashboard 
@user_passes_test(is_manager, login_url='no-permission')
def manager_deshboard(request):
   
    counts = Task.objects.aggregate(
        total=Count('id'), 
        completed=Count('id', filter=Q(status="COMPLETED")),
        in_progress=Count('id', filter=Q(status="IN_PROGRESS")),
        pending=Count('id', filter=Q(status="PENDING")),
    )
    
    type = request.GET.get('type', 'all')
    base_query = Task.objects.select_related('details').prefetch_related('assigned_to')  # One to One ->  selected_related Many to Many -> prefetch_related
    
    if type == 'completed':
        tasks = base_query.filter(status='COMPLETED')
    elif type == 'in_progress':
        tasks = base_query.filter(status='IN_PROGRESS')
    elif type == 'pending':
        tasks = base_query.filter(status='PENDING')
    elif type == 'all':
        tasks = base_query.all()
    # Retriving task data
    context = {
        "tasks": tasks,
        "counts": counts
    }
    return render(request, 'dashboard/manager-dashboard.html', context)

class ManagerDashboard(LoginRequiredMixin,PermissionRequiredMixin,ListView):
    permission_required = 'tasks.add_task'
    login_url = 'sign-in'
    template_name = 'dashboard/manager-dashboard.html'
    context_object_name = 'tasks'
    
    def get_queryset(self):
        self.counts = Task.objects.aggregate(
        total=Count('id'), 
        completed=Count('id', filter=Q(status="COMPLETED")),
        in_progress=Count('id', filter=Q(status="IN_PROGRESS")),
        pending=Count('id', filter=Q(status="PENDING")),
        )
    
        type = self.request.GET.get('type', 'all')
        base_query = Task.objects.select_related('details').prefetch_related('assigned_to')  # One to One ->  selected_related Many to Many -> prefetch_related
    
        if type == 'completed':
            tasks = base_query.filter(status='COMPLETED')
        elif type == 'in_progress':
            tasks = base_query.filter(status='IN_PROGRESS')
        elif type == 'pending':
            tasks = base_query.filter(status='PENDING')
        elif type == 'all':
            tasks = base_query.all()
            
        return tasks
            
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['counts'] = self.counts
        print(context, "form get context data ✅✅✅✅✅✅")
        return context
    


# user dashboard 
@user_passes_test(is_employee, login_url='no-permission')
def employee_deshboard(request):
    return render(request, 'dashboard/user-dashboard.html')




def test(request):
    context = {
        "names": ["Mahmud", "Ahamed", "Jhone"]
    }
    return render(request, 'test.html', context )

@login_required
@permission_required("tasks.add_task", login_url='no-permission')
def create_task(request):
    task_form = TaskModelForm() # For GET
    task_detail_form = TaskDetailModelForm()
    if  request.method == "POST":
        task_form = TaskModelForm(request.POST ) # For GET
        task_detail_form = TaskDetailModelForm(request.POST,request.FILES)
        if task_form.is_valid() and  task_detail_form.is_valid():
            task = task_form.save()
            task_detail = task_detail_form.save(commit=False)
            task_detail.task = task
            task_detail.save()
            messages.success(request,"Task Created Successfully")
            return redirect('create-task')   


# variable for list of decorators
decorators = [login_required, permission_required("tasks.add_task", login_url='no-permission')]

# CLASS BASE VIEW CREATE TASK
class CreateTask(ContextMixin,LoginRequiredMixin,PermissionRequiredMixin,View):
    """FOR CREATING TASK"""
    permission_required = 'tasks.add_task'
    login_url = 'sign-in'
    template_name = 'task_form.html'
    
    # OverWriting of Contex Mixin
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task_form'] = kwargs.get('task_form', TaskModelForm())
        context['task_detail_form'] = kwargs.get('task_detail_form', TaskDetailModelForm())
        return context
    # GET 
    def get(self, request, *args, **kwargs ):
        context = self.get_context_data()
        return render(request, self.template_name, context)
    
    # POST
    def post(self, request, *args, **kwargs):
        task_form = TaskModelForm(request.POST ) # For GET
        task_detail_form = TaskDetailModelForm(request.POST,request.FILES)
        if task_form.is_valid() and  task_detail_form.is_valid():
            task = task_form.save()
            task_detail = task_detail_form.save(commit=False)
            task_detail.task = task
            task_detail.save()
            messages.success(request,"Task Created Successfully")
            context = self.get_context_data(
                task_form=task_form, task_detail_form=task_detail_form)
            return render(request, self.template_name, context)
    

@login_required
@permission_required("tasks.change_task", login_url='no-permission')
def update_task(request, id):
    task = Task.objects.get(id=id)
    task_form = TaskModelForm(instance=task) # For GET
    if  task.details:
        task_detail_form = TaskDetailModelForm(instance=task.details)
    if  request.method == "POST":
        task_form = TaskModelForm(request.POST, instance=task) # For GET
        task_detail_form = TaskDetailModelForm(request.POST,instance=task.details)
        if task_form.is_valid() and  task_detail_form.is_valid():
            """For  Model  Form Date"""
            task = task_form.save()
            task_detail = task_detail_form.save(commit=False)
            task_detail.task = task
            task_detail.save()
            messages.success(request,"Task Updated Successfully")
            return redirect('update-task',id)  
    context = {"task_form":  task_form, "task_detail_form": task_detail_form}
    return render(request, 'task_form.html', context)


# CLASS BASE VIEW FOR UPDATE TASK
class UpdateTask(UpdateView):
    model = Task
    form_class = TaskModelForm
    template_name = 'task_form.html'
    context_object_name = 'task'
    pk_url_kwarg = 'id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.get_object()
        
        context['task_form'] = self.get_form()
        
        if hasattr(self.object, 'details') and self.object.details :
            context['task_detail_form'] = TaskDetailModelForm(instance=self.object.details )
        else:
            context['task_detail_form'] = TaskDetailModelForm()
            
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        task_form = TaskModelForm(request.POST, instance = self.object)
        
        task_detail_form = TaskDetailModelForm(request.POST,request.FILES, instance= getattr(self.object,'details', None))
        
        if task_form.is_valid() and  task_detail_form.is_valid():
            """For  Model  Form Date"""
            task = task_form.save()
            task_detail = task_detail_form.save(commit=False)
            task_detail.task = task
            task_detail.save()
            messages.success(request,"Task Updated Successfully")
            return redirect('update-task',self.object.id)  
        return redirect('update-task', self.object.id)
        
  
class DeleteTask(DeleteView, LoginRequiredMixin, PermissionRequiredMixin,):       
    model = Task
    pk_url_kwarg = 'id'
    success_url = reverse_lazy('manager-dashboard')
            



@login_required
@permission_required("tasks.view_task", login_url='no-permission')
def view_task(request):
    projects = Project.objects.annotate(
        num_task=Count('task')
    ).order_by('num_task')
   
    
    return render(request, 'show_task.html', {"projects": projects})


# CLASS BASED VIEW FOR VIEW TASK'S
view_project_decorators = [login_required, permission_required("projects.view_project", login_url='no-permission')] 
@method_decorator(view_project_decorators, name='dispatch')
class ViewProject(ListView):
    model = Project
    context_object_name = 'projects'
    template_name = 'show_task.html'
    
    def get_queryset(self):
        queryset = Project.objects.annotate(
        num_task=Count('task')
    ).order_by('num_task')
        return queryset
    
    
    
    
@login_required
@permission_required("tasks.view_task", login_url='no-permission')   
def task_details(request, task_id):
    task = Task.objects.get(id=task_id)
    status_choice =  Task.STATUS_CHOICES
    if request.method == 'POST':
        selected_status =  request.POST.get('task_status')
        task.status = selected_status
        task.save()
        return redirect( 'task-details', task.id)
    return render(request, 'task_details.html', {"task": task, 'status_choices': status_choice})
 
# CLASS BASED VIEW FOR TASK DETAILS 
class TaskDetail(DetailView):
    model = Task
    template_name = 'task_details.html'
    context_object_name = 'task'
    pk_url_kwarg = 'task_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Task.STATUS_CHOICES
        return context
    
    def post(self, request, *args, **kwargs):
        task = self.get_object()
        selected_status =  request.POST.get('task_status')
        task.status = selected_status
        task.save()
        return redirect( 'task-details', task.id)






@login_required
def dashboard(request):
    if is_manager(request.user):
        return redirect('manager-dashboard')
    elif is_employee(request.user):
        return redirect('user-dashboard')
    elif is_admin(request.user):
        return redirect('admin-dashboard')
    return redirect('no-permission')