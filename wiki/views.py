import os
import markdown
from django.utils.text import slugify
from django.utils.http import urlquote
from markdown.extensions.toc import TocExtension
from django.shortcuts import render
from wiki.models import *
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, FileResponse
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator


@permission_required('wiki.add_post', raise_exception=True)
def wiki_add(request):
    return render(request, 'wiki/wiki_add.html', locals())


@csrf_exempt
def upload_image(request):
    if request.method == 'POST':
        try:
            image_file = UploadImage.objects.create(
                image=request.FILES.get('editormd-image-file')
            )
            return JsonResponse({'success': 1, 'message': "上传成功！", 'url': image_file.image.url})
        except Exception as e:
            return JsonResponse({'success': 0, 'message': '上传失败！{}'.format(e), 'url': None})


@permission_required('wiki.add_post', raise_exception=True)
def wiki_list(request):
    posts = Post.objects.select_related('author')
    paginator_obj = Paginator(posts, 5)
    request_page_num = request.GET.get('page', 1)
    page_obj = paginator_obj.page(request_page_num)
    total_page_number = paginator_obj.num_pages
    page_list = get_pages(int(total_page_number), int(request_page_num))
    return render(request, 'wiki/wiki_list.html', locals())


@permission_required('wiki.add_post', raise_exception=True)
def wiki_view(request, pk):
    post = Post.objects.select_related('author').get(id=pk)
    post.increase_views()
    md = markdown.Markdown(extensions=[
        'markdown.extensions.extra',
        TocExtension(slugify=slugify),
    ])

    post.md_content = md.convert(post.md_content)
    return render(request, 'wiki/wiki_view.html', {'post': post, 'toc': md.toc})


@permission_required('wiki.change_post', raise_exception=True)
def wiki_edit(request, pk):
    post = Post.objects.select_related('author').get(id=pk)
    return render(request, 'wiki/wiki_edit.html', locals())


def get_pages(total_page=1, current_page=1):
    """
    example: get_pages(10,1) result=[1,2,3,4,5]
    example: get_pages(10,9) result=[6,7,8,9,10]
    页码个数由display_page设定
    """
    display_page = 5
    front_offset = int(display_page / 2)
    if display_page % 2 == 1:
        behind_offset = front_offset
    else:
        behind_offset = front_offset - 1

    if total_page < display_page:
        return list(range(1, total_page + 1))
    elif current_page <= front_offset:
        return list(range(1, display_page + 1))
    elif current_page >= total_page - behind_offset:
        start_page = total_page - display_page + 1
        return list(range(start_page, total_page + 1))
    else:
        start_page = current_page - front_offset
        end_page = current_page + behind_offset
        return list(range(start_page, end_page + 1))


@permission_required('wiki.add_wikifile', raise_exception=True)
def wiki_file_list(request):
    if request.method == 'POST':
        try:
            wiki_file = WikiFile.objects.create(
                upload_user=request.user,
                wiki_file=request.FILES.get('upload_wiki_file')
            )
            file_name = wiki_file.wiki_file.name.split('/')[-1]
            res = {
                'code': 200,
                'message': '上传成功！',
                'id': wiki_file.id,
                'file_name': file_name,
                'upload_time': wiki_file.upload_time,
                'upload_user': wiki_file.upload_user.username
            }
            return JsonResponse(res)
        except Exception as e:
            return JsonResponse({'code': 500, 'message': '上传失败！{}'.format(e)})
    else:
        wiki_files = WikiFile.objects.all()
        return render(request, 'wiki/wiki_file.html', locals())


@permission_required('wiki.delete_wikifile', raise_exception=True)
def wiki_file_del(request, pk):
    if request.method == 'DELETE':
        try:
            file = WikiFile.objects.get(id=pk)
            file.delete()
            os.remove(file.wiki_file.path)
            return JsonResponse({'code': 200, 'msg': '删除成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '删除失败！，{}'.format(e)})


def wiki_file_download(request, pk):
    file_obj = WikiFile.objects.get(id=pk)
    file_name = file_obj.wiki_file.name.split('/')[-1]
    file = open(file_obj.wiki_file.path, 'rb')
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{filename}"'.format(filename=urlquote(file_name))
    return response
