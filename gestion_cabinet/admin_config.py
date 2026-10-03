from django.contrib import admin
 
def configure_admin():
    admin.site.site_header = 'Cabinet Dentaire'
    admin.site.site_title = 'Cabinet Dentaire'
    admin.site.index_title = 'Administration' 