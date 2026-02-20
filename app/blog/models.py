from django import forms
from django.db import models
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail.search import index
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.search_promotions.models import Query

class BlogPostsListPage(Page):
    def get_context(self, request):
        context = super().get_context(request)

        blogpages = (
            self.get_parent()
            .get_children()
            .type(BlogPostPage)
            .live()
            .order_by('-first_published_at')
        )
        tag = request.GET.get('tag')
        if tag:
            blogpages = blogpages.filter(blogpostpage__tags__name=tag)

        context['posts'] = blogpages[:5]

        return context

class BlogIndexPage(Page):
    def get_context(self, request):
        context = super().get_context(request)
        
        context['blogpages'] = (
            self.get_children()
            .type(BlogPostPage)
            .live()
            .order_by('-first_published_at')
        )[:5]

        context['featured_posts'] = (
            self.get_children()
            .type(BlogPostPage)
            .live()
            .filter(blogpostpage__is_featured=True)
            .order_by('-first_published_at')
        )[:4]

        return context

class BlogPostPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'BlogPostPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )

class BlogPostPage(Page):
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    body = RichTextField(blank=True)
    is_featured = models.BooleanField(default=False)
    authors = ParentalManyToManyField('blog.Author', blank=True)
    tags = ClusterTaggableManager(through=BlogPostPageTag, blank=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            "is_featured",
            "date",
            FieldPanel("authors", widget=forms.CheckboxSelectMultiple),
            'tags',
        ], heading="Blog information"),
        "intro", "body", 'gallery_images'
    ]

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    def main_image(self):
        gallery_item = self.gallery_images.first()
        if not gallery_item:
            return None
        return gallery_item.image


class BlogPostPageGalleryImage(Orderable):
    page = ParentalKey(BlogPostPage, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = ["image", "caption"]

class BlogPostSearchPage(Page):
    def get_context(self, request):
        context = super().get_context(request)

        search_query = request.GET.get('query', None)
        if search_query:
            search_results = (
                Page.objects
                .type(BlogPostPage)
                .live()
                .search(search_query)
            )
            # Log the query so Wagtail can suggest promoted results
            Query.get(search_query).add_hit()
        else:
            search_results = Page.objects.none()

        context['search_results'] = search_results
        context['search_query'] = search_query

        return context

@register_snippet
class Author(models.Model):
    name = models.CharField(max_length=255)
    author_image = models.ForeignKey(
        'wagtailimages.Image', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )

    panels = ["name", "author_image"]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'

