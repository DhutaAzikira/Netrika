from django.contrib import admin

import admin_app.models

admin.site.register(admin_app.models.Packages)
admin.site.register(admin_app.models.Transactions)
admin.site.register(admin_app.models.Subscriptions)
admin.site.register(admin_app.models.SystemSetting)
