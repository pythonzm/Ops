# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      search_indexes
   Description:
   Author:          Administrator
   date：           2018-11-06
-------------------------------------------------
   Change Activity:
                    2018-11-06:
-------------------------------------------------
"""
from haystack import indexes
from wiki.models import Post


class PostIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Post

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
