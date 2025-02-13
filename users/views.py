from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from users.forms import RegisterForm,CustomRegistrationForm
from django.contrib.auth.models import  Group
from django.contrib.auth  import login, authenticate, logout
from django.contrib import  messages
from django.contrib.auth.forms import AuthenticationForm
from users.forms  import LoginForm, AssignedRoleForm, CreateGroupForm, CustomPasswordChangeForm, CustomPasswordResetForm,CustomPasswordResetConfirmForm, EditProfileForm
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Prefetch
from django.contrib.auth.views import LoginView, PasswordChangeView,PasswordChangeDoneView,PasswordResetConfirmView, PasswordResetView
from django.views.generic import TemplateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth import get_user_model
from django.views import View
from django.views.generic.base import ContextMixin
User = get_user_model()

# Create your views here.

# Test for users
def is_admin(user):
    return user.groups.filter(name='Admin').exists()




def sign_up(request):
    if request.method == 'GET':
        form = CustomRegistrationForm()
    if request.method == 'POST':
        form = CustomRegistrationForm(request.POST)
        if form.is_valid():
           user = form.save(commit=False)
           print('user', user)
           user.set_password(form.cleaned_data.get('password1'))
           print(form.cleaned_data)
           user.is_active = False
           user.save()
           messages.success(request, 'A Confirmation mail sent. Please Check your Email')
           return redirect('sign-in')
           
    
    return render(request,'registration/register.html', {"form":    form})


class CustomLoginView(LoginView):
    form_class = LoginForm
    
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        return next_url if next_url else super().get_success_url()
    
  
  
class ChangePassword(PasswordChangeView):
    template_name='accounts/password_change.html'
    form_class = CustomPasswordChangeForm
    

def sign_in(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            print(user)
            login(request, user)
            return redirect('home')
        
            
    return render(request,'registration/login.html', {'form': form})

@login_required
def sign_out(request):
    if request.method == 'POST':
        logout(request)
        return redirect('sign-in')
        


def activate_user(request, user_id, token):
    try:
        user = User.objects.get(id=user_id)
        if  default_token_generator.check_token(user,  token):
            user.is_active = True
            user.save()
            return redirect('sign-in')
        
        else:
            return HttpResponse('Invalid Id or Token')
    except User.DoesNotExist:
        return HttpResponse('User not found')
  
@user_passes_test(is_admin, login_url='no-permission')
def admin_dashboard(request):
    users= User.objects.prefetch_related(
        Prefetch('groups', queryset=Group.objects.all(), to_attr='all_groups')                               
    ).all()
    for user in users:
        if user.all_groups:
            user.group_name = user.all_groups[0].name
        else:
            user.group_name = 'No Group Assigned'
        
    return render(request,'admin/dashboard.html', {"users": users})


class AssignRoleView(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = User
    form_class = AssignedRoleForm
    template_name = 'admin/assign_role.html'
    context_object_name = 'user'
    pk_url_kwarg = 'user_id'
    permission_required = "auth.change_user"
    
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = AssignedRoleForm(request.POST)
        
        if form.is_valid():
            role = form.cleaned_data.get('role')
            self.object.groups.clear() 
            self.object.groups.add(role)
            messages.success(request, f'User {self.object.username} has been assigned to the {role.name} role')
            return redirect('admin-dashboard')
        return redirect('admin-dashboard')
    def get_success_url(self):
        return reverse_lazy('admin-dashboard')
  
  
@user_passes_test(is_admin, login_url='no-permission') 
def create_group(request):
    form = CreateGroupForm()
    if request.method == 'POST':
        form = CreateGroupForm(request.POST)
        
        if form.is_valid():
            group = form.save()
            messages.success(request, f'Group {group.name} has been created successfully')
            return redirect('create-group')
        
    return render(request, 'admin/create_group.html', {'form': form}) 


class CreateGroup(ContextMixin,LoginRequiredMixin,PermissionRequiredMixin,View):
    permission_required = 'tasks.add_task'
    login_url = 'sign-in'
    template_name = 'admin/create_group.html'
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = kwargs.get('form', CreateGroupForm())
        return context
    # GET 
    def get(self, request, *args, **kwargs ):
        context = self.get_context_data()
        return render(request, self.template_name, context)
    # POST
    def post(self, request, *args, **kwargs):
        form = CreateGroupForm(request.POST)
        
        if form.is_valid():
            group = form.save()
            messages.success(request, f'Group {group.name} has been created successfully')
            return redirect('create-group')




class GrouplistView(ListView):
    model = Group
    context_object_name = 'groups'
    template_name = 'admin/group_list.html'
    queryset = Group.objects.prefetch_related('permissions').all()
    
class ProfileView(TemplateView):
    template_name = 'accounts/profile.html'
    # pass
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['username'] = user.username
        context['email'] = user.email 
        context['name'] = user.get_full_name()
        context['bio'] = user.bio
        context['profile_image'] = user.profile_image
        context['member_since'] = user.date_joined
        context['last_login'] = user.last_login
        return context
    
"""   
class EditProfileView(UpdateView):
    model = User
    form_class = EditProfileForm
    template_name = 'accounts/update_profile.html'
    context_object_name = 'form'
    
    def get_object(self):
        return self.request.user
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['userprofile'] = UserProfile.objects.get(user=self.request.user)
        return kwargs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = UserProfile.objects.get(user=self.request.user)
        context['form'] = self.form_class(instance=self.object, userprofile= user_profile)
        return context
    
    
    def form_valid(self, form):
        form.save(commit=True)
        return redirect('profile')
"""  

class EditProfileView(UpdateView):
    model = User
    form_class = EditProfileForm
    template_name = 'accounts/update_profile.html'
    context_object_name = 'form'
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        form.save()
        return redirect('profile')




  
class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'registration/reset_password.html'
    success_url = reverse_lazy('sign-in')
    html_email_template_name = 'registration/reset_email.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['protocol'] = 'https' if self.request.is_secure() else 'http'
        context['domain'] = self.request.get_host()
        return context
    
    def form_valid(self, form):
        messages.success(
            self.request, 'A Reset email sent. Please check your email'
        )
        return super().form_valid(form)
        
        
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomPasswordResetConfirmForm
    template_name = 'registration/reset_password.html'
    success_url = reverse_lazy('sign-in')
    
    def form_valid(self, form):
        messages.success(
            self.request, 'Password reset successfully'
        )
        return super().form_valid(form)
    
    