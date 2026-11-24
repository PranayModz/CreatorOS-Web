import logging
import re
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, JsonResponse
from django.db.models import Sum
from django.contrib import messages

from .models import SavedContent, ContentPlan, Analytics
from .forms import ContentPlanForm, AnalyticsForm, RegisterForm
from .services import (
    generate_ai_content,
    check_ai_status,
    get_last_provider,
    get_last_model
)


logger = logging.getLogger(__name__)


# ==========================================
# CREATOROS AI TOOLS CONFIGURATION
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
            'content calendar with daily post ideas, '
            'formats, hooks and publishing suggestions.'
        ),
    },

    'script': {
        'name': 'AI Script Generator',
        'instruction': (
            'Generate a professional video script with '
            'a powerful hook, narration, scene breakdown '
            'and call to action. Follow the requested '
            'video duration and language.'
        ),
    },

    'title': {
        'name': 'AI Title Generator',
        'instruction': (
            'Generate 10 engaging SEO-friendly titles. '
            'Use relevant keywords and avoid '
            'misleading clickbait.'
        ),
    },

    'description': {
        'name': 'AI Description Generator',
        'instruction': (
            'Generate a professional social media '
            'description with relevant keywords '
            'and a natural call to action.'
        ),
    },

    'hashtags': {
        'name': 'AI Hashtag Generator',
        'instruction': (
            'Generate 15 relevant hashtags including '
            'niche-specific and broad hashtags. '
            'Avoid unrelated hashtags.'
        ),
    },

    'tags': {
        'name': 'AI Tags Generator',
        'instruction': (
            'Generate 20 relevant search keywords '
            'and video tags in comma-separated format.'
        ),
    },

    'hooks': {
        'name': 'AI Hook Generator',
        'instruction': (
            'Generate 10 short and engaging opening '
            'hooks suitable for the selected platform.'
        ),
    },

    'thumbnail': {
        'name': 'AI Thumbnail Advisor',
        'instruction': (
            'Generate 5 professional thumbnail concepts. '
            'Include headline text, color combinations, '
            'background, composition and visual elements.'
        ),
    },

    'seo': {
        'name': 'AI SEO Analyzer',
        'instruction': (
            'Analyze the supplied content and recommend '
            'SEO improvements, relevant keywords, '
            'titles and descriptions. Never invent '
            'search volume or ranking statistics.'
        ),
    },

    'monetization': {
        'name': 'AI Monetization Advisor',
        'instruction': (
            'Provide practical monetization strategies. '
            'Explain possible revenue sources and '
            'identify eligibility requirements that '
            'need official verification. Never guarantee '
            'income or monetization approval.'
        ),
    },

    'analyzer': {
        'name': 'AI Content Analyzer',
        'instruction': (
            'Analyze the supplied content and identify '
            'strengths, weaknesses, audience retention '
            'opportunities and actionable improvements.'
        ),
    },

    'upload_time': {
        'name': 'AI Upload Time Advisor',
        'instruction': (
            'Recommend publishing times based on '
            'provided audience activity and timezone. '
            'If audience analytics are unavailable, '
            'suggest a posting-time experiment instead '
            'of claiming a guaranteed best time.'
        ),
    },

    'assistant': {
        'name': 'CreatorOS AI Assistant',
        'instruction': (
            'Act as a professional content creator '
            'assistant. Understand the user question '
            'and provide accurate, practical and '
            'step-by-step guidance.'
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

        username = request.POST.get(
            'username', ''
        ).strip()

        password = request.POST.get(
            'password', ''
        )

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

        'ai_tools': TOOLS,

        'ai_tools_count': len(TOOLS),

    }

    return render(
        request,
        'dashboard.html',
        context
    )


# ==========================================
# MULTI-AI CONNECTION STATUS
# ==========================================

@login_required
@require_GET
def ai_status(request):

    status = check_ai_status()

    return JsonResponse(status)


# ==========================================
# CENTRAL AI GENERATION
# ==========================================

@login_required
def ai_tool(request, tool):

    if tool not in TOOLS:

        raise Http404('AI Tool not found')

    config = TOOLS[tool]

    result = ''
    ai_provider = 'Automatic'
    ai_model = ''
    topic = ''
    platform = 'YouTube'
    language = 'English'
    tone = 'Engaging'
    duration = '30 seconds'

    if request.method == 'POST':

        topic = request.POST.get(
            'topic', ''
        ).strip()

        platform = request.POST.get(
            'platform', 'YouTube'
        )

        language = request.POST.get('language', 'English').strip()
        aliases = {
            'hi': 'Hindi', 'hindi': 'Hindi', 'हिंदी': 'Hindi', 'हिन्दी': 'Hindi',
            'mr': 'Marathi', 'marathi': 'Marathi', 'मराठी': 'Marathi',
            'en': 'English', 'english': 'English', 'hinglish': 'Hinglish',
        }
        language = aliases.get(language.casefold(), language or 'English')
        language_rules = {
            'Hindi': 'पूरा उत्तर हिंदी में देवनागरी लिपि में लिखें। शीर्षक और व्याख्या भी हिंदी में हों। Roman Hindi या अंग्रेज़ी में उत्तर न दें।',
            'Marathi': 'संपूर्ण उत्तर मराठीत देवनागरी लिपीत लिहा. शीर्षके आणि स्पष्टीकरण मराठीत असावे.',
            'English': 'Write the entire response in English.',
            'Hinglish': 'Write in natural Hindi-English mix using Roman script.',
        }
        language_instruction = language_rules.get(
            language, f'Write the entire response in {language}.'
        )

        tone = request.POST.get(
            'tone', 'Engaging'
        )

        duration = request.POST.get(
            'duration', '30 seconds'
        )

        action = request.POST.get(
            'action', 'generate'
        )

        # ==================================
        # SAVE GENERATED CONTENT
        # ==================================

        if action == 'save':

            content = request.POST.get(
                'result', ''
            ).strip()

            result = content

            if topic and content:

                SavedContent.objects.create(

                    title=topic[:255],

                    module=config['name'],

                    prompt=topic,

                    content=content

                )

                messages.success(
                    request,
                    'AI content saved successfully!'
                )

                return redirect('saved_content')

            messages.error(
                request,
                'Content cannot be empty.'
            )

        # ==================================
        # VALIDATE USER INPUT
        # ==================================

        elif not topic or len(topic) > 4000:

            messages.error(
                request,
                'Enter a topic between 1 and 4000 characters.'
            )

        # ==================================
        # GENERATE CONTENT USING AUTOMATIC AI FALLBACK
        # ==================================

        else:

            prompt = f"""
You are CreatorOS AI, an expert digital content
creator and social media strategist.

Selected AI Tool:
{config['name']}

Your Task:
{config['instruction']}

User Requirements:
{topic}

Target Platform:
{platform}

Output Language:
{language}

MANDATORY LANGUAGE RULE:
{language_instruction}
Use this language even if the topic is written in English.

Content Tone:
{tone}

Video Duration:
{duration}

Important Instructions:

1. Follow the selected language.
2. Follow the user requirements.
3. Use the requested content tone.
4. Follow video duration when relevant.
5. Generate original and practical content.
6. Use clear headings when appropriate.
7. Avoid unnecessary introductions.
8. Never invent analytics or live trends.
9. Never guarantee views or earnings.
10. Prioritize quality and accuracy.

Generate the requested content now.
Remember: {language_instruction}
"""

            try:

                result = generate_ai_content(prompt)

                # Retry once if Hindi/Marathi output has no Devanagari.
                if language in ('Hindi', 'Marathi') and not re.search(r'[\u0900-\u097F]', result):
                    result = generate_ai_content(
                        f"{language_instruction}\n"
                        f"Rewrite the following answer in {language}, preserving its meaning:\n{result}"
                    )
                    if not re.search(r'[\u0900-\u097F]', result):
                        result = ''
                        raise ValueError(
                            f'AI could not generate {language} output. Try again or use a stronger model.'
                        )

                ai_provider = get_last_provider()
                ai_model = get_last_model()

                messages.success(
                    request,
                    f'AI content generated successfully using {ai_provider}!'
                )

            except ValueError as error:

                result = ''
                messages.error(
                    request,
                    str(error)
                )

            except Exception:

                result = ''
                logger.exception(
                    'CreatorOS AI generation failed'
                )

                messages.error(
                    request,
                    'AI generation failed. '
                    'Please try again later.'
                )

    return render(request, 'ai_tool.html', {

        'tool_name': config['name'],

        'tool': tool,

        'result': result,

        'topic': topic,

        'platform': platform,

        'language': language,

        'tone': tone,

        'duration': duration,

        'ai_provider': ai_provider,
        'ai_model': ai_model,

        'ai_tools': TOOLS,

    })


# ==========================================
# SAVED CONTENT
# ==========================================

@login_required
def saved_content(request):

    query = request.GET.get(
        'q', ''
    ).strip()

    items = SavedContent.objects.filter(
        title__icontains=query
    ).order_by('-created_at')

    return render(request, 'saved_content.html', {

        'items': items,

        'query': query,

    })


# ==========================================
# EDIT SAVED CONTENT
# ==========================================

@login_required
def edit_content(request, pk):

    item = get_object_or_404(
        SavedContent,
        pk=pk
    )

    if request.method == 'POST':

        title = request.POST.get(
            'title', ''
        ).strip()

        content = request.POST.get(
            'content', ''
        ).strip()

        if title and content:

            item.title = title[:255]

            item.content = content

            item.save()

            messages.success(
                request,
                'Content updated successfully!'
            )

            return redirect('saved_content')

        messages.error(
            request,
            'Title and content cannot be empty.'
        )

    return render(request, 'edit_content.html', {

        'item': item

    })


# ==========================================
# DELETE SAVED CONTENT
# ==========================================

@login_required
@require_POST
def delete_content(request, pk):

    item = get_object_or_404(
        SavedContent,
        pk=pk
    )

    item.delete()

    messages.success(
        request,
        'Content deleted successfully!'
    )

    return redirect('saved_content')


# ==========================================
# SOCIAL MEDIA PLANNER
# ==========================================

@login_required
def planner(request):

    form = ContentPlanForm(

        request.POST
        if request.method == 'POST'
        else None

    )

    if request.method == 'POST' and form.is_valid():

        form.save()

        messages.success(
            request,
            'Content plan created successfully!'
        )

        return redirect('planner')

    plans = ContentPlan.objects.order_by(
        'publish_date'
    )

    return render(request, 'planner.html', {

        'form': form,

        'plans': plans,

    })


# ==========================================
# EDIT CONTENT PLAN
# ==========================================

@login_required
def edit_plan(request, pk):

    plan = get_object_or_404(
        ContentPlan,
        pk=pk
    )

    form = ContentPlanForm(

        request.POST
        if request.method == 'POST'
        else None,

        instance=plan

    )

    if request.method == 'POST' and form.is_valid():

        form.save()

        messages.success(
            request,
            'Content plan updated successfully!'
        )

        return redirect('planner')

    return render(request, 'edit_plan.html', {

        'form': form,

        'plan': plan,

    })


# ==========================================
# DELETE CONTENT PLAN
# ==========================================

@login_required
@require_POST
def delete_plan(request, pk):

    plan = get_object_or_404(
        ContentPlan,
        pk=pk
    )

    plan.delete()

    messages.success(
        request,
        'Content plan deleted successfully!'
    )

    return redirect('planner')


# ==========================================
# CREATOR ANALYTICS
# ==========================================

@login_required
def analytics(request):

    form = AnalyticsForm(

        request.POST
        if request.method == 'POST'
        else None

    )

    if request.method == 'POST' and form.is_valid():

        form.save()

        messages.success(
            request,
            'Analytics record added successfully!'
        )

        return redirect('analytics')

    records = Analytics.objects.order_by('date')

    return render(request, 'analytics.html', {

        'form': form,

        'records': records,

        'labels': [
            f'{r.platform} {r.date}'
            for r in records
        ],

        'chart_views': [
            r.views
            for r in records
        ],

        'chart_likes': [
            r.likes
            for r in records
        ],

    })


# ==========================================
# DELETE ANALYTICS
# ==========================================

@login_required
@require_POST
def delete_analytics(request, pk):

    record = get_object_or_404(
        Analytics,
        pk=pk
    )

    record.delete()

    messages.success(
        request,
        'Analytics record deleted successfully!'
    )

    return redirect('analytics')
