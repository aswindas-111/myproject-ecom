from django.shortcuts import render,redirect
from django.contrib import messages
from . models import Category,Product,Banner,Category_slider,Author,Testimonial
from django.http.response import JsonResponse
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


# ...START- FUNCTION OF HOME PAGE...
def home(request):
    '''FUNCTION OF HOMEPAGE OF THE WEBSITE'''
    
    # Construct a cache key for the home page
    cache_key = 'home_page_data'
    
    # Try to retrieve the cached data
    cached_data = cache.get(cache_key)

    if cached_data is None:
        # If the data is not in the cache, 
        trending_products = Product.objects.filter(trending=1).select_related('category')
        cate_slider = Category_slider.objects.all()
        authors = Author.objects.all()
        testimonial = Testimonial.objects.filter(status=1)
        banner = Banner.objects.filter(status=1)

        context = {
            'trending_products': trending_products,
            'cate_slider': cate_slider,
            'authors': authors,
            'testimonial': testimonial,
            'banner': banner,
        }

        # Cache the data for future requests
        cache.set(cache_key, context, timeout=10)  # Cache for 10 sec

        return render(request, 'store/index.html', context)
    else:
        # If the data is in the cache,
        return render(request, 'store/index.html', cached_data)
# ...END- FUNCTION OF HOME PAGE...




# ...START- FUNCTION OF AUTHORS...
def get_authors_cache_key():
    return 'authors'

@receiver(post_save, sender=Author)
@receiver(post_delete, sender=Author)
def invalidate_authors_cache(sender, instance, **kwargs):
    cache_key = get_authors_cache_key()
    cache.delete(cache_key)

def authors(request):
    '''AUTHORS'''
    # Check if data is already cached
    authors = cache.get('authors')
    
    if authors is None:
        # If data is not cached, retrieve it from the database
        authors = Author.objects.all()
        
        # Cache the data for future requests
        cache.set('authors', authors, timeout=3600)  # Cache for 1hr
    context = {
        'authors': authors
    }
    
    return render(request, 'store/authors/authors.html', context)
# ...END- FUNCTION OF AUTHORS...




# ...START- FUNCTION OF AUTHORS VIEW PAGE...
def get_author_cache_key(auth_name):
    return f'author_{auth_name}'

@receiver(post_save, sender=Author)
@receiver(post_delete, sender=Author)
def invalidate_author_cache(sender, instance, **kwargs):
    if hasattr(instance, 'name'):
        author_cache_key = get_author_cache_key(instance.name)
        cache.delete(author_cache_key)

def authorsview(request, auth_name):
    '''AUTHORS VIEW PAGE'''
    # Check if the author data is already cached
    author_cache_key = get_author_cache_key(auth_name)
    author = cache.get(author_cache_key)

    if author is None:
        # If data is not cached, retrieve it from the database
        author = Author.objects.filter(name=auth_name).first()

        if author:
            # Cache the author data for future requests
            cache.set(author_cache_key, author, timeout=3600)  # Cache for 1 hr

    if author:
        context = {
            'author': author
        }
        return render(request, 'store/authors/authors_view.html', context)
    else:
        return redirect('authors')
# ...END- FUNCTION OF AUTHORS VIEW PAGE...


    
    
    
# ...START- FUNCTION OF ABOUT US...
def about_us(request):
    '''ABOUT US'''
    # Check if the view is already cached
    cached_response = cache.get('about_us_view')
    
    if cached_response is None:
        # If the view is not cached, render the template
        cached_response = render(request, 'store/footer/about_us.html')

        # Cache the entire view response for future requests
        cache.set('about_us_view', cached_response, timeout=3600)  # Cache for 1 hr

    return cached_response
# ...END- FUNCTION OF ABOUT US...




# ...START-FUNCTION OF CATEGORY OF BOOKS...
def category(request):
    '''FUNCTION OF CATEGORY OF BOOKS'''
    category = Category.objects.filter(status=0)
    context = {
        'category':category
        }
    return render(request,'store/category.html',context)
# ...END-FUNCTION OF CATEGORY OF BOOKS...




# ...START- FUNCTION OF PRODUCTS LISTING OF EACH CATEGORY...
def categoryview(request,name):
    '''FUNCTION OF PRODUCT LISTING'''
    if(Category.objects.filter(name=name,status=0)):                
        # products = Product.objects.filter(category__name=name,status=0)
        products = Product.objects.filter(category__name=name,status=0).select_related('category')
        category = Category.objects.filter(name=name).first()
        context = {
            'products':products,
            'category':category
            }
        return render(request,'store/products/index.html',context)
    else:
        messages.warning(request,"no such category found")
        return redirect('category')
    
# ...END- FUNCTION OF PRODUCTS LISTING OF EACH CATEGORY...

    
    
    
# ...START- FUNCTION OF DETAIL VIEW OF EACH PRODUCT...
@receiver([post_save, post_delete], sender=Category)
@receiver([post_save, post_delete], sender=Product)
def invalidate_cache(sender, instance, **kwargs):
    # Construct the cache key based on the instance's data
    if sender == Category:
        cache_key = f"productview_{instance.name}_"
    elif sender == Product:
        cache_key = f"productview_{instance.category.name}_{instance.name}"

    # Delete the cached result associated with the cache_key
    cache.delete(cache_key)

# Connect the signal handlers
post_save.connect(invalidate_cache, sender=Category)
post_delete.connect(invalidate_cache, sender=Category)
post_save.connect(invalidate_cache, sender=Product)
post_delete.connect(invalidate_cache, sender=Product)

def productview(request, cate_name, prod_name):
    '''DETAIL VIEW OF EACH PRODUCT'''
    # Check if the result is already in the cache
    cache_key = f"productview_{cate_name}_{prod_name}"
    cached_result = cache.get(cache_key)

    if cached_result is not None:
        context = cached_result
    else:
        if Category.objects.filter(name=cate_name, status=0).exists():
            if Product.objects.filter(name=prod_name, status=0).exists():
                products = Product.objects.filter(name=prod_name, status=0).first()
                context = {'products': products}
            else:
                messages.error(request, "No such product found")
                return redirect('category')
        else:
            messages.error(request, "No such category found")
            return redirect('category')

        # Cache the result for future requests
        cache.set(cache_key, context, timeout=3600)  # Cache the result for 1 hour 

    return render(request, 'store/products/view.html', context)
# ...END- FUNCTION OF DETAIL VIEW OF EACH PRODUCT...




# ...START SEARCH PRODUCTS FUNCTION...
def productlistAjax(request):
    '''FUNCTION OF GETTING ALL AVAILABLE PRODUCTS IN DATABASE'''
    products = Product.objects.filter(status=0).values_list('name',flat=True)
    productsList = list(products)
    return JsonResponse(productsList,safe=False)

def searchproduct(request):
    '''SEARCH PRODUCTS'''
    if request.method == "POST":
            searchedterm = request.POST.get('productsearch')
            if searchedterm == "":
                return redirect(request.META.get('HTTP_REFERER'))
            else:
                product = Product.objects.filter(name__contains=searchedterm).first()
                
                if product:
                    return redirect('category'+'/'+product.category.name+'/'+product.name)
                else:
                    messages.info(request,"No product matched your search")
                    return redirect(request.META.get('HTTP_REFERER'))
                    
                
    return redirect(request.META.get('HTTP_REFERER'))   
#to get previous page address
# ...END SEARCH PRODUCTS FUNCTION...