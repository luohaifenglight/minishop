
# 操作

## python manage.py
需要指定不同的配置文件：

$>python manage.py shell --settings=hipposhop.settings.dev
$>python manage.py shell --settings=hipposhop.settings.prod




#项目环境

hipposhop项目基于Python3.6 和 Django 2.0.6



##关于requirments

当需要在本地开发环境下运行，安装requirements/dev.txt中的依赖包

当在生产环境下运行我的代码，安装requirements/prod.txt中的依赖包

当做测试的时候，安装requirements/test.txt中的依赖包


## 听云SDK
听云的SDK包需要单独安装：

https://report.tingyun.com/server/download/serverSdk


# 规范

## 环境

### virtualenv命名

hipposhop的virtualenv环境命名如下：

* hipposhop-env

注意： 中间是横线，不是下划线

## 业务逻辑

### 错误代码

业务使用的错误代码需要在hippoconig的错误代码表（ErrorCode）中有定义
注意：要先定义，后使用

## model

### model字段
有可能在运营后台被修改的关键数据，需要有下面字段：
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    

### 开启时区

开启时区支持， USE_TZ = True
要注意UTC和Local时间的转换








