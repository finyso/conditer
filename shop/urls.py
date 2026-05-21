from django.urls import re_path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    re_path(r'^$', views.home, name='home'),
    re_path(r'^about/$', views.about, name='about'),
    re_path(r'^news/$', views.NewsListView.as_view(), name='news_list'),
    re_path(r'^news/(?P<pk>\d+)/$', views.NewsDetailView.as_view(), name='news_detail'),
    re_path(r'^glossary/$', views.GlossaryListView.as_view(), name='glossary'),
    re_path(r'^contacts/$', views.contacts, name='contacts'),
    re_path(r'^vacancies/$', views.VacancyListView.as_view(), name='vacancies'),
    re_path(r'^reviews/$', views.ReviewListView.as_view(), name='reviews'),
    re_path(r'^reviews/add/$', views.add_review, name='add_review'),
    re_path(r'^promocodes/$', views.PromoCodeListView.as_view(), name='promocodes'),
    re_path(r'^products/$', views.ProductListView.as_view(), name='products'),
    re_path(r'^statistics/$', views.statistics, name='statistics'),
    re_path(r'^privacy/$', views.privacy_policy, name='privacy_policy'),
    
    # Клиентские маршруты
    re_path(r'^orders/$', views.order_list, name='orders'),
    re_path(r'^order/create/$', views.order_create, name='order_create'),
    re_path(r'^cart/$', views.cart_view, name='cart_view'),
    re_path(r'^cart/add/(?P<product_id>\d+)/$', views.add_to_cart, name='add_to_cart'),
    re_path(r'^cart/remove/(?P<product_id>\d+)/$', views.remove_from_cart, name='remove_from_cart'),
    re_path(r'^cart/update/(?P<product_id>\d+)/$', views.update_cart, name='update_cart'),
    
    # Сотруднические маршруты
    re_path(r'^employee/dashboard/$', views.employee_dashboard, name='employee_dashboard'),
    re_path(r'^employee/order/create/$', views.employee_order_create, name='employee_order_create'),
    re_path(r'^employee/order/(?P<order_id>\d+)/$', views.employee_order_detail, name='employee_order_detail'),
    re_path(r'^employee/order/(?P<order_id>\d+)/edit/$', views.employee_order_edit, name='employee_order_edit'),
    re_path(r'^employee/order/(?P<order_id>\d+)/delete/$', views.employee_order_delete, name='employee_order_delete'),
    re_path(r'^employee/clients/$', views.employee_clients, name='employee_clients'),

    re_path(r'^pickup-points/$', views.pickup_points, name='pickup_points'),
    re_path(r'^calendar/$', views.calendar_view, name='calendar'),
    re_path(r'^login/$', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    re_path(r'^logout/$', views.custom_logout, name='logout'),
    re_path(r'^register/$', views.ClientRegistrationView.as_view(), name='register'),
    re_path(r'^redirect-after-login/$', views.redirect_after_login, name='redirect_after_login'),

    # Управление товарами в заказе (для сотрудников)
    re_path(r'^employee/order/(?P<order_id>\d+)/add-item/$', views.employee_order_add_item, name='employee_order_add_item'),
    re_path(r'^employee/order/(?P<order_id>\d+)/edit-item/(?P<item_id>\d+)/$', views.employee_order_edit_item, name='employee_order_edit_item'),
    re_path(r'^employee/order/(?P<order_id>\d+)/delete-item/(?P<item_id>\d+)/$', views.employee_order_delete_item, name='employee_order_delete_item'),

    # Админские маршруты
    re_path(r'^admin-panel/products/$', views.admin_products, name='admin_products'),
    re_path(r'^admin-panel/product/create/$', views.admin_product_create, name='admin_product_create'),
    re_path(r'^admin-panel/product/(?P<product_id>\d+)/edit/$', views.admin_product_edit, name='admin_product_edit'),
    re_path(r'^admin-panel/product/(?P<product_id>\d+)/delete/$', views.admin_product_delete, name='admin_product_delete'),
    re_path(r'^admin-panel/categories/$', views.admin_categories, name='admin_categories'),
    re_path(r'^admin-panel/sales/$', views.admin_sales, name='admin_sales'),
]