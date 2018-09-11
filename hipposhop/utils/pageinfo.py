# -*- coding: utf-8 -*-

class Pagination:
    def __init__(self, request):
        self.page_size = int(request.GET.get('page_size', 50))
        self.page_no = int(request.GET.get('page_no', 1))
        if self.page_no < 1:
            self.page_no = 1
        if self.page_size < 0 or self.page_size > 100:
            self.page_size = 20
        self.start = (self.page_no - 1) * self.page_size
        self.end = self.page_no * self.page_size
