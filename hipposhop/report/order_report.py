# -*- coding: utf-8 -*-
import os
import xlwt

from django.conf import settings
from django.db.models import Q
from order.orderservice import OrderService, OrderState


def set_file_path(pathname):
    base_dir = os.path.abspath(os.path.join(settings.BASE_DIR, ".."))
    data_file_path = os.path.join(base_dir, pathname)
    return data_file_path


class OrderReport(object):
    report_abs_path_excel = None
    report_abs_path_txt = None

    def __init__(self, filename, sheetname, header=None, header_width=None):
        self.filename = filename
        self.sheet_name = sheetname
        self.header = header
        self.header_width = header_width

    def get_jielong_report(self, channel):
        data_file_path = set_file_path("data")
        txt_file = self.filename.replace(".xls", ".txt")
        report_abs_path_excel = os.path.join(data_file_path, self.filename)
        OrderReport.report_abs_path_excel = report_abs_path_excel

        report_abs_path_txt = report_abs_path_excel.replace(self.filename, txt_file)

        OrderReport.report_abs_path_txt = report_abs_path_txt
        filenames = report_abs_path_excel + "," + report_abs_path_txt
        # if os.path.exists(report_abs_path_txt) and os.path.exists(report_abs_path_excel):
        #     return filenames

        self.create_channel_report(channel)
        return filenames

    def get_jielong_order(self, jielong_id):
        """
        根据接龙活动查订单
        :param jielong_id:
        :return:  channel order list
        """
        other_query = ~Q(status__in=[OrderState.REFUNDING, OrderState.REFUNDED])
        order_list = OrderService.order_queryset(jielong_id=jielong_id, other_query=other_query)
        count = order_list.count()
        print("channel:%s order num:%s" % (jielong_id, count))
        return order_list

    def create_channel_report(self, jielong_id):
        order_list = self.get_jielong_order(jielong_id)
        if not order_list:
            return None

        workbook, sheet = self.create_excel_book()
        self.set_sheet_header(sheet, style=self.get_sheet_style())
        self._create_order_report(sheet, order_list)
        workbook.save(OrderReport.report_abs_path_excel)

    def create_excel_book(self):
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet(self.sheet_name)
        workbook.save(OrderReport.report_abs_path_excel)
        return workbook, sheet

    def get_sheet_style(self):
        # 创建对齐配置
        al_normal = xlwt.Alignment()
        al_normal.horz = xlwt.Alignment.HORZ_LEFT | xlwt.Alignment.WRAP_AT_RIGHT
        al_normal.wrap = xlwt.Alignment.WRAP_AT_RIGHT
        al_normal.vert = xlwt.Alignment.VERT_CENTER

        # 创建边框配置
        borders = xlwt.Borders()
        borders.bottom = xlwt.Borders.THICK
        # 创建样式
        sheet_style_normal = xlwt.XFStyle()
        sheet_style_normal.alignment = al_normal
        # sheetStyle.alignment.wrap = 1
        return sheet_style_normal

    def set_sheet_header(self, sheet, style):
        if self.header:
            for i, text in enumerate(self.header):
                sheet.row(0).write(i, text, style=style)
        if self.header_width:
            for j, text in enumerate(self.header_width):
                sheet.col(j).width = int(text)
        default_row_height = sheet.row(0).height
        sheet.row(0).height = default_row_height * 2

    def _create_order_report(self, sheet, data_list, flush_bound=500):
        sheet_style_normal = self.get_sheet_style()
        row_index = 1
        with open(OrderReport.report_abs_path_txt, mode="w", encoding="utf-8") as f:
            for item in data_list:
                order_detail = OrderService.order_detail(item.trade_parent_id)
                string = ""
                for order in order_detail["goods"]:
                    sheet.row(row_index).write(0, str(order_detail["trade_id"]), style=sheet_style_normal)
                    sheet.row(row_index).write(1, order["title"], style=sheet_style_normal)
                    sheet.row(row_index).write(2, str(order["buy_num"]), style=sheet_style_normal)
                    sheet.row(row_index).write(3, str(order["price"]), style=sheet_style_normal)
                    sheet.row(row_index).write(4, order_detail["address"]["receiver"], style=sheet_style_normal)
                    sheet.row(row_index).write(5, str(order_detail["address"]["tel"]), style=sheet_style_normal)
                    sheet.row(row_index).write(6, order_detail["address"]["address"], style=sheet_style_normal)
                    sheet.row(row_index).write(7, order_detail["comment"], style=sheet_style_normal)
                    sheet.row(row_index).write(8, order_detail["seller_comment"], style=sheet_style_normal)
                    # str_item = "姓名: %s。\t电话: %s。\t地址: %s。\t商品名称: %s。\t商品数量: %s\n" % (
                    #     order_detail["address"]["receiver"], order_detail["address"]["tel"], order_detail["address"]["address"], order["title"], str(order["buy_num"])
                    # )
                    str_item = "%s。%s。%s。%s * %s\n" % (
                        order_detail["address"]["receiver"], order_detail["address"]["tel"], order_detail["address"]["address"], order["title"], str(order["buy_num"])
                    )
                    string += str_item
                    row_index += 1

                f.write(string)
                if row_index % flush_bound == 0:
                    sheet.flush_row_data()
                # ToDo
                if row_index >= 65535:
                    # Excel 2003格式最大行数
                    print("Warning: excel reach max row num.")
                    break


