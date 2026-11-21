
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.db.models import Sum
from django.contrib import messages

from .models import SavedContent, ContentPlan, Analytics
from .forms import ContentPlanForm, AnalyticsForm, RegisterForm
from .services import generate_ai_content


# ==========================================
# AI TOOLS CONFIGURATION
# ==========================================

TOOLS = {
    'writer': {
        'name': 'AI Writer',
        'instruction': (
            'Create engaging social media content, '
            'including scripts, titles, captions and hashtags.'
        ),
    },

    'prompt': {
        'name': 'Prompt Designer',
        'instruction': (
            'Create a detailed professional AI prompt '
            'based on the user requirements.'
        ),
    },

    'video': {
        'name': 'AI Video Concept',
        'instruction': (
            'Create a video concept with a hook, '
            'voiceover, storyboard and scene breakdown.'
        ),
    },

    'ideas': {
        'name': 'Idea Generator',
        'instruction': (
            'Generate 10 creative and actionable '
            'social media content ideas.'
        ),
    },

    'planning': {
        'name': 'AI Content Planner',
        'instruction': (
            'Create a structured 7-day social media '
            'content calendar with daily post ideas.'
        ),
    },
}


# ==========================================
# REGISTRATION
# ==========================================

def register_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':

        form = RegisterForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Account created successfully! Please login.'
            )

            return redirect('login')

        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)

    else:
        form = RegisterForm()

    return render(request, 'register.html', {
        'form': form
    })


# ==========================================
# LOGIN
# ==========================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            messages.success(
                request,
                f'Welcome back, {user.username}!'
            )

            return redirect('dashboard')

        messages.error(
            request,
            'Invalid username or password.'
        )

    return render(request, 'login.html')


# ==========================================
# LOGOUT
# ==========================================

@login_required
@require_POST
def logout_view(request):

    logout(request)

    messages.success(
        request,
        'You have been logged out successfully.'
    )

    return redirect('login')


# ==========================================
# DASHBOARD
# ==========================================

@login_required
def dashboard(request):

    context = {
        'saved_count': SavedContent.objects.count(),

        'planned_count': ContentPlan.objects.count(),

        'views_count': Analytics.objects.aggregate(
            total=Sum('views')
        )['total'] or 0,

        'recent_content': SavedContent.objects.order_by(
            '-created_at'
        )[:5],
    }

    return render(request, 'dashboard.html', context)


# ==========================================
# AI GENERATION
# ==========================================

@login_required
def ai_tool(request, tool):

    if tool not in TOOLS:
        raise Http404('Tool not found')

    config = TOOLS[tool]

    result = ''
    topic = ''
    platform = 'YouTube'
    language = 'English'

    if request.method == 'POST':

        topic = request.POST.get('topic', '').strip()

        platform = request.POST.get(
            'platform', 'YouTube'
        )

        language = request.POST.get(
            'language', 'English'
        )

        if request.POST.get('action') == 'save':

            content = request.POST.get('result', '').strip()

            if topic and content:

                SavedContent.objects.create(
                    title=topic[:255],
                    module=config['name'],
                    prompt=topic,
                    content=content
                )

                messages.success(
                    request,
                    'Content saved!'
                )

                return redirect('saved_content')

            messages.error(
                request,
                'Content cannot be empty.'
            )

        elif not topic or len(topic) > 4000:

            messages.error(
                request,
                'Enter a topic between 1 and 4000 characters.'
            )

        else:

            prompt = f"""
            You are an expert digital content creator.

            Task: {config['instruction']}
            Topic: {topic}
            Platform: {platform}
            Language: {language}

            Provide practical and original content.
            Avoid unsupported factual claims.
            """

            try:

                result = generate_ai_content(prompt)

            except Exception:

                messages.error(
                    request,
                    'AI generation failed. Check API key, '
                    'model availability and API quota.'
                )

    return render(request, 'ai_tool.html', {
        'tool_name': config['name'],
        'tool': tool,
        'result': result,
        'topic': topic,
        'platform': platform,
        'language': language,
    })


# ==========================================
# SAVED CONTENT
# ==========================================

@login_required
def saved_content(request):

    query = request.GET.get('q', '')

    items = SavedContent.objects.filter(
        title__icontains=query
    ).order_by('-created_at')

    return render(request, 'saved_content.html', {
        'items': items,
        'query': query,
    })


@login_required
def edit_content(request, pk):

    item = get_object_or_404(
        SavedContent,
        pk=pk
    )

    if request.method == 'POST':

        title = request.POST.get('title', '').strip()

        content = request.POST.get('content', '').strip()

        if title and content:

            item.title = title[:255]
            item.content = content
            item.save()

            return redirect('saved_content')

    return render(request, 'edit_content.html', {
        'item': item
    })


@login_required
@require_POST
def delete_content(request, pk):

    item = get_object_or_404(
        SavedContent,
        pk=pk
    )

    item.delete()

    return redirect('saved_content')


# ==========================================
# SOCIAL MEDIA PLANNER
# ==========================================

@login_required
def planner(request):

    form = ContentPlanForm(
        request.POST if request.method == 'POST' else None
    )

    if request.method == 'POST' and form.is_valid():

        form.save()

        return redirect('planner')

    plans = ContentPlan.objects.order_by(
        'publish_date'
    )

    return render(request, 'planner.html', {
        'form': form,
        'plans': plans,
    })


@login_required
def edit_plan(request, pk):

    plan = get_object_or_404(
        ContentPlan,
        pk=pk
    )

    form = ContentPlanForm(
        request.POST if request.method == 'POST' else None,
        instance=plan
    )

    if request.method == 'POST' and form.is_valid():

        form.save()

        return redirect('planner')

    return render(request, 'edit_plan.html', {
        'form': form
    })


@login_required
@require_POST
def delete_plan(request, pk):

    plan = get_object_or_404(
        ContentPlan,
        pk=pk
    )

    plan.delete()

    return redirect('planner')


# ==========================================
# CREATOR ANALYTICS
# ==========================================

@login_required
def analytics(request):

    form = AnalyticsForm(
        request.POST if request.method == 'POST' else None
    )

    if request.method == 'POST' and form.is_valid():

        form.save()

        return redirect('analytics')

    records = Analytics.objects.order_by('date')

    return render(request, 'analytics.html', {

        'form': form,
        'records': records,

        'labels': [
            f'{r.platform} {r.date}' for r in records
        ],

        'chart_views': [
            r.views for r in records
        ],

        'chart_likes': [
            r.likes for r in records
        ],

    })


@login_required
@require_POST
def delete_analytics(request, pk):

    record = get_object_or_404(
        Analytics,
        pk=pk
    )

    record.delete()

    return redirect('analytics')
