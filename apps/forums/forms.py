from django import forms

from forums.models import Forum
from forums.models import Topic

class ForumForm(forms.ModelForm):
    
    class Meta:
        model = Forum
        fields = ('title', 'body', 'tags')

class TopicForm(forms.ModelForm):
    
    class Meta:
        model = Topic
        fields = ('forum', 'title', 'body', 'tags')

class ForumTopicForm(forms.ModelForm):
    
    class Meta:
        model = Topic
        fields = ('title', 'body', 'tags')
