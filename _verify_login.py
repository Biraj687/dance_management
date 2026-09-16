import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "manage_project.settings.dev")
django.setup()

from django.test import Client

c = Client()
r = c.get("/accounts/login/")
b = r.content.decode("utf-8", errors="replace")
print("status", r.status_code)
print("white_bg", "'bg-base': '#FFFFFF'" in b)
print("logo_h20", "h-20" in b and "images/logo.png" in b)
print("no_dark", "#2F2E29" not in b and "#3A392F" not in b)

# Main pages after the |abs fix
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username="admin@gmail.com")
c.force_login(user)
for path in ["/students/", "/packages/", "/billing/", "/accounts/profile/"]:
    resp = c.get(path)
    body = resp.content.decode("utf-8", errors="replace")
    print(path, resp.status_code, "no_dark=" + str("#2F2E29" not in body), "custom_css=" + str("custom.css" in body))